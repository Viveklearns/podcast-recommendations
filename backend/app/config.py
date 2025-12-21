from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/podcast_recs"

    # API Keys
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_BOOKS_API_KEY: str = ""
    TMDB_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    # Application
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://podbooks.ai",
        "https://www.podbooks.ai",
        "https://podbooks-ai.vercel.app"
    ]

    # Lenny's Podcast Configuration
    LENNY_YOUTUBE_CHANNEL_ID: str = "@LennysPodcast"
    LENNY_PODCAST_NAME: str = "Lenny's Podcast"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
