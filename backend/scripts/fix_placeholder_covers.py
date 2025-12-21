#!/usr/bin/env python3
"""
Fix books that have placeholder cover images from Amazon
"""
import sys
import os
import requests
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.recommendation import Recommendation
from sqlalchemy.orm.attributes import flag_modified


def is_placeholder_image(url):
    """Check if URL points to a placeholder image"""
    if not url:
        return True

    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get('content-type', '')

        # Amazon returns image/gif for placeholders
        if 'image/gif' in content_type and 'amazon' in url.lower():
            return True

        # Check if it's actually a valid image
        if response.status_code != 200:
            return True

        return False
    except:
        return True


def try_open_library_isbn(isbn):
    """Try Open Library API with ISBN"""
    if not isbn:
        return None

    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        response = requests.get(url, timeout=10)
        data = response.json()

        key = f"ISBN:{isbn}"
        if key in data and 'cover' in data[key]:
            cover = data[key]['cover'].get('large') or data[key]['cover'].get('medium')
            if cover:
                # Verify it's not a placeholder
                test = requests.head(cover, timeout=5)
                if test.status_code == 200 and 'image/jpeg' in test.headers.get('content-type', ''):
                    return cover
    except:
        pass

    return None


def try_open_library_search(title, author):
    """Try Open Library search API"""
    try:
        from urllib.parse import quote
        query = f"{title} {author}" if author else title
        url = f"https://openlibrary.org/search.json?q={quote(query)}&limit=1"

        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('docs') and len(data['docs']) > 0:
            book = data['docs'][0]
            cover_id = book.get('cover_i')
            if cover_id:
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                # Verify it's a real image
                test = requests.head(cover_url, timeout=5)
                if test.status_code == 200:
                    return cover_url
    except:
        pass

    return None


def try_google_books(title, author, isbn):
    """Try Google Books API"""
    try:
        from app.services.google_books_service import GoogleBooksService

        service = GoogleBooksService()
        queries = [
            f'isbn:{isbn}' if isbn else None,
            f'intitle:"{title}"',
            f'intitle:"{title}" inauthor:"{author}"' if author else None,
        ]

        for query in queries:
            if not query:
                continue

            try:
                params = {'q': query, 'maxResults': 1}
                if service.api_key:
                    params['key'] = service.api_key

                response = requests.get(service.BASE_URL, params=params, timeout=10)
                data = response.json()

                if data.get('totalItems', 0) > 0:
                    metadata = service._extract_book_metadata(data['items'][0])
                    if metadata.get('image_url'):
                        # Verify it's accessible
                        test = requests.head(metadata['image_url'], timeout=5)
                        if test.status_code == 200:
                            return metadata
            except:
                continue
    except:
        pass

    return None


def main():
    db = SessionLocal()

    try:
        # Get all books
        all_books = db.query(Recommendation).filter(
            Recommendation.type == 'book'
        ).all()

        print(f"\n📚 Checking {len(all_books)} books for placeholder covers\n")

        books_to_fix = []

        # First pass: identify placeholder images
        for i, book in enumerate(all_books, 1):
            if i % 100 == 0:
                print(f"Checked {i}/{len(all_books)}...")

            metadata = book.extra_metadata or {}
            cover_url = metadata.get('coverImageUrl')

            if cover_url and is_placeholder_image(cover_url):
                books_to_fix.append(book)

        print(f"\n⚠️  Found {len(books_to_fix)} books with placeholder/broken covers\n")

        if len(books_to_fix) == 0:
            print("✅ No placeholder covers found!")
            return

        updated_count = 0
        source_stats = {}

        for i, book in enumerate(books_to_fix, 1):
            print(f"[{i}/{len(books_to_fix)}] {book.title}")

            metadata = book.extra_metadata or {}
            author = metadata.get('author') or book.recommended_by
            isbn_13 = metadata.get('isbn_13') or metadata.get('isbn')
            isbn_10 = metadata.get('isbn_10')

            # Try Open Library first (better quality)
            print(f"  📚 Trying Open Library ISBN...")
            result = try_open_library_isbn(isbn_13 or isbn_10)
            source = "Open Library ISBN"

            if not result:
                print(f"  🔍 Trying Open Library search...")
                result = try_open_library_search(book.title, author)
                source = "Open Library Search"

            if not result:
                print(f"  🌐 Trying Google Books...")
                result = try_google_books(book.title, author, isbn_13 or isbn_10)
                source = "Google Books"

            if result:
                if isinstance(result, dict):
                    # Google Books returned full metadata
                    metadata.update(result)
                    cover_url = result.get('image_url')
                else:
                    # Just a cover URL
                    metadata['coverImageUrl'] = result
                    cover_url = result

                book.extra_metadata = metadata
                flag_modified(book, 'extra_metadata')
                updated_count += 1
                source_stats[source] = source_stats.get(source, 0) + 1
                print(f"  ✅ Found cover from {source}")
            else:
                # Remove the placeholder URL
                metadata['coverImageUrl'] = None
                book.extra_metadata = metadata
                flag_modified(book, 'extra_metadata')
                print(f"  ❌ No valid cover found, removed placeholder")

            # Rate limiting
            time.sleep(0.5)

            # Commit every 10 books
            if i % 10 == 0:
                db.commit()
                print(f"\n💾 Saved progress ({updated_count} covers fixed so far)\n")

        # Final commit
        db.commit()

        print(f"\n" + "="*60)
        print(f"✅ Placeholder Cover Cleanup Complete!")
        print(f"="*60)
        print(f"Placeholder covers checked: {len(books_to_fix)}")
        print(f"Valid covers found: {updated_count}")
        print(f"\nBy source:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {source}: {count}")
        print(f"Removed placeholders: {len(books_to_fix) - updated_count}")
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
