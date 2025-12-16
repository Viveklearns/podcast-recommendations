# Data Extraction Pipeline Documentation

## Overview: From YouTube URL to Recommendations Table

This document explains the complete pipeline for extracting podcast recommendations from YouTube videos.

---

## Pipeline Flow

```
YouTube URL
    ↓
[1. YouTube Discovery Service] → Video metadata
    ↓
[2. YouTube Transcript API] → Raw transcript
    ↓
[3. YouTube Service] → Chunked transcript
    ↓
[4. Claude AI Service] → Raw recommendations JSON
    ↓
[5. Book Enrichment Service] → Enhanced metadata
    ↓
[6. Database Models] → Stored recommendations
    ↓
[7. FastAPI Backend] → JSON API
    ↓
[8. Next.js Frontend] → User Interface
```

---

## Detailed Module Breakdown

### **Module 1: YouTube Discovery Service**
**File:** `app/services/youtube_discovery_service.py`

**Purpose:** Discover and fetch video metadata from YouTube

**Key Functions:**
- `extract_video_id(url)` - Extract video ID from YouTube URL
- `get_playlist_videos(playlist_url)` - Fetch all videos from a playlist
- `get_video_title(video_id)` - Scrape video title from HTML
- `_parse_length_text(length)` - Convert duration (e.g., "1:23:45" → 5025 seconds)

**Technology:**
- Web scraping (requests + BeautifulSoup)
- YouTube Data API v3 (optional, with fallback)
- RSS feed parsing (feedparser)

**Input:** YouTube URL or playlist URL
**Output:** Video metadata (title, duration, published date, URL)

---

### **Module 2: YouTube Transcript API**
**Library:** `youtube-transcript-api` (external package)

**Purpose:** Fetch transcripts/captions from YouTube videos

**Key Functions:**
- `YouTubeTranscriptApi.get_transcript(video_id)` - Get transcript for a video

**Technology:**
- YouTube's internal transcript API
- No API key required
- Rate limited by YouTube

**Input:** Video ID (e.g., "tpntW9Tte4M")
**Output:** List of transcript segments with text and timestamps

**Example Output:**
```python
[
  {'text': 'Welcome to the podcast', 'start': 0.0, 'duration': 2.5},
  {'text': 'Today we discuss...', 'start': 2.5, 'duration': 3.0}
]
```

---

### **Module 3: YouTube Service**
**File:** `app/services/youtube_service.py`

**Purpose:** Process transcripts and prepare them for AI analysis

**Key Functions:**
- `get_transcript(video_id)` - Fetch and combine transcript segments
- `chunk_transcript(transcript, chunk_size=8000)` - Split long transcripts into smaller chunks
- `extract_guest_name_from_title(title)` - Extract guest name using regex

**Technology:**
- String manipulation
- Regular expressions for name extraction

**Input:** Video ID
**Output:**
- Full transcript as plain text
- Chunked transcript (list of 8000-character segments)
- Guest name extracted from title

**Example Chunking:**
```python
transcript = "Very long transcript..." (100,000 chars)
chunks = chunk_transcript(transcript, chunk_size=8000)
# Result: ['chunk 1...', 'chunk 2...', 'chunk 3...'] (13 chunks)
```

---

### **Module 4: Claude AI Service**
**File:** `app/services/claude_service.py`

**Purpose:** Analyze transcripts and extract recommendations using AI

**Key Functions:**
- `extract_recommendations_from_chunks(chunks, episode_title, guest_name)` - Main extraction
- `_parse_recommendations_response(text)` - Parse Claude's JSON response
- `_deduplicate_recommendations(all_recs)` - Remove duplicates

**Technology:**
- Anthropic Claude API (Claude Sonnet 4.5)
- JSON parsing
- Prompt engineering

**Input:**
- Transcript chunks (list of strings)
- Episode title
- Guest name

