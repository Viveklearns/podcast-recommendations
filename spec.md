# Podcast Recommendations Aggregator - Technical Specification

## Project Overview

A web application that automatically extracts and aggregates book, movie, TV show, and other recommendations from top US podcasts. Users can browse, search, and discover recommendations made by podcast guests and hosts.

---

## Core Features

### 1. Recommendation Extraction
- Automatically process podcast episodes from top 5 US podcasts
- Extract recommendations using AI-powered transcript analysis
- Categorize recommendations (books, movies, TV shows, products, other)
- Associate recommendations with specific episodes, guests, and timestamps

### 2. User Interface
- Browse recommendations by category
- Search by recommendation title, author, podcast, or guest name
- Filter by podcast, date range, or category
- View recommendation details with context (why it was recommended)
- Link back to source episode with timestamp

### 3. Data Collection Pipeline
- YouTube Transcript API (primary source)
- Podcast RSS feeds with transcripts (fallback)
- Automated weekly/daily refresh cycle
- Duplicate detection and recommendation aggregation

---

## Technical Architecture

### Data Flow
```
Podcasts → Transcript Extraction → Claude API Analysis →
Data Enrichment → Database Storage → Web Interface
```

### Components

#### 1. Transcript Extractor Service
- **YouTube Transcript Fetcher**: Uses `youtube-transcript-api` library
- **RSS Feed Parser**: Parses podcast RSS feeds for transcript URLs
- **Fallback Logic**: Try YouTube first, then RSS
- **Storage**: Raw transcripts cached locally or in S3

#### 2. Recommendation Analyzer (Claude Integration)
- **Input**: Transcript chunks (5000-10000 tokens per chunk)
- **Processing**: Send to Claude API with structured prompt
- **Output**: Structured JSON with categorized recommendations
- **Post-processing**: Deduplication, confidence scoring

#### 3. Data Enrichment Service
- **Books**: Google Books API (ISBN, cover, author, description, rating)
- **Movies/TV**: TMDB API (poster, year, director, rating)
- **Validation**: Verify extracted titles match real items
- **Metadata**: Store enriched data alongside raw recommendations

#### 4. Database Schema
See detailed schema below

#### 5. Web Application
- **Frontend**: React/Next.js with Tailwind CSS
- **Backend**: Python (FastAPI) or Node.js (Express)
- **API**: RESTful endpoints for browsing/searching recommendations

---

## Book Data Quality Requirements

### Display Validation Rules

Books must meet ALL of the following criteria to be displayed on the website:

1. **Required Fields:**
   - ✅ Book title (exact, not "Not specified")
   - ✅ Author name (not "Not mentioned")
   - ✅ Valid ISBN (ISBN-10 or ISBN-13)
   - ✅ Amazon purchase link
   - ✅ Book cover image URL
   - ✅ Actual guest name (not "Guest 1", "Guest 2", etc.)

2. **ISBN Verification:**
   - Must validate ISBN using Google Books API
   - Book must exist in Google Books database
   - ISBN format must be correct (10 or 13 digits)

3. **Guest Attribution:**
   - Extract actual guest name from transcript or episode metadata
   - Never use placeholder names like "Guest 1", "Guest 2"
   - If guest name cannot be determined, book should not be displayed

4. **Image Sourcing Priority:**
   - **Primary**: Google Books API (`imageLinks.large` or `imageLinks.thumbnail`)
   - **Fallback**: Open Library (`https://covers.openlibrary.org/b/isbn/{ISBN}-L.jpg`)
   - **Last Resort**: Placeholder image (only if no other source available)

5. **Amazon Links:**
   - Generate from ISBN: `https://www.amazon.com/dp/{ISBN-10}`
   - Validate that product page exists
   - Optional: Add affiliate tag `?tag=yourId` for monetization

### Book Detail Page Requirements

When a book link is clicked, the detail page MUST show:

1. **Visual:**
   - Large book cover image
   - High-resolution (at least 400px width)

2. **Book Information:**
   - Title
   - Author(s)
   - ISBN (displayed for reference)
   - Publisher
   - Publication year
   - Page count (if available)

3. **Recommendation Context:**
   - Who recommended it (actual guest name + podcast)
   - Podcast name and episode title
   - Date of episode
   - Why they recommended it (context)
   - Direct quote from episode
   - Timestamp in episode (if available)

4. **Actions:**
   - **Primary CTA**: "Buy on Amazon" button → `amazon_url`
   - **Secondary**: "View on Google Books" → Google Books link
   - **Tertiary**: "Listen to Episode" → YouTube/podcast link with timestamp

