"""
Discover Recent Podcast Episodes from YouTube

This script automatically discovers recent episodes from configured YouTube channels
and prepares them for processing.

Usage:
    python scripts/discover_episodes.py
    python scripts/discover_episodes.py --months 3  # Last 3 months
    python scripts/discover_episodes.py --podcast "lenny"  # Specific podcast
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
from app.database import SessionLocal, Base, engine
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Podcast configuration
PODCASTS = {
    'lenny': {
        'name': "Lenny's Podcast",
        'channel_handle': '@LennysPodcast',
        'category': 'Product Management & Startups',
        'image_url': 'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400'
    },
    'tim_ferriss': {
        'name': 'The Tim Ferriss Show',
        'channel_handle': '@timferriss',
        'category': 'Business & Self-Improvement',
        'image_url': 'https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=400'
    },
    'huberman': {
        'name': 'Huberman Lab',
        'channel_handle': '@hubermanlab',
        'category': 'Science & Health',
        'image_url': 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400'
    }
}


def create_database():
    """Create all database tables"""
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)


def get_or_create_podcast(db, podcast_config: dict) -> Podcast:
    """Get or create podcast entry"""
    podcast = db.query(Podcast).filter(
        Podcast.name == podcast_config['name']
    ).first()

    if not podcast:
        logger.info(f"Creating podcast: {podcast_config['name']}")
        podcast = Podcast(
            name=podcast_config['name'],
            youtube_channel_id=podcast_config['channel_handle'],
            category=podcast_config['category'],
            image_url=podcast_config['image_url'],
            last_fetched_at=datetime.utcnow()
        )
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
    else:
        # Update last fetched time
        podcast.last_fetched_at = datetime.utcnow()
        db.commit()

    return podcast


def discover_and_save_episodes(
    podcast_key: str,
    months_back: int = 6,
    max_results: int = 50,
    dry_run: bool = False
):
    """
    Discover episodes from a podcast and save to database

    Args:
        podcast_key: Key from PODCASTS dict
        months_back: How many months back to search
        max_results: Maximum number of episodes to discover
        dry_run: If True, don't save to database
    """
    if podcast_key not in PODCASTS:
        logger.error(f"Unknown podcast: {podcast_key}")
        return

    podcast_config = PODCASTS[podcast_key]

    logger.info(f"\n{'='*80}")
    logger.info(f"Discovering episodes for: {podcast_config['name']}")
    logger.info(f"Channel: {podcast_config['channel_handle']}")
    logger.info(f"Time range: Last {months_back} months")
    logger.info(f"{'='*80}\n")

    # Initialize discovery service
    discovery_service = YouTubeDiscoveryService()

    # Discover videos
    videos = discovery_service.discover_recent_videos(
        channel_handle=podcast_config['channel_handle'],
        months_back=months_back,
        max_results=max_results
    )

    if not videos:
        logger.warning(f"No videos discovered for {podcast_config['name']}")
        return

    logger.info(f"\nDiscovered {len(videos)} videos")

    if dry_run:
        logger.info("\n=== DRY RUN - Videos found: ===")
        for i, video in enumerate(videos, 1):
            logger.info(f"\n{i}. {video['title']}")
            logger.info(f"   URL: {video['youtube_url']}")
            logger.info(f"   Published: {video['published_date']}")
        return

    # Save to database
    db = SessionLocal()
    try:
        podcast = get_or_create_podcast(db, podcast_config)

        new_episodes = 0
        existing_episodes = 0

        for video in videos:
            # Check if episode already exists
            existing = db.query(Episode).filter(
                Episode.youtube_url == video['youtube_url']
            ).first()

            if existing:
                existing_episodes += 1
                logger.debug(f"Episode already exists: {video['title']}")
                continue

            # Create new episode
            episode = Episode(
                podcast_id=podcast.id,
                title=video['title'],
                description=video.get('description', ''),
                published_date=datetime.fromisoformat(
                    video['published_date'].replace('Z', '+00:00')
                ),
                youtube_url=video['youtube_url'],
                transcript_source='youtube',
                processing_status='pending',
                guest_names=[]
            )

            db.add(episode)
            new_episodes += 1
            logger.info(f"✅ Added new episode: {video['title'][:60]}...")

        db.commit()

        logger.info(f"\n{'='*80}")
        logger.info(f"Summary for {podcast_config['name']}:")
        logger.info(f"  New episodes added: {new_episodes}")
        logger.info(f"  Already in database: {existing_episodes}")
        logger.info(f"  Total discovered: {len(videos)}")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Error saving episodes: {e}")
        db.rollback()
    finally:
        db.close()


def discover_all_podcasts(months_back: int = 6, max_results: int = 50, dry_run: bool = False):
    """Discover episodes from all configured podcasts"""
    logger.info(f"\n{'#'*80}")
    logger.info(f"# Discovering episodes from {len(PODCASTS)} podcasts")
    logger.info(f"# Time range: Last {months_back} months")
    logger.info(f"{'#'*80}\n")

    for podcast_key in PODCASTS.keys():
        discover_and_save_episodes(
            podcast_key=podcast_key,
            months_back=months_back,
            max_results=max_results,
            dry_run=dry_run
        )


def list_pending_episodes():
    """List all pending episodes that need processing"""
    db = SessionLocal()
    try:
        pending = db.query(Episode).filter(
            Episode.processing_status == 'pending'
        ).all()

        logger.info(f"\n{'='*80}")
        logger.info(f"Pending Episodes: {len(pending)}")
        logger.info(f"{'='*80}\n")

        for episode in pending:
            podcast = db.query(Podcast).filter(Podcast.id == episode.podcast_id).first()
            logger.info(f"📝 {episode.title[:60]}...")
            logger.info(f"   Podcast: {podcast.name if podcast else 'Unknown'}")
            logger.info(f"   URL: {episode.youtube_url}")
            logger.info(f"   Published: {episode.published_date}")
            logger.info("")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Discover recent podcast episodes from YouTube'
    )
    parser.add_argument(
        '--podcast',
        type=str,
        choices=list(PODCASTS.keys()) + ['all'],
        default='all',
        help='Which podcast to discover (default: all)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=6,
        help='How many months back to search (default: 6)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of videos to discover (default: 50)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be discovered without saving to database'
    )
    parser.add_argument(
        '--list-pending',
        action='store_true',
        help='List all pending episodes that need processing'
    )

    args = parser.parse_args()

    # Create database tables
    create_database()

    if args.list_pending:
        list_pending_episodes()
        return

    if args.podcast == 'all':
        discover_all_podcasts(
            months_back=args.months,
            max_results=args.max_results,
            dry_run=args.dry_run
        )
    else:
        discover_and_save_episodes(
            podcast_key=args.podcast,
            months_back=args.months,
            max_results=args.max_results,
            dry_run=args.dry_run
        )

    # Show pending episodes after discovery
    if not args.dry_run:
        logger.info("\n")
        list_pending_episodes()


if __name__ == "__main__":
    main()