**Prompt Template:**
```
Analyze the following podcast transcript and extract all recommendations.

Episode Title: {episode_title}
Guest Name: {guest_name}

Transcript:
{transcript_chunk}

For each recommendation, return JSON:
{
  "type": "book|movie|product|app|podcast|other",
  "title": "Title of recommendation",
  "context": "Why it was recommended",
  "quote": "Direct quote from episode",
  "recommended_by": "Guest Name or Host Name",
  "confidence": 0.0-1.0
}
```

**Output:** List of recommendation dictionaries
```python
[
  {
    "type": "book",
    "title": "Atomic Habits",
    "context": "Recommended for building better habits",
    "quote": "I highly recommend reading Atomic Habits...",
    "recommended_by": "Andrew Huberman",
    "confidence": 0.9
  }
]
```

**API Details:**
- Model: claude-sonnet-4-5-20250929
- Max tokens: 4096
- Temperature: 0 (deterministic)
- Processes each chunk independently
- Combines and deduplicates results

---

### **Module 5: Book Enrichment Service**
**File:** `app/services/book_enrichment_service.py`

**Purpose:** Enrich book recommendations with metadata from Google Books

**Key Functions:**
- `enrich_book_recommendation(rec_data)` - Main enrichment
- `search_google_books(title, author)` - Search Google Books API
- `validate_book_for_display(book_dict)` - Validate completeness

**Technology:**
- Google Books API
- ISBN lookup
- Data validation

**Input:** Book recommendation from Claude
```python
{
  "type": "book",
  "title": "Atomic Habits",
  "context": "...",
  "recommended_by": "Andrew Huberman"
}
```

**Output:** Enriched book data
```python
{
  "type": "book",
  "title": "Atomic Habits",
  "author": "James Clear",
  "isbn": "9780735211292",
  "isbn_10": "0735211299",
  "isbn_13": "9780735211292",
  "publisher": "Penguin Random House",
  "publishedYear": "2018",
  "pageCount": 320,
  "description": "Tiny changes, remarkable results...",
  "coverImageUrl": "https://books.google.com/...",
  "amazonUrl": "https://amazon.com/dp/0735211299",
  "googleBooksUrl": "https://books.google.com/books?id=...",
  "googleBooksId": "fFCjDQAAQBAJ",
  "categories": ["Self-Help", "Psychology"],
  "verified": true
}
```

**API Details:**
- Endpoint: `https://www.googleapis.com/books/v1/volumes`
- Rate limited: 1000 requests/day (free tier)
- API key from environment variable

---

### **Module 6: Database Models**
**Files:**
- `app/models/podcast.py`
- `app/models/episode.py`
- `app/models/recommendation.py`

**Purpose:** Store all extracted data in SQLite database

**Database Schema:**

**Podcasts Table:**
```sql
CREATE TABLE podcasts (
  id VARCHAR PRIMARY KEY,
  name VARCHAR,
  youtube_channel_id VARCHAR,
  category VARCHAR,
  image_url VARCHAR,
  created_at TIMESTAMP,
  last_fetched_at TIMESTAMP
);
```

**Episodes Table:**
```sql
CREATE TABLE episodes (
  id VARCHAR PRIMARY KEY,
  podcast_id VARCHAR FOREIGN KEY,
  title VARCHAR,
  description TEXT,
  published_date TIMESTAMP,
  duration_seconds INTEGER,
  youtube_url VARCHAR,
  guest_names JSON,  -- ["Guest Name 1", "Guest Name 2"]
  transcript_source VARCHAR,
  processing_status VARCHAR,  -- pending|processing|completed|failed
  processed_at TIMESTAMP,
  created_at TIMESTAMP
);
```

