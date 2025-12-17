#!/usr/bin/env python3
"""
Database migration script to add metadata fields to episodes table

This adds:
- transcript_metadata: JSON field for transcript verification data
- claude_processing_metadata: JSON field for chunk processing data
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
    """Add metadata columns to episodes table"""

    logger.info("Starting database migration...")

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(episodes)"))
        columns = [row[1] for row in result]

        if 'transcript_metadata' in columns and 'claude_processing_metadata' in columns:
            logger.info("Metadata columns already exist. Migration not needed.")
            return

        # Add transcript_metadata column if it doesn't exist
        if 'transcript_metadata' not in columns:
            logger.info("Adding transcript_metadata column...")
            conn.execute(text("""
                ALTER TABLE episodes
                ADD COLUMN transcript_metadata JSON
            """))
            conn.commit()
            logger.info("✓ Added transcript_metadata column")
        else:
            logger.info("transcript_metadata column already exists")

        # Add claude_processing_metadata column if it doesn't exist
        if 'claude_processing_metadata' not in columns:
            logger.info("Adding claude_processing_metadata column...")
            conn.execute(text("""
                ALTER TABLE episodes
                ADD COLUMN claude_processing_metadata JSON
            """))
            conn.commit()
            logger.info("✓ Added claude_processing_metadata column")
        else:
            logger.info("claude_processing_metadata column already exists")

    logger.info("Migration completed successfully!")


def rollback():
    """Remove metadata columns from episodes table"""

    logger.info("Rolling back migration...")
    logger.warning("SQLite doesn't support DROP COLUMN directly.")
    logger.warning("To rollback, you would need to:")
    logger.warning("1. Create a new table without these columns")
    logger.warning("2. Copy data over")
    logger.warning("3. Drop old table and rename new one")
    logger.warning("This is not implemented in this script for safety reasons.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate database to add metadata fields")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the migration (remove columns)"
    )

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
