"""
Fetch Tim Ferriss Show episodes from YouTube playlist

Only includes episodes that are 60+ minutes long.

Usage:
    python scripts/add_tim_ferriss_playlist.py
    python scripts/add_tim_ferriss_playlist.py --dry-run
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_discovery_service import YouTubeDiscoveryService
from app.models.podcast import Podcast
from app.models.episode import Episode
from app.database import SessionLocal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tim Ferriss Show playlist
TIM_FERRISS_PLAYLIST = "https://www.youtube.com/playlist?list=PLuu6fDad2eJyWPm9dQfuorm2uuYHBZDCB"

# Minimum duration: 60 minutes = 3600 seconds
MIN_DURATION_SECONDS = 3600


def main():
    parser = argparse.ArgumentParser(
        description='Fetch Tim Ferriss Show episodes from playlist (60+ minutes only)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without saving to database'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of episodes to fetch (default: 50)'
    )

    args = parser.parse_args()

    logger.info(f"\n{'='*80}")
    logger.info(f"Fetching Tim Ferriss Show episodes from playlist")
    logger.info(f"Minimum duration: 60 minutes")
    logger.info(f"Playlist: {TIM_FERRISS_PLAYLIST}")
    logger.info(f"{'='*80}\n")

    # Initialize discovery service
    discovery_service = YouTubeDiscoveryService()

    # Fetch playlist videos (60+ minutes only)
    videos = discovery_service.get_playlist_videos(
        playlist_url=TIM_FERRISS_PLAYLIST,
        min_duration_seconds=MIN_DURATION_SECONDS,
        max_results=args.max_results
    )

    if not videos:
        logger.warning("No videos found in playlist")
        return

    logger.info(f"\nFound {len(videos)} episodes (60+ minutes)")

    if args.dry_run:
        logger.info("\n=== DRY RUN - Episodes found: ===\n")
        for i, video in enumerate(videos, 1):
            duration_mins = video['duration_seconds'] // 60
            logger.info(f"{i}. {video['title'][:70]}...")
            logger.info(f"   Duration: {duration_mins} minutes")
            logger.info(f"   URL: {video['youtube_url']}")
            logger.info("")
        return

    # Save to database
    db = SessionLocal()
    try:
        # Get or create Tim Ferriss Show podcast
        podcast = db.query(Podcast).filter(
            Podcast.name == 'The Tim Ferriss Show'
        ).first()

        if not podcast:
            logger.info("Creating 'The Tim Ferriss Show' podcast entry")
            podcast = Podcast(
                name='The Tim Ferriss Show',
                youtube_channel_id='@timferriss',
                category='Business & Self-Improvement',
                image_url='https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=400',
                last_fetched_at=datetime.utcnow()
            )
            db.add(podcast)
            db.commit()
            db.refresh(podcast)

        # First, delete existing Tim Ferriss episodes that are pending
        # (to replace with properly filtered ones)
        deleted = db.query(Episode).filter(
            Episode.podcast_id == podcast.id,
            Episode.processing_status == 'pending'
        ).delete()

        if deleted > 0:
            logger.info(f"Removed {deleted} old pending episodes")
            db.commit()

        new_episodes = 0
        existing_episodes = 0

        for video in videos:
            # Check if episode already exists (and is completed)
            existing = db.query(Episode).filter(
                Episode.youtube_url == video['youtube_url'],
                Episode.processing_status == 'completed'
            ).first()

            if existing:
                existing_episodes += 1
                logger.debug(f"Already processed: {video['title'][:50]}...")
                continue

            # Create new episode
            duration_mins = video['duration_seconds'] // 60
            episode = Episode(
                podcast_id=podcast.id,
                title=video['title'],
                description=video.get('description', ''),
                published_date=datetime.fromisoformat(
                    video['published_date'].replace('Z', '+00:00')
                ),
                duration_seconds=video.get('duration_seconds'),
                youtube_url=video['youtube_url'],
                transcript_source='youtube',
                processing_status='pending',
                guest_names=[]
            )

            db.add(episode)
            new_episodes += 1
            logger.info(f"✅ Added ({duration_mins} min): {video['title'][:60]}...")

        db.commit()

        logger.info(f"\n{'='*80}")
        logger.info(f"Summary for The Tim Ferriss Show:")
        logger.info(f"  New episodes added: {new_episodes}")
        logger.info(f"  Already processed: {existing_episodes}")
        logger.info(f"  Total found: {len(videos)}")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Error saving episodes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