**Recommendations Table:**
```sql
CREATE TABLE recommendations (
  id VARCHAR PRIMARY KEY,
  episode_id VARCHAR FOREIGN KEY,
  type VARCHAR,  -- book|movie|product|app|podcast|other
  title VARCHAR,
  recommendation_context TEXT,
  quote_from_episode TEXT,
  timestamp_seconds INTEGER,
  recommended_by VARCHAR,  -- Guest or host name
  confidence_score FLOAT,  -- 0.0-1.0
  extra_metadata JSON,  -- Book ISBNs, movie ratings, etc.
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Technology:**
- SQLAlchemy ORM
- SQLite database
- JSON fields for flexible metadata

---

### **Module 7: FastAPI Backend**
**File:** `app/main.py`

**Purpose:** Expose data via REST API

**Key Endpoints:**

```
GET /api/stats
→ Returns: { totalPodcasts, totalEpisodes, totalRecommendations, totalBooks, totalMovies }

GET /api/podcasts
→ Returns: List of all podcasts

GET /api/episodes?limit=20&offset=0
→ Returns: List of episodes with pagination

GET /api/recommendations?type=book&limit=50&offset=0
→ Returns: List of recommendations with filtering
  - Filter by type (book, movie, product, etc.)
  - Filter by podcast_id
  - Pagination with limit/offset
  - Sort by recent or popular

GET /api/recommendations/{id}
→ Returns: Single recommendation with full details

GET /api/search?q=atomic+habits
→ Returns: Search results across recommendations
```

**Technology:**
- FastAPI framework
- CORS enabled for frontend
- Automatic OpenAPI docs at `/docs`

---

### **Module 8: Next.js Frontend**
**Directory:** `/podcast-app/src/`

**Purpose:** Display recommendations to users

**Key Pages:**

**1. Homepage (`/`)**
- File: `src/app/page.tsx`
- Shows featured recommendations, books, movies
- Stats overview

**2. Browse Page (`/browse`)**
- File: `src/app/browse/page.tsx`
- Filter by type (books, movies, products)
- Shows all 247 recommendations

**3. Data Table (`/data`)**
- File: `src/app/data/page.tsx`
- Complete data view with all fields
- Search and filter capabilities
- CSV export

**4. Recommendation Detail (`/recommendations/[id]`)**
- File: `src/app/recommendations/[id]/page.tsx`
- Full details for single recommendation
- Amazon/Google Books links for books
- Episode and podcast context

**Technology:**
- Next.js 14 (React framework)
- TypeScript
- Tailwind CSS
- Client-side data fetching with useEffect

---

## Processing Scripts

### **Script 1: Discovery and Episode Import**
**File:** `scripts/discover_episodes.py`

**Usage:**
```bash
python scripts/discover_episodes.py --podcast "Huberman Lab"
```

**What it does:**
1. Fetches videos from YouTube channel/playlist
2. Filters by duration (60+ minutes for Tim Ferriss)
3. Creates episode records with status='pending'
4. Stores in database

---

### **Script 2: Recommendation Extraction**
**File:** `scripts/process_all_pending.py`

**Usage:**
```bash
python scripts/process_all_pending.py --limit 10
python scripts/process_all_pending.py --podcast "Lenny's Podcast"
```

**What it does:**
1. Finds all episodes with status='pending'
2. For each episode:
   - Fetch transcript (Module 2)
   - Extract guest name (Module 3)
   - Chunk transcript (Module 3)
   - Analyze with Claude (Module 4)
   - Enrich books (Module 5)
   - Save recommendations (Module 6)
   - Mark episode as 'completed'
3. Includes 5-second delay between episodes to avoid rate limiting

**Output:**
```
Processing episode 1/109
================================================================================
Processing: Atomic Habits | James Clear
Podcast: Lenny's Podcast
URL: https://www.youtube.com/watch?v=...
================================================================================

Fetching video metadata...
Fetching transcript...
Transcript length: 95,432 characters
Extracting recommendations with Claude API...
Split transcript into 12 chunks
Processing chunk 1/12
Processing chunk 2/12
...
Found 8 recommendations

