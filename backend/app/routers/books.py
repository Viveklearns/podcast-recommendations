from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
from app.database import get_db
from app.models.book_aggregate import BookAggregate

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("/aggregated")
def get_aggregated_books(
    theme: Optional[str] = Query(None, description="Filter by primary theme"),
    sort: str = Query("recommendation_count", description="Sort field: recommendation_count, title, published_year"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of books to return"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated book recommendations (deduplicated).
    Each book appears once with all recommenders listed.
    """

    # Build query
    query = db.query(BookAggregate)

    # Filter by theme if specified
    if theme:
        query = query.filter(BookAggregate.primary_theme == theme)

    # Apply sorting
    sort_column = getattr(BookAggregate, sort, BookAggregate.recommendation_count)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply limit
    query = query.limit(limit)

    # Execute query
    books = query.all()

    # Convert to dict format
    result = []
    for book in books:
        result.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn,
            "isbn10": book.isbn_10,
            "isbn13": book.isbn_13,
            "coverImageUrl": book.cover_image_url,
            "description": book.description,
            "amazonUrl": book.amazon_url,
            "googleBooksUrl": book.google_books_url,
            "googleBooksId": book.google_books_id,
            "primaryTheme": book.primary_theme,
            "subthemes": book.subthemes,
            "categories": book.categories,
            "topics": book.topics,
            "pageCount": book.page_count,
            "publishedYear": book.published_year,
            "publisher": book.publisher,
            "style": book.style,
            "fictionType": book.fiction_type,
            "businessCategory": book.business_category,
            "targetAudience": book.target_audience,
            "recommendedBy": book.recommended_by,  # Array of names
            "recommendationCount": book.recommendation_count,
            "createdAt": book.created_at.isoformat() if book.created_at else None,
            "updatedAt": book.updated_at.isoformat() if book.updated_at else None,
        })

    return result


@router.get("/themes")
def get_themes(db: Session = Depends(get_db)):
    """
    Get list of all unique themes with book counts.
    """
    from sqlalchemy import func

    result = db.query(
        BookAggregate.primary_theme,
        func.count(BookAggregate.id).label('count')
    ).group_by(
        BookAggregate.primary_theme
    ).order_by(
        desc('count')
    ).all()

    return [
        {"theme": theme, "count": count}
        for theme, count in result
        if theme  # Filter out None values
    ]


@router.get("/by-guest")
def get_books_by_guest(
    guest: Optional[str] = Query(None, description="Filter by guest name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of episodes to return"),
    db: Session = Depends(get_db)
):
    """
    Get book recommendations grouped by episode in chronological order.
    Shows one entry per episode with all books recommended in that episode.
    """
    from app.models import Recommendation, Episode, Podcast
    from sqlalchemy import func

    # Query: Get episodes that have book recommendations
    query = db.query(
        Episode.id.label('episode_id'),
        Episode.title.label('episode_title'),
        Episode.published_date.label('episode_date'),
        Episode.youtube_url.label('episode_url'),
        Podcast.name.label('podcast_name'),
        Podcast.id.label('podcast_id'),
        func.array_agg(Recommendation.id).label('recommendation_ids')
    ).join(
        Recommendation, Recommendation.episode_id == Episode.id
    ).join(
        Podcast, Episode.podcast_id == Podcast.id
    ).filter(
        Recommendation.type == 'book'
    )

    # Apply guest filter if specified
    if guest:
        query = query.filter(Recommendation.recommended_by.ilike(f'%{guest}%'))

    # Group by episode
    query = query.group_by(
        Episode.id,
        Episode.title,
        Episode.published_date,
        Episode.youtube_url,
        Podcast.name,
        Podcast.id
    ).order_by(
        desc(Episode.published_date)
    ).limit(limit)

    episodes_data = query.all()

    # For each episode, get all book recommendations
    result = []
    for ep in episodes_data:
        # Get all books for this episode
        books_query = db.query(Recommendation).filter(
            Recommendation.episode_id == ep.episode_id,
            Recommendation.type == 'book'
        )

        # Apply guest filter to books if specified
        if guest:
            books_query = books_query.filter(Recommendation.recommended_by.ilike(f'%{guest}%'))

        books = books_query.all()

        # Format books
        books_formatted = []
        guest_name = None
        for book in books:
            if not guest_name and book.recommended_by:
                guest_name = book.recommended_by

            book_data = {
                "id": book.id,
                "title": book.title,
                "recommendedBy": book.recommended_by,
            }

            # Add metadata if available
            if book.extra_metadata:
                book_data.update({
                    "author": book.extra_metadata.get('author'),
                    "coverImageUrl": book.extra_metadata.get('coverImageUrl') or book.extra_metadata.get('cover_image_url'),
                    "description": book.extra_metadata.get('description'),
                    "amazonUrl": book.extra_metadata.get('amazonUrl') or book.extra_metadata.get('amazon_url'),
                    "primaryTheme": book.extra_metadata.get('primaryTheme') or book.extra_metadata.get('primary_theme'),
                    "isbn": book.extra_metadata.get('isbn'),
                    "isbn10": book.extra_metadata.get('isbn_10') or book.extra_metadata.get('isbn10'),
                    "isbn13": book.extra_metadata.get('isbn_13') or book.extra_metadata.get('isbn13'),
                })

            books_formatted.append(book_data)

        result.append({
            "episodeId": ep.episode_id,
            "episodeTitle": ep.episode_title,
            "episodeDate": ep.episode_date.isoformat() if ep.episode_date else None,
            "episodeUrl": ep.episode_url,
            "podcastName": ep.podcast_name,
            "podcastId": ep.podcast_id,
            "guestName": guest_name,
            "books": books_formatted,
            "bookCount": len(books_formatted)
        })

    return {
        "total": len(result),
        "episodes": result
    }
