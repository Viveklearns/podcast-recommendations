from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.models import Podcast, Episode, Recommendation
from app.models.processing_metrics import ProcessingMetrics
from app.config import settings
from app.services.book_enrichment_service import BookEnrichmentService
from app.routers import books
from typing import List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Podcast Recommendations API",
    description="API for browsing podcast recommendations extracted from top podcasts",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books.router)


# Create tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready!")


# Helper function to filter valid recommendations
def filter_valid_recommendations(recommendations: List[Recommendation]) -> List[dict]:
    """
    Filter recommendations to only include valid ones based on type-specific rules

    For now, we include all recommendations to show the full dataset.
    Books without enrichment data will be shown but may have incomplete information.

    Args:
        recommendations: List of Recommendation model instances

    Returns:
        List of validated recommendation dictionaries
    """
    valid_recs = []

    for rec in recommendations:
        rec_dict = rec.to_dict()
        # Include all recommendations - show everything we extracted
        valid_recs.append(rec_dict)

    return valid_recs


# Health check
@app.get("/")
async def root():
    return {
        "message": "Podcast Recommendations API",
        "version": "1.0.0",
        "status": "running"
    }


# Get all podcasts
@app.get("/api/podcasts")
async def get_podcasts(db: Session = Depends(get_db)):
    """Get all podcasts"""
    podcasts = db.query(Podcast).all()
    return [p.to_dict() for p in podcasts]


# Get podcast by ID
@app.get("/api/podcasts/{podcast_id}")
async def get_podcast(podcast_id: str, db: Session = Depends(get_db)):
    """Get a specific podcast"""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return podcast.to_dict()


# Get episodes for a podcast
@app.get("/api/podcasts/{podcast_id}/episodes")
async def get_podcast_episodes(podcast_id: str, db: Session = Depends(get_db)):
    """Get all episodes for a podcast"""
    episodes = db.query(Episode).filter(Episode.podcast_id == podcast_id).all()
    return [e.to_dict() for e in episodes]


# Get all episodes
@app.get("/api/episodes")
async def get_episodes(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all episodes"""
    episodes = db.query(Episode).offset(offset).limit(limit).all()
    return [e.to_dict() for e in episodes]


# Get episode by ID
@app.get("/api/episodes/{episode_id}")
async def get_episode(episode_id: str, db: Session = Depends(get_db)):
    """Get a specific episode"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode.to_dict()


# Get all recommendations
@app.get("/api/recommendations")
async def get_recommendations(
    type: Optional[str] = None,
    podcast_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort: str = "recent",
    db: Session = Depends(get_db)
):
    """
    Get all recommendations with optional filtering

    Args:
        type: Filter by recommendation type (book, movie, tv_show, etc.)
        podcast_id: Filter by podcast ID
        limit: Number of results to return
        offset: Number of results to skip
        sort: Sort order (recent, popular)
    """
    query = db.query(Recommendation).join(Episode)

    # Apply filters
    if type:
        query = query.filter(Recommendation.type == type)

    if podcast_id:
        query = query.filter(Episode.podcast_id == podcast_id)

    # Apply sorting
    if sort == "recent":
        query = query.order_by(Recommendation.created_at.desc())

    # Pagination
    recommendations = query.offset(offset).limit(limit).all()

    # Filter to only return valid recommendations (especially books with complete data)
    return filter_valid_recommendations(recommendations)


# Get recommendation by ID
@app.get("/api/recommendations/{recommendation_id}")
async def get_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    """Get a specific recommendation with full details"""
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id
    ).first()

    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # Get episode and podcast details
    episode = db.query(Episode).filter(Episode.id == recommendation.episode_id).first()
    podcast = db.query(Podcast).filter(Podcast.id == episode.podcast_id).first() if episode else None

    result = recommendation.to_dict()
    if episode:
        result["episode"] = episode.to_dict()
    if podcast:
        result["podcast"] = podcast.to_dict()

    return result


