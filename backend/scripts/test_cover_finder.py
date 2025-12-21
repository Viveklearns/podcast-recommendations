#!/usr/bin/env python3
"""
Test cover finding with all Amazon variations and enhanced validation
"""
import sys
import os
import requests
from PIL import Image
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from sqlalchemy import text


def validate_image_url(url, source_name="Unknown"):
    """
    Comprehensive image validation
    Returns: (is_valid, reason, details_dict)
    """
    try:
        # First, HEAD request to check headers
        response = requests.head(url, timeout=5, allow_redirects=True)

        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", {}

        content_type = response.headers.get('content-type', '').lower()
        content_length = int(response.headers.get('content-length', 0))

        # Check content type
        if 'image/gif' in content_type:
            return False, "Placeholder GIF", {'content_type': content_type, 'size': content_length}

        if content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
            return False, f"Invalid type: {content_type}", {'content_type': content_type}

        # Check file size
        if content_length < 10000:  # 10KB minimum
            return False, f"Too small: {content_length} bytes", {'content_type': content_type, 'size': content_length}

        if content_length == 43:  # Known Amazon placeholder
            return False, "Known placeholder (43 bytes)", {'size': 43}

        # If we got here, looks promising! Now download and check dimensions
        response = requests.get(url, timeout=10)
        img = Image.open(io.BytesIO(response.content))
        width, height = img.size

        if width < 100 or height < 100:
            return False, f"Dimensions too small: {width}x{height}", {'width': width, 'height': height, 'size': content_length}

        aspect_ratio = width / height

        details = {
            'content_type': content_type,
            'size': content_length,
            'width': width,
            'height': height,
            'aspect_ratio': round(aspect_ratio, 2)
        }

        return True, "Valid image", details

    except Exception as e:
        return False, f"Error: {str(e)}", {}


def try_amazon_variations(isbn_10, isbn_13):
    """
    Try multiple Amazon URL patterns
    Returns: (url, details) or (None, None)
    """
    patterns = [
        # ISBN-10 variations
        (isbn_10, ".01.LZZZZZZZ.jpg", "ISBN-10 LZZZZZZZ"),
        (isbn_10, ".01._SCLZZZZZZZ_SX500_.jpg", "ISBN-10 SX500"),
        (isbn_10, ".01._SX300_.jpg", "ISBN-10 SX300"),
        (isbn_10, ".01.jpg", "ISBN-10 basic"),
        # ISBN-13 variations
        (isbn_13, ".01.LZZZZZZZ.jpg", "ISBN-13 LZZZZZZZ"),
        (isbn_13, ".01._SCLZZZZZZZ_SX500_.jpg", "ISBN-13 SX500"),
        (isbn_13, ".01._SX300_.jpg", "ISBN-13 SX300"),
        (isbn_13, ".01.jpg", "ISBN-13 basic"),
    ]

    for isbn, suffix, pattern_name in patterns:
        if not isbn:
            continue

        url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn}{suffix}"
        print(f"    Trying Amazon {pattern_name}...")

        is_valid, reason, details = validate_image_url(url, "Amazon")

        if is_valid:
            return url, details, pattern_name
        else:
            print(f"      ❌ {reason}")

    return None, None, None


def try_open_library(isbn_10, isbn_13, title, author):
    """Try Open Library sources"""

    # Try ISBN lookup first
    for isbn in [isbn_13, isbn_10]:
        if not isbn:
            continue

        print(f"    Trying Open Library ISBN: {isbn}...")
        try:
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            response = requests.get(url, timeout=10)
            data = response.json()

            key = f"ISBN:{isbn}"
            if key in data and 'cover' in data[key]:
                cover_url = data[key]['cover'].get('large') or data[key]['cover'].get('medium')
                if cover_url:
                    is_valid, reason, details = validate_image_url(cover_url, "Open Library")
                    if is_valid:
                        return cover_url, details, "Open Library ISBN"
                    else:
                        print(f"      ❌ {reason}")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Try search
    print(f"    Trying Open Library search...")
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
                is_valid, reason, details = validate_image_url(cover_url, "Open Library")
                if is_valid:
                    return cover_url, details, "Open Library Search"
                else:
                    print(f"      ❌ {reason}")
    except Exception as e:
        print(f"      ❌ Error: {e}")

    return None, None, None


