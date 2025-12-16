"""
Script to process Lenny's Podcast episodes and extract recommendations

Usage:
    python scripts/process_lenny.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.youtube_service import YouTubeService
from app.services.claude_service import ClaudeService
from app.services.enrichment_service import EnrichmentService
from app.models.podcast import Podcast
from app.models.episode import Episode
from app.models.recommendation import Recommendation
from app.database import SessionLocal, Base, engine
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Last 5 episodes from Lenny's Podcast
# TO ADD URLS: Go to https://www.youtube.com/@LennysPodcast/videos
# Click on the 5 most recent episodes, copy the YouTube URLs
# Replace the VIDEO_ID placeholders below with the actual video IDs from the URLs
#
# Recent guests based on 2025 episodes:
LENNY_EPISODES = [
    {
        "title": "Lenny's Podcast Episode 1",
        "youtube_url": "https://www.youtube.com/watch?v=-LywX3T5Scc",
        "description": "Recent episode from Lenny's Podcast",
        "published_date": "2025-01-15",
        "guest": "Guest 1"
    },
    {
        "title": "Lenny's Podcast Episode 2",
        "youtube_url": "https://www.youtube.com/watch?v=JMeXWVw0r3E",
        "description": "Recent episode from Lenny's Podcast",
        "published_date": "2025-01-10",
        "guest": "Guest 2"
    },
    {
        "title": "Lenny's Podcast Episode 3",
        "youtube_url": "https://www.youtube.com/watch?v=qbvY0dQgSJ4",
        "description": "Recent episode from Lenny's Podcast",
        "published_date": "2025-01-05",
        "guest": "Guest 3"
    },
    {
        "title": "Lenny's Podcast Episode 4",
        "youtube_url": "https://www.youtube.com/watch?v=SWcDfPVTizQ",
        "description": "Recent episode from Lenny's Podcast",
        "published_date": "2024-12-28",
        "guest": "Guest 4"
    },
    {
        "title": "Lenny's Podcast Episode 5",
        "youtube_url": "https://www.youtube.com/watch?v=WyJV6VwEGA8",
        "description": "Recent episode from Lenny's Podcast",
        "published_date": "2024-12-20",
        "guest": "Guest 5"
    },
]


def create_database():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created!")


def get_or_create_podcast(db) -> Podcast:
    """Get or create Lenny's Podcast entry"""
    podcast = db.query(Podcast).filter(Podcast.name == "Lenny's Podcast").first()

    if not podcast:
        logger.info("Creating Lenny's Podcast entry...")
        podcast = Podcast(
            name="Lenny's Podcast",
            youtube_channel_id="@LennysPodcast",
            category="Product Management & Startups",
            image_url="https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400",
            last_fetched_at=datetime.utcnow()
        )
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
        logger.info(f"Created podcast: {podcast.name} (ID: {podcast.id})")

    return podcast


