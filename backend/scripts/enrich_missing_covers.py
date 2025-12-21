#!/usr/bin/env python3
"""
Enhanced cover enrichment with multiple fallback sources
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


def isbn13_to_isbn10(isbn13):
    """Convert ISBN-13 to ISBN-10"""
    if not isbn13 or len(isbn13) != 13:
        return None

    isbn10_base = isbn13[3:12]

    # Calculate check digit
    check_sum = sum((10 - i) * int(digit) for i, digit in enumerate(isbn10_base))
    check_digit = (11 - (check_sum % 11)) % 11

    return isbn10_base + ('X' if check_digit == 10 else str(check_digit))


def try_amazon_direct(isbn):
    """Try Amazon's direct image URL pattern"""
    if not isbn:
        return None

    # Try ISBN-10 first (Amazon prefers this)
    isbn_10 = isbn13_to_isbn10(isbn) if len(isbn) == 13 else isbn

    if isbn_10:
        url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn_10}.01.LZZZZZZZ.jpg"
        try:
            response = requests.head(url, timeout=5)
            # Check that it's a real image, not Amazon's placeholder GIF
            content_type = response.headers.get('content-type', '')
            if response.status_code == 200 and 'image/jpeg' in content_type:
                return url
        except:
            pass

    return None


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
            return data[key]['cover'].get('large') or data[key]['cover'].get('medium')
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
                return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except:
        pass

    return None


def try_google_books(title, author):
    """Try Google Books API"""
    try:
        from app.services.google_books_service import GoogleBooksService

        service = GoogleBooksService()
        queries = [
            f'intitle:{title}',
            f'{title} inauthor:{author}' if author else title,
        ]

        for query in queries:
            try:
                params = {'q': query, 'maxResults': 1}
                if service.api_key:
                    params['key'] = service.api_key

                response = requests.get(service.BASE_URL, params=params, timeout=10)
                data = response.json()

                if data.get('totalItems', 0) > 0:
                    metadata = service._extract_book_metadata(data['items'][0])
                    if metadata.get('image_url'):
                        return metadata
            except:
                continue
    except:
        pass

    return None


def get_cover_with_fallbacks(title, author, isbn):
    """Try multiple sources in order of reliability"""

    # Strategy 1: Amazon direct URL (fastest, most reliable)
    if isbn:
        print(f"  📦 Trying Amazon direct URL...")
        cover = try_amazon_direct(isbn)
        if cover:
            return cover, "Amazon Direct"

    # Strategy 2: Open Library by ISBN
    if isbn:
        print(f"  📚 Trying Open Library ISBN lookup...")
        cover = try_open_library_isbn(isbn)
        if cover:
            return cover, "Open Library ISBN"

    # Strategy 3: Open Library search
    print(f"  🔍 Trying Open Library search...")
    cover = try_open_library_search(title, author)
    if cover:
        return cover, "Open Library Search"

    # Strategy 4: Google Books
    print(f"  🌐 Trying Google Books...")
    result = try_google_books(title, author)
    if result and result.get('image_url'):
        return result, "Google Books"

    return None, None


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
        source_stats = {}

        for i, book in enumerate(books_without_covers, 1):
            print(f"[{i}/{len(books_without_covers)}] {book.title}")

            metadata = book.extra_metadata or {}
            author = metadata.get('author') or book.recommended_by
            isbn = metadata.get('isbn_13') or metadata.get('isbn_10') or metadata.get('isbn')

            # Try all sources
            result, source = get_cover_with_fallbacks(book.title, author, isbn)

            if result:
                if isinstance(result, dict):
                    # Google Books returned full metadata
                    metadata.update(result)
                    cover_url = result.get('image_url')
                else:
                    # Just a cover URL
                    metadata['coverImageUrl'] = result
                    cover_url = result

                # Verify image exists and is not a placeholder
                try:
                    img_response = requests.head(cover_url, timeout=5)
                    content_type = img_response.headers.get('content-type', '')

                    # Check for Amazon placeholder GIFs
                    is_placeholder = (img_response.status_code == 200 and
                                    'image/gif' in content_type and
                                    'amazon' in cover_url.lower())

                    if img_response.status_code == 200 and not is_placeholder:
                        book.extra_metadata = metadata
                        flag_modified(book, 'extra_metadata')
                        updated_count += 1
                        source_stats[source] = source_stats.get(source, 0) + 1
                        print(f"  ✅ Got cover from {source}")
                    elif is_placeholder:
                        print(f"  ⚠️  Amazon returned placeholder image, skipping")
                    else:
                        print(f"  ❌ Cover URL returned {img_response.status_code}")
                except Exception as e:
                    print(f"  ⚠️  Could not verify image: {e}")
            else:
                print(f"  ❌ No cover found from any source")

            # Rate limiting
            time.sleep(0.5)

            # Commit every 10 books
            if i % 10 == 0:
                db.commit()
                print(f"\n💾 Saved progress ({updated_count} covers found so far)\n")

        # Final commit
        db.commit()

        print(f"\n" + "="*60)
        print(f"✅ Enhanced Enrichment Complete!")
        print(f"="*60)
        print(f"Total books processed: {len(books_without_covers)}")
        print(f"Covers found: {updated_count}")
        print(f"\nBy source:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {source}: {count}")
        print(f"Still missing: {len(books_without_covers) - updated_count}")
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
