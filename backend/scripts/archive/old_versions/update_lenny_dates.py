#!/usr/bin/env python3
"""
Update the published dates for Lenny's Podcast episodes
Uses relative dates from YouTube playlist ("2 days ago", "1 month ago", etc.)
based on November 2025 as reference
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


def parse_relative_date(relative_text):
    """
    Convert relative date like '2 days ago', '1 month ago' to datetime
    Reference: November 18, 2025
    """
    reference_date = datetime(2025, 11, 18)

    if not relative_text:
        return None

    relative_text = relative_text.lower().strip()

    # Extract number
    number_match = re.search(r'(\d+)', relative_text)
    number = int(number_match.group(1)) if number_match else 1

    if 'day' in relative_text:
        return reference_date - timedelta(days=number)
    elif 'week' in relative_text:
        return reference_date - timedelta(weeks=number)
    elif 'month' in relative_text:
        return reference_date - timedelta(days=number * 30)
    elif 'year' in relative_text:
        return reference_date - timedelta(days=number * 365)
    elif 'hour' in relative_text:
        return reference_date - timedelta(hours=number)
    else:
        return None


def fetch_playlist_dates():
    """Fetch relative dates from YouTube playlist page (first ~100 videos)"""

    playlist_url = 'https://www.youtube.com/playlist?list=PL2fLjt2dG0N6unOOF3nHWYGcJJIQR1NKm'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    logger.info('Fetching playlist page to get relative dates...')
    response = requests.get(playlist_url, headers=headers, timeout=15)

    match = re.search(r'var ytInitialData = ({.*?});', response.text)
    if not match:
        logger.error('Could not find ytInitialData')
        return {}

    data = json.loads(match.group(1))

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

    video_dates = {}
    for item in contents:
        if 'playlistVideoRenderer' not in item:
            continue

        video = item['playlistVideoRenderer']
        video_id = video.get('videoId')

        # Extract relative date from videoInfo
        video_info = video.get('videoInfo', {})
        info_runs = video_info.get('runs', [])

        relative_date_text = ''
        for run in info_runs:
            text = run.get('text', '')
            if 'ago' in text.lower():
                relative_date_text = text
                break

        if video_id and relative_date_text:
            published_date = parse_relative_date(relative_date_text)
            if published_date:
                video_dates[video_id] = {
                    'relative': relative_date_text,
                    'date': published_date
                }

    logger.info(f'✅ Got relative dates for {len(video_dates)} videos from playlist page\n')
    return video_dates


def main():
    # Fetch dates from playlist
    video_dates = fetch_playlist_dates()

    if not video_dates:
        logger.error('No dates fetched!')
        return

    # Update database
    db = SessionLocal()
    try:
        podcast = db.query(Podcast).filter(Podcast.name == "Lenny's Podcast").first()
        if not podcast:
            logger.error("Lenny's Podcast not found in database!")
            return

        episodes = db.query(Episode).filter(Episode.podcast_id == podcast.id).all()

        logger.info(f'Found {len(episodes)} episodes in database')
        logger.info(f'Updating dates for episodes that match playlist...\n')

        updated_count = 0
        not_found_count = 0

        for episode in episodes:
            # Extract video ID from URL
            match = re.search(r'v=([^&]+)', episode.youtube_url)
            if not match:
                continue

            video_id = match.group(1)

            if video_id in video_dates:
                date_info = video_dates[video_id]
                episode.published_date = date_info['date']
                updated_count += 1

                if updated_count <= 10:  # Show first 10
                    logger.info(f'✅ Updated: {episode.title[:55]}...')
                    logger.info(f'   {date_info["relative"]} → {date_info["date"].strftime("%Y-%m-%d")}')
                    logger.info('')
            else:
                not_found_count += 1

        db.commit()

        logger.info(f'\n{"="*80}')
        logger.info('SUMMARY')
        logger.info(f'{"="*80}')
        logger.info(f'Episodes updated: {updated_count}')
        logger.info(f'Episodes not found in playlist page: {not_found_count}')
        logger.info(f'  (These are older episodes beyond the first ~100)')
        logger.info(f'Total episodes: {len(episodes)}')
        logger.info(f'{"="*80}\n')

        logger.info('Note: Episodes not on the first page will keep their estimated dates.')
        logger.info('This covers the most recent ~2-3 months accurately.\n')

    except Exception as e:
        logger.error(f'Error: {e}')
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
