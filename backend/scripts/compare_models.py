#!/usr/bin/env python3
"""
Compare Sonnet vs Haiku output quality for recommendation extraction
Tests on already-processed episodes to see quality differences
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService
from app.models.episode import Episode
from app.database import SessionLocal
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compare_models_on_episode(episode_id: str):
    """Compare Sonnet vs Haiku on a specific episode"""

    db = SessionLocal()
    try:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()

        if not episode:
            logger.error(f"Episode {episode_id} not found")
            return

        logger.info(f"\n{'='*80}")
        logger.info(f"COMPARING MODELS ON: {episode.title[:60]}...")
        logger.info(f"{'='*80}\n")

        # Get transcript
        youtube_service = YouTubeService()
        video_id = youtube_service.extract_video_id(episode.youtube_url)

        logger.info("Fetching transcript...")
        transcript_result = youtube_service.get_transcript_with_verification(video_id)

        if not transcript_result:
            logger.error("Failed to fetch transcript")
            return

        transcript = transcript_result['transcript']
        guest_name = episode.guest_names[0] if episode.guest_names else ""

        logger.info(f"Transcript length: {len(transcript)} characters\n")

        # Test with Sonnet
        logger.info("🔵 Testing with SONNET 4...")
        sonnet_service = ClaudeService(model="claude-sonnet-4-20250514")
        sonnet_recs, sonnet_meta = sonnet_service.extract_recommendations_smart(
            transcript, episode.title, guest_name
        )

        logger.info(f"✅ Sonnet found: {len(sonnet_recs)} recommendations")
        logger.info(f"   Processing mode: {sonnet_meta['processing_mode']}")
        logger.info(f"   Time: ~{sonnet_meta.get('processing_time', 'unknown')}s\n")

        # Test with Haiku
        logger.info("🟢 Testing with HAIKU 4...")
        haiku_service = ClaudeService(model="claude-haiku-4-20250514")
        haiku_recs, haiku_meta = haiku_service.extract_recommendations_smart(
            transcript, episode.title, guest_name
        )

        logger.info(f"✅ Haiku found: {len(haiku_recs)} recommendations")
        logger.info(f"   Processing mode: {haiku_meta['processing_mode']}")
        logger.info(f"   Time: ~{haiku_meta.get('processing_time', 'unknown')}s\n")

        # Compare results
        logger.info(f"\n{'='*80}")
        logger.info("COMPARISON RESULTS")
        logger.info(f"{'='*80}\n")

        logger.info(f"📊 Quantity:")
        logger.info(f"   Sonnet: {len(sonnet_recs)} recommendations")
        logger.info(f"   Haiku:  {len(haiku_recs)} recommendations")
        logger.info(f"   Difference: {abs(len(sonnet_recs) - len(haiku_recs))}\n")

        # Show Sonnet recommendations
        logger.info(f"🔵 SONNET RECOMMENDATIONS:")
        logger.info(f"-" * 80)
        for i, rec in enumerate(sonnet_recs, 1):
            logger.info(f"{i}. [{rec['type'].upper()}] {rec['title']}")
            logger.info(f"   By: {rec.get('recommended_by', 'Unknown')}")
            logger.info(f"   Context: {rec.get('context', '')[:100]}...")
            logger.info("")

        # Show Haiku recommendations
        logger.info(f"\n🟢 HAIKU RECOMMENDATIONS:")
        logger.info(f"-" * 80)
        for i, rec in enumerate(haiku_recs, 1):
            logger.info(f"{i}. [{rec['type'].upper()}] {rec['title']}")
            logger.info(f"   By: {rec.get('recommended_by', 'Unknown')}")
            logger.info(f"   Context: {rec.get('context', '')[:100]}...")
            logger.info("")

        # Find common recommendations
        sonnet_titles = set(r['title'].lower() for r in sonnet_recs)
        haiku_titles = set(r['title'].lower() for r in haiku_recs)
        common = sonnet_titles & haiku_titles
        sonnet_only = sonnet_titles - haiku_titles
        haiku_only = haiku_titles - sonnet_titles

        logger.info(f"\n📊 OVERLAP ANALYSIS:")
        logger.info(f"-" * 80)
        logger.info(f"Common to both: {len(common)}")
        logger.info(f"Sonnet only: {len(sonnet_only)}")
        logger.info(f"Haiku only: {len(haiku_only)}")

        if common:
            logger.info(f"\nCommon recommendations:")
            for title in common:
                logger.info(f"  ✓ {title}")

        if sonnet_only:
            logger.info(f"\nSonnet found but Haiku missed:")
            for title in sonnet_only:
                logger.info(f"  🔵 {title}")

        if haiku_only:
            logger.info(f"\nHaiku found but Sonnet missed:")
            for title in haiku_only:
                logger.info(f"  🟢 {title}")

        logger.info(f"\n{'='*80}\n")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Test on 2 completed episodes"""

    db = SessionLocal()
    try:
        # Get 2 completed episodes
        completed_episodes = db.query(Episode).filter(
            Episode.processing_status == 'completed'
        ).limit(2).all()

        if not completed_episodes:
            logger.error("No completed episodes found to test!")
            return

        logger.info(f"\n🧪 Running model comparison test on {len(completed_episodes)} episodes\n")

        for episode in completed_episodes:
            compare_models_on_episode(episode.id)
            logger.info("\n" + "="*80 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
