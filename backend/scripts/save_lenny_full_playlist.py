#!/usr/bin/env python3
"""
Save ALL Lenny's Podcast episodes from YouTube playlist
Uses web scraping to get relative dates like "2 days ago", "1 month ago"
and converts them to approximate dates based on current date (Nov 2025)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import re
from datetime import datetime, timedelta
from app.models.podcast import Podcast
from app.models.episode import Episode
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_guest_from_title(title):
    """Extract guest name from title"""
    # Pattern 1: '| Guest Name (Company)' or '| Guest Name'
    match = re.search(r'\|\s*([^(]+?)(?:\s*\(|$)', title)
    if match:
        guest = match.group(1).strip()
        guest = re.sub(r'\s+(co-founder|CEO|founder|VP|Chief|CTO|CPO).*$', '', guest, flags=re.IGNORECASE)
        return guest.strip()

    # Pattern 2: 'with Guest Name'
    match = re.search(r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', title)
    if match:
        return match.group(1).strip()

    return ''


def parse_relative_date(relative_text):
    """
    Convert relative date like '2 days ago', '1 month ago', '3 years ago'
    to approximate datetime based on November 2025
    """
    # Reference date: November 18, 2025 (today according to your system)
    reference_date = datetime(2025, 11, 18)

    if not relative_text:
        return reference_date

    relative_text = relative_text.lower().strip()

    # Extract number
    number_match = re.search(r'(\d+)', relative_text)
    number = int(number_match.group(1)) if number_match else 1

    if 'day' in relative_text:
        return reference_date - timedelta(days=number)
    elif 'week' in relative_text:
        return reference_date - timedelta(weeks=number)
    elif 'month' in relative_text:
        # Approximate: 1 month = 30 days
        return reference_date - timedelta(days=number * 30)
    elif 'year' in relative_text:
        # Approximate: 1 year = 365 days
        return reference_date - timedelta(days=number * 365)
    elif 'hour' in relative_text:
        return reference_date - timedelta(hours=number)
    else:
        # If we can't parse it, return reference date
        return reference_date


def fetch_all_playlist_videos(playlist_url):
    """Fetch ALL videos from YouTube playlist with relative dates"""

    logger.info(f'Fetching ALL videos from playlist...')
    logger.info(f'Scraping YouTube to get relative dates (e.g., "2 months ago")...\n')

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

        response = requests.get(playlist_url, headers=headers, timeout=15)

        # Extract ytInitialData
        match = re.search(r'var ytInitialData = ({.*?});', response.text)
        if not match:
            logger.error('Could not find ytInitialData')
            return []

        data = json.loads(match.group(1))

        # Navigate to playlist videos
        contents = (data.get('contents', {})
                       .get('twoColumnBrowseResultsRenderer', {})
                       .get('tabs', [])[0]
                       .get('tabRenderer', {})
                       .get('content', {})
                       .get('sectionListRenderer', {})
                       .get('contents', [])[0]
                       .get('itemSectionRenderer', {})
                       .get('contents', [])[0]
                       .get('playlistVideoListRenderer', {})
                       .get('contents', []))

        videos = []
        for item in contents:
            if 'playlistVideoRenderer' not in item:
                continue

            video = item['playlistVideoRenderer']
            video_id = video.get('videoId')
            title_runs = video.get('title', {}).get('runs', [])
            title = title_runs[0].get('text', '') if title_runs else ''

            # Extract relative date from videoInfo
            video_info = video.get('videoInfo', {})
            info_runs = video_info.get('runs', [])

            # Find the relative date (usually last item after views)
            relative_date_text = ''
            for run in info_runs:
                text = run.get('text', '')
                if 'ago' in text.lower():
                    relative_date_text = text
                    break

            if video_id and title:
                guest = extract_guest_from_title(title)
                published_date = parse_relative_date(relative_date_text)

                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'guest': guest,
                    'published_date': published_date,
                    'relative_date': relative_date_text
                })

        logger.info(f'✅ Fetched {len(videos)} videos from first page')
        logger.info(f'Note: YouTube playlist pages only show ~100 videos at a time')
        logger.info(f'For all 294 episodes, we\'ll need to use continuation tokens or yt-dlp\n')

        return videos

    except Exception as e:
        logger.error(f'Error fetching playlist: {e}')
        import traceback
        traceback.print_exc()
        return []


def main():
    playlist_url = 'https://www.youtube.com/playlist?list=PL2fLjt2dG0N6unOOF3nHWYGcJJIQR1NKm'

    # Fetch ALL videos
    videos = fetch_all_playlist_videos(playlist_url)

    if not videos:
        logger.error('No videos found!')
        return

    logger.info(f'\n{"="*80}')
    logger.info(f'Found {len(videos)} episodes from Lenny\'s Podcast playlist')
    logger.info(f'{"="*80}\n')

    # Save to database
    db = SessionLocal()
    try:
        # Get or create podcast
        podcast = db.query(Podcast).filter(Podcast.name == "Lenny's Podcast").first()

        if not podcast:
            logger.info("Creating Lenny's Podcast entry...")
            podcast = Podcast(
                name="Lenny's Podcast",
                youtube_channel_id='@LennysPodcast',
                category='Product Management & Startups',
                image_url='https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400',
                last_fetched_at=datetime.utcnow()
            )
            db.add(podcast)
            db.commit()
            db.refresh(podcast)

        new_count = 0
        existing_count = 0

        for i, video in enumerate(videos):
            # Check if already exists
            existing = db.query(Episode).filter(Episode.youtube_url == video['url']).first()

            if existing:
                existing_count += 1
                if (i+1) % 50 == 0:  # Log progress every 50
                    logger.info(f'Processed {i+1}/{len(videos)} episodes...')
                continue

            # Create new episode
            episode = Episode(
                podcast_id=podcast.id,
                title=video['title'],
                description='',
                published_date=video['published_date'] or datetime.now(),
                youtube_url=video['url'],
                transcript_source='youtube',
                processing_status='pending',
                guest_names=[video['guest']] if video['guest'] else []
            )

            db.add(episode)
            new_count += 1

            if new_count <= 10 or (i+1) % 50 == 0:  # Show first 10 and progress
                logger.info(f'{i+1}. ✅ Added: {video["title"][:60]}...')
                logger.info(f'   Guest: {video["guest"] or "Unknown"}')
                logger.info(f'   Relative: {video.get("relative_date", "Unknown")}')
                if video['published_date']:
                    logger.info(f'   Date: {video["published_date"].strftime("%Y-%m-%d")}')
                logger.info('')

        db.commit()

        logger.info(f'\n{"="*80}')
        logger.info('SUMMARY')
        logger.info(f'{"="*80}')
        logger.info(f'New episodes added: {new_count}')
        logger.info(f'Already in database: {existing_count}')
        logger.info(f'Total discovered: {len(videos)}')
        logger.info(f'{"="*80}\n')

    except Exception as e:
        logger.error(f'Error: {e}')
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