Recommendation 1/8:
  Type: book
  Title: Atomic Habits
  By: James Clear
  Enriching book with Google Books API...
  ✅ Enriched: 9780735211292

✅ Episode completed: 8 recommendations saved
```

---

## Data Flow Example: Complete Journey

### Step-by-Step: From YouTube to Frontend

**Starting Point:** `https://www.youtube.com/watch?v=tpntW9Tte4M`

**Step 1: Video Discovery**
```python
# YouTubeDiscoveryService extracts metadata
video_id = "tpntW9Tte4M"
title = "Erasing Fears & Traumas Using Modern Neuroscience"
duration = 1942  # seconds
```

**Step 2: Transcript Fetching**
```python
# YouTubeTranscriptApi fetches transcript
transcript = """
Welcome to the Huberman Lab podcast where we discuss
science and science-based tools for everyday life...
[32,962 characters total]
"""
```

**Step 3: Transcript Chunking**
```python
# YouTubeService chunks into manageable pieces
chunks = [
  "Welcome to the Huberman Lab podcast... [7976 chars]",
  "...continuing the discussion... [7925 chars]",
  "...and in conclusion... [7870 chars]",
  "...final thoughts... [3487 chars]"
]  # 5 chunks total
```

**Step 4: Claude AI Analysis**
```python
# ClaudeService sends each chunk to AI
# Chunk 1 → Claude → []
# Chunk 2 → Claude → []
# Chunk 3 → Claude → []
# Chunk 4 → Claude → [
#   {"type": "product", "title": "Cyclic Hyperventilation Breathing Protocol", ...},
#   {"type": "other", "title": "Ketamine Assisted Psychotherapy", ...},
#   {"type": "other", "title": "MDMA Assisted Psychotherapy", ...}
# ]
# Chunk 5 → Claude → [
#   {"type": "product", "title": "Saffron (30 milligrams)", ...},
#   {"type": "product", "title": "Inositol (18 grams)", ...}
# ]

# Combined & deduplicated: 5 recommendations
```

**Step 5: Book Enrichment** (skipped - no books in this example)

**Step 6: Database Storage**
```sql
INSERT INTO recommendations VALUES (
  'aef216ca-59c4-4224-a08d-eb8f94897441',  -- id
  'dac107e0-e0bb-4fd0-afbb-1f0cf1f8567c',  -- episode_id
  'product',  -- type
  'Cyclic Hyperventilation Breathing Protocol',  -- title
  'A five-minute daily breathing protocol...',  -- context
  'So, what we've been doing in human subjects...',  -- quote
  0,  -- timestamp_seconds
  'Andrew Huberman',  -- recommended_by
  0.9,  -- confidence_score
  '{}',  -- extra_metadata
  '2025-11-09 04:25:28',  -- created_at
  '2025-11-09 04:25:28'   -- updated_at
);
```

**Step 7: API Exposure**
```bash
GET http://localhost:8000/api/recommendations/aef216ca-59c4-4224-a08d-eb8f94897441

Response:
{
  "id": "aef216ca-59c4-4224-a08d-eb8f94897441",
  "episodeId": "dac107e0-e0bb-4fd0-afbb-1f0cf1f8567c",
  "type": "product",
  "title": "Cyclic Hyperventilation Breathing Protocol",
  "recommendationContext": "A five-minute daily breathing protocol...",
  "quoteFromEpisode": "So, what we've been doing in human subjects...",
  "timestampSeconds": 0,
  "recommendedBy": "Andrew Huberman",
  "confidenceScore": 0.9
}
```

**Step 8: Frontend Display**
```typescript
// Next.js fetches from API
const rec = await fetch('http://localhost:8000/api/recommendations/...')
const data = await rec.json()

// Renders in React component
<RecommendationCard recommendation={data} />
```

