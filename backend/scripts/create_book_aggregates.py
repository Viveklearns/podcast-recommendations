#!/usr/bin/env python3
"""
Create and populate the book_aggregates table by deduplicating book recommendations.
Books are grouped by ISBN (or title if ISBN is missing).
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import Base
from app.models.book_aggregate import BookAggregate
import uuid


def create_book_aggregates():
    print("🚀 Creating book_aggregates table and populating data...")

    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create table
        print("\n📋 Creating book_aggregates table...")
        Base.metadata.create_all(bind=engine, tables=[BookAggregate.__table__])
        print("✅ Table created")

        # Fetch all book recommendations
        print("\n📚 Fetching book recommendations...")
        result = session.execute(text("""
            SELECT
                id, title, recommended_by, extra_metadata
            FROM recommendations
            WHERE type = 'book'
        """))

        books = result.fetchall()
        print(f"✅ Found {len(books)} book recommendations")

        # Deduplicate by ISBN (or title if no ISBN)
        print("\n🔄 Deduplicating books...")
        book_map = {}

        for book in books:
            # Extract metadata from JSON
            metadata = book.extra_metadata or {}

            # Use ISBN as unique key, fallback to title
            isbn_13 = metadata.get('isbn_13') or metadata.get('isbn13')
            isbn_10 = metadata.get('isbn_10') or metadata.get('isbn10')
            isbn = metadata.get('isbn')
            unique_key = isbn_13 or isbn_10 or isbn or book.title

            if unique_key not in book_map:
                # First occurrence of this book
                book_map[unique_key] = {
                    'id': str(uuid.uuid4()),
                    'isbn': isbn,
                    'isbn_10': isbn_10,
                    'isbn_13': isbn_13,
                    'title': book.title,
                    'author': metadata.get('author'),
                    'cover_image_url': metadata.get('coverImageUrl') or metadata.get('cover_image_url'),
                    'description': metadata.get('description'),
                    'amazon_url': metadata.get('amazonUrl') or metadata.get('amazon_url'),
                    'google_books_url': metadata.get('googleBooksUrl') or metadata.get('google_books_url'),
                    'google_books_id': metadata.get('googleBooksId') or metadata.get('google_books_id'),
                    'primary_theme': metadata.get('primaryTheme') or metadata.get('primary_theme'),
                    'subthemes': metadata.get('subthemes'),
                    'categories': metadata.get('categories'),
                    'topics': metadata.get('topics'),
                    'page_count': metadata.get('pageCount') or metadata.get('page_count'),
                    'published_year': metadata.get('publishedYear') or metadata.get('published_year'),
                    'publisher': metadata.get('publisher'),
                    'style': metadata.get('style'),
                    'fiction_type': metadata.get('fictionType') or metadata.get('fiction_type'),
                    'business_category': metadata.get('businessCategory') or metadata.get('business_category'),
                    'target_audience': metadata.get('targetAudience') or metadata.get('target_audience'),
                    'recommended_by': [book.recommended_by] if book.recommended_by else [],
                    'recommendation_count': 1,
                    'recommendation_ids': [book.id]
                }
            else:
                # Book already exists, add recommender
                if book.recommended_by and book.recommended_by not in book_map[unique_key]['recommended_by']:
                    book_map[unique_key]['recommended_by'].append(book.recommended_by)
                book_map[unique_key]['recommendation_count'] += 1
                book_map[unique_key]['recommendation_ids'].append(book.id)

        print(f"✅ Deduplicated to {len(book_map)} unique books")

        # Clear existing aggregates
        print("\n🗑️  Clearing existing book_aggregates...")
        session.execute(text("DELETE FROM book_aggregates"))
        session.commit()

        # Insert aggregated books
        print("\n💾 Inserting aggregated books...")
        count = 0
        for book_data in book_map.values():
            aggregate = BookAggregate(**book_data)
            session.add(aggregate)
            count += 1

            if count % 100 == 0:
                print(f"   Inserted {count}/{len(book_map)} books...")
                session.commit()

        session.commit()
        print(f"✅ Inserted {len(book_map)} aggregated books")

        # Show top recommended books
        print("\n🏆 Top 10 most recommended books:")
        result = session.execute(text("""
            SELECT title, author, recommendation_count, recommended_by
            FROM book_aggregates
            ORDER BY recommendation_count DESC
            LIMIT 10
        """))

        for i, book in enumerate(result.fetchall(), 1):
            recommenders = ', '.join(book.recommended_by[:3])
            if len(book.recommended_by) > 3:
                recommenders += f" +{len(book.recommended_by) - 3} more"
            print(f"   {i}. {book.title} ({book.recommendation_count}x) - {recommenders}")

        print("\n✅ Book aggregation complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    create_book_aggregates()
