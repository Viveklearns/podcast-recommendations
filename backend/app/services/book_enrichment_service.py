import logging
from typing import Optional, Dict
from app.services.google_books_service import GoogleBooksService
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class BookEnrichmentService:
    """Service for enriching book recommendations with metadata"""

    def __init__(self):
        self.google_books = GoogleBooksService()

    def enrich_book_recommendation(self, book_data: Dict) -> Optional[Dict]:
        """
        Enrich a book recommendation with complete metadata

        Args:
            book_data: Dict with at minimum 'title' and optionally 'author_creator'

        Returns:
            Enriched book data dict or None if enrichment fails
        """
        title = book_data.get('title', '').strip()
        author = book_data.get('author_creator', '').strip()

        # Skip if title is missing or placeholder
        if not title or title.lower() in ['not specified', 'not mentioned', 'unknown']:
            logger.info(f"Skipping book with invalid title: {title}")
            return None

        # Skip if author is placeholder
        if author.lower() in ['not mentioned', 'not specified', 'unknown']:
            author = None

        logger.info(f"Enriching book: '{title}' by '{author}'")

        # Search Google Books
        google_data = self.google_books.search_book(title, author)

        if not google_data:
            logger.warning(f"Could not find book in Google Books: {title}")
            return None

        # Verify this is a good match
        if not self._is_good_match(title, author, google_data):
            logger.warning(f"Book match confidence too low for: {title}")
            return None

        # Check for required fields
        if not self._has_required_fields(google_data):
            logger.warning(f"Book missing required fields: {title}")
            return None

        # Build enriched data (using camelCase for frontend compatibility)
        enriched = {
            'title': google_data['title'],
            'author': google_data['author'],
            'isbn': google_data.get('isbn_13') or google_data.get('isbn_10'),
            'isbn_10': google_data.get('isbn_10'),
            'isbn_13': google_data.get('isbn_13'),
            'coverImageUrl': google_data.get('image_url'),  # Frontend expects camelCase
            'amazonUrl': google_data.get('amazon_url'),  # Frontend expects camelCase
            'googleBooksId': google_data.get('google_books_id'),  # Frontend expects camelCase
            'publisher': google_data.get('publisher'),
            'publishedYear': google_data.get('published_year'),  # Frontend expects camelCase
            'pageCount': google_data.get('page_count'),  # Frontend expects camelCase
            'description': google_data.get('description'),
            'categories': google_data.get('categories', []),
            'googleBooksUrl': google_data.get('info_link'),  # Frontend expects camelCase
            'verified': True
        }

        # Add Amazon fallback image if still missing
        # This shouldn't be needed since _extract_book_metadata now uses Amazon,
        # but keep as extra safety check
        if not enriched.get('coverImageUrl'):
            if enriched.get('isbn_10'):
                enriched['coverImageUrl'] = self.google_books.get_amazon_image_url(enriched['isbn_10'])
            elif enriched.get('isbn_13'):
                # Convert ISBN-13 to ISBN-10 for Amazon
                isbn_10 = self.google_books._isbn13_to_isbn10(enriched['isbn_13'])
                if isbn_10:
                    enriched['coverImageUrl'] = self.google_books.get_amazon_image_url(isbn_10)
                else:
                    # Final fallback to Open Library
                    enriched['coverImageUrl'] = self.google_books.get_fallback_image_url(enriched['isbn_13'])

        logger.info(f"Successfully enriched book: {enriched['title']}")
        return enriched

    def _is_good_match(self, original_title: str, original_author: Optional[str],
                      google_data: Dict) -> bool:
        """
        Check if Google Books result is a good match

        Args:
            original_title: Original title from extraction
            original_author: Original author from extraction (can be None)
            google_data: Data from Google Books

        Returns:
            True if good match, False otherwise
        """
        found_title = google_data.get('title', '')

        # Title similarity check (fuzzy matching)
        title_similarity = fuzz.ratio(
            original_title.lower(),
            found_title.lower()
        )

        # Require at least 70% title match
        if title_similarity < 70:
            logger.info(f"Title match too low ({title_similarity}%): '{original_title}' vs '{found_title}'")
            return False

        # If we have an author, check that too
        if original_author:
            found_authors = google_data.get('authors', [])
            found_author_str = ' '.join(found_authors).lower()

            author_similarity = fuzz.partial_ratio(
                original_author.lower(),
                found_author_str
            )

            # Require at least 60% author match if author was provided
            if author_similarity < 60:
                logger.info(f"Author match too low ({author_similarity}%): '{original_author}' vs '{found_authors}'")
                return False

        return True

    def _has_required_fields(self, google_data: Dict) -> bool:
        """
        Check if Google Books data has all required fields

        Required:
        - title
        - author
        - ISBN (10 or 13)
        - image_url OR ability to generate fallback
        - amazon_url OR ability to generate from ISBN

        Args:
            google_data: Data from Google Books

        Returns:
            True if all required fields present
        """
        has_title = bool(google_data.get('title'))
        has_author = bool(google_data.get('author'))
        has_isbn = bool(google_data.get('isbn_10') or google_data.get('isbn_13'))
        has_image = bool(google_data.get('image_url'))
        has_amazon_url = bool(google_data.get('amazon_url'))

        # We can generate fallback image from ISBN if needed
        # We can generate Amazon URL from ISBN if needed
        required_fields_met = (
            has_title and
            has_author and
            has_isbn
        )

        if not required_fields_met:
            missing = []
            if not has_title:
                missing.append('title')
            if not has_author:
                missing.append('author')
            if not has_isbn:
                missing.append('ISBN')
            logger.info(f"Missing required fields: {', '.join(missing)}")

        return required_fields_met

    def validate_book_for_display(self, book_dict: Dict) -> bool:
        """
        Validate if a book has all required fields for display

        Args:
            book_dict: Book recommendation dict

        Returns:
            True if book should be displayed, False otherwise
        """
        # Check title
        title = book_dict.get('title', '')
        if not title or title.lower() in ['not specified', 'not mentioned']:
            return False

        # Check recommended_by (guest name)
        recommended_by = book_dict.get('recommendedBy') or book_dict.get('recommended_by')
        if not recommended_by or 'Guest ' in str(recommended_by):
            return False

        # Check author
        author = book_dict.get('author')
        if not author or author.lower() in ['not mentioned', 'not specified']:
            return False

        # Check ISBN
        isbn = book_dict.get('isbn') or book_dict.get('isbn_10') or book_dict.get('isbn_13')
        if not isbn:
            return False

        # Check Amazon URL (use camelCase which is what we now store)
        amazon_url = book_dict.get('amazonUrl') or book_dict.get('amazon_url')
        if not amazon_url:
            return False

        # Check image (use camelCase which is what we now store)
        image_url = book_dict.get('coverImageUrl') or book_dict.get('image_url')
        if not image_url:
            return False

        return True
