#!/usr/bin/env python3
"""
Database migration script to create processing_metrics table

This table tracks quality metrics for each processing run,
tagged by phase (Phase 1, 2, 3)
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Create processing_metrics table"""

    logger.info("Starting database migration...")

    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='processing_metrics'
        """))

        if result.fetchone():
            logger.info("processing_metrics table already exists. Migration not needed.")
            return

        # Create processing_metrics table
        logger.info("Creating processing_metrics table...")
        conn.execute(text("""
            CREATE TABLE processing_metrics (
                id VARCHAR PRIMARY KEY,
                episode_id VARCHAR NOT NULL,

                -- Phase tracking
                phase VARCHAR NOT NULL,
                processing_date TIMESTAMP NOT NULL,

                -- Transcript quality metrics
                total_segments INTEGER,
                character_count INTEGER,
                word_count INTEGER,
                start_time FLOAT,
                end_time FLOAT,
                duration_covered_seconds FLOAT,
                gaps_detected INTEGER,
                is_complete BOOLEAN,

                -- Claude processing metrics
                total_chunks INTEGER,
                total_characters_sent INTEGER,
                first_chunk_position INTEGER,
                last_chunk_position INTEGER,
                coverage_verified BOOLEAN,

                -- Recommendation metrics
                total_recommendations_found INTEGER,
                unique_recommendations INTEGER,
                books_found INTEGER,
                movies_found INTEGER,
                products_found INTEGER,

                -- Cost & performance metrics
                ai_model_used VARCHAR,
                estimated_cost FLOAT,
                processing_time_seconds FLOAT,

                -- Quality flags
                had_errors BOOLEAN DEFAULT 0,
                error_message VARCHAR,

                created_at TIMESTAMP NOT NULL,

                FOREIGN KEY (episode_id) REFERENCES episodes(id)
            )
        """))
        conn.commit()

        # Create indexes for common queries
        logger.info("Creating indexes...")

        conn.execute(text("""
            CREATE INDEX idx_processing_metrics_episode_id
            ON processing_metrics(episode_id)
        """))
        conn.commit()

        conn.execute(text("""
            CREATE INDEX idx_processing_metrics_phase
            ON processing_metrics(phase)
        """))
        conn.commit()

        conn.execute(text("""
            CREATE INDEX idx_processing_metrics_processing_date
            ON processing_metrics(processing_date)
        """))
        conn.commit()

        logger.info("✓ Created processing_metrics table")
        logger.info("✓ Created indexes")

    logger.info("Migration completed successfully!")


def rollback():
    """Drop processing_metrics table"""

    logger.info("Rolling back migration...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS processing_metrics"))
        conn.commit()
        logger.info("✓ Dropped processing_metrics table")

    logger.info("Rollback completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate database to add processing_metrics table")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the migration (drop table)"
    )

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
