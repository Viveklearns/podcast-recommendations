#!/usr/bin/env python3
"""
Test the smart processing method that intelligently chooses between
single-pass and chunked processing based on transcript size.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_smart_processing(video_url: str):
    """Test smart processing on a video URL"""

    youtube_service = YouTubeService()
    claude_service = ClaudeService()

    # Extract video info
    video_id = youtube_service.extract_video_id(video_url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {video_url}")
        return

    print(f"{'='*80}")
    print(f"TESTING SMART PROCESSING")
    print(f"{'='*80}\n")
    print(f"Video ID: {video_id}")
    print(f"URL: {video_url}\n")

    # Get video title
    title = youtube_service.get_video_title(video_id)
    print(f"Title: {title}\n")

    # Get transcript
    print("Fetching transcript...")
    result = youtube_service.get_transcript_with_verification(video_id)

    if not result:
        logger.error("Failed to fetch transcript")
        return

    transcript = result['transcript']
    transcript_metadata = result['metadata']

    print(f"✅ Transcript fetched!")
    print(f"   Characters: {transcript_metadata['character_count']:,}")
    print(f"   Words: {transcript_metadata['word_count']:,}")
    print(f"   Duration: {transcript_metadata['duration_covered_seconds']/60:.1f} minutes\n")

    # Test smart processing
    print(f"{'='*80}")
    print("RUNNING SMART PROCESSING")
    print(f"{'='*80}\n")

    recommendations, processing_metadata = claude_service.extract_recommendations_smart(
        transcript,
        episode_title=title,
        guest_name=""
    )

    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}\n")

    print(f"Processing mode: {processing_metadata['processing_mode'].upper()}")
    print(f"Total chunks: {processing_metadata['total_chunks']}")
    print(f"Characters processed: {processing_metadata['total_characters_sent']:,}")
    print(f"Recommendations found: {len(recommendations)}\n")

    if recommendations:
        print("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.get('title', 'N/A')}")
            print(f"   Type: {rec.get('type', 'N/A')}")
            print(f"   Recommended by: {rec.get('recommended_by', 'N/A')}")
            print(f"   Confidence: {rec.get('confidence', 0):.2f}")
            if rec.get('author_creator'):
                print(f"   Creator: {rec.get('author_creator')}")
            print(f"   Context: {rec.get('context', 'N/A')[:100]}...")
    else:
        print("No recommendations found.")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        # Default to the video we just tested
        video_url = "https://www.youtube.com/watch?v=1sClhfuCxP0"

    test_smart_processing(video_url)
