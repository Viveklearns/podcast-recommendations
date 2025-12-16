from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re
from typing import List, Dict, Optional
import logging
import requests

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for fetching YouTube video information and transcripts"""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]*)',
            r'youtube\.com\/embed\/([^&\n?]*)',
            r'youtube\.com\/v\/([^&\n?]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def get_video_duration(video_id: str) -> Optional[int]:
        """
        Fetch video duration from YouTube (in seconds)
        Uses web scraping to extract duration from HTML
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Extract duration from ytInitialPlayerResponse JSON in HTML
            match = re.search(r'"lengthSeconds":"(\d+)"', response.text)
            if match:
                duration_seconds = int(match.group(1))
                logger.info(f"Video duration for {video_id}: {duration_seconds}s ({duration_seconds/60:.1f} min)")
                return duration_seconds

            logger.warning(f"Could not extract duration for video {video_id}")
            return None

        except Exception as e:
            logger.error(f"Error fetching video duration for {video_id}: {str(e)}")
            return None

    @staticmethod
    def get_video_title(video_id: str) -> Optional[str]:
        """
        Fetch video title from YouTube
        Uses web scraping as a simple method without API key requirement
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Extract title from HTML
            # YouTube's title is in the <title> tag
            match = re.search(r'<title>(.+?)</title>', response.text)
            if match:
                title = match.group(1)
                # Remove the " - YouTube" suffix
                title = re.sub(r'\s*-\s*YouTube\s*$', '', title)
                logger.info(f"Extracted title for video {video_id}: {title}")
                return title.strip()

            logger.warning(f"Could not extract title for video {video_id}")
            return None

        except Exception as e:
            logger.error(f"Error fetching video title for {video_id}: {str(e)}")
            return None

    @staticmethod
    def get_transcript(video_id: str) -> Optional[str]:
        """
        Fetch transcript for a YouTube video
        Returns the full transcript as a single string
        """
        try:
            # Create an instance and fetch transcript
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(
                video_id,
                languages=['en', 'en-US', 'en-GB']
            )

            # Combine all transcript snippets into one string
            full_transcript = " ".join([snippet.text for snippet in transcript_result.snippets])

            logger.info(f"Successfully fetched transcript for video {video_id}")
            return full_transcript

        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No English transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {str(e)}")
            return None

    @staticmethod
    def get_transcript_with_verification(video_id: str) -> Optional[Dict]:
        """
        Fetch transcript with completeness verification
        Returns dict with transcript and metadata for quality checks

        Returns:
            Dict with 'transcript' and 'metadata' keys, or None if fetch fails
        """
        try:
            # Fetch actual video duration from YouTube
            video_duration_seconds = YouTubeService.get_video_duration(video_id)

            # Create an instance and fetch transcript
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(
                video_id,
                languages=['en', 'en-US', 'en-GB']
            )

            # Extract all segments
            segments = list(transcript_result.snippets)

            if not segments:
                logger.warning(f"No transcript segments found for video {video_id}")
                return None

            # Verification checks
            total_segments = len(segments)
            first_segment = segments[0]
            last_segment = segments[-1]

            # Calculate total duration covered by transcript
            start_time = first_segment.start
            end_time = last_segment.start + last_segment.duration
            duration_covered = end_time - start_time

            # Combine text
            full_transcript = " ".join([s.text for s in segments])
            char_count = len(full_transcript)
            word_count = len(full_transcript.split())

            # Check for gaps (segments should be continuous)
            gaps = []
            for i in range(len(segments) - 1):
                current_end = segments[i].start + segments[i].duration
                next_start = segments[i + 1].start
                gap = next_start - current_end
                if gap > 2.0:  # Gap larger than 2 seconds
                    gaps.append({
                        'position': i,
                        'gap_seconds': round(gap, 2),
                        'time': round(current_end, 2)
                    })

            # Log verification results
            logger.info(f"Transcript verification for {video_id}:")
            if video_duration_seconds:
                logger.info(f"  - Video duration (YouTube): {video_duration_seconds}s ({video_duration_seconds/60:.1f} minutes)")
            logger.info(f"  - Total segments: {total_segments}")
            logger.info(f"  - First timestamp: {start_time:.2f}s")
            logger.info(f"  - Last timestamp: {end_time:.2f}s")
            logger.info(f"  - Duration covered (transcript): {duration_covered:.2f}s ({duration_covered/60:.1f} minutes)")
            logger.info(f"  - Character count: {char_count:,}")
            logger.info(f"  - Word count: {word_count:,}")
            logger.info(f"  - Gaps found: {len(gaps)}")

            # Check coverage
            if video_duration_seconds:
                coverage_percent = (duration_covered / video_duration_seconds) * 100
                logger.info(f"  - Transcript coverage: {coverage_percent:.1f}%")
                if coverage_percent < 95:
                    logger.warning(f"  - ⚠️ Transcript covers only {coverage_percent:.1f}% of video!")

            if gaps:
                logger.warning(f"  - Large gaps detected at: {[g['time'] for g in gaps[:5]]}")

            # Quality checks
            is_complete = (
                total_segments > 10 and  # At least 10 segments
                char_count > 1000 and    # At least 1000 characters
                len(gaps) < total_segments * 0.1  # Less than 10% gaps
            )

            if not is_complete:
                logger.warning(f"Transcript may be incomplete for {video_id}")

            # Calculate coverage percentage
            coverage_percent = None
            if video_duration_seconds and video_duration_seconds > 0:
                coverage_percent = round((duration_covered / video_duration_seconds) * 100, 1)

            return {
                'transcript': full_transcript,
                'metadata': {
                    'total_segments': total_segments,
                    'start_time': round(start_time, 2),
                    'end_time': round(end_time, 2),
                    'duration_covered_seconds': round(duration_covered, 2),
                    'video_duration_seconds': video_duration_seconds,  # Actual video duration from YouTube
                    'coverage_percent': coverage_percent,  # How much of video has transcript
                    'character_count': char_count,
                    'word_count': word_count,
                    'gaps_detected': len(gaps),
                    'is_complete': is_complete,
                    'gaps': gaps[:10]  # Store first 10 gaps
                }
            }

        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No English transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {str(e)}")
            return None

    @staticmethod
    def get_transcript_with_timestamps(video_id: str) -> Optional[List[Dict]]:
        """
        Fetch transcript with timestamp information
        Returns list of segments with start time, duration, and text
        """
        try:
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(
                video_id,
                languages=['en', 'en-US', 'en-GB']
            )

            # Convert snippets to dictionaries
            transcript_list = [
                {
                    'text': snippet.text,
                    'start': snippet.start,
                    'duration': snippet.duration
                }
                for snippet in transcript_result.snippets
            ]

            logger.info(f"Successfully fetched timestamped transcript for video {video_id}")
            return transcript_list

        except Exception as e:
            logger.error(f"Error fetching timestamped transcript for {video_id}: {str(e)}")
            return None

    @staticmethod
    def search_channel_videos(channel_handle: str, max_results: int = 10) -> List[Dict]:
        """
        Search for recent videos from a channel
        Note: This is a simplified version. For production, use YouTube Data API.

        For now, returns a placeholder. You'll need to manually provide video URLs
        or implement YouTube Data API integration.
        """
        # TODO: Implement with YouTube Data API if needed
        # For now, we'll manually provide Lenny's recent video URLs
        logger.warning("Channel video search not implemented. Use manual video URLs.")
        return []

    @staticmethod
    def chunk_transcript(transcript: str, chunk_size: int = 8000, overlap: int = 500) -> List[str]:
        """
        Split a long transcript into smaller chunks for processing

        Args:
            transcript: Full transcript text
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        if len(transcript) <= chunk_size:
            return [transcript]

        chunks = []
        start = 0

        while start < len(transcript):
            end = start + chunk_size

            # Try to break at a sentence boundary
            if end < len(transcript):
                # Look for sentence ending punctuation
                last_period = transcript.rfind('.', start, end)
                last_question = transcript.rfind('?', start, end)
                last_exclaim = transcript.rfind('!', start, end)

                break_point = max(last_period, last_question, last_exclaim)
                if break_point > start:
                    end = break_point + 1

            chunks.append(transcript[start:end].strip())
            start = end - overlap if end < len(transcript) else end

        return chunks
