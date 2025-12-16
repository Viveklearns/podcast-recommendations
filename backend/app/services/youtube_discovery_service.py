"""
YouTube Channel Discovery Service

This service discovers recent videos from YouTube channels using:
1. YouTube Data API v3 (if API key is available)
2. RSS feed fallback (no API key needed)
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re
from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeDiscoveryService:
    """Service for discovering recent videos from YouTube channels"""

    def __init__(self):
        self.youtube_api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        # Don't use API if key is a placeholder
        self.use_api = (
            bool(self.youtube_api_key) and
            self.youtube_api_key != 'your_youtube_api_key_here' and
            not self.youtube_api_key.startswith('your_')
        )

    def get_channel_id_from_handle(self, handle: str) -> Optional[str]:
        """
        Convert channel handle to channel ID

        Args:
            handle: YouTube channel handle (e.g., '@LennysPodcast')

        Returns:
            Channel ID or None if not found
        """
        # Remove @ if present
        handle = handle.lstrip('@')

        # Channel ID mapping for known podcasts
        known_channels = {
            'LennysPodcast': 'UCM0iyU9Qt7cwckQxv7Veilg',
            'lennys podcast': 'UCM0iyU9Qt7cwckQxv7Veilg',
            'timferriss': 'UCznv7Vf9nBdJYvBagFdAHWw',
            'tim ferriss': 'UCznv7Vf9nBdJYvBagFdAHWw',
            'hubermanlab': 'UC2D2CMWXMOVWx7giW1n3LIg',
            'joerogan': 'UCzQUP1qoWDoEbmsQxvdjxgQ',
            'TheDiaryOfACEO': 'UCdWVvn47tFLD6BnHa8c7_DA',
        }

        # Try exact match first
        if handle in known_channels:
            return known_channels[handle]

        # Try case-insensitive match
        for key, value in known_channels.items():
            if key.lower() == handle.lower():
                return value

        # If API is available, try to fetch channel ID
        if self.use_api:
            return self._fetch_channel_id_from_api(handle)

        logger.warning(f"Could not find channel ID for handle: {handle}")
        return None

    def _fetch_channel_id_from_api(self, handle: str) -> Optional[str]:
        """Fetch channel ID using YouTube Data API"""
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': handle,
                'type': 'channel',
                'key': self.youtube_api_key,
                'maxResults': 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('items'):
                channel_id = data['items'][0]['id']['channelId']
                logger.info(f"Found channel ID for {handle}: {channel_id}")
                return channel_id

        except Exception as e:
            logger.error(f"Error fetching channel ID from API: {e}")

        return None

    def discover_recent_videos(
        self,
        channel_handle: str,
        months_back: int = 6,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Discover recent videos from a YouTube channel

        Args:
            channel_handle: Channel handle (e.g., '@LennysPodcast')
            months_back: How many months back to search (default: 6)
            max_results: Maximum number of videos to return

        Returns:
            List of video metadata dictionaries
        """
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=30 * months_back)

        if self.use_api:
            logger.info(f"Using YouTube Data API to discover videos from {channel_handle}")
            channel_id = self.get_channel_id_from_handle(channel_handle)
            if not channel_id:
                logger.error(f"Could not find channel ID for {channel_handle}")
                return []
            return self._discover_via_api(channel_id, date_threshold, max_results)
        else:
            logger.info(f"Using RSS/web scraping to discover videos from {channel_handle}")
            # For RSS/scraping, pass the original handle
            return self._discover_via_rss_or_scrape(channel_handle, date_threshold, max_results)

    def _discover_via_rss_or_scrape(
        self,
        channel_handle: str,
        date_threshold: datetime,
        max_results: int
    ) -> List[Dict]:
        """Try RSS first, then fallback to web scraping"""
        # Try web scraping first (more reliable)
        videos = self._discover_via_web_scrape(channel_handle, date_threshold, max_results)

        if videos:
            return videos

        # Fallback to RSS with channel ID
        channel_id = self.get_channel_id_from_handle(channel_handle)
        if channel_id:
            return self._discover_via_rss(channel_id, date_threshold, max_results)

        return []

    def _discover_via_api(
        self,
        channel_id: str,
        date_threshold: datetime,
        max_results: int
    ) -> List[Dict]:
        """Discover videos using YouTube Data API v3"""
        try:
            url = "https://www.googleapis.com/youtube/v3/search"

            videos = []
            page_token = None

            while len(videos) < max_results:
                params = {
                    'part': 'snippet',
                    'channelId': channel_id,
                    'maxResults': min(50, max_results - len(videos)),
                    'order': 'date',
                    'type': 'video',
                    'key': self.youtube_api_key,
                    'publishedAfter': date_threshold.isoformat() + 'Z'
                }

                if page_token:
                    params['pageToken'] = page_token

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for item in data.get('items', []):
                    video_data = self._parse_api_video(item)
                    if video_data and self._is_valid_episode(video_data):
                        videos.append(video_data)

                page_token = data.get('nextPageToken')
                if not page_token:
                    break

            logger.info(f"Discovered {len(videos)} videos via API")
            return videos[:max_results]

        except Exception as e:
            logger.error(f"Error discovering videos via API: {e}")
            return []

    def _discover_via_rss(
        self,
        channel_id: str,
        date_threshold: datetime,
        max_results: int
    ) -> List[Dict]:
        """Discover videos using YouTube RSS feed (no API key required)"""
        try:
            # Try both channel_id and user formats
            rss_urls = [
                f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                f"https://www.youtube.com/feeds/videos.xml?user={channel_id}"
            ]

            feed = None
            for rss_url in rss_urls:
                logger.debug(f"Trying RSS URL: {rss_url}")
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    logger.info(f"Successfully fetched RSS feed from {rss_url}")
                    break

            if not feed or not feed.entries:
                logger.warning("No entries found in RSS feed, trying web scraping...")
                return self._discover_via_web_scrape(channel_id, date_threshold, max_results)

            videos = []
            for entry in feed.entries[:max_results * 2]:  # Get more to account for filtering
                video_data = self._parse_rss_video(entry)

                if not video_data:
                    continue

                # Check if video is within date range
                try:
                    published_date = datetime.fromisoformat(video_data['published_date'].replace('Z', '+00:00'))
                    if published_date.replace(tzinfo=None) < date_threshold:
                        continue
                except Exception as e:
                    logger.debug(f"Error parsing date: {e}")
                    continue

                # Filter out shorts and clips
                if self._is_valid_episode(video_data):
                    videos.append(video_data)
                    if len(videos) >= max_results:
                        break

            logger.info(f"Discovered {len(videos)} videos via RSS feed")
            return videos

        except Exception as e:
            logger.error(f"Error discovering videos via RSS: {e}")
            # Fallback to web scraping
            return self._discover_via_web_scrape(channel_id, date_threshold, max_results)

    def _discover_via_web_scrape(
        self,
        channel_handle: str,
        date_threshold: datetime,
        max_results: int
    ) -> List[Dict]:
        """
        Discover videos by scraping YouTube channel page
        This is a fallback when RSS doesn't work
        """
        try:
            # Remove @ if present
            handle = channel_handle.lstrip('@')

            # Try channel URL
            url = f"https://www.youtube.com/{handle}/videos"

            logger.info(f"Scraping channel page: {url}")

            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            html = response.text

            # Extract video IDs and titles from the page
            # YouTube embeds video data in ytInitialData JSON

            # Method 1: Extract from ytInitialData
            yt_initial_data_match = re.search(r'var ytInitialData = ({.*?});', html)
            if yt_initial_data_match:
                try:
                    import json
                    yt_data = json.loads(yt_initial_data_match.group(1))
                    videos = self._parse_yt_initial_data(yt_data, max_results)
                    if videos:
                        logger.info(f"Discovered {len(videos)} videos via ytInitialData")
                        return videos
                except Exception as e:
                    logger.debug(f"Failed to parse ytInitialData: {e}")

            # Method 2: Fallback to regex patterns
            video_pattern = r'"videoId":"([^"]+)"'
            title_pattern = r'"title":{"runs":\[{"text":"([^"]+)"}]'

            video_ids = re.findall(video_pattern, html)
            titles = re.findall(title_pattern, html)

            # Remove duplicates while preserving order
            seen = set()
            unique_videos = []
            for vid_id, title in zip(video_ids[:max_results * 3], titles[:max_results * 3]):
                if vid_id not in seen and len(title) > 10:  # Filter out UI elements
                    seen.add(vid_id)
                    unique_videos.append({
                        'video_id': vid_id,
                        'youtube_url': f"https://www.youtube.com/watch?v={vid_id}",
                        'title': title,
                        'description': '',
                        'published_date': datetime.now().isoformat(),  # Approximate
                        'thumbnail_url': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        'channel_title': handle
                    })

            # Filter valid episodes
            videos = [v for v in unique_videos if self._is_valid_episode(v)][:max_results]

            logger.info(f"Discovered {len(videos)} videos via web scraping")
            return videos

        except Exception as e:
            logger.error(f"Error discovering videos via web scraping: {e}")
            return []

    def _parse_yt_initial_data(self, yt_data: dict, max_results: int) -> List[Dict]:
        """Parse video data from YouTube's ytInitialData"""
        try:
            videos = []

            # Navigate through YouTube's data structure
            tabs = yt_data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])

            for tab in tabs:
                tab_renderer = tab.get('tabRenderer', {})
                if tab_renderer.get('selected'):
                    content = tab_renderer.get('content', {})
                    section_list = content.get('richGridRenderer', {}).get('contents', [])

                    for item in section_list:
                        video_renderer = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})

                        if video_renderer:
                            video_id = video_renderer.get('videoId')
                            title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text', '')

                            if video_id and title:
                                videos.append({
                                    'video_id': video_id,
                                    'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                                    'title': title,
                                    'description': '',
                                    'published_date': datetime.now().isoformat(),
                                    'thumbnail_url': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                                    'channel_title': ''
                                })

                                if len(videos) >= max_results:
                                    break

            # Filter valid episodes
            return [v for v in videos if self._is_valid_episode(v)][:max_results]

        except Exception as e:
            logger.debug(f"Error parsing ytInitialData: {e}")
            return []

    def _parse_api_video(self, item: Dict) -> Optional[Dict]:
        """Parse video data from API response"""
        try:
            snippet = item.get('snippet', {})
            video_id = item.get('id', {}).get('videoId')

            if not video_id:
                return None

            return {
                'video_id': video_id,
                'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'published_date': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'channel_title': snippet.get('channelTitle', '')
            }
        except Exception as e:
            logger.error(f"Error parsing API video data: {e}")
            return None

    def _parse_rss_video(self, entry) -> Optional[Dict]:
        """Parse video data from RSS feed entry"""
        try:
            # Extract video ID from link
            video_id = entry.yt_videoid if hasattr(entry, 'yt_videoid') else None

            if not video_id and entry.link:
                # Try to extract from URL
                match = re.search(r'watch\?v=([^&]+)', entry.link)
                if match:
                    video_id = match.group(1)

            if not video_id:
                return None

            return {
                'video_id': video_id,
                'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                'title': entry.title if hasattr(entry, 'title') else '',
                'description': entry.summary if hasattr(entry, 'summary') else '',
                'published_date': entry.published if hasattr(entry, 'published') else '',
                'thumbnail_url': entry.media_thumbnail[0]['url'] if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail else '',
                'channel_title': entry.author if hasattr(entry, 'author') else ''
            }
        except Exception as e:
            logger.error(f"Error parsing RSS video data: {e}")
            return None

    def _is_valid_episode(self, video_data: Dict) -> bool:
        """
        Filter out shorts, clips, and other non-episode content

        Returns True if this appears to be a full episode
        """
        title = video_data.get('title', '').lower()
        description = video_data.get('description', '').lower()

        # Filter out YouTube Shorts (typically under 60 seconds)
        if '#shorts' in title or '#shorts' in description:
            return False

        # Filter out clips (common keywords)
        clip_keywords = [
            'clip', 'highlight', 'teaser', 'trailer',
            'preview', 'snippet', 'shorts', 'announcement'
        ]

        for keyword in clip_keywords:
            if keyword in title:
                # Allow "clip" if it's part of a longer word
                if keyword == 'clip' and re.search(r'\bclip\b', title):
                    return False
                elif keyword != 'clip':
                    return False

        # Must have a substantial title
        if len(title) < 10:
            return False

        return True

    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific video

        Args:
            video_id: YouTube video ID

        Returns:
            Video details dictionary
        """
        if self.use_api:
            return self._get_video_details_api(video_id)
        else:
            # For RSS method, we already have basic details
            # Just return what we can construct
            return {
                'video_id': video_id,
                'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
            }

    def _get_video_details_api(self, video_id: str) -> Optional[Dict]:
        """Get video details using YouTube Data API"""
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': video_id,
                'key': self.youtube_api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get('items'):
                return None

            item = data['items'][0]
            snippet = item.get('snippet', {})
            content_details = item.get('contentDetails', {})
            statistics = item.get('statistics', {})

            # Parse ISO 8601 duration to seconds
            duration_str = content_details.get('duration', 'PT0S')
            duration_seconds = self._parse_duration(duration_str)

            return {
                'video_id': video_id,
                'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'published_date': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'duration_seconds': duration_seconds,
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'channel_title': snippet.get('channelTitle', '')
            }

        except Exception as e:
            logger.error(f"Error fetching video details from API: {e}")
            return None

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration to seconds

        Example: 'PT1H23M45S' -> 5025 seconds
        """
        try:
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
            if not match:
                return 0

            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)

            return hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            logger.error(f"Error parsing duration {duration_str}: {e}")
            return 0

    def get_playlist_videos(
        self,
        playlist_url: str,
        min_duration_seconds: int = 0,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Get videos from a YouTube playlist

        Args:
            playlist_url: YouTube playlist URL
            min_duration_seconds: Minimum video duration (e.g., 3600 for 60 minutes)
            max_results: Maximum number of videos to return

        Returns:
            List of video metadata dictionaries
        """
        # Extract playlist ID
        playlist_id = self._extract_playlist_id(playlist_url)
        if not playlist_id:
            logger.error(f"Could not extract playlist ID from URL: {playlist_url}")
            return []

        logger.info(f"Fetching videos from playlist: {playlist_id}")

        # Try to scrape playlist page
        videos = self._scrape_playlist(playlist_id, min_duration_seconds, max_results)

        return videos

    def _extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL"""
        patterns = [
            r'list=([^&]+)',
            r'playlist\?list=([^&]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _scrape_playlist(
        self,
        playlist_id: str,
        min_duration_seconds: int,
        max_results: int
    ) -> List[Dict]:
        """Scrape playlist page to get video list"""
        try:
            url = f"https://www.youtube.com/playlist?list={playlist_id}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            html = response.text

            # Extract ytInitialData
            yt_initial_data_match = re.search(r'var ytInitialData = ({.*?});', html)
            if not yt_initial_data_match:
                logger.error("Could not find ytInitialData in playlist page")
                return []

            import json
            yt_data = json.loads(yt_initial_data_match.group(1))

            # Navigate to playlist video renderer
            videos = []
            try:
                contents = (
                    yt_data.get('contents', {})
                    .get('twoColumnBrowseResultsRenderer', {})
                    .get('tabs', [{}])[0]
                    .get('tabRenderer', {})
                    .get('content', {})
                    .get('sectionListRenderer', {})
                    .get('contents', [{}])[0]
                    .get('itemSectionRenderer', {})
                    .get('contents', [{}])[0]
                    .get('playlistVideoListRenderer', {})
                    .get('contents', [])
                )

                for item in contents:
                    video_renderer = item.get('playlistVideoRenderer', {})
                    if not video_renderer:
                        continue

                    video_id = video_renderer.get('videoId')
                    title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text', '')

                    # Get duration from lengthText
                    length_text = video_renderer.get('lengthText', {}).get('simpleText', '')
                    duration_seconds = self._parse_length_text(length_text)

                    if not video_id or not title:
                        continue

                    # Filter by minimum duration
                    if min_duration_seconds > 0 and duration_seconds < min_duration_seconds:
                        logger.debug(f"Skipping {title} (duration: {duration_seconds}s < {min_duration_seconds}s)")
                        continue

                    videos.append({
                        'video_id': video_id,
                        'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': title,
                        'description': '',
                        'published_date': datetime.now().isoformat(),
                        'duration_seconds': duration_seconds,
                        'thumbnail_url': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        'channel_title': ''
                    })

                    if len(videos) >= max_results:
                        break

                logger.info(f"Found {len(videos)} videos (60+ minutes) in playlist")
                return videos

            except Exception as e:
                logger.error(f"Error parsing playlist data: {e}")
                return []

        except Exception as e:
            logger.error(f"Error scraping playlist: {e}")
            return []

    def _parse_length_text(self, length_text: str) -> int:
        """
        Parse YouTube length text to seconds

        Examples:
            '1:23:45' -> 5025 seconds
            '23:45' -> 1425 seconds
            '5:30' -> 330 seconds
        """
        try:
            parts = length_text.split(':')
            if len(parts) == 3:  # H:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 1:  # SS
                return int(parts[0])
            return 0
        except Exception as e:
            logger.debug(f"Error parsing length text '{length_text}': {e}")
            return 0