**Step 9: User Sees:**
```
┌─────────────────────────────────────┐
│ Cyclic Hyperventilation Breathing  │
│ Protocol                            │
│                                     │
│ Type: Product                       │
│ Recommended by: Andrew Huberman    │
│                                     │
│ "A five-minute daily breathing     │
│ protocol involving hyperventilation│
│ followed by breath holds..."       │
│                                     │
│ [View Details →]                   │
└─────────────────────────────────────┘
```

---

## Technology Stack Summary

### Backend
- **Python 3.13**
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM
- **SQLite** - Database
- **youtube-transcript-api** - Transcript fetching
- **anthropic** - Claude AI SDK
- **requests** - HTTP client
- **beautifulsoup4** - HTML parsing
- **feedparser** - RSS parsing

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Hooks** - State management

### External APIs
- **Anthropic Claude API** - AI recommendation extraction
- **Google Books API** - Book metadata enrichment
- **YouTube Transcript API** - Transcript fetching (no key required)

---

## Rate Limits & Constraints

1. **YouTube Transcript API**
   - Rate limited by IP address
   - ~10-15 requests before temporary ban
   - Solution: 5-second delays between requests

2. **Claude API**
   - Rate limit: Variable (depends on tier)
   - Cost: ~$3 per million input tokens, ~$15 per million output tokens
   - Average: ~$0.20 per episode (with 100k char transcript)

3. **Google Books API**
   - Free tier: 1000 requests/day
   - Sufficient for enriching book recommendations

---

## Configuration

### Environment Variables
```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_BOOKS_API_KEY=AIza...
DATABASE_URL=sqlite:///./podcast_recommendations.db
CORS_ORIGINS=["http://localhost:3000"]
```

### Processing Settings
```python
# Transcript chunking
CHUNK_SIZE = 8000  # characters per chunk

# Rate limiting
DELAY_BETWEEN_EPISODES = 5  # seconds

# API timeouts
REQUEST_TIMEOUT = 30  # seconds
```

---

## Error Handling

### Common Errors

1. **TranscriptsDisabled**
   - Cause: Video has no transcript/captions
   - Action: Skip episode, mark as failed

2. **VideoUnavailable**
   - Cause: Video deleted or private
   - Action: Skip episode, mark as failed

3. **Rate Limit (429)**
   - Cause: Too many YouTube requests
   - Action: Wait 24 hours, retry

4. **Claude API Error**
   - Cause: API key invalid or rate limit
   - Action: Check API key, reduce requests

5. **Google Books Not Found**
   - Cause: Book not in Google Books database
   - Action: Save without enrichment

---

## Performance Metrics

### Current Dataset (20 episodes, 247 recommendations)

**Processing Time:**
- Average per episode: ~2 minutes
- Total for 20 episodes: ~40 minutes

**Breakdown:**
- Transcript fetch: ~2 seconds
- Claude analysis: ~90 seconds (5 chunks × 18s each)
- Book enrichment: ~10 seconds (for books)
- Database save: <1 second

**Cost:**
- Claude API: ~$0.20 per episode
- Google Books: Free (under 1000/day)
- YouTube Transcripts: Free

**Total for 110 episodes:**
- Time: ~3.5 hours
- Cost: ~$22 (Claude API only)

---

## Future Improvements

1. **Parallel Processing**
   - Process multiple episodes simultaneously
   - Reduce total time from 3.5 hours to 30 minutes

2. **Better Rate Limit Handling**
   - Exponential backoff
   - IP rotation for YouTube
   - Proxy support

3. **Enhanced Enrichment**
   - TMDB API for movies
   - Product search APIs for products
   - Podcast API for podcast recommendations

4. **Incremental Processing**
   - Resume failed episodes
   - Track progress per episode
   - Retry with different strategies

5. **Quality Improvements**
   - Better guest name extraction
   - Timestamp accuracy
   - Confidence scoring improvements

---

## Questions?

For more details on any module, see the source code:
- Backend: `/backend/app/`
- Scripts: `/backend/scripts/`
- Frontend: `/podcast-app/src/`