5. **Related Content:**
   - Other books from same guest
   - Other books from same podcast
   - Similar recommendations

### Data Enrichment Pipeline for Books

```
1. Claude API extracts book mention
   ↓
2. Extract: title, author (approximate)
   ↓
3. Search Google Books API by title + author
   ↓
4. Match best result (fuzzy matching with confidence score)
   ↓
5. Extract metadata:
   - ISBN-10 and ISBN-13
   - Cover image URL (high resolution)
   - Publisher, publication date
   - Page count
   - Google Books ID
   ↓
6. Validate ISBN with Google Books API
   ↓
7. Generate Amazon URL from ISBN-10
   ↓
8. Verify all required fields present
   ↓
9. If ALL fields valid: Save to database with verified=true
   If ANY field missing: Log for manual review, do NOT display
```

---

## Data Models

### Podcast
```json
{
  "id": "uuid",
  "name": "The Tim Ferriss Show",
  "youtube_channel_id": "UCznv7Vf9nBdJYvBagFdAHWw",
  "rss_feed_url": "https://...",
  "category": "Business/Education",
  "image_url": "https://...",
  "created_at": "timestamp",
  "last_fetched_at": "timestamp"
}
```

### Episode
```json
{
  "id": "uuid",
  "podcast_id": "foreign_key",
  "title": "Episode 783: Hugh Jackman Returns",
  "description": "...",
  "published_date": "2024-03-15",
  "duration_seconds": 7200,
  "youtube_url": "https://youtube.com/watch?v=...",
  "audio_url": "https://...",
  "transcript_url": "https://... (if available)",
  "guest_names": ["Hugh Jackman"],
  "transcript_source": "youtube|rss|manual",
  "processing_status": "pending|processing|completed|failed",
  "processed_at": "timestamp",
  "created_at": "timestamp"
}
```

