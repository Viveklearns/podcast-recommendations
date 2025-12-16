from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from datetime import datetime
import uuid
from app.database import Base


class ProcessingMetrics(Base):
    """
    Track quality metrics for each episode processing run
    Allows comparison across different phases (Phase 1, 2, 3)
    """
    __tablename__ = "processing_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=False)

    # Phase tracking
    phase = Column(String, nullable=False)  # 'phase_1', 'phase_2', 'phase_3'
    processing_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Transcript quality metrics
    total_segments = Column(Integer)
    character_count = Column(Integer)
    word_count = Column(Integer)
    start_time = Column(Float)
    end_time = Column(Float)
    duration_covered_seconds = Column(Float)
    video_duration_seconds = Column(Float)  # Actual video length from YouTube
    coverage_percent = Column(Float)  # Percentage of video covered by transcript
    gaps_detected = Column(Integer)
    is_complete = Column(Boolean)

    # Claude processing metrics
    total_chunks = Column(Integer)
    total_characters_sent = Column(Integer)
    first_chunk_position = Column(Integer)
    last_chunk_position = Column(Integer)
    coverage_verified = Column(Boolean)

    # Recommendation metrics
    total_recommendations_found = Column(Integer)
    unique_recommendations = Column(Integer)
    books_found = Column(Integer)
    movies_found = Column(Integer)
    products_found = Column(Integer)

    # Cost & performance metrics
    ai_model_used = Column(String)  # 'claude-sonnet-4', 'gemini-1.5-flash', etc.
    estimated_cost = Column(Float)  # In USD
    processing_time_seconds = Column(Float)

    # Quality flags
    had_errors = Column(Boolean, default=False)
    error_message = Column(String)

    # Video metadata
    youtube_url = Column(String)  # YouTube video URL

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "episodeId": self.episode_id,
            "phase": self.phase,
            "processingDate": self.processing_date.isoformat() if self.processing_date else None,

            # Transcript metrics
            "transcriptQuality": {
                "totalSegments": self.total_segments,
                "characterCount": self.character_count,
                "wordCount": self.word_count,
                "startTime": self.start_time,
                "endTime": self.end_time,
                "durationCoveredSeconds": self.duration_covered_seconds,
                "videoDurationSeconds": self.video_duration_seconds,
                "coveragePercent": self.coverage_percent,
                "gapsDetected": self.gaps_detected,
                "isComplete": self.is_complete,
            },

            # Claude metrics
            "claudeProcessing": {
                "totalChunks": self.total_chunks,
                "charactersSent": self.total_characters_sent,
                "firstChunkPosition": self.first_chunk_position,
                "lastChunkPosition": self.last_chunk_position,
                "coverageVerified": self.coverage_verified,
            },

            # Recommendations
            "recommendations": {
                "total": self.total_recommendations_found,
                "unique": self.unique_recommendations,
                "books": self.books_found,
                "movies": self.movies_found,
                "products": self.products_found,
            },

            # Performance
            "performance": {
                "aiModel": self.ai_model_used,
                "estimatedCost": self.estimated_cost,
                "processingTimeSeconds": self.processing_time_seconds,
            },

            # Quality
            "hadErrors": self.had_errors,
            "errorMessage": self.error_message,
            "createdAt": self.created_at.isoformat() if self.created_at else None,

            # Video info
            "youtubeUrl": self.youtube_url,
        }