# Search recommendations
@app.get("/api/search")
async def search_recommendations(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search recommendations by title or context"""
    recommendations = db.query(Recommendation).filter(
        (Recommendation.title.ilike(f"%{q}%")) |
        (Recommendation.recommendation_context.ilike(f"%{q}%"))
    ).limit(limit).all()

    # Filter to only return valid recommendations (especially books with complete data)
    return filter_valid_recommendations(recommendations)


# Get stats
@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_podcasts = db.query(Podcast).count()
    total_episodes = db.query(Episode).count()
    total_recommendations = db.query(Recommendation).count()
    total_books = db.query(Recommendation).filter(Recommendation.type == "book").count()
    total_movies = db.query(Recommendation).filter(Recommendation.type.in_(["movie", "tv_show"])).count()

    return {
        "totalPodcasts": total_podcasts,
        "totalEpisodes": total_episodes,
        "totalRecommendations": total_recommendations,
        "totalBooks": total_books,
        "totalMovies": total_movies,
    }


# Get recommendations by category
@app.get("/api/analytics/categories")
async def get_recommendations_by_category(db: Session = Depends(get_db)):
    """
    Get breakdown of recommendations by category/type
    Returns count and percentage for each type
    """
    from sqlalchemy import func

    # Get total count
    total_count = db.query(Recommendation).count()

    # Get counts by type
    category_counts = db.query(
        Recommendation.type,
        func.count(Recommendation.id).label('count')
    ).group_by(Recommendation.type).order_by(func.count(Recommendation.id).desc()).all()

    # Format response with percentages
    categories = []
    for type_name, count in category_counts:
        categories.append({
            "type": type_name,
            "count": count,
            "percentage": round((count / total_count * 100), 2) if total_count > 0 else 0
        })

    return {
        "total": total_count,
        "categories": categories
    }


# Get most recommended books
@app.get("/api/analytics/top-books")
async def get_top_recommended_books(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get books that have been recommended multiple times across episodes
    Returns the most frequently recommended books
    """
    from sqlalchemy import func

    # Query for books recommended multiple times
    top_books = db.query(
        Recommendation.title,
        func.count(Recommendation.id).label('times_recommended'),
        func.max(Recommendation.extra_metadata).label('sample_metadata')
    ).filter(
        Recommendation.type == 'book'
    ).group_by(
        func.lower(Recommendation.title)
    ).having(
        func.count(Recommendation.id) > 1
    ).order_by(
        func.count(Recommendation.id).desc()
    ).limit(limit).all()

    # Format response
    books = []
    for title, times_recommended, sample_metadata in top_books:
        book_data = {
            "title": title,
            "timesRecommended": times_recommended
        }

        # Add metadata if available
        if sample_metadata:
            import json
            try:
                metadata = json.loads(sample_metadata) if isinstance(sample_metadata, str) else sample_metadata
                if metadata:
                    book_data["author"] = metadata.get("author")
                    book_data["coverImageUrl"] = metadata.get("coverImageUrl")
                    book_data["isbn"] = metadata.get("isbn")
                    book_data["amazonUrl"] = metadata.get("amazonUrl")
            except:
                pass

        books.append(book_data)

    return {
        "total": len(books),
        "books": books
    }


# Get most recommended items by type
@app.get("/api/analytics/top-recommendations/{rec_type}")
async def get_top_recommendations_by_type(
    rec_type: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get most recommended items for a specific type (books, products, movies, etc.)
    """
    from sqlalchemy import func

    # Query for items recommended multiple times
    top_items = db.query(
        Recommendation.title,
        func.count(Recommendation.id).label('times_recommended')
    ).filter(
        Recommendation.type == rec_type
    ).group_by(
        func.lower(Recommendation.title)
    ).having(
        func.count(Recommendation.id) > 1
    ).order_by(
        func.count(Recommendation.id).desc()
    ).limit(limit).all()

    # Format response
    items = []
    for title, times_recommended in top_items:
        items.append({
            "title": title,
            "timesRecommended": times_recommended
        })

    return {
        "type": rec_type,
        "total": len(items),
        "items": items
    }


@app.get("/dbtable")
@app.get("/api/dbtable")
async def get_processing_metrics_table(db: Session = Depends(get_db)):
    """
    Get all processing metrics in table format
    Shows Phase 1 quality checks for all processed episodes
    """
    metrics = db.query(ProcessingMetrics).order_by(
        ProcessingMetrics.processing_date.desc()
    ).all()

    # Convert to dict format
    metrics_data = []
    for m in metrics:
        metrics_data.append({
            "id": m.id,
            "episodeId": m.episode_id,
            "phase": m.phase,
            "processingDate": m.processing_date.isoformat() if m.processing_date else None,

            # Transcript quality
            "transcriptQuality": {
                "totalSegments": m.total_segments,
                "characterCount": m.character_count,
                "wordCount": m.word_count,
                "startTime": m.start_time,
                "endTime": m.end_time,
                "durationCoveredSeconds": m.duration_covered_seconds,
                "videoDurationSeconds": m.video_duration_seconds,
                "coveragePercent": m.coverage_percent,
                "gapsDetected": m.gaps_detected,
                "isComplete": m.is_complete,
            },

            # Claude processing
            "claudeProcessing": {
                "totalChunks": m.total_chunks,
                "charactersSent": m.total_characters_sent,
                "firstChunkPosition": m.first_chunk_position,
                "lastChunkPosition": m.last_chunk_position,
                "coverageVerified": m.coverage_verified,
            },

            # Recommendations
            "recommendations": {
                "totalFound": m.total_recommendations_found,
                "unique": m.unique_recommendations,
                "books": m.books_found,
                "movies": m.movies_found,
                "products": m.products_found,
            },

            # Performance
            "performance": {
                "aiModel": m.ai_model_used,
                "estimatedCostUSD": m.estimated_cost,
                "processingTimeSeconds": m.processing_time_seconds,
                "processingTimeMinutes": round(m.processing_time_seconds / 60.0, 1) if m.processing_time_seconds else None,
            },

            # Quality flags
            "hadErrors": m.had_errors,
            "errorMessage": m.error_message,
            "createdAt": m.created_at.isoformat() if m.created_at else None,

            # Video info
            "youtubeUrl": m.youtube_url,
        })

    return {
        "total": len(metrics_data),
        "metrics": metrics_data
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
