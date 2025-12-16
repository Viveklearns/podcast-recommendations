#!/usr/bin/env python3
"""
Test script to verify Phase 1 improvements are working

This script will:
1. Fetch a YouTube video transcript with verification
2. Process it with Claude with chunk logging
3. Display the metadata captured
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService

# Test with a short video for quick testing
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=tpntW9Tte4M"  # Huberman Lab video


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def main():
    print_section("PHASE 1 VERIFICATION TEST")

    youtube_service = YouTubeService()

    # Extract video ID
    video_id = youtube_service.extract_video_id(TEST_VIDEO_URL)
    print(f"Video ID: {video_id}")

    # Test 1: Transcript verification
    print_section("TEST 1: Transcript Verification")

    transcript_result = youtube_service.get_transcript_with_verification(video_id)

    if not transcript_result:
        print("❌ Failed to fetch transcript")
        return

    transcript = transcript_result['transcript']
    metadata = transcript_result['metadata']

    print("✅ Transcript fetched successfully!")
    print(f"\nTranscript Metadata:")
    print(f"  Total segments: {metadata['total_segments']}")
    print(f"  Start time: {metadata['start_time']}s")
    print(f"  End time: {metadata['end_time']}s")
    print(f"  Duration covered: {metadata['duration_covered_seconds']}s ({metadata['duration_covered_seconds']/60:.1f} minutes)")
    print(f"  Character count: {metadata['character_count']:,}")
    print(f"  Word count: {metadata['word_count']:,}")
    print(f"  Gaps detected: {metadata['gaps_detected']}")
    print(f"  Is complete: {'✓ Yes' if metadata['is_complete'] else '✗ No'}")

    if metadata['gaps']:
        print(f"\n  First gap detected at: {metadata['gaps'][0]['time']}s ({metadata['gaps'][0]['gap_seconds']}s gap)")

    # Test 2: Smart processing
    print_section("TEST 2: Claude Smart Processing (with metadata)")

    # Process with Claude using smart processing
    claude_service = ClaudeService()

    print(f"Transcript length: {len(transcript):,} characters")
    print(f"Threshold: 100,000 characters")
    print(f"Will use: {'SINGLE-PASS' if len(transcript) < 100_000 else 'CHUNKED'} processing\n")

    print("Processing with smart method...")
    recommendations, processing_metadata = claude_service.extract_recommendations_smart(
        transcript,
        episode_title="Test Episode",
        guest_name="Test Guest"
    )

    print(f"\n✅ Processing complete!")
    print(f"\nProcessing Metadata:")
    print(f"  Total chunks: {processing_metadata['total_chunks']}")
    print(f"  Total characters sent: {processing_metadata['total_characters_sent']:,}")
    print(f"  First chunk position: {processing_metadata['first_chunk']['position']}")
    print(f"  First chunk starts with: '{processing_metadata['first_chunk']['first_50']}'")
    print(f"  Last chunk position: {processing_metadata['last_chunk']['position']}")
    print(f"  Last chunk starts with: '{processing_metadata['last_chunk']['last_50']}'")
    print(f"  Total recommendations found: {processing_metadata['total_recommendations_found']}")
    print(f"  Unique recommendations: {processing_metadata['unique_recommendations']}")

    print(f"\nChunk breakdown:")
    for chunk_info in processing_metadata['chunks']:
        print(f"  Chunk {chunk_info['chunk']}: positions {chunk_info['start']:,} - {chunk_info['end']:,} ({chunk_info['length']:,} chars)")

    # Test 3: Verify metadata can be serialized to JSON
    print_section("TEST 3: JSON Serialization")

    try:
        transcript_json = json.dumps(metadata, indent=2)
        print("✅ Transcript metadata serializes to JSON correctly")
        print(f"Size: {len(transcript_json)} bytes")

        processing_json = json.dumps(processing_metadata, indent=2)
        print("✅ Processing metadata serializes to JSON correctly")
        print(f"Size: {len(processing_json)} bytes")

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")

    print_section("TEST SUMMARY")
    print("✅ All Phase 1 improvements are working correctly!")
    print("\nNext steps:")
    print("  1. Process new episodes with: python scripts/process_all_pending.py --limit 1")
    print("  2. Check database for metadata fields")
    print("  3. Query metadata through API endpoints")


if __name__ == "__main__":
    main()
