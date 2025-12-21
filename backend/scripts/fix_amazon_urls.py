#!/usr/bin/env python3
"""
Fix Amazon URLs to use title + author format instead of ISBN
"""
import sys
import os
from urllib.parse import quote_plus

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.recommendation import Recommendation
import json

def main():
    db = SessionLocal()

    try:
        # Get all book recommendations
        books = db.query(Recommendation).filter(Recommendation.type == 'book').all()

        updated_count = 0

        for book in books:
            if not book.extra_metadata:
                continue

            metadata = book.extra_metadata

            # Get title and author
            title = book.title or metadata.get('title')
            author = metadata.get('author')

            if not title:
                continue

            # Generate new Amazon URL
            search_query = title
            if author:
                search_query += ' ' + author

            new_amazon_url = f"https://www.amazon.com/s?k={quote_plus(search_query)}"

            # Update metadata - need to mark as modified for SQLAlchemy
            metadata['amazonUrl'] = new_amazon_url

            # Force SQLAlchemy to detect the change
            from sqlalchemy.orm.attributes import flag_modified
            book.extra_metadata = metadata
            flag_modified(book, 'extra_metadata')

            updated_count += 1

        db.commit()
        print(f"✅ Updated {updated_count} Amazon URLs")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
