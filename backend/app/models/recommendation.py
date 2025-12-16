from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=False)
    type = Column(String, nullable=False)  # 'book', 'movie', 'tv_show', 'app', 'podcast', 'product', 'other'

    # Common fields
    title = Column(String, nullable=False)

    # Context fields (common to all types)
    recommendation_context = Column(Text)
    quote_from_episode = Column(Text)
    timestamp_seconds = Column(Integer)
    recommended_by = Column(String)
    confidence_score = Column(Float)
    model_used = Column(String)  # e.g., "claude-sonnet-4-20250514", "claude-haiku-4-20250514"

    # Flexible JSON field for type-specific data
    # For books: author, isbn, publisher, published_year, page_count, goodreads_rating, etc.
    # For movies/TV: director, release_year, imdb_id, tmdb_id, genre, rating, etc.
    # For apps/products: category, url, price, etc.
    extra_metadata = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="recommendations")

    def to_dict(self):
        base_dict = {
            "id": self.id,
            "episodeId": self.episode_id,
            "type": self.type,
            "title": self.title,
            "recommendationContext": self.recommendation_context,
            "quoteFromEpisode": self.quote_from_episode,
            "timestampSeconds": self.timestamp_seconds,
            "recommendedBy": self.recommended_by,
            "confidenceScore": self.confidence_score,
            "modelUsed": self.model_used,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Merge extra_metadata fields
        if self.extra_metadata:
            base_dict.update(self.extra_metadata)

        return base_dict
