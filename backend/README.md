# Podcast Recommendations Backend

Python FastAPI backend for extracting and managing podcast recommendations.

## Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `GOOGLE_BOOKS_API_KEY` - Get from https://console.cloud.google.com/ (optional for enrichment)
- `TMDB_API_KEY` - Get from https://www.themoviedb.org/settings/api (optional for enrichment)

### 3. Set Up Database

```bash
# Install PostgreSQL if needed
# On macOS: brew install postgresql

# Create database
createdb podcast_recs

# Or update DATABASE_URL in .env to use your existing PostgreSQL
```

### 4. Initialize Database

```bash
python -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
```

## Processing Lenny's Podcast

### Quick Start

```bash
# Process last 5 episodes from Lenny's Podcast
python scripts/process_lenny.py
```

This will:
1. Fetch the last 5 episodes from Lenny's Podcast YouTube channel
2. Extract transcripts using YouTube Transcript API
3. Use Claude API to identify recommendations
4. Enrich recommendations with Google Books and TMDB data
5. Save everything to the database

### API Server

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

API will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── models/
│   │   ├── podcast.py          # Podcast model
│   │   ├── episode.py          # Episode model
│   │   └── recommendation.py   # Recommendation model
│   ├── services/
│   │   ├── youtube_service.py  # YouTube API & transcripts
│   │   ├── claude_service.py   # Claude AI integration
│   │   └── enrichment_service.py  # Google Books, TMDB
│   └── api/
│       └── routes.py           # API endpoints
├── scripts/
│   └── process_lenny.py        # Process Lenny's Podcast
├── requirements.txt
└── .env
```

## API Endpoints

- `GET /api/podcasts` - List all podcasts
- `GET /api/podcasts/{id}` - Get podcast details
- `GET /api/episodes` - List episodes
- `GET /api/recommendations` - List recommendations (with filters)
- `GET /api/recommendations/{id}` - Get recommendation details
- `POST /api/process/podcast/{id}` - Trigger processing for a podcast

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| ANTHROPIC_API_KEY | Claude API key | Yes |
| GOOGLE_BOOKS_API_KEY | Google Books API key | No |
| TMDB_API_KEY | TMDB API key | No |
| YOUTUBE_API_KEY | YouTube Data API key | No |

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests (when available)
pytest

# Format code
black app/
```

## Next Steps

1. Get your ANTHROPIC_API_KEY from Anthropic
2. Run `python scripts/process_lenny.py` to process episodes
3. Start the API server
4. Connect the Next.js frontend to http://localhost:8000
