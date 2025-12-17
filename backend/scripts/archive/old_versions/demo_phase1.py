#!/usr/bin/env python3
"""
Quick demo to show Phase 1 improvements in action

This will process ONE episode and show all the captured metadata
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService

# Use a short video for demo
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=tpntW9Tte4M"

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def main():
    print_header("PHASE 1 DATA QUALITY CHECKS - LIVE DEMO")

    youtube_service = YouTubeService()
    claude_service = ClaudeService()

    # Step 1: Get video ID
    video_id = youtube_service.extract_video_id(TEST_VIDEO_URL)
    print(f"📹 Video ID: {video_id}")

    # =================================================================
    # PHASE 1 CHECK #1: TRANSCRIPT VERIFICATION
    # =================================================================
    print_header("CHECK #1: TRANSCRIPT VERIFICATION")
    print("⏳ Fetching transcript with verification...")

    result = youtube_service.get_transcript_with_verification(video_id)

    if not result:
        print("❌ Failed to fetch transcript")
        return

    transcript = result['transcript']
    metadata = result['metadata']

    print("✅ Transcript fetched and verified!\n")

    # Display checks
    print("🔍 QUALITY CHECKS:")
    print(f"   ✓ Total segments captured: {metadata['total_segments']}")
    print(f"   ✓ Character count: {metadata['character_count']:,}")
    print(f"   ✓ Word count: {metadata['word_count']:,}")
    print(f"   ✓ Duration covered: {metadata['duration_covered_seconds']/60:.1f} minutes")
    print(f"   ✓ Gaps detected: {metadata['gaps_detected']}")
    print(f"   ✓ Is complete: {'YES ✅' if metadata['is_complete'] else 'NO ⚠️'}")

    print("\n📍 COVERAGE VERIFICATION:")
    print(f"   Start time: {metadata['start_time']}s")
    print(f"   End time: {metadata['end_time']}s")
    print(f"   Total duration: {metadata['end_time'] - metadata['start_time']:.1f}s")

    if metadata['gaps']:
        print(f"\n⚠️  GAPS FOUND: {len(metadata['gaps'])} gaps detected")
        for gap in metadata['gaps'][:3]:
            print(f"      - Gap at {gap['time']}s ({gap['gap_seconds']}s gap)")
    else:
        print(f"\n✅ NO GAPS: Transcript is continuous")

    # Show this can be stored in database
    print("\n💾 DATABASE STORAGE:")
    print("   This metadata would be stored in: episode.transcript_metadata")
    print(f"   JSON size: {len(json.dumps(metadata))} bytes")

    # =================================================================
    # PHASE 1 CHECK #2: CLAUDE SMART PROCESSING
    # =================================================================
    print_header("CHECK #2: CLAUDE SMART PROCESSING VERIFICATION")

    print(f"📊 Transcript length: {len(transcript):,} characters")
    print(f"   Decision threshold: 100,000 characters")

    if len(transcript) < 100_000:
        print(f"   → Will use SINGLE-PASS processing (faster!)\n")
    else:
        print(f"   → Will use CHUNKED processing (transcript is large)\n")

    # Process with Claude using smart processing
    print(f"⏳ Processing with Claude (smart processing)...")

    recs, claude_metadata = claude_service.extract_recommendations_smart(
        transcript,
        episode_title="Demo Episode",
        guest_name="Demo Guest"
    )

    print(f"✅ Processing complete!\n")

    # Display Claude checks
    print("🔍 PROCESSING VERIFICATION:")
    print(f"   ✓ Processing mode: {claude_metadata.get('processing_mode', 'N/A').upper()}")
    print(f"   ✓ Chunks processed: {claude_metadata['total_chunks']}")
    print(f"   ✓ Total characters sent: {claude_metadata['total_characters_sent']:,}")
    print(f"   ✓ First chunk position: {claude_metadata['first_chunk']['position']}")
    print(f"   ✓ Last chunk position: {claude_metadata['last_chunk']['position']}")
    print(f"   ✓ Recommendations found: {claude_metadata['total_recommendations_found']}")
    print(f"   ✓ Unique after dedup: {claude_metadata['unique_recommendations']}")

    print("\n📍 COVERAGE VERIFICATION:")
    total_sent = claude_metadata['total_characters_sent']
    expected = len(transcript)
    print(f"   Expected to send: {expected:,} chars")
    print(f"   Actually sent: {total_sent:,} chars")
    print(f"   Match: {'YES ✅' if total_sent == expected else 'NO ⚠️'}")

    print("\n📦 PROCESSING BREAKDOWN:")
    for chunk_info in claude_metadata['chunks']:
        print(f"   Chunk {chunk_info['chunk']}: positions {chunk_info['start']:,} → {chunk_info['end']:,} ({chunk_info['length']:,} chars)")

    if claude_metadata.get('processing_mode') == 'single_pass':
        print(f"\n   ✅ Single-pass processing: Entire transcript processed in one API call!")

    # Show this can be stored in database
    print("\n💾 DATABASE STORAGE:")
    print("   This metadata would be stored in: episode.claude_processing_metadata")
    print(f"   JSON size: {len(json.dumps(claude_metadata))} bytes")

    # =================================================================
    # SUMMARY
    # =================================================================
    print_header("SUMMARY: WHAT PHASE 1 GIVES YOU")

    print("✅ TRANSCRIPT QUALITY ASSURANCE:")
    print("   • Know if transcript is complete (no truncation)")
    print("   • Detect gaps in coverage")
    print("   • Verify segment counts and timestamps")
    print("")
    print("✅ CLAUDE PROCESSING VERIFICATION:")
    print("   • Confirm all chunks were processed")
    print("   • Track exact characters sent (for cost)")
    print("   • Verify no text was skipped")
    print("   • Debug which chunks found recommendations")
    print("")
    print("✅ DEBUGGING & MONITORING:")
    print("   • If recommendations missing → check transcript completeness")
    print("   • If costs high → see exact character counts")
    print("   • If quality low → identify problematic segments")
    print("")
    print("📊 ALL DATA STORED IN DATABASE:")
    print("   • episode.transcript_metadata (JSON)")
    print("   • episode.claude_processing_metadata (JSON)")
    print("")
    print("🚀 READY TO USE:")
    print("   • Process new episodes with: python scripts/process_all_pending.py")
    print("   • View metadata with: python scripts/view_metadata.py")
    print("   • Query via API: GET /api/episodes/{id}")
    print("")
    print("=" * 80)
    print(" " * 25 + "PHASE 1 COMPLETE! ✅")
    print("=" * 80)


if __name__ == "__main__":
    main()
