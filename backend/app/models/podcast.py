from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    youtube_channel_id = Column(String)
    rss_feed_url = Column(String)
    category = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_fetched_at = Column(DateTime)

    # Relationships
    episodes = relationship("Episode", back_populates="podcast", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "youtubeChannelId": self.youtube_channel_id,
            "rssFeedUrl": self.rss_feed_url,
            "category": self.category,
            "imageUrl": self.image_url,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastFetchedAt": self.last_fetched_at.isoformat() if self.last_fetched_at else None,
        }
