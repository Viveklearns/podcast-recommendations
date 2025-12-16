"""
Fix Lenny's Podcast episodes by fetching from correct playlist

Deletes all pending Lenny episodes and replaces with correct ones from:
https://www.youtube.com/playlist?list=PL2fLjt2dG0N6unOOF3nHWYGcJJIQR1NKm

Usage:
    python scripts/fix_lenny_episodes.py
    python scripts/fix_lenny_episodes.py --dry-run
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

# Correct Lenny's Podcast playlist
LENNY_PLAYLIST = "https://www.youtube.com/playlist?list=PL2fLjt2dG0N6unOOF3nHWYGcJJIQR1NKm"


def main():
    parser = argparse.ArgumentParser(
        description="Fix Lenny's Podcast episodes from correct playlist"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of episodes to fetch (default: 50)'
    )

    args = parser.parse_args()

    logger.info(f"\n{'='*80}")
    logger.info(f"Fixing Lenny's Podcast episodes from correct playlist")
    logger.info(f"Playlist: {LENNY_PLAYLIST}")
    logger.info(f"{'='*80}\n")

    # Initialize discovery service
    discovery_service = YouTubeDiscoveryService()

    # Fetch correct playlist videos
    logger.info("Fetching episodes from playlist...")
    videos = discovery_service.get_playlist_videos(
        playlist_url=LENNY_PLAYLIST,
        min_duration_seconds=0,  # No minimum duration for Lenny's Podcast
        max_results=args.max_results
    )

    if not videos:
        logger.error("No videos found in playlist")
        return

    logger.info(f"\nFound {len(videos)} episodes in playlist")

    if args.dry_run:
        logger.info("\n=== DRY RUN - Episodes that will be added: ===\n")
        for i, video in enumerate(videos, 1):
            logger.info(f"{i}. {video['title']}")
            logger.info(f"   URL: {video['youtube_url']}")
            logger.info("")
        return

    # Update database
    db = SessionLocal()
    try:
        # Get Lenny's Podcast
        podcast = db.query(Podcast).filter(
            Podcast.name == "Lenny's Podcast"
        ).first()

        if not podcast:
            logger.error("Lenny's Podcast not found in database")
            return

        # Delete all pending Lenny episodes (they're wrong)
        deleted = db.query(Episode).filter(
            Episode.podcast_id == podcast.id,
            Episode.processing_status == 'pending'
        ).delete()

        logger.info(f"Removed {deleted} incorrect pending episodes")
        db.commit()

        # Add correct episodes
        new_episodes = 0
        existing_episodes = 0

        for video in videos:
            # Check if episode already exists and is completed
            existing = db.query(Episode).filter(
                Episode.youtube_url == video['youtube_url'],
                Episode.processing_status == 'completed'
            ).first()

            if existing:
                existing_episodes += 1
                logger.debug(f"Already processed: {video['title'][:50]}...")
                continue

            # Create new episode
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
            logger.info(f"✅ Added: {video['title'][:60]}...")

        db.commit()

        logger.info(f"\n{'='*80}")
        logger.info(f"Summary for Lenny's Podcast:")
        logger.info(f"  Incorrect episodes removed: {deleted}")
        logger.info(f"  New episodes added: {new_episodes}")
        logger.info(f"  Already processed: {existing_episodes}")
        logger.info(f"  Total found in playlist: {len(videos)}")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Error updating episodes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
