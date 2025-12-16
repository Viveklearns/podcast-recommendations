# Podcast Recommendations Aggregator

A web application that automatically extracts and aggregates book, movie, TV show, and other recommendations from podcast transcripts using AI-powered analysis.

## Project Overview

This system processes podcast episodes from YouTube, extracts recommendations using Claude AI, enriches the data with metadata from Google Books API, and provides a web interface to browse and search recommendations.

## Current Status

- **Episodes Processed:** 291/294 (99%)
- **Total Recommendations:** 2,152
- **Books with Complete Data:** 547 (67.5%)
- **Podcast:** Lenny's Podcast

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** SQLite (with WAL mode)
- **AI Model:** Claude Sonnet 4 (Anthropic)
- **APIs:**
  - YouTube Transcript API
  - Google Books API
  - Anthropic Claude API

### Frontend
- **Framework:** Next.js 16 (React)
- **Styling:** Tailwind CSS
- **Language:** TypeScript

## Project Structure

```
podcast/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic services
│   │   └── main.py       # FastAPI application
│   ├── scripts/          # Processing scripts
│   │   ├── process_all_pending.py
│   │   ├── fix_guest_names.py
│   │   └── auto_retry.sh
│   └── podcast_recs.db   # SQLite database
├── podcast-app/          # Next.js frontend
│   └── src/
│       ├── app/
│       │   ├── analytics/   # Analytics dashboard
│       │   └── data/        # Data table view
│       └── components/
└── spec.md               # Technical specification
```

## Setup & Installation

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Add your API keys:
# - ANTHROPIC_API_KEY
# - GOOGLE_BOOKS_API_KEY (optional)
```

4. Run the API server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd podcast-app
npm install
```

2. Run the development server:
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

## API Endpoints

### Recommendations
- `GET /api/recommendations` - List all recommendations
- `GET /api/recommendations/{id}` - Get single recommendation
- `GET /api/analytics/categories` - Breakdown by category
- `GET /api/analytics/top-books` - Most recommended books

### Episodes & Podcasts
- `GET /api/episodes` - List episodes
- `GET /api/podcasts` - List podcasts
- `GET /api/stats` - Overall statistics

## Features

### Data Collection
- ✅ YouTube transcript extraction
- ✅ Smart processing (single-pass vs chunked based on size)
- ✅ Auto-retry system for failed episodes
- ✅ Transcript quality verification (100% coverage)

### AI Analysis
- ✅ Claude Sonnet 4 for recommendation extraction
- ✅ Guest name extraction from episode titles
- ✅ Confidence scoring
- ✅ Context and quote extraction

### Data Enrichment
- ✅ Google Books API integration
- ✅ ISBN, author, cover images
- ✅ Amazon purchase links
- ✅ Publisher, year, page count

### Web Interface
- ✅ Analytics dashboard with charts
- ✅ Data table with filters and search
- ✅ Book cover images
- ✅ Export to CSV

## Database Schema

### Episodes
- Episode metadata (title, URL, duration)
- Guest names
- Processing status
- Transcript metadata
- Claude processing metadata

### Recommendations
- Type (book, movie, tv_show, product, etc.)
- Title, author/creator
- Context and quotes
- Confidence score
- Enrichment data (ISBN, cover, links)
- Model tracking (which AI model extracted it)

### Processing Metrics
- Quality verification data
- Processing time and cost
- Coverage statistics

## Processing Pipeline

1. **Fetch Transcript** - YouTube Transcript API
2. **Extract Guest Name** - Regex from episode title
3. **AI Analysis** - Claude Sonnet 4 extracts recommendations
4. **Enrich Data** - Google Books API for book metadata
5. **Store Results** - SQLite database with full metadata

## Scripts

### Process Episodes
```bash
# Process all pending episodes
python scripts/process_all_pending.py

# Process specific number of episodes
python scripts/process_all_pending.py --limit 10

# Auto-retry every 15 minutes
./scripts/auto_retry.sh
```

### Fix Data
```bash
# Re-extract guest names from all episodes
python scripts/fix_guest_names.py
```

## Cost Estimates

- **Claude API:** ~$0.08 per episode (Sonnet 4)
- **Total for 291 episodes:** ~$17
- **Google Books API:** Free
- **YouTube Transcripts:** Free

## Future Enhancements

- [ ] Add more podcasts (Tim Ferriss, Huberman Lab, etc.)
- [ ] Movie/TV show enrichment (TMDB API)
- [ ] User accounts and favorites
- [ ] Search functionality
- [ ] Filter by date, guest, podcast
- [ ] Recommendation detail pages
- [ ] Mobile optimization

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

Private project - All rights reserved
