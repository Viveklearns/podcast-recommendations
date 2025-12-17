#!/usr/bin/env python3
"""
Demo: Save sample metrics to see the database in action
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.services.metrics_service import MetricsService
from app.models.episode import Episode

# Sample data from our test
transcript_metadata = {
    'total_segments': 884,
    'start_time': 0.24,
    'end_time': 2106.26,
    'duration_covered_seconds': 2106.02,
    'character_count': 32962,
    'word_count': 5686,
    'gaps_detected': 0,
    'is_complete': True,
    'gaps': []
}

claude_metadata = {
    'total_chunks': 5,
    'total_characters_sent': 32962,
    'first_chunk': {'position': 0, 'first_50': 'Welcome to Huberman Lab...'},
    'last_chunk': {'position': 25002, 'last_50': '...thank you for joining us.'},
    'chunks': [
        {'chunk': 1, 'start': 0, 'end': 7960, 'length': 7960},
        {'chunk': 2, 'start': 7460, 'end': 15420, 'length': 7960},
        {'chunk': 3, 'start': 14920, 'end': 22790, 'length': 7870},
        {'chunk': 4, 'start': 22290, 'end': 30001, 'length': 7711},
        {'chunk': 5, 'start': 29501, 'end': 32962, 'length': 3461},
    ],
    'total_recommendations_found': 8,
    'unique_recommendations': 5
}

sample_recommendations = [
    {'type': 'book', 'title': 'Atomic Habits'},
    {'type': 'book', 'title': 'Deep Work'},
    {'type': 'movie', 'title': 'The Social Network'},
    {'type': 'product', 'title': 'Whoop Band'},
    {'type': 'product', 'title': 'Oura Ring'},
]

def main():
    db = SessionLocal()

    try:
        # Get a real episode from database
        episode = db.query(Episode).first()

        if not episode:
            print("❌ No episodes found in database")
            return

        print(f"📊 Saving sample metrics for: {episode.title[:60]}...")

        # Save Phase 1 metrics
        metrics_service = MetricsService()

        metrics = metrics_service.save_processing_metrics(
            db=db,
            episode_id=episode.id,
            phase="phase_1",
            transcript_metadata=transcript_metadata,
            claude_metadata=claude_metadata,
            recommendations=sample_recommendations,
            ai_model="claude-sonnet-4-20250514",
            estimated_cost=0.0247,
            processing_time=142.5,
            had_errors=False,
            error_message=None
        )

        print(f"✅ Metrics saved successfully!")
        print(f"\nSaved metrics:")
        print(f"  ID: {metrics.id}")
        print(f"  Phase: {metrics.phase}")
        print(f"  Segments: {metrics.total_segments}")
        print(f"  Characters: {metrics.character_count:,}")
        print(f"  Complete: {metrics.is_complete}")
        print(f"  Cost: ${metrics.estimated_cost:.4f}")
        print(f"  Time: {metrics.processing_time_seconds:.1f}s")
        print(f"  Recommendations: {metrics.unique_recommendations}")

        print(f"\n🔍 Now view the data:")
        print(f"  python scripts/view_phase_metrics.py --phase phase_1")
        print(f"  python scripts/view_phase_metrics.py --list")

    finally:
        db.close()


if __name__ == "__main__":
    main()
