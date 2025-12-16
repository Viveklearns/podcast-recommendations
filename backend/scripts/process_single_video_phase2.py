#!/usr/bin/env python3
"""
Process a single video URL with Phase 2 checks (using Claude Haiku 4)
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService
from app.services.book_enrichment_service import BookEnrichmentService
from app.services.metrics_service import MetricsService
from app.models.episode import Episode
from app.models.podcast import Podcast
from app.models.recommendation import Recommendation
from app.database import SessionLocal
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_video(video_url: str):
    """Process a single video URL with Phase 2 (Haiku)"""
    start_time = time.time()

    db = SessionLocal()

    try:
        # Initialize services - Using Claude Haiku 4 for Phase 2
        youtube_service = YouTubeService()
        claude_service = ClaudeService(model="claude-haiku-4-20250514")  # Phase 2: Haiku
        enrichment_service = BookEnrichmentService()
        metrics_service = MetricsService()

        # Extract video ID
        video_id = youtube_service.extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return

        logger.info(f"🚀 PHASE 2 PROCESSING (Claude Haiku 4)")
        logger.info(f"Processing video: {video_id}")
        logger.info(f"URL: {video_url}\n")

        # Get video metadata
        logger.info("Fetching video metadata...")
        video_title = youtube_service.get_video_title(video_id)

        logger.info(f"Title: {video_title}\n")

        # Fetch transcript with verification
        logger.info("Fetching transcript with Phase 1 verification...")
        transcript_result = youtube_service.get_transcript_with_verification(video_id)

        if not transcript_result:
            logger.error("Failed to fetch transcript")
            return

        transcript = transcript_result['transcript']
        transcript_metadata = transcript_result['metadata']

        logger.info(f"✅ Transcript fetched and verified!")
        logger.info(f"   Characters: {transcript_metadata['character_count']:,}")
        logger.info(f"   Complete: {transcript_metadata['is_complete']}\n")

        # Extract recommendations with Claude Haiku (Phase 2) - smart processing
        logger.info("🤖 Extracting recommendations with Claude Haiku 4 (Phase 2 - smart processing)...")

        recommendations, claude_metadata = claude_service.extract_recommendations_smart(
            transcript,
            episode_title=video_title,
            guest_name=""
        )

        logger.info(f"✅ Found {len(recommendations)} recommendations\n")

        # Create or get podcast
        podcast = db.query(Podcast).filter(Podcast.name == "Ad-hoc Videos").first()
        if not podcast:
            podcast = Podcast(name="Ad-hoc Videos", category="general")
            db.add(podcast)
            db.commit()
            db.refresh(podcast)

        # Create episode
        episode = Episode(
            podcast_id=podcast.id,
            title=video_title + " [Phase 2 - Haiku]",  # Tag with phase
            youtube_url=video_url,
            transcript_source='youtube',
            transcript_metadata=transcript_metadata,
            claude_processing_metadata=claude_metadata,
            processing_status='completed',
            processed_at=datetime.utcnow()
        )
        db.add(episode)
        db.commit()
        db.refresh(episode)

        logger.info(f"✅ Episode created: {episode.id}\n")

        # Save recommendations
        saved_count = 0
        for rec_data in recommendations:
            # Enrich books
            if rec_data.get('type') == 'book':
                enriched_data = enrichment_service.enrich_book_recommendation(rec_data)
                if enriched_data:
                    rec_data.update(enriched_data)

            # Extract metadata
            extra_metadata = {}
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
                recommended_by=rec_data.get('recommended_by', 'Unknown'),
                confidence_score=rec_data.get('confidence', 0.0),
                extra_metadata=extra_metadata
            )

            db.add(recommendation)
            saved_count += 1

        db.commit()

        # Calculate metrics for Phase 2 (Haiku pricing)
        processing_time = time.time() - start_time
        ai_model = "claude-haiku-4-20250514"  # Phase 2 model

        # Haiku pricing: $0.40 per million input tokens, $2.00 per million output tokens
        input_tokens = transcript_metadata.get('character_count', 0) / 4
        output_tokens = 500  # Estimated output tokens
        estimated_cost = (input_tokens / 1_000_000) * 0.40 + (output_tokens / 1_000_000) * 2.00

        # Save processing metrics as Phase 2
        logger.info("💾 Saving Phase 2 processing metrics...")
        metrics_service.save_processing_metrics(
            db=db,
            episode_id=episode.id,
            phase="phase_2",  # Mark as Phase 2
            transcript_metadata=transcript_metadata,
            claude_metadata=claude_metadata,
            recommendations=recommendations,
            ai_model=ai_model,
            estimated_cost=estimated_cost,
            processing_time=processing_time,
            youtube_url=video_url,
            had_errors=False,
            error_message=None
        )

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ PHASE 2 PROCESSING COMPLETE! (Claude Haiku 4)")
        logger.info(f"{'='*80}")
        logger.info(f"Episode ID: {episode.id}")
        logger.info(f"Recommendations: {saved_count}")
        logger.info(f"Processing time: {processing_time:.1f}s ({processing_time/60:.1f} min)")
        logger.info(f"Estimated cost (Haiku): ${estimated_cost:.4f}")
        logger.info(f"\nView data at: http://localhost:8000/dbtable")
        logger.info(f"Compare Phase 1 vs Phase 2 in the /dbtable endpoint!")

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python process_single_video_phase2.py <youtube_url>")
        sys.exit(1)

    video_url = sys.argv[1]
    process_video(video_url)
