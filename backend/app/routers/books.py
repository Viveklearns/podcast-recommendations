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
