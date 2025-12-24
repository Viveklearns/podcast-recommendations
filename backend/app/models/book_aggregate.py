from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Float
from sqlalchemy.sql import func
from app.database import Base


class BookAggregate(Base):
    """
    Aggregated view of book recommendations.
    Deduplicates books recommended by multiple people.
    """
    __tablename__ = "book_aggregates"

    id = Column(String, primary_key=True)

    # Book identifiers
    isbn = Column(String, index=True, nullable=True)  # Not unique - multiple editions
    isbn_10 = Column(String, nullable=True)
    isbn_13 = Column(String, nullable=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True)

    # Book metadata
    cover_image_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    amazon_url = Column(String, nullable=True)
    google_books_url = Column(String, nullable=True)
    google_books_id = Column(String, nullable=True)

    # Categorization
    primary_theme = Column(String, nullable=True, index=True)
    subthemes = Column(JSON, nullable=True)  # Array of strings
    categories = Column(JSON, nullable=True)  # Array of strings
    topics = Column(JSON, nullable=True)  # Array of strings

    # Book details
    page_count = Column(Integer, nullable=True)
    published_year = Column(Integer, nullable=True)
    publisher = Column(String, nullable=True)
    style = Column(String, nullable=True)
    fiction_type = Column(String, nullable=True)
    business_category = Column(String, nullable=True)
    target_audience = Column(Text, nullable=True)

    # Aggregated recommendation data
    recommended_by = Column(JSON, nullable=False)  # Array of recommender names
    recommendation_count = Column(Integer, nullable=False, default=1, index=True)
    recommendation_ids = Column(JSON, nullable=True)  # Array of original recommendation IDs

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BookAggregate(title='{self.title}', recommendations={self.recommendation_count})>"
