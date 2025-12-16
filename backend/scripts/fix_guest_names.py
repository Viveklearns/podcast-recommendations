#!/usr/bin/env python3
"""
Fix guest names in all existing episodes
Re-extracts guest names from episode titles using the corrected logic
"""

import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.episode import Episode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_guest_name_from_title(title: str) -> str:
    """Extract guest name from episode title"""
    # Lenny's Podcast format: "Topic description | Guest Name (optional title)"
    # Pattern 1: Extract everything after the pipe "|"
    if '|' in title:
        # Get part after pipe
        after_pipe = title.split('|', 1)[1].strip()
        # Remove any parenthetical info like "(co-founder)", "(Meta, Google)", etc.
        guest_name = re.sub(r'\s*\([^)]*\)\s*$', '', after_pipe).strip()
        # Remove HTML entities
        guest_name = guest_name.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')
        if len(guest_name) < 100 and any(c.isalpha() for c in guest_name):
            return guest_name

    # Pattern 2: "Something with Name" or "Something w/ Name"
    match = re.search(r'(?:with|w/)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
    if match:
        return match.group(1).strip()

    return ""


def main():
    db = SessionLocal()

    try:
        # Get all episodes
        episodes = db.query(Episode).all()

        logger.info(f"Found {len(episodes)} episodes to process")

        updated_count = 0
        no_guest_count = 0

        for episode in episodes:
            # Extract guest name from title
            guest_name = extract_guest_name_from_title(episode.title)

            if guest_name:
                old_guest_names = episode.guest_names
                episode.guest_names = [guest_name]
                updated_count += 1

                logger.info(f"Updated: {episode.title[:60]}...")
                logger.info(f"  Old: {old_guest_names}")
                logger.info(f"  New: {episode.guest_names}")
            else:
                no_guest_count += 1
                logger.warning(f"No guest found: {episode.title[:60]}...")

        # Commit all changes
        db.commit()

        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total episodes: {len(episodes)}")
        logger.info(f"Updated with guest names: {updated_count}")
        logger.info(f"No guest name found: {no_guest_count}")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
