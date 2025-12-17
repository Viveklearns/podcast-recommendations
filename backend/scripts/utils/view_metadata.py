#!/usr/bin/env python3
"""
View captured metadata from Phase 1 improvements

This script shows the verification data stored in the database
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.episode import Episode
from app.models.recommendation import Recommendation


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def format_json(data):
    """Pretty print JSON data"""
    if data:
        return json.dumps(data, indent=2)
    return "No data"


def view_episode_metadata(episode_id=None):
    """View metadata for a specific episode or the most recent one"""

    db = SessionLocal()

    try:
        if episode_id:
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
        else:
            # Get most recently processed episode
            episode = db.query(Episode)\
                .filter(Episode.processing_status == 'completed')\
                .order_by(Episode.processed_at.desc())\
                .first()

        if not episode:
            print("❌ No completed episodes found")
            return

        print_section("EPISODE INFORMATION")
        print(f"Title: {episode.title}")
        print(f"Status: {episode.processing_status}")
        print(f"Processed: {episode.processed_at}")
        print(f"YouTube URL: {episode.youtube_url}")

        # Count recommendations
        rec_count = db.query(Recommendation).filter(Recommendation.episode_id == episode.id).count()
        print(f"Recommendations: {rec_count}")

        # Transcript Metadata
        print_section("TRANSCRIPT METADATA")
        if episode.transcript_metadata:
            metadata = episode.transcript_metadata
            print("✅ Transcript metadata captured!")
            print(f"\n📊 Statistics:")
            print(f"  Total segments: {metadata.get('total_segments', 'N/A')}")
            print(f"  Start time: {metadata.get('start_time', 'N/A')}s")
            print(f"  End time: {metadata.get('end_time', 'N/A')}s")
            print(f"  Duration: {metadata.get('duration_covered_seconds', 0)/60:.1f} minutes")
            print(f"  Characters: {metadata.get('character_count', 0):,}")
            print(f"  Words: {metadata.get('word_count', 0):,}")
            print(f"  Gaps detected: {metadata.get('gaps_detected', 0)}")
            print(f"  Is complete: {'✓ Yes' if metadata.get('is_complete') else '✗ No'}")

            if metadata.get('gaps'):
                print(f"\n⚠️  Gaps found:")
                for gap in metadata['gaps'][:5]:
                    print(f"    - Gap at {gap['time']}s ({gap['gap_seconds']}s)")

            print(f"\n📄 Full JSON:")
            print(format_json(metadata))
        else:
            print("❌ No transcript metadata (episode processed before Phase 1)")

        # Claude Processing Metadata
        print_section("CLAUDE PROCESSING METADATA")
        if episode.claude_processing_metadata:
            metadata = episode.claude_processing_metadata
            print("✅ Claude processing metadata captured!")
            print(f"\n📊 Processing Statistics:")
            print(f"  Total chunks: {metadata.get('total_chunks', 'N/A')}")
            print(f"  Characters sent to Claude: {metadata.get('total_characters_sent', 0):,}")
            print(f"  Recommendations found: {metadata.get('total_recommendations_found', 0)}")
            print(f"  Unique recommendations: {metadata.get('unique_recommendations', 0)}")

            print(f"\n📍 Coverage Verification:")
            first_chunk = metadata.get('first_chunk', {})
            last_chunk = metadata.get('last_chunk', {})
            print(f"  First chunk position: {first_chunk.get('position', 'N/A')}")
            print(f"  First chunk starts: '{first_chunk.get('first_50', 'N/A')[:50]}...'")
            print(f"  Last chunk position: {last_chunk.get('position', 'N/A')}")
            print(f"  Last chunk starts: '{last_chunk.get('last_50', 'N/A')[:50]}...'")

            print(f"\n📦 Chunk Breakdown:")
            for chunk in metadata.get('chunks', [])[:5]:
                print(f"    Chunk {chunk['chunk']}: {chunk['start']:,} → {chunk['end']:,} ({chunk['length']:,} chars)")

            if len(metadata.get('chunks', [])) > 5:
                print(f"    ... and {len(metadata['chunks']) - 5} more chunks")

            print(f"\n📄 Full JSON:")
            print(format_json(metadata))
        else:
            print("❌ No Claude processing metadata (episode processed before Phase 1)")

        # Summary
        print_section("QUALITY CHECKS SUMMARY")

        has_transcript = episode.transcript_metadata is not None
        has_claude = episode.claude_processing_metadata is not None

        if has_transcript and has_claude:
            print("✅ This episode has FULL Phase 1 metadata!")

            # Verify data quality
            trans_meta = episode.transcript_metadata
            claude_meta = episode.claude_processing_metadata

            checks = []
            checks.append(("Transcript complete", trans_meta.get('is_complete', False)))
            checks.append(("No gaps detected", trans_meta.get('gaps_detected', 0) == 0))
            checks.append(("All chunks processed", claude_meta.get('total_chunks', 0) > 0))
            checks.append(("Characters match",
                          abs(trans_meta.get('character_count', 0) - claude_meta.get('total_characters_sent', 0)) < 1000))

            print("\n🔍 Quality Verification:")
            for check_name, passed in checks:
                status = "✅" if passed else "⚠️"
                print(f"  {status} {check_name}")

        elif has_transcript or has_claude:
            print("⚠️  This episode has PARTIAL Phase 1 metadata")
            print(f"  Transcript metadata: {'✅' if has_transcript else '❌'}")
            print(f"  Claude metadata: {'✅' if has_claude else '❌'}")
        else:
            print("❌ This episode was processed BEFORE Phase 1")
            print("   Run: python scripts/process_all_pending.py --limit 1")
            print("   to process a new episode with Phase 1 metadata")

    finally:
        db.close()


def list_episodes_with_metadata():
    """List all episodes and their metadata status"""

    db = SessionLocal()

    try:
        print_section("EPISODES METADATA STATUS")

        episodes = db.query(Episode).order_by(Episode.processed_at.desc()).limit(20).all()

        print(f"{'Status':<12} {'Metadata':<15} {'Title':<50} {'Recs':<5}")
        print("-" * 85)

        for ep in episodes:
            status = ep.processing_status
            has_trans = "✅" if ep.transcript_metadata else "❌"
            has_claude = "✅" if ep.claude_processing_metadata else "❌"
            metadata_status = f"{has_trans} T  {has_claude} C"
            title = (ep.title[:47] + "...") if len(ep.title) > 50 else ep.title
            rec_count = db.query(Recommendation).filter(Recommendation.episode_id == ep.id).count()

            print(f"{status:<12} {metadata_status:<15} {title:<50} {rec_count:<5}")

        print("\n" + "-" * 85)

        # Summary stats
        total = db.query(Episode).count()
        with_transcript = db.query(Episode).filter(Episode.transcript_metadata.isnot(None)).count()
        with_claude = db.query(Episode).filter(Episode.claude_processing_metadata.isnot(None)).count()

        print(f"\n📊 Summary:")
        print(f"  Total episodes: {total}")
        print(f"  With transcript metadata: {with_transcript}")
        print(f"  With Claude metadata: {with_claude}")
        print(f"  Full Phase 1 metadata: {min(with_transcript, with_claude)}")

    finally:
        db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='View Phase 1 metadata from episodes'
    )
    parser.add_argument(
        '--episode-id',
        type=str,
        help='View specific episode by ID'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all episodes with metadata status'
    )

    args = parser.parse_args()

    if args.list:
        list_episodes_with_metadata()
    else:
        view_episode_metadata(args.episode_id)


if __name__ == "__main__":
    main()