def extract_guest_name_from_title(title: str) -> str:
    """
    Extract guest name from episode title

    Common patterns in Lenny's Podcast:
    - "Name | Topic"
    - "Name: Topic"
    - "Name on Topic"
    - "Topic with Name"
    """
    import re

    # Pattern 1: "Name | Something" or "Name: Something"
    match = re.match(r'^([^|:]+)[\|:]', title)
    if match:
        name = match.group(1).strip()
        # Verify it looks like a name (not too long, contains letters)
        if len(name) < 50 and any(c.isalpha() for c in name):
            return name

    # Pattern 2: "Something with Name" or "Something w/ Name"
    match = re.search(r'(?:with|w/)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
    if match:
        return match.group(1).strip()

    return ""


def process_episode(db, podcast: Podcast, episode_data: dict) -> None:
    """Process a single episode"""
    youtube_url = episode_data["youtube_url"]
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {episode_data['title']}")
    logger.info(f"URL: {youtube_url}")
    logger.info(f"{'='*80}\n")

    # Check if episode already exists
    existing = db.query(Episode).filter(Episode.youtube_url == youtube_url).first()
    if existing and existing.processing_status == "completed":
        logger.info(f"Episode already processed. Skipping.")
        return

    # Initialize services
    youtube_service = YouTubeService()
    claude_service = ClaudeService()
    enrichment_service = EnrichmentService()

    # Extract video ID
    video_id = youtube_service.extract_video_id(youtube_url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {youtube_url}")
        return

    # Get video metadata from YouTube
    logger.info("Fetching video metadata...")
    video_title = youtube_service.get_video_title(video_id) or episode_data["title"]
    logger.info(f"Video title: {video_title}")

    # Extract guest name from title
    guest_name = extract_guest_name_from_title(video_title) or episode_data.get("guest", "")
    if guest_name and not guest_name.startswith("Guest "):
        logger.info(f"Extracted guest name from title: {guest_name}")
    else:
        guest_name = ""

    # Fetch transcript
    logger.info("Fetching transcript...")
    transcript = youtube_service.get_transcript(video_id)

    if not transcript:
        logger.error("Failed to fetch transcript. Skipping episode.")
        return

    logger.info(f"Transcript length: {len(transcript)} characters")

    # Create or update episode
    episode = existing or Episode(
        podcast_id=podcast.id,
        title=video_title,
        description=episode_data.get("description", ""),
        published_date=datetime.strptime(episode_data["published_date"], "%Y-%m-%d"),
        youtube_url=youtube_url,
        guest_names=[guest_name] if guest_name else [],
        transcript_source="youtube",
        processing_status="processing"
    )

    if not existing:
        db.add(episode)
        db.commit()
        db.refresh(episode)

    # Extract recommendations using Claude (smart processing)
    logger.info("Extracting recommendations with Claude API (smart processing)...")

    recommendations, claude_metadata = claude_service.extract_recommendations_smart(
        transcript,
        episode_title=video_title,
        guest_name=guest_name
    )

    logger.info(f"Found {len(recommendations)} recommendations")

    # Save recommendations
    saved_count = 0
    skipped_count = 0

    for i, rec_data in enumerate(recommendations, 1):
        logger.info(f"\nRecommendation {i}/{len(recommendations)}:")
        logger.info(f"  Type: {rec_data.get('type')}")
        logger.info(f"  Title: {rec_data.get('title')}")
        logger.info(f"  Confidence: {rec_data.get('confidence')}")

        # Enrich recommendation
        logger.info(f"  Enriching with external APIs...")
        enriched = enrichment_service.enrich_recommendation(rec_data)

        # Skip if enrichment failed (e.g., book missing required data)
        if enriched is None:
            logger.warning(f"  ⚠️  Skipping recommendation (enrichment failed)")
            skipped_count += 1
            continue

        # Create recommendation model
        rec = Recommendation(
            episode_id=episode.id,
            type=enriched.get("type", "other"),
            title=enriched.get("title", ""),
            recommendation_context=enriched.get("context", ""),
            quote_from_episode=enriched.get("quote", ""),
            timestamp_seconds=0,  # TODO: Extract from transcript if needed
            recommended_by=enriched.get("recommended_by", episode_data.get("guest", "")),
            confidence_score=enriched.get("confidence", 0.5),
            extra_metadata={
                k: v for k, v in enriched.items()
                if k not in ["type", "title", "context", "quote", "confidence", "recommended_by"]
            }
        )

        db.add(rec)
        saved_count += 1
        logger.info(f"  ✅ Saved recommendation")

    # Mark episode as completed
    episode.processing_status = "completed"
    episode.processed_at = datetime.utcnow()
    db.commit()

    logger.info(f"\n✅ Successfully processed episode: {episode_data['title']}")
    logger.info(f"   Extracted: {len(recommendations)} recommendations")
    logger.info(f"   Saved: {saved_count} recommendations")
    logger.info(f"   Skipped: {skipped_count} recommendations (failed enrichment)\n")


def main():
    """Main processing function"""
    logger.info("="*80)
    logger.info("Starting Lenny's Podcast Processing")
    logger.info("="*80)

    # Create database
    create_database()

    # Create database session
    db = SessionLocal()

    try:
        # Get or create podcast
        podcast = get_or_create_podcast(db)

        # Process each episode
        for episode_data in LENNY_EPISODES:
            try:
                process_episode(db, podcast, episode_data)
            except Exception as e:
                logger.error(f"Error processing episode: {str(e)}", exc_info=True)
                continue

        logger.info("\n" + "="*80)
        logger.info("Processing complete!")
        logger.info("="*80)

        # Show summary
        total_episodes = db.query(Episode).filter(Episode.podcast_id == podcast.id).count()
        total_recommendations = db.query(Recommendation).join(Episode).filter(
            Episode.podcast_id == podcast.id
        ).count()

        logger.info(f"\nSummary:")
        logger.info(f"  Total episodes processed: {total_episodes}")
        logger.info(f"  Total recommendations extracted: {total_recommendations}")

    finally:
        db.close()


if __name__ == "__main__":
    logger.info("\n📺 Lenny's Podcast Recommendation Extractor")
    logger.info("="*80)
    logger.info("\nProcessing 5 episodes from Lenny's Podcast...")
    logger.info("This will take approximately 5-10 minutes\n")

    main()
