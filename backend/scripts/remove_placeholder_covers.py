#!/usr/bin/env python3
"""
Remove placeholder Amazon cover URLs from all books
"""
import sys
import os
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.recommendation import Recommendation
from sqlalchemy.orm.attributes import flag_modified


def is_placeholder_image(url):
    """Check if URL points to a placeholder image"""
    if not url:
        return False

    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get('content-type', '').lower()

        # Amazon returns image/gif for placeholders
        if 'image/gif' in content_type and 'amazon' in url.lower():
            return True

        # Check file size - placeholders are tiny
        size = int(response.headers.get('content-length', 0))
        if size == 43:  # Known Amazon placeholder size
            return True

        if size < 1000:  # Less than 1KB is likely placeholder
            return True

        return False
    except:
        return True  # If we can't verify, assume it's bad


def main():
    db = SessionLocal()

    try:
        # Get all books
        all_books = db.query(Recommendation).filter(
            Recommendation.type == 'book'
        ).all()

        print(f"\n🔍 Checking {len(all_books)} books for placeholder covers...\n")

        placeholder_count = 0
        checked = 0

        for book in all_books:
            metadata = book.extra_metadata or {}
            cover_url = metadata.get('coverImageUrl')

            if not cover_url:
                continue

            checked += 1

            # Check every 10 books
            if checked % 50 == 0:
                print(f"Checked {checked} books, found {placeholder_count} placeholders so far...")

            if is_placeholder_image(cover_url):
                placeholder_count += 1
                print(f"  Removing placeholder from: {book.title}")
                print(f"    URL: {cover_url[:80]}...")

                # Remove the placeholder URL
                metadata['coverImageUrl'] = None
                book.extra_metadata = metadata
                flag_modified(book, 'extra_metadata')

        # Commit changes
        db.commit()

        print(f"\n" + "="*60)
        print(f"✅ Placeholder Removal Complete!")
        print(f"="*60)
        print(f"Total books checked: {checked}")
        print(f"Placeholders removed: {placeholder_count}")
        print(f"="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
