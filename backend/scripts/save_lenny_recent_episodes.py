#!/usr/bin/env python3
"""
Save recent Lenny's Podcast episodes to database
Fetches from YouTube channel page and extracts guest names
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import re
import json
from datetime import datetime, timedelta
from app.models.podcast import Podcast
from app.models.episode import Episode
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_guest_from_title(title):
    """
    Extract guest name from Lenny's Podcast title format.
    Common patterns:
    - 'Topic | Guest Name (Company)'
    - 'Topic | Guest Name'
    - 'Topic with Guest Name'
    """
    # Pattern 1: '| Guest Name (Company)' or '| Guest Name'
    match = re.search(r'\|\s*([^(]+?)(?:\s*\(|$)', title)
    if match:
        guest = match.group(1).strip()
        # Clean up common suffixes
        guest = re.sub(r'\s+(co-founder|CEO|founder|VP|Chief|CTO|CPO).*$', '', guest, flags=re.IGNORECASE)
        return guest.strip()

    # Pattern 2: 'with Guest Name'
    match = re.search(r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', title)
    if match:
        return match.group(1).strip()

    return ''


def parse_relative_date(relative_text):
    """Convert '2 days ago', '3 weeks ago' to approximate datetime"""
    now = datetime.now()

    if 'day' in relative_text:
        match = re.search(r'(\d+)', relative_text)
        days = int(match.group(1)) if match else 1
        return now - timedelta(days=days)
    elif 'week' in relative_text:
        match = re.search(r'(\d+)', relative_text)
        weeks = int(match.group(1)) if match else 1
        return now - timedelta(weeks=weeks)
    elif 'month' in relative_text:
        match = re.search(r'(\d+)', relative_text)
        months = int(match.group(1)) if match else 1
        return now - timedelta(days=months*30)  # Approximate
    elif 'hour' in relative_text:
        match = re.search(r'(\d+)', relative_text)
        hours = int(match.group(1)) if match else 1
        return now - timedelta(hours=hours)
    else:
        return now


def fetch_recent_videos():
    """Fetch recent videos from Lenny's Podcast YouTube channel"""
    url = 'https://www.youtube.com/@LennysPodcast/videos'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    logger.info('Fetching Lenny\'s Podcast channel page...')
    response = requests.get(url, headers=headers, timeout=15)

    # Extract ytInitialData
    match = re.search(r'var ytInitialData = ({.*?});', response.text)
    if not match:
        logger.error('Could not find ytInitialData on page')
        return []

    data = json.loads(match.group(1))

    # Navigate to videos
    tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
    videos = []

    for tab in tabs:
        if 'tabRenderer' not in tab:
            continue

        if not tab['tabRenderer'].get('selected'):
            continue

        contents = (tab.get('tabRenderer', {})
                       .get('content', {})
                       .get('richGridRenderer', {})
                       .get('contents', []))

        logger.info(f'Found {len(contents)} items in selected tab')

        for item in contents:
            if 'richItemRenderer' not in item:
                continue

            video_renderer = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})

            if not video_renderer:
                continue

            video_id = video_renderer.get('videoId')
            title_runs = video_renderer.get('title', {}).get('runs', [])
            title = title_runs[0].get('text', '') if title_runs else ''
            published_text = video_renderer.get('publishedTimeText', {}).get('simpleText', '')

            if video_id and title:
                guest = extract_guest_from_title(title)
                pub_date = parse_relative_date(published_text)

                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'published': published_text,
                    'published_date': pub_date,
                    'guest': guest
                })

    logger.info(f'Extracted {len(videos)} videos')
    return videos


def main():
    # Fetch videos
    videos = fetch_recent_videos()

    if not videos:
        logger.error('No videos found!')
        return

    logger.info(f'\n{"="*80}')
    logger.info(f'Found {len(videos)} episodes from Lenny\'s Podcast')
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

        for i, video in enumerate(videos, 1):
            # Check if already exists
            existing = db.query(Episode).filter(Episode.youtube_url == video['url']).first()

            if existing:
                existing_count += 1
                logger.info(f'{i}. ⏭️  Already exists: {video["title"][:60]}...')
                continue

            # Create new episode
            episode = Episode(
                podcast_id=podcast.id,
                title=video['title'],
                description='',
                published_date=video['published_date'],
                youtube_url=video['url'],
                transcript_source='youtube',
                processing_status='pending',
                guest_names=[video['guest']] if video['guest'] else []
            )

            db.add(episode)
            new_count += 1

            logger.info(f'{i}. ✅ Added: {video["title"][:60]}...')
            logger.info(f'   Guest: {video["guest"] or "Unknown"}')
            logger.info(f'   Published: {video["published"]}\n')

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
