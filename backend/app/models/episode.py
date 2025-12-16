from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    podcast_id = Column(String, ForeignKey("podcasts.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    published_date = Column(DateTime)
    duration_seconds = Column(Integer)
    youtube_url = Column(String)
    audio_url = Column(String)
    transcript_url = Column(String)
    guest_names = Column(JSON, default=[])
    transcript_source = Column(String)  # 'youtube', 'rss', 'manual'
    processing_status = Column(String, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Data quality metadata fields
    transcript_metadata = Column(JSON)  # Stores transcript verification data
    claude_processing_metadata = Column(JSON)  # Stores chunk processing data

    # Relationships
    podcast = relationship("Podcast", back_populates="episodes")
    recommendations = relationship("Recommendation", back_populates="episode", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "podcastId": self.podcast_id,
            "title": self.title,
            "description": self.description,
            "publishedDate": self.published_date.isoformat() if self.published_date else None,
            "durationSeconds": self.duration_seconds,
            "youtubeUrl": self.youtube_url,
            "audioUrl": self.audio_url,
            "transcriptUrl": self.transcript_url,
            "guestNames": self.guest_names or [],
            "transcriptSource": self.transcript_source,
            "processingStatus": self.processing_status,
            "processedAt": self.processed_at.isoformat() if self.processed_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "transcriptMetadata": self.transcript_metadata,
            "claudeProcessingMetadata": self.claude_processing_metadata,
        }
