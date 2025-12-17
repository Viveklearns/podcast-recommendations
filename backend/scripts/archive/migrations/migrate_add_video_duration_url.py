#!/usr/bin/env python3
"""
Migration: Add video_duration_seconds, coverage_percent, and youtube_url to processing_metrics
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add new columns to processing_metrics table"""

    with engine.connect() as conn:
        logger.info("Adding new columns to processing_metrics table...")

        try:
            # Add video_duration_seconds column
            conn.execute(text("""
                ALTER TABLE processing_metrics
                ADD COLUMN video_duration_seconds FLOAT;
            """))
            logger.info("✅ Added video_duration_seconds column")
        except Exception as e:
            logger.warning(f"Column video_duration_seconds may already exist: {e}")

        try:
            # Add coverage_percent column
            conn.execute(text("""
                ALTER TABLE processing_metrics
                ADD COLUMN coverage_percent FLOAT;
            """))
            logger.info("✅ Added coverage_percent column")
        except Exception as e:
            logger.warning(f"Column coverage_percent may already exist: {e}")

        try:
            # Add youtube_url column
            conn.execute(text("""
                ALTER TABLE processing_metrics
                ADD COLUMN youtube_url VARCHAR;
            """))
            logger.info("✅ Added youtube_url column")
        except Exception as e:
            logger.warning(f"Column youtube_url may already exist: {e}")

        conn.commit()
        logger.info("✅ Migration complete!")

        # Verify columns exist
        result = conn.execute(text("PRAGMA table_info(processing_metrics);"))
        columns = [row[1] for row in result.fetchall()]
        logger.info(f"\nCurrent columns in processing_metrics: {columns}")


if __name__ == "__main__":
    migrate()