def try_google_books(title, author, isbn_13, isbn_10):
    """Try Google Books API"""

    from app.services.google_books_service import GoogleBooksService

    service = GoogleBooksService()

    queries = [
        f'isbn:{isbn_13}' if isbn_13 else None,
        f'isbn:{isbn_10}' if isbn_10 else None,
        f'intitle:"{title}"',
        f'intitle:"{title}" inauthor:"{author}"' if author else None,
    ]

    for query in queries:
        if not query:
            continue

        print(f"    Trying Google Books: {query[:50]}...")

        try:
            params = {'q': query, 'maxResults': 1}
            if service.api_key:
                params['key'] = service.api_key

            response = requests.get(service.BASE_URL, params=params, timeout=10)
            data = response.json()

            if data.get('totalItems', 0) > 0:
                metadata = service._extract_book_metadata(data['items'][0])
                if metadata.get('image_url'):
                    is_valid, reason, details = validate_image_url(metadata['image_url'], "Google Books")
                    if is_valid:
                        return metadata['image_url'], details, f"Google Books ({query[:30]})"
                    else:
                        print(f"      ❌ {reason}")
        except Exception as e:
            print(f"      ❌ Error: {e}")

    return None, None, None


def main():
    # Test books
    test_books = [
        "Predictably Irrational",
        "Stumbling on Happiness",
        "The Psychology of Money",
        "High Growth Handbook"
    ]

    db = SessionLocal()

    results = []

    for book_title in test_books:
        print(f"\n{'='*80}")
        print(f"Testing: {book_title}")
        print(f"{'='*80}")

        # Get book data
        result = db.execute(text("""
            SELECT
                title,
                json_extract(extra_metadata, '$.author') as author,
                json_extract(extra_metadata, '$.isbn_10') as isbn_10,
                json_extract(extra_metadata, '$.isbn_13') as isbn_13,
                json_extract(extra_metadata, '$.coverImageUrl') as current_cover
            FROM recommendations
            WHERE type = 'book'
            AND title LIKE :title
            LIMIT 1
        """), {"title": f"%{book_title}%"}).fetchone()

        if not result:
            print(f"❌ Book not found in database")
            continue

        title, author, isbn_10, isbn_13, current_cover = result

        print(f"Title: {title}")
        print(f"Author: {author}")
        print(f"ISBN-10: {isbn_10}")
        print(f"ISBN-13: {isbn_13}")
        print(f"Current cover: {current_cover[:80] if current_cover else 'None'}...")

        # Try Amazon variations
        print(f"\n  🔍 TRYING AMAZON...")
        amazon_url, amazon_details, amazon_pattern = try_amazon_variations(isbn_10, isbn_13)

        if amazon_url:
            print(f"  ✅ Found on Amazon ({amazon_pattern})")
            print(f"     URL: {amazon_url}")
            print(f"     Details: {amazon_details}")
            results.append({
                'title': title,
                'source': f'Amazon ({amazon_pattern})',
                'url': amazon_url,
                'details': amazon_details
            })
            continue

        # Try Google Books
        print(f"\n  🔍 TRYING GOOGLE BOOKS...")
        google_url, google_details, google_method = try_google_books(title, author, isbn_13, isbn_10)

        if google_url:
            print(f"  ✅ Found on Google Books ({google_method})")
            print(f"     URL: {google_url}")
            print(f"     Details: {google_details}")
            results.append({
                'title': title,
                'source': f'Google Books ({google_method})',
                'url': google_url,
                'details': google_details
            })
            continue

        # Try Open Library
        print(f"\n  🔍 TRYING OPEN LIBRARY...")
        ol_url, ol_details, ol_method = try_open_library(isbn_10, isbn_13, title, author)

        if ol_url:
            print(f"  ✅ Found on Open Library ({ol_method})")
            print(f"     URL: {ol_url}")
            print(f"     Details: {ol_details}")
            results.append({
                'title': title,
                'source': f'Open Library ({ol_method})',
                'url': ol_url,
                'details': ol_details
            })
            continue

        print(f"\n  ❌ No valid cover found from any source")
        results.append({
            'title': title,
            'source': 'NONE',
            'url': None,
            'details': {}
        })

    # Summary
    print(f"\n\n{'='*80}")
    print(f"SUMMARY - FOUND COVERS")
    print(f"{'='*80}\n")

    for r in results:
        print(f"📖 {r['title']}")
        if r['url']:
            print(f"   Source: {r['source']}")
            print(f"   URL: {r['url']}")
            print(f"   Size: {r['details'].get('size', 'N/A')} bytes")
            print(f"   Dimensions: {r['details'].get('width', 'N/A')}x{r['details'].get('height', 'N/A')}")
            print(f"   Aspect ratio: {r['details'].get('aspect_ratio', 'N/A')}")
        else:
            print(f"   ❌ No cover found")
        print()

    db.close()


if __name__ == "__main__":
    main()
