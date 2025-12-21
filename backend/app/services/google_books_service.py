import requests
import logging
from typing import Optional, Dict, List
import re

logger = logging.getLogger(__name__)


class GoogleBooksService:
    """Service for interacting with Google Books API"""

    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Books service

        Args:
            api_key: Optional Google Books API key (not required for basic usage)
        """
        self.api_key = api_key

    def search_book(self, title: str, author: Optional[str] = None) -> Optional[Dict]:
        """
        Search for a book by title and optionally author

        Args:
            title: Book title
            author: Optional author name

        Returns:
            Book data dict or None if not found
        """
        try:
            # Build query
            query_parts = [f'intitle:{title}']
            if author:
                query_parts.append(f'inauthor:{author}')

            query = '+'.join(query_parts)

            params = {
                'q': query,
                'maxResults': 5,  # Get top 5 results
                'printType': 'books',
                'langRestrict': 'en'
            }

            if self.api_key:
                params['key'] = self.api_key

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('totalItems', 0) == 0:
                logger.warning(f"No books found for: {title} by {author}")
                return None

            # Return the best match (first result)
            best_match = data['items'][0]
            return self._extract_book_metadata(best_match)

        except Exception as e:
            logger.error(f"Error searching for book '{title}': {str(e)}")
            return None

    def get_book_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        Get book details by ISBN

        Args:
            isbn: ISBN-10 or ISBN-13

        Returns:
            Book data dict or None if not found
        """
        try:
            # Clean ISBN (remove hyphens, spaces)
            clean_isbn = re.sub(r'[^0-9X]', '', isbn.upper())

            params = {
                'q': f'isbn:{clean_isbn}',
                'maxResults': 1
            }

            if self.api_key:
                params['key'] = self.api_key

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('totalItems', 0) == 0:
                logger.warning(f"No book found for ISBN: {isbn}")
                return None

            return self._extract_book_metadata(data['items'][0])

        except Exception as e:
            logger.error(f"Error fetching book by ISBN '{isbn}': {str(e)}")
            return None

    def validate_isbn(self, isbn: str) -> bool:
        """
        Validate if an ISBN exists in Google Books

        Args:
            isbn: ISBN to validate

        Returns:
            True if valid ISBN found, False otherwise
        """
        result = self.get_book_by_isbn(isbn)
        return result is not None

    def _extract_book_metadata(self, book_item: Dict) -> Dict:
        """
        Extract relevant metadata from Google Books API response

        Args:
            book_item: Book item from Google Books API

        Returns:
            Extracted metadata dict
        """
        volume_info = book_item.get('volumeInfo', {})

        # Extract ISBNs
        isbn_10 = None
        isbn_13 = None
        for identifier in volume_info.get('industryIdentifiers', []):
            if identifier['type'] == 'ISBN_10':
                isbn_10 = identifier['identifier']
            elif identifier['type'] == 'ISBN_13':
                isbn_13 = identifier['identifier']

        # Get image links from Google Books (used for thumbnails and fallback)
        image_links = volume_info.get('imageLinks', {})

        # Prefer Amazon images (highest quality, most reliable)
        # Amazon images require ISBN-10
        image_url = None
        amazon_isbn_10 = isbn_10 or (self._isbn13_to_isbn10(isbn_13) if isbn_13 else None)

        if amazon_isbn_10:
            # Amazon's image URL pattern (multiple formats for better coverage)
            image_url = self.get_amazon_image_url(amazon_isbn_10)

        # Fallback to Open Library if Amazon doesn't have ISBN-10
        if not image_url:
            if isbn_13:
                image_url = self.get_open_library_cover(isbn_13)
            elif isbn_10:
                image_url = self.get_open_library_cover(isbn_10)

        # Final fallback to Google Books images
        if not image_url:
            google_image = (
                image_links.get('large') or
                image_links.get('medium') or
                image_links.get('thumbnail') or
                image_links.get('smallThumbnail')
            )
            # Upgrade HTTP to HTTPS for Google Books images
            if google_image:
                image_url = google_image.replace('http://', 'https://')

        # Build metadata
        metadata = {
            'google_books_id': book_item.get('id'),
            'title': volume_info.get('title'),
            'subtitle': volume_info.get('subtitle'),
            'authors': volume_info.get('authors', []),
            'author': ', '.join(volume_info.get('authors', [])),
            'publisher': volume_info.get('publisher'),
            'published_date': volume_info.get('publishedDate'),
            'published_year': self._extract_year(volume_info.get('publishedDate')),
            'description': volume_info.get('description'),
            'isbn_10': isbn_10,
            'isbn_13': isbn_13,
            'page_count': volume_info.get('pageCount'),
            'categories': volume_info.get('categories', []),
            'average_rating': volume_info.get('averageRating'),
            'ratings_count': volume_info.get('ratingsCount'),
            'image_url': image_url,
            'thumbnail_url': image_links.get('thumbnail'),
            'preview_link': volume_info.get('previewLink'),
            'info_link': volume_info.get('infoLink'),
            'canonical_volume_link': volume_info.get('canonicalVolumeLink'),
        }

        # Generate Amazon URL - use title + author for better reliability
        # Format: https://www.amazon.com/s?k=Title+Author
        from urllib.parse import quote_plus
        title = volume_info.get('title', '')
        authors = volume_info.get('authors', [])
        if title:
            search_query = title
            if authors:
                search_query += ' ' + authors[0]
            metadata['amazon_url'] = f"https://www.amazon.com/s?k={quote_plus(search_query)}"

        return metadata

    def _extract_year(self, date_string: Optional[str]) -> Optional[int]:
        """Extract year from date string like '2020-01-15' or '2020'"""
        if not date_string:
            return None
        try:
            return int(date_string.split('-')[0])
        except (ValueError, IndexError):
            return None

    def _isbn13_to_isbn10(self, isbn13: str) -> Optional[str]:
        """
        Convert ISBN-13 to ISBN-10

        Args:
            isbn13: ISBN-13 string

        Returns:
            ISBN-10 or None if conversion fails
        """
        try:
            # Remove any non-digit characters
            isbn13 = re.sub(r'\D', '', isbn13)

            # ISBN-13 must start with 978 or 979
            if not isbn13.startswith('978'):
                return None

            # Get the middle 9 digits
            isbn10_base = isbn13[3:12]

            # Calculate check digit
            check_sum = 0
            for i, digit in enumerate(isbn10_base):
                check_sum += int(digit) * (10 - i)

            check_digit = (11 - (check_sum % 11)) % 11
            check_char = 'X' if check_digit == 10 else str(check_digit)

            return isbn10_base + check_char

        except Exception as e:
            logger.error(f"Error converting ISBN-13 to ISBN-10: {str(e)}")
            return None

    def get_amazon_image_url(self, isbn_10: str) -> str:
        """
        Get book cover image URL from Amazon

        Amazon provides high-quality book cover images using ISBN-10.
        Uses multiple URL patterns for better coverage.

        Args:
            isbn_10: ISBN-10 of the book

        Returns:
            Amazon image URL
        """
        clean_isbn = re.sub(r'[^0-9X]', '', isbn_10.upper())
        # Amazon's primary image URL pattern (large size)
        # This pattern works for most books and provides high-quality images
        return f"https://images-na.ssl-images-amazon.com/images/P/{clean_isbn}.01._SCLZZZZZZZ_SX500_.jpg"

    def get_open_library_cover(self, isbn: str, size: str = 'L') -> str:
        """
        Get high-quality book cover URL from Open Library

        Open Library provides high-quality, HTTPS book covers that are more
        reliable than Google Books images.

        Args:
            isbn: ISBN of the book
            size: Image size - 'S' (small), 'M' (medium), 'L' (large)

        Returns:
            Open Library cover URL (always returns a URL, browser handles 404s gracefully)
        """
        clean_isbn = re.sub(r'[^0-9X]', '', isbn.upper())
        return f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-{size}.jpg"

    def get_fallback_image_url(self, isbn: str) -> str:
        """
        Get fallback book cover from Open Library (without validation)

        Args:
            isbn: ISBN of the book

        Returns:
            Open Library cover URL
        """
        clean_isbn = re.sub(r'[^0-9X]', '', isbn.upper())
        return f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg"
