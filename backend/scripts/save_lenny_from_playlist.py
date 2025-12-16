#!/usr/bin/env python3
"""
Save Lenny's Podcast episodes from YouTube playlist
Fetches from: https://www.youtube.com/playlist?list=PL2fLjt2dG0N6unOOF3nHWYGcJJIQR1NKm
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


def fetch_playlist_videos(playlist_url):
    """Fetch all videos from YouTube playlist"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    logger.info(f'Fetching playlist: {playlist_url}')
    response = requests.get(playlist_url, headers=headers, timeout=15)

    # Extract ytInitialData
    match = re.search(r'var ytInitialData = ({.*?});', response.text)
    if not match:
        logger.error('Could not find ytInitialData')
        return []

    data = json.loads(match.group(1))

    # Navigate to playlist videos
    try:
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
            if 'playlistVideoRenderer' in item:
                video = item['playlistVideoRenderer']
                video_id = video.get('videoId')
                title_runs = video.get('title', {}).get('runs', [])
                title = title_runs[0].get('text', '') if title_runs else ''

                # Get index (position in playlist)
                index = video.get('index', {}).get('simpleText', '')

                if video_id and title:
                    guest = extract_guest_from_title(title)

                    videos.append({
                        'video_id': video_id,
                        'title': title,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'guest': guest,
                        'index': index
                    })

        logger.info(f'Found {len(videos)} videos in playlist')
        return videos

    except Exception as e:
        logger.error(f'Error parsing playlist: {e}')
        import traceback
        traceback.print_exc()
        return []


def main():
    playlist_url = 'https://www.youtube.com/playlist?list=PL2fLjt2dG0N6unOOF3nHWYGcJJIQR1NKm'

    # Fetch videos
    videos = fetch_playlist_videos(playlist_url)

    if not videos:
        logger.error('No videos found!')
        return

    logger.info(f'\n{"="*80}')
    logger.info(f'Found {len(videos)} episodes from playlist')
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

        # Estimate published date based on index (newer = lower index)
        # Assume weekly episodes, starting from today going backwards
        base_date = datetime.now()

        for i, video in enumerate(videos):
            # Check if already exists
            existing = db.query(Episode).filter(Episode.youtube_url == video['url']).first()

            if existing:
                existing_count += 1
                logger.info(f'{i+1}. ⏭️  Already exists: {video["title"][:60]}...')
                continue

            # Estimate date: newer episodes have lower index
            estimated_date = base_date - timedelta(weeks=i)

            # Create new episode
            episode = Episode(
                podcast_id=podcast.id,
                title=video['title'],
                description='',
                published_date=estimated_date,
                youtube_url=video['url'],
                transcript_source='youtube',
                processing_status='pending',
                guest_names=[video['guest']] if video['guest'] else []
            )

            db.add(episode)
            new_count += 1

            logger.info(f'{i+1}. ✅ Added: {video["title"][:60]}...')
            logger.info(f'   Guest: {video["guest"] or "Unknown"}')
            logger.info(f'   Estimated date: {estimated_date.strftime("%Y-%m-%d")}\n')

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