### Recommendation (Book)
```json
{
  "id": "uuid",
  "episode_id": "foreign_key",
  "type": "book",
  "title": "Meditations",
  "author": "Marcus Aurelius",
  "isbn": "978-0143036784",
  "description": "Timeless wisdom from Roman emperor...",
  "cover_image_url": "https://...",
  "publisher": "Penguin Classics",
  "published_year": 2006,
  "page_count": 304,
  "goodreads_rating": 4.23,
  "amazon_url": "https://...",
  "google_books_url": "https://...",

  "recommendation_context": "Hugh mentioned this as the book that changed his perspective on stoicism",
  "quote_from_episode": "This book has been on my nightstand for years...",
  "timestamp_seconds": 3845,
  "recommended_by": "Hugh Jackman (Guest)",
  "confidence_score": 0.95,

  "extraction_metadata": {
    "extracted_at": "timestamp",
    "claude_model": "claude-sonnet-4-5",
    "original_mention": "I highly recommend Meditations by Marcus Aurelius"
  },

  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Recommendation (Movie/TV Show)
```json
{
  "id": "uuid",
  "episode_id": "foreign_key",
  "type": "movie|tv_show",
  "title": "The Bear",
  "creator_director": "Christopher Storer",
  "release_year": 2022,
  "tmdb_id": 136315,
  "imdb_id": "tt14452776",
  "poster_url": "https://...",
  "backdrop_url": "https://...",
  "genre": ["Drama", "Comedy"],
  "runtime_minutes": 30,
  "seasons": 2,
  "episodes": 18,
  "rating": 8.6,
  "streaming_platforms": ["Hulu", "Disney+"],
  "trailer_url": "https://...",

  "recommendation_context": "Guest praised it as the best show about creativity under pressure",
  "quote_from_episode": "If you haven't watched The Bear, stop what you're doing...",
  "timestamp_seconds": 4200,
  "recommended_by": "Guest Name",
  "confidence_score": 0.92,

  "extraction_metadata": {
    "extracted_at": "timestamp",
    "claude_model": "claude-sonnet-4-5",
    "original_mention": "..."
  },

  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Recommendation (Other)
```json
{
  "id": "uuid",
  "episode_id": "foreign_key",
  "type": "podcast|product|app|website|course|other",
  "title": "Notion",
  "category": "Productivity App",
  "description": "All-in-one workspace for notes and collaboration",
  "url": "https://notion.so",
  "image_url": "https://...",
  "price": "Free / $8/mo",

  "recommendation_context": "Guest uses it for all project management",
  "quote_from_episode": "Notion completely changed how I organize my life",
  "timestamp_seconds": 2100,
  "recommended_by": "Guest Name",
  "confidence_score": 0.88,

  "extraction_metadata": {
    "extracted_at": "timestamp",
    "claude_model": "claude-sonnet-4-5",
    "original_mention": "..."
  },

  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

## Recommendation Data Dimensions

### Books
**Core Fields:**
- Title (required)
- Author(s) (required)
- ISBN (for unique identification)
- Cover image URL
- Publication year
- Page count
- Publisher

**Enrichment Data:**
- Description/synopsis
- Goodreads rating
- Amazon rating
- Genre/categories
- Links (Amazon, Goodreads, Google Books)

**Context Fields:**
- Why recommended (extracted context)
- Quote from episode
- Timestamp in episode
- Who recommended it (guest/host name)
- Confidence score (0-1)

### Movies & TV Shows
**Core Fields:**
- Title (required)
- Director/Creator (required)
- Release year
- Type (movie vs. TV show)
- Poster image URL

**Enrichment Data:**
- TMDB/IMDB ID
- Runtime/episode count
- Seasons (for TV)
- Genre tags
- Rating (IMDB/TMDB)
- Streaming platforms
- Trailer URL
- Cast (top 3-5)

**Context Fields:**
- Why recommended
- Quote from episode
- Timestamp
- Recommended by
- Confidence score

### Other Recommendations
**Core Fields:**
- Title/Name (required)
- Category (podcast, app, product, website, course, tool)
- Description
- URL/link

**Optional Fields:**
- Image/logo
- Price/cost
- Platform (iOS, web, etc.)

**Context Fields:**
- Why recommended
- Quote from episode
- Timestamp
- Recommended by
- Confidence score

---

## API Endpoints

### Public API

#### Get Recommendations
```
GET /api/recommendations
Query params:
  - type: book|movie|tv_show|other
  - podcast_id: uuid
  - limit: int (default 20)
  - offset: int (default 0)
  - sort: recent|popular|rating
  - search: string

Response: Array of recommendation objects
```

#### Get Single Recommendation
```
GET /api/recommendations/:id
Response: Full recommendation object with episode details
```

#### Get Podcasts
```
GET /api/podcasts
Response: Array of tracked podcasts with episode counts
```

#### Get Episodes
```
GET /api/episodes/:podcast_id
Query params:
  - limit, offset

Response: Array of episodes with recommendation counts
```

#### Search
```
GET /api/search?q=meditations
Response: Mixed results (books, movies, shows) matching query
```

### Admin API (Future)
```
POST /api/admin/podcasts - Add new podcast to track
POST /api/admin/episodes/:id/reprocess - Reprocess episode
GET /api/admin/stats - System statistics
```

---

## Claude API Integration

### Prompt Structure

```
System Prompt:
You are an expert at analyzing podcast transcripts and extracting recommendations.
Your task is to identify when a podcast guest or host explicitly recommends books,
movies, TV shows, products, or other resources.

User Prompt:
Analyze the following podcast transcript segment and extract all recommendations.

Transcript:
[TRANSCRIPT TEXT]

For each recommendation found, return a JSON object with:
{
  "recommendations": [
    {
      "type": "book|movie|tv_show|podcast|product|other",
      "title": "exact title mentioned",
      "author_creator": "if mentioned",
      "context": "1-2 sentence summary of why it was recommended",
      "quote": "direct quote from transcript showing the recommendation",
      "confidence": 0.0-1.0,
      "timestamp_indicator": "any time markers mentioned in transcript"
    }
  ]
}

Guidelines:
- Only include items that were EXPLICITLY recommended or highly praised
- Exclude casual mentions or neutral references
- If a book/movie title is unclear, include your best interpretation
- Mark confidence as high (0.9-1.0) for clear recommendations,
  medium (0.6-0.9) for likely recommendations,
  low (0.3-0.6) for uncertain mentions
```

### Processing Strategy
1. **Chunking**: Split transcripts into ~8000 token chunks with 500 token overlap
2. **Parallel Processing**: Send multiple chunks to Claude simultaneously
3. **Aggregation**: Combine results and deduplicate
4. **Validation**: Cross-reference extracted titles with external APIs
5. **Human Review**: Flag low-confidence items for manual review (optional)

---

## Initial Podcast Selection (Top 5 US Podcasts)

1. **The Joe Rogan Experience** - `@joerogan` on YouTube
2. **The Tim Ferriss Show** - `@timferriss` on YouTube
3. **Huberman Lab** - `@hubermanlab` on YouTube
4. **Call Her Daddy** - `@callherdaddy` on YouTube
5. **The Diary of a CEO** - `@TheDiaryOfACEO` on YouTube

*Note: Can be configured in database, easily expandable*

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async support, automatic docs)
- **Database**: PostgreSQL 15+ with pgvector (for future semantic search)
- **Caching**: Redis
- **Task Queue**: Celery with Redis broker
- **APIs**:
  - youtube-transcript-api
  - Anthropic Claude API
  - Google Books API
  - TMDB API

### Frontend
- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **State Management**: React Query + Zustand
- **UI Components**: Shadcn/ui

### Infrastructure
- **Hosting**: Vercel (frontend) + Railway/Render (backend)
- **Storage**: AWS S3 (transcript cache, images)
- **Monitoring**: Sentry (errors), Posthog (analytics)

---

## Security & Rate Limiting

### API Keys
- Store in environment variables
- Rotate regularly
- Use different keys for dev/staging/prod

### Rate Limiting
- Claude API: ~50 requests/min (depending on tier)
- YouTube API: 10,000 units/day (1 transcript = 1-3 units)
- Google Books: 1,000 requests/day
- TMDB: 40 requests/10 seconds

### Caching Strategy
- Cache transcripts for 90 days
- Cache API enrichment data for 30 days
- Cache search results for 1 hour

---

## Cost Estimates (Monthly)

### APIs
- Claude API: ~$50-100 (5 podcasts, ~50 episodes/month)
- YouTube Transcript: Free
- Google Books: Free (within limits)
- TMDB: Free (within limits)

### Infrastructure
- Database: $10-20 (managed PostgreSQL)
- Redis: $10 (managed)
- Storage: $5-10 (S3)
- Hosting: $0-20 (Vercel free + Railway/Render hobby)

**Total: ~$75-150/month**

---

## Future Enhancements

1. **User Accounts**: Save favorite recommendations, create lists
2. **Email Notifications**: Weekly digest of new recommendations
3. **Community Features**: Upvote/comment on recommendations
4. **Mobile App**: Native iOS/Android apps
5. **Browser Extension**: Save recommendations while browsing
6. **Advanced Search**: Semantic search using embeddings
7. **Recommendation Engine**: Suggest items based on user preferences
8. **Spotify Integration**: Support Spotify-exclusive podcasts
9. **Affiliate Links**: Monetization through Amazon affiliate program
10. **Export Features**: Export recommendations to Notion, Goodreads, etc.

---

## Success Metrics

### Technical
- Process 50+ episodes per week
- 90%+ uptime
- <2 second page load time
- 85%+ recommendation extraction accuracy

### User Engagement
- 1,000+ monthly active users (6 months)
- 50+ daily searches
- 20%+ click-through to source episodes
- 10%+ click-through to purchase/view recommendations

---

## Development Timeline

See `todo.md` for detailed milestones and task breakdown.

---

## Current Milestone: Automated YouTube Video Discovery

### YouTube Podcast Link Discovery Module
**Goal**: Automatically discover and fetch recent podcast episodes from YouTube channels without manual URL entry

**Features:**
- Search YouTube channels for recent videos (last 6 months)
- Support for multiple podcasts:
  - Lenny's Podcast (@LennysPodcast)
  - The Tim Ferriss Show (@timferriss)
  - Additional podcasts as configured
- Automatic video metadata extraction:
  - Video title
  - YouTube URL
  - Published date
  - Duration
  - Description
- Filter out non-episode content (shorts, clips, announcements)
- Store discovered episodes for processing

**Implementation:**
- YouTube Data API v3 integration (preferred)
- Fallback: Web scraping using RSS feeds
- Configurable date range (default: last 6 months)
- Automatic deduplication with existing episodes
- Scheduled discovery runs (weekly/daily)

**Benefits:**
- Eliminates manual URL entry
- Ensures no episodes are missed
- Scales to multiple podcasts easily
- Keeps database up-to-date automatically

---

## Future Milestone Ideas

### User Subscription & Notifications
- **Subscribe for new activities**: Allow users to subscribe and get notified when new recommendations are added
- **Free activities nearby**: Add location-based filtering to show free/local activities and events
- **Birthday party venues**: Expand beyond media recommendations to include:
  - Urban Air trampoline parks
  - Gyms and fitness centers
  - Party venues and event spaces
  - Local activity centers

### Implementation Notes
- Add user accounts and email subscription system
- Integrate location services for nearby recommendations
- Create new recommendation categories for physical venues/activities
- Add filtering by price (free/paid) and location radius
