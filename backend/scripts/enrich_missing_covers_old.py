#!/usr/bin/env python3
"""
Enrich missing book covers using Open Library API
"""
import sys
import os
import requests
import time
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.recommendation import Recommendation
from sqlalchemy.orm.attributes import flag_modified

def get_open_library_cover_by_title(title, author=None):
    """Try to get cover from Open Library using title search"""
    try:
        # Build search query
        query = title
        if author:
            query += f" {author}"

        # Search for the book
        search_url = f"https://openlibrary.org/search.json?q={quote(query)}&limit=1"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('docs') and len(data['docs']) > 0:
            book = data['docs'][0]

            # Get cover ID
            cover_id = book.get('cover_i')
            if cover_id:
                # Return large cover URL
                return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

            # Try ISBN if available
            isbn = book.get('isbn', [])
            if isbn:
                isbn_13 = [i for i in isbn if len(i) == 13]
                isbn_10 = [i for i in isbn if len(i) == 10]

                if isbn_10:
                    return f"https://covers.openlibrary.org/b/isbn/{isbn_10[0]}-L.jpg"
                if isbn_13:
                    return f"https://covers.openlibrary.org/b/isbn/{isbn_13[0]}-L.jpg"

        return None

    except Exception as e:
        print(f"  ⚠️  Open Library error for '{title}': {e}")
        return None


def fuzzy_google_books_search(title, author):
    """Retry Google Books with fuzzy/flexible search"""
    from app.services.google_books_service import GoogleBooksService

    service = GoogleBooksService()

    # Try multiple query strategies
    queries = [
        f'intitle:{title}',  # Without quotes
        f'{title} inauthor:{author}' if author else title,
        ' '.join(title.split()[:3]),  # First 3 words
    ]

    for query in queries:
        try:
            params = {'q': query, 'maxResults': 1}
            if service.api_key:
                params['key'] = service.api_key

            response = requests.get(service.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('totalItems', 0) > 0:
                # Extract metadata
                metadata = service._extract_book_metadata(data['items'][0])
                return metadata

        except Exception:
            continue

    return None


def main():
    db = SessionLocal()

    try:
        # Get books without covers
        books_without_covers = db.query(Recommendation).filter(
            Recommendation.type == 'book',
            Recommendation.extra_metadata.op('->>')('coverImageUrl').is_(None)
        ).all()

        print(f"\n📚 Found {len(books_without_covers)} books without covers\n")

        updated_count = 0
        open_library_count = 0
        google_books_count = 0

        for i, book in enumerate(books_without_covers, 1):
            print(f"[{i}/{len(books_without_covers)}] {book.title}")

            metadata = book.extra_metadata or {}
            author = metadata.get('author') or book.recommended_by

            # Strategy 1: Try Open Library
            cover_url = get_open_library_cover_by_title(book.title, author)

            if cover_url:
                # Verify the image actually exists
                try:
                    img_response = requests.head(cover_url, timeout=5)
                    if img_response.status_code == 200:
                        metadata['coverImageUrl'] = cover_url
                        book.extra_metadata = metadata
                        flag_modified(book, 'extra_metadata')
                        updated_count += 1
                        open_library_count += 1
                        print(f"  ✅ Got cover from Open Library")
                    else:
                        cover_url = None
                except:
                    cover_url = None

            # Strategy 2: Try fuzzy Google Books search
            if not cover_url:
                print(f"  🔄 Trying fuzzy Google Books search...")
                google_data = fuzzy_google_books_search(book.title, author)

                if google_data and google_data.get('image_url'):
                    # Update with all Google Books data
                    metadata.update(google_data)
                    book.extra_metadata = metadata
                    flag_modified(book, 'extra_metadata')
                    updated_count += 1
                    google_books_count += 1
                    print(f"  ✅ Got data from Google Books (fuzzy search)")
                else:
                    print(f"  ❌ No cover found")

            # Rate limiting
            time.sleep(0.5)

            # Commit every 10 books
            if i % 10 == 0:
                db.commit()
                print(f"\n💾 Saved progress ({updated_count} covers found so far)\n")

        # Final commit
        db.commit()

        print(f"\n" + "="*60)
        print(f"✅ Enrichment Complete!")
        print(f"="*60)
        print(f"Total books processed: {len(books_without_covers)}")
        print(f"Covers found: {updated_count}")
        print(f"  - Open Library: {open_library_count}")
        print(f"  - Google Books (fuzzy): {google_books_count}")
        print(f"Still missing: {len(books_without_covers) - updated_count}")
        print(f"="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
