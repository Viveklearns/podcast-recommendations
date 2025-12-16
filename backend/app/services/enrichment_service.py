import requests
from app.config import settings
import logging
from typing import Optional, Dict
from app.services.book_enrichment_service import BookEnrichmentService

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service for enriching recommendations with external API data"""

    def __init__(self):
        self.book_enrichment = BookEnrichmentService()

    @staticmethod
    def enrich_book(title: str, author: str = "") -> Dict:
        """
        Enrich book recommendation with Google Books API data

        Returns dictionary with book metadata
        """
        if not settings.GOOGLE_BOOKS_API_KEY or settings.GOOGLE_BOOKS_API_KEY == "your_google_books_api_key_here":
            logger.warning("Google Books API key not configured, skipping enrichment")
            return {}

        try:
            # Build search query
            query = f"{title}"
            if author:
                query += f" {author}"

            url = "https://www.googleapis.com/books/v1/volumes"
            params = {
                "q": query,
                "key": settings.GOOGLE_BOOKS_API_KEY,
                "maxResults": 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "items" in data and len(data["items"]) > 0:
                book = data["items"][0]["volumeInfo"]

                enriched_data = {
                    "author": book.get("authors", [author])[0] if book.get("authors") else author,
                    "description": book.get("description", ""),
                    "publisher": book.get("publisher", ""),
                    "publishedYear": book.get("publishedDate", "")[:4] if book.get("publishedDate") else None,
                    "pageCount": book.get("pageCount"),
                    "coverImageUrl": book.get("imageLinks", {}).get("thumbnail", ""),
                    "isbn": next(
                        (identifier["identifier"] for identifier in book.get("industryIdentifiers", [])
                         if identifier.get("type") == "ISBN_13"),
                        None
                    ),
                    "googleBooksUrl": book.get("infoLink", ""),
                }

                # Clean up the data
                enriched_data = {k: v for k, v in enriched_data.items() if v}

                logger.info(f"Successfully enriched book: {title}")
                return enriched_data

        except Exception as e:
            logger.error(f"Error enriching book '{title}': {str(e)}")

        return {}

    @staticmethod
    def enrich_movie_tv(title: str, year: Optional[int] = None, media_type: str = "movie") -> Dict:
        """
        Enrich movie/TV recommendation with TMDB API data

        Args:
            title: Movie or TV show title
            year: Release year (optional, helps with matching)
            media_type: "movie" or "tv_show"

        Returns dictionary with movie/TV metadata
        """
        if not settings.TMDB_API_KEY or settings.TMDB_API_KEY == "your_tmdb_api_key_here":
            logger.warning("TMDB API key not configured, skipping enrichment")
            return {}

        try:
            # Map our type to TMDB type
            tmdb_type = "tv" if media_type == "tv_show" else "movie"

            # Search for the title
            search_url = f"https://api.themoviedb.org/3/search/{tmdb_type}"
            params = {
                "api_key": settings.TMDB_API_KEY,
                "query": title,
                "language": "en-US"
            }

            if year:
                params["year"] = year if tmdb_type == "movie" else None
                params["first_air_date_year"] = year if tmdb_type == "tv" else None

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                item = data["results"][0]

                enriched_data = {
                    "tmdbId": item.get("id"),
                    "description": item.get("overview", ""),
                    "releaseYear": (item.get("release_date") or item.get("first_air_date", ""))[:4],
                    "rating": item.get("vote_average"),
                    "posterUrl": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "",
                    "backdropUrl": f"https://image.tmdb.org/t/p/w1280{item['backdrop_path']}" if item.get("backdrop_path") else "",
                    "genre": [],  # Would need separate API call for detailed genre names
                }

                # Clean up
                enriched_data = {k: v for k, v in enriched_data.items() if v}

                logger.info(f"Successfully enriched {media_type}: {title}")
                return enriched_data

        except Exception as e:
            logger.error(f"Error enriching {media_type} '{title}': {str(e)}")

        return {}

    def enrich_recommendation(self, recommendation: Dict) -> Optional[Dict]:
        """
        Enrich a recommendation based on its type

        Args:
            recommendation: Dict with at minimum 'type' and 'title' keys

        Returns:
            Updated recommendation dict with enriched metadata, or None if enrichment fails
        """
        rec_type = recommendation.get("type")
        title = recommendation.get("title")

        if not title:
            logger.warning("Recommendation missing title, skipping")
            return None

        # Special handling for books - use new book enrichment service
        if rec_type == "book":
            logger.info(f"Enriching book: {title}")
            enriched_book = self.book_enrichment.enrich_book_recommendation(recommendation)

            if not enriched_book:
                logger.warning(f"Book enrichment failed for: {title}")
                return None  # Skip books that can't be enriched

            # Merge enriched data back into recommendation
            recommendation.update(enriched_book)
            return recommendation

        # For non-books, use existing enrichment (optional)
        enriched_data = {}

        if rec_type in ["movie", "tv_show"]:
            enriched_data = EnrichmentService.enrich_movie_tv(title, media_type=rec_type)

        # Merge enriched data into recommendation
        recommendation.update(enriched_data)

        return recommendation
