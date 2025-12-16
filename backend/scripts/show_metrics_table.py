#!/usr/bin/env python3
"""
Display processing metrics in a pretty table format
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.processing_metrics import ProcessingMetrics


def show_table():
    """Display all metrics in table format"""
    db = SessionLocal()

    try:
        metrics = db.query(ProcessingMetrics).order_by(
            ProcessingMetrics.processing_date.desc()
        ).all()

        if not metrics:
            print("No metrics found yet.")
            return

        print("\n" + "="*200)
        print("PROCESSING METRICS - ALL DATA")
        print("="*200 + "\n")

        # Header
        print(f"{'Phase':<10} {'Segments':<10} {'Chars':<10} {'Words':<8} {'Gaps':<6} {'Complete':<10} "
              f"{'Chunks':<8} {'Total Recs':<11} {'Unique':<8} {'Books':<7} {'Movies':<8} {'Products':<10} "
              f"{'AI Model':<25} {'Cost ($)':<10} {'Time (s)':<10} {'Errors':<8}")
        print("-"*200)

        # Data rows
        for m in metrics:
            phase = m.phase[:10]
            segments = str(m.total_segments or 0)
            chars = f"{m.character_count:,}" if m.character_count else "0"
            words = str(m.word_count or 0)
            gaps = str(m.gaps_detected or 0)
            complete = "Yes" if m.is_complete else "No"
            chunks = str(m.total_chunks or 0)
            total_recs = str(m.total_recommendations_found or 0)
            unique = str(m.unique_recommendations or 0)
            books = str(m.books_found or 0)
            movies = str(m.movies_found or 0)
            products = str(m.products_found or 0)
            model = (m.ai_model_used[:22] + "...") if m.ai_model_used and len(m.ai_model_used) > 25 else (m.ai_model_used or "N/A")
            cost = f"${m.estimated_cost:.4f}" if m.estimated_cost else "$0"
            time = f"{m.processing_time_seconds:.1f}" if m.processing_time_seconds else "0"
            errors = "Yes" if m.had_errors else "No"

            print(f"{phase:<10} {segments:<10} {chars:<10} {words:<8} {gaps:<6} {complete:<10} "
                  f"{chunks:<8} {total_recs:<11} {unique:<8} {books:<7} {movies:<8} {products:<10} "
                  f"{model:<25} {cost:<10} {time:<10} {errors:<8}")

        print("-"*200)
        print(f"\nTotal records: {len(metrics)}")

        # Show detailed view for each record
        print("\n" + "="*200)
        print("DETAILED VIEW")
        print("="*200 + "\n")

        for i, m in enumerate(metrics, 1):
            print(f"Record {i}:")
            print(f"  ID: {m.id}")
            print(f"  Episode ID: {m.episode_id}")
            print(f"  Phase: {m.phase}")
            print(f"  Processing Date: {m.processing_date}")
            print(f"  ")
            print(f"  Transcript Quality:")
            print(f"    - Total segments: {m.total_segments}")
            print(f"    - Character count: {m.character_count:,}")
            print(f"    - Word count: {m.word_count:,}")
            print(f"    - Start time: {m.start_time}s")
            print(f"    - End time: {m.end_time}s")
            print(f"    - Duration covered: {m.duration_covered_seconds}s ({m.duration_covered_seconds/60:.1f} min)")
            print(f"    - Gaps detected: {m.gaps_detected}")
            print(f"    - Is complete: {'Yes' if m.is_complete else 'No'}")
            print(f"  ")
            print(f"  Claude Processing:")
            print(f"    - Total chunks: {m.total_chunks}")
            print(f"    - Characters sent: {m.total_characters_sent:,}")
            print(f"    - First chunk position: {m.first_chunk_position}")
            print(f"    - Last chunk position: {m.last_chunk_position}")
            print(f"    - Coverage verified: {'Yes' if m.coverage_verified else 'No'}")
            print(f"  ")
            print(f"  Recommendations:")
            print(f"    - Total found: {m.total_recommendations_found}")
            print(f"    - Unique (after dedup): {m.unique_recommendations}")
            print(f"    - Books: {m.books_found}")
            print(f"    - Movies: {m.movies_found}")
            print(f"    - Products: {m.products_found}")
            print(f"  ")
            print(f"  Performance:")
            print(f"    - AI Model: {m.ai_model_used}")
            print(f"    - Estimated cost: ${m.estimated_cost:.4f}")
            print(f"    - Processing time: {m.processing_time_seconds:.1f}s ({m.processing_time_seconds/60:.1f} min)")
            print(f"  ")
            print(f"  Quality:")
            print(f"    - Had errors: {'Yes' if m.had_errors else 'No'}")
            if m.error_message:
                print(f"    - Error message: {m.error_message}")
            print(f"    - Created at: {m.created_at}")
            print()

    finally:
        db.close()


if __name__ == "__main__":
    show_table()
