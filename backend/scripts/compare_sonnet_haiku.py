#!/usr/bin/env python3
"""
Special comparison: Process same episodes with both Sonnet and Haiku
Keeps both sets of recommendations for comparison
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService
from app.models.episode import Episode
from app.models.recommendation import Recommendation
from app.database import SessionLocal
from sqlalchemy import text
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compare_models_and_save(episode_id: str, db):
    """
    Process one episode with both Sonnet and Haiku
    Save both sets of recommendations with their respective model_used values
    """

    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        logger.error(f"Episode {episode_id} not found")
        return None

    logger.info(f"\n{'='*80}")
    logger.info(f"COMPARING MODELS ON: {episode.title[:70]}...")
    logger.info(f"{'='*80}\n")

    # Get transcript
    youtube_service = YouTubeService()
    video_id = youtube_service.extract_video_id(episode.youtube_url)

    logger.info("Fetching transcript...")
    transcript_result = youtube_service.get_transcript_with_verification(video_id)

    if not transcript_result:
        logger.error("Failed to fetch transcript")
        return None

    transcript = transcript_result['transcript']
    guest_name = episode.guest_names[0] if episode.guest_names else ""

    logger.info(f"Transcript length: {len(transcript)} characters\n")

    # Delete existing Haiku recommendations for this episode
    logger.info("Removing existing Haiku recommendations to avoid duplicates...")
    db.query(Recommendation).filter(
        Recommendation.episode_id == episode_id,
        Recommendation.model_used == 'claude-3-5-haiku-20241022'
    ).delete()
    db.commit()

    results = {
        'episode_title': episode.title,
        'episode_id': episode_id,
        'transcript_length': len(transcript),
        'sonnet': {},
        'haiku': {}
    }

    # Process with SONNET
    logger.info("🔵 Processing with SONNET 4...")
    sonnet_service = ClaudeService(model="claude-sonnet-4-20250514")
    sonnet_recs, sonnet_meta = sonnet_service.extract_recommendations_smart(
        transcript, episode.title, guest_name
    )

    logger.info(f"✅ Sonnet found: {len(sonnet_recs)} recommendations")
    results['sonnet']['count'] = len(sonnet_recs)
    results['sonnet']['recommendations'] = sonnet_recs

    # Save Sonnet recommendations
    logger.info("Saving Sonnet recommendations...")
    for rec_data in sonnet_recs:
        # Prepare extra metadata
        extra_metadata = {}
        for field in ['author', 'isbn', 'isbn_10', 'isbn_13', 'publisher', 'publishedYear',
                     'pageCount', 'goodreadsRating', 'amazonUrl', 'goodreadsUrl',
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
            model_used='claude-sonnet-4-20250514',
            extra_metadata=extra_metadata
        )
        db.add(recommendation)

    db.commit()
    logger.info(f"✅ Saved {len(sonnet_recs)} Sonnet recommendations\n")

    # Process with HAIKU
    logger.info("🟢 Processing with HAIKU 3.5...")
    haiku_service = ClaudeService(model="claude-3-5-haiku-20241022")
    haiku_recs, haiku_meta = haiku_service.extract_recommendations_smart(
        transcript, episode.title, guest_name
    )

    logger.info(f"✅ Haiku found: {len(haiku_recs)} recommendations")
    results['haiku']['count'] = len(haiku_recs)
    results['haiku']['recommendations'] = haiku_recs

    # Save Haiku recommendations
    logger.info("Saving Haiku recommendations...")
    for rec_data in haiku_recs:
        # Prepare extra metadata
        extra_metadata = {}
        for field in ['author', 'isbn', 'isbn_10', 'isbn_13', 'publisher', 'publishedYear',
                     'pageCount', 'goodreadsRating', 'amazonUrl', 'goodreadsUrl',
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
            model_used='claude-3-5-haiku-20241022',
            extra_metadata=extra_metadata
        )
        db.add(recommendation)

    db.commit()
    logger.info(f"✅ Saved {len(haiku_recs)} Haiku recommendations\n")

    # Compare results
    logger.info(f"\n{'='*80}")
    logger.info("COMPARISON SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Episode: {episode.title[:70]}...")
    logger.info(f"Sonnet: {len(sonnet_recs)} recommendations")
    logger.info(f"Haiku:  {len(haiku_recs)} recommendations")
    logger.info(f"Difference: {abs(len(sonnet_recs) - len(haiku_recs))}")

    # Find overlap
    sonnet_titles = set(r['title'].lower() for r in sonnet_recs)
    haiku_titles = set(r['title'].lower() for r in haiku_recs)
    common = sonnet_titles & haiku_titles
    sonnet_only = sonnet_titles - haiku_titles
    haiku_only = haiku_titles - sonnet_titles

    logger.info(f"\nOverlap:")
    logger.info(f"  Common: {len(common)}")
    logger.info(f"  Sonnet only: {len(sonnet_only)}")
    logger.info(f"  Haiku only: {len(haiku_only)}")

    if common:
        logger.info(f"\nCommon recommendations:")
        for title in list(common)[:5]:
            logger.info(f"  ✓ {title}")

    if sonnet_only:
        logger.info(f"\nSonnet found but Haiku missed:")
        for title in list(sonnet_only)[:5]:
            logger.info(f"  🔵 {title}")

    if haiku_only:
        logger.info(f"\nHaiku found but Sonnet missed:")
        for title in list(haiku_only)[:5]:
            logger.info(f"  🟢 {title}")

    logger.info(f"{'='*80}\n")

    results['overlap'] = {
        'common': len(common),
        'sonnet_only': len(sonnet_only),
        'haiku_only': len(haiku_only)
    }

    return results


def main():
    """
    Get the last 2 episodes processed with Haiku and reprocess with both models
    """

    db = SessionLocal()
    try:
        # Find the last 2 episodes that have Haiku recommendations
        logger.info("Finding last 2 episodes processed with Haiku...")

        episodes_with_haiku = db.execute(text("""
            SELECT DISTINCT e.id, e.title, e.processed_at
            FROM episodes e
            JOIN recommendations r ON e.id = r.episode_id
            WHERE r.model_used = 'claude-3-5-haiku-20241022'
            ORDER BY e.processed_at DESC
            LIMIT 2
        """)).fetchall()

        if not episodes_with_haiku:
            logger.error("No episodes found with Haiku recommendations!")
            return

        logger.info(f"\n{'='*80}")
        logger.info(f"Found {len(episodes_with_haiku)} episodes to compare")
        logger.info(f"{'='*80}\n")

        all_results = []

        for idx, (episode_id, title, processed_at) in enumerate(episodes_with_haiku, 1):
            logger.info(f"\n{'#'*80}")
            logger.info(f"COMPARISON {idx}/2")
            logger.info(f"{'#'*80}\n")

            result = compare_models_and_save(episode_id, db)
            if result:
                all_results.append(result)

        # Save comparison results to JSON
        comparison_file = f"comparison_sonnet_vs_haiku_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(comparison_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ COMPARISON COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Results saved to: {comparison_file}")
        logger.info(f"Both Sonnet and Haiku recommendations are now in the database")
        logger.info(f"Query with: WHERE model_used = 'claude-sonnet-4-20250514' OR model_used = 'claude-3-5-haiku-20241022'")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
