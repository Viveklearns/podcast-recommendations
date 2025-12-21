#!/usr/bin/env python3
"""
Enrich book covers using Google Books API with high-quality zoom=4 images
"""
import sys
import os
import requests
import time
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.recommendation import Recommendation
from sqlalchemy.orm.attributes import flag_modified


def verify_image_url(url):
    """
    Comprehensive verification that URL points to a valid, high-quality image
    Returns: (is_valid, reason, size_bytes)
    """
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)

        # Check HTTP status
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", 0

        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'image/gif' in content_type:
            return False, "Placeholder GIF detected", 0

        if not any(img_type in content_type for img_type in ['image/jpeg', 'image/jpg', 'image/png']):
            return False, f"Invalid content-type: {content_type}", 0

        # Check file size
        size = int(response.headers.get('content-length', 0))
        if size < 10000:  # Less than 10KB
            return False, f"Image too small: {size} bytes", size

        if size == 43:  # Known Amazon placeholder size
            return False, "Known placeholder (43 bytes)", size

        return True, "Valid", size

    except Exception as e:
        return False, f"Error: {str(e)}", 0


def get_google_books_cover(title, author=None, isbn_13=None, isbn_10=None):
    """
    Get high-quality cover from Google Books using imageLinks with zoom=4
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"

    # Try different query strategies in order of specificity
    queries = []

    # ISBN searches are most accurate
    if isbn_13:
        queries.append(f"isbn:{isbn_13}")
    if isbn_10:
        queries.append(f"isbn:{isbn_10}")

    # Title + author search
    if author:
        # Use + for spaces in Google Books API
        title_clean = quote(title)
        author_clean = quote(author)
        queries.append(f"intitle:{title_clean}+inauthor:{author_clean}")

    # Title only search
    title_clean = quote(title)
    queries.append(f"intitle:{title_clean}")

    for query in queries:
        try:
            params = {'q': query, 'maxResults': 1}
            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()

            if data.get('totalItems', 0) > 0:
                volume_info = data['items'][0].get('volumeInfo', {})
                image_links = volume_info.get('imageLinks', {})

                if image_links:
                    book_id = data['items'][0].get('id')

                    # Construct high-quality URL with zoom=4
                    cover_url = f"http://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=4&edge=curl&source=gbs_api"

                    # Verify the image is valid and high-quality
                    is_valid, reason, size = verify_image_url(cover_url)

                    if is_valid:
                        return cover_url, query, size
                    else:
                        # Image didn't pass validation, try next query
                        continue
        except Exception as e:
            continue

    return None, None, None


def main():
    db = SessionLocal()

    try:
        # Get all books without covers
        books_without_covers = db.query(Recommendation).filter(
            Recommendation.type == 'book'
        ).all()

        # Filter to only those truly without covers
        books_to_process = []
        for book in books_without_covers:
            metadata = book.extra_metadata or {}
            cover_url = metadata.get('coverImageUrl')

            # Skip if has a valid cover
            if cover_url:
                continue

            books_to_process.append(book)

        print(f"\n📚 Found {len(books_to_process)} books without covers")
        print(f"🔍 Will search Google Books for high-quality covers (zoom=4)\n")

        updated_count = 0
        failed_count = 0

        for i, book in enumerate(books_to_process, 1):
            print(f"[{i}/{len(books_to_process)}] {book.title}")

            metadata = book.extra_metadata or {}
            author = metadata.get('author') or book.recommended_by
            isbn_13 = metadata.get('isbn_13') or metadata.get('isbn')
            isbn_10 = metadata.get('isbn_10')

            # Try Google Books
            cover_url, query_used, size = get_google_books_cover(
                title=book.title,
                author=author,
                isbn_13=isbn_13,
                isbn_10=isbn_10
            )

            if cover_url:
                metadata['coverImageUrl'] = cover_url
                book.extra_metadata = metadata
                flag_modified(book, 'extra_metadata')
                updated_count += 1

                size_kb = size / 1024
                print(f"  ✅ Found cover ({size_kb:.1f}KB)")
                print(f"     Query: {query_used[:60]}...")
                print(f"     URL: {cover_url[:80]}...")
            else:
                failed_count += 1
                print(f"  ❌ No cover found in Google Books")

            # Rate limiting
            time.sleep(0.5)

            # Commit every 10 books
            if i % 10 == 0:
                db.commit()
                print(f"\n💾 Saved progress ({updated_count} covers found so far)\n")

        # Final commit
        db.commit()

        print(f"\n" + "="*60)
        print(f"✅ Google Books Cover Enrichment Complete!")
        print(f"="*60)
        print(f"Total books processed: {len(books_to_process)}")
        print(f"Covers found: {updated_count}")
        print(f"Not found: {failed_count}")
        print(f"Success rate: {(updated_count/len(books_to_process)*100):.1f}%")
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
