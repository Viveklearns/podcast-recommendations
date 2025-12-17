"""
Process all pending episodes from all podcasts

This script processes all episodes with status='pending' and extracts recommendations
using Claude AI, then enriches the data.

Usage:
    python scripts/process_all_pending.py
    python scripts/process_all_pending.py --limit 5  # Process only 5 episodes
    python scripts/process_all_pending.py --podcast "Lenny's Podcast"  # Specific podcast
"""

import sys
import os
import argparse
from datetime import datetime
import logging
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService
from app.services.book_enrichment_service import BookEnrichmentService
from app.services.metrics_service import MetricsService
from app.models.podcast import Podcast
from app.models.episode import Episode
from app.models.recommendation import Recommendation
from app.database import SessionLocal
from sqlalchemy import func

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing_all.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def safe_commit(db, max_retries=3, retry_delay=1):
    """
    Safely commit database changes with retry logic for SQLite locking issues
    """
    from sqlalchemy.exc import OperationalError

    for attempt in range(max_retries):
        try:
            db.commit()
            return True
        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                db.rollback()
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                db.rollback()
                raise
    return False


def extract_guest_name_from_title(title: str) -> str:
    """Extract guest name from episode title"""
    import re

    # Lenny's Podcast format: "Topic description | Guest Name (optional title)"
    # Pattern 1: Extract everything after the pipe "|"
    if '|' in title:
        # Get part after pipe
        after_pipe = title.split('|', 1)[1].strip()
        # Remove any parenthetical info like "(co-founder)", "(Meta, Google)", etc.
        guest_name = re.sub(r'\s*\([^)]*\)\s*$', '', after_pipe).strip()
        # Remove HTML entities
        guest_name = guest_name.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')
        if len(guest_name) < 100 and any(c.isalpha() for c in guest_name):
            return guest_name

    # Pattern 2: "Something with Name" or "Something w/ Name"
    match = re.search(r'(?:with|w/)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
    if match:
        return match.group(1).strip()

    return ""


def process_episode(db, episode: Episode) -> dict:
    """Process a single episode and return stats"""
    start_time = time.time()  # Track processing time

    podcast = db.query(Podcast).filter(Podcast.id == episode.podcast_id).first()

    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {episode.title[:70]}...")
    logger.info(f"Podcast: {podcast.name}")
    logger.info(f"URL: {episode.youtube_url}")
    logger.info(f"{'='*80}\n")

    # Initialize services
    youtube_service = YouTubeService()
    claude_service = ClaudeService()
    enrichment_service = BookEnrichmentService()
    metrics_service = MetricsService()

    # Extract video ID
    video_id = youtube_service.extract_video_id(episode.youtube_url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {episode.youtube_url}")
        episode.processing_status = "failed"
        safe_commit(db)
        return {"success": False, "recommendations": 0}

    # Get video metadata
    logger.info("Fetching video metadata...")
    video_title = youtube_service.get_video_title(video_id) or episode.title

    # Extract guest name
    guest_name = extract_guest_name_from_title(video_title)
    if guest_name:
        logger.info(f"Extracted guest name: {guest_name}")
        episode.guest_names = [guest_name]

    # Update episode title if needed
    if video_title != episode.title:
        episode.title = video_title

    # Fetch transcript with verification
    logger.info("Fetching transcript with verification...")
    transcript_result = youtube_service.get_transcript_with_verification(video_id)

    if not transcript_result:
        logger.error("Failed to fetch transcript")
        episode.processing_status = "failed"
        safe_commit(db)
        return {"success": False, "recommendations": 0}

    transcript = transcript_result['transcript']
    transcript_metadata = transcript_result['metadata']

    # Store transcript metadata
    episode.transcript_metadata = transcript_metadata
    episode.transcript_source = 'youtube'

    logger.info(f"Transcript length: {len(transcript)} characters")
    logger.info(f"Transcript completeness: {'✓ Complete' if transcript_metadata['is_complete'] else '⚠ Incomplete'}")

    # Mark as processing
    episode.processing_status = "processing"
    safe_commit(db)

    # Extract recommendations using Claude with smart processing
    logger.info("Extracting recommendations with Claude API (smart processing)...")

    recommendations, claude_metadata = claude_service.extract_recommendations_smart(
        transcript,
        episode_title=video_title,
        guest_name=guest_name
    )

    # Store Claude processing metadata
    episode.claude_processing_metadata = claude_metadata

    logger.info(f"Found {len(recommendations)} recommendations")

    # Save recommendations
    saved_count = 0
    skipped_count = 0

    for i, rec_data in enumerate(recommendations, 1):
        logger.info(f"\nRecommendation {i}/{len(recommendations)}:")
        logger.info(f"  Type: {rec_data.get('type')}")
        logger.info(f"  Title: {rec_data.get('title')}")
        logger.info(f"  By: {rec_data.get('recommended_by', 'Unknown')}")

        # Enrich book recommendations
        if rec_data.get('type') == 'book':
            logger.info("  Enriching book with Google Books API...")
            enriched_data = enrichment_service.enrich_book_recommendation(rec_data)

            if enriched_data:
                rec_data.update(enriched_data)
                logger.info(f"  ✅ Enriched: {rec_data.get('isbn', 'No ISBN')}")
            else:
                logger.warning("  ⚠️ Could not enrich book data")

        # Create recommendation
        extra_metadata = {}

        # Extract type-specific fields
        if rec_data.get('type') == 'book':
            for field in ['author', 'isbn', 'isbn_10', 'isbn_13', 'publisher',
                         'publishedYear', 'pageCount', 'description', 'coverImageUrl',
                         'amazonUrl', 'googleBooksUrl', 'googleBooksId', 'categories', 'verified']:
                if field in rec_data:
                    extra_metadata[field] = rec_data[field]

        recommendation = Recommendation(
            episode_id=episode.id,
            type=rec_data.get('type', 'other'),
            title=rec_data.get('title', ''),
            recommendation_context=rec_data.get('context', ''),
            quote_from_episode=rec_data.get('quote', ''),
            timestamp_seconds=rec_data.get('timestamp_seconds', 0),
            recommended_by=rec_data.get('recommended_by', guest_name or 'Unknown'),
            confidence_score=rec_data.get('confidence', 0.0),
            model_used=claude_service.model,  # Track which Claude model was used
            extra_metadata=extra_metadata
        )

        db.add(recommendation)
        saved_count += 1

    # Mark episode as completed
    episode.processing_status = "completed"
    episode.processed_at = datetime.utcnow()
    safe_commit(db)

    # Calculate metrics
    processing_time = time.time() - start_time
    ai_model = "claude-sonnet-4-20250514"
    # Rough cost estimate: $3/M input tokens, ~4 chars per token
    input_tokens = transcript_metadata.get('character_count', 0) / 4
    estimated_cost = (input_tokens / 1_000_000) * 3.0

    # Save processing metrics to database
    logger.info("\n💾 Saving processing metrics...")
    metrics_service.save_processing_metrics(
        db=db,
        episode_id=episode.id,
        phase="phase_1",  # Phase 1: Data Quality Verification
        transcript_metadata=transcript_metadata,
        claude_metadata=claude_metadata,
        recommendations=recommendations,
        ai_model=ai_model,
        estimated_cost=estimated_cost,
        processing_time=processing_time,
        had_errors=False,
        error_message=None
    )

    logger.info(f"\n✅ Episode completed: {saved_count} recommendations saved")
    logger.info(f"⏱️  Processing time: {processing_time:.1f} seconds")
    logger.info(f"💰 Estimated cost: ${estimated_cost:.4f}")

    return {
        "success": True,
        "recommendations": saved_count,
        "skipped": skipped_count,
        "processing_time": processing_time,
        "estimated_cost": estimated_cost
    }


def main():
    parser = argparse.ArgumentParser(
        description='Process all pending podcast episodes'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of episodes to process'
    )
    parser.add_argument(
        '--podcast',
        type=str,
        help='Only process episodes from specific podcast'
    )

    args = parser.parse_args()

    logger.info(f"\n{'#'*80}")
    logger.info(f"# Starting batch processing of pending episodes")
    logger.info(f"{'#'*80}\n")

    db = SessionLocal()

    try:
        # Query pending episodes
        query = db.query(Episode).filter(Episode.processing_status == 'pending')

        if args.podcast:
            podcast = db.query(Podcast).filter(Podcast.name == args.podcast).first()
            if podcast:
                query = query.filter(Episode.podcast_id == podcast.id)
                logger.info(f"Filtering to podcast: {args.podcast}")
            else:
                logger.error(f"Podcast not found: {args.podcast}")
                return

        if args.limit:
            query = query.limit(args.limit)
            logger.info(f"Limiting to {args.limit} episodes")

        pending_episodes = query.all()

        total = len(pending_episodes)
        logger.info(f"\nFound {total} pending episodes to process\n")

        if total == 0:
            logger.info("No pending episodes found!")
            return

        # Process each episode
        total_recommendations = 0
        successful = 0
        failed = 0

        for idx, episode in enumerate(pending_episodes, 1):
            logger.info(f"\n{'*'*80}")
            logger.info(f"Processing episode {idx}/{total}")
            logger.info(f"{'*'*80}")

            try:
                result = process_episode(db, episode)

                if result['success']:
                    successful += 1
                    total_recommendations += result['recommendations']
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error processing episode: {e}")
                try:
                    db.rollback()  # Rollback failed transaction first
                    episode.processing_status = "failed"
                    safe_commit(db)
                except Exception as commit_error:
                    logger.error(f"Error updating failed status: {commit_error}")
                    db.rollback()
                failed += 1

            # Add delay between episodes to avoid YouTube rate limiting
            if idx < total:  # Don't wait after the last episode
                logger.info("Waiting 20 seconds before next episode to avoid YouTube blocking...")
                time.sleep(20)

        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info(f"PROCESSING COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Episodes processed: {successful}/{total}")
        logger.info(f"Episodes failed: {failed}/{total}")
        logger.info(f"Total recommendations extracted: {total_recommendations}")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
