# Milestone 2: Backend Setup Complete! 🎉

## What We've Built

### ✅ Complete Python Backend
- **FastAPI Application** with CORS configured for Next.js frontend
- **Database Models** for Podcasts, Episodes, and Recommendations
- **YouTube Transcript Service** to extract transcripts from videos
- **Claude AI Integration** to identify recommendations from transcripts
- **Data Enrichment** services for Google Books and TMDB APIs
- **RESTful API Endpoints** for the frontend to consume
- **Processing Script** ready to extract recommendations from Lenny's Podcast

### 📁 Backend Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── config.py            # Configuration with your API key
│   ├── database.py          # PostgreSQL setup
│   ├── models/              # Database models
│   │   ├── podcast.py
│   │   ├── episode.py
│   │   └── recommendation.py
│   └── services/            # Business logic
│       ├── youtube_service.py     # YouTube transcript extraction
│       ├── claude_service.py      # Claude AI for recommendations
│       └── enrichment_service.py  # Google Books & TMDB
├── scripts/
│   └── process_lenny.py     # Process Lenny's episodes
├── requirements.txt         # Python dependencies
└── .env                     # Your API keys (DONE ✅)
```

---

## 🚀 Next Steps to Test

### Step 1: Install Dependencies

```bash
cd /Users/vivekgupta/Desktop/podcast/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux

# Install packages
pip install -r requirements.txt
```

### Step 2: Set Up Database (Optional for Testing)

For quick testing, we can use SQLite instead of PostgreSQL:

Update `backend/.env`:
```bash
# Change this line:
DATABASE_URL=postgresql://user:password@localhost:5432/podcast_recs

# To this (SQLite - no install needed):
DATABASE_URL=sqlite:///./podcast_recs.db
```

### Step 3: Get Lenny's Recent Episode URLs

1. Go to: https://www.youtube.com/@LennysPodcast/videos
2. Find the last 5 episodes
3. Copy the YouTube URLs (e.g., `https://www.youtube.com/watch?v=VIDEO_ID`)

### Step 4: Update Processing Script

Edit `backend/scripts/process_lenny.py` and update the `LENNY_EPISODES` list:

```python
LENNY_EPISODES = [
    {
        "title": "Actual episode title from YouTube",
        "youtube_url": "https://www.youtube.com/watch?v=ACTUAL_VIDEO_ID",
        "description": "Episode description",
        "published_date": "2024-10-28",  # Approximate date
        "guest": "Guest Name"
    },
    # ... add 4 more
]
```

### Step 5: Run the Processing Script

```bash
cd /Users/vivekgupta/Desktop/podcast/backend

# Make sure venv is activated
source venv/bin/activate

# Run the script
python scripts/process_lenny.py
```

This will:
1. ✅ Create the database tables
2. ✅ Fetch transcripts from YouTube
3. ✅ Use Claude to extract recommendations
4. ✅ Enrich with Google Books/TMDB (if API keys provided)
5. ✅ Save everything to the database

**Expected output:**
```
Processing: Episode Title
Fetching transcript...
Transcript length: 45231 characters
Extracting recommendations with Claude API...
Found 8 recommendations
✅ Successfully processed episode
```

### Step 6: Start the API Server

```bash
# In the backend directory with venv activated
uvicorn app.main:app --reload --port 8000
```

API will be running at: **http://localhost:8000**

Test it: http://localhost:8000/api/recommendations

### Step 7: Test API Endpoints

```bash
# Get all recommendations
curl http://localhost:8000/api/recommendations

# Get stats
curl http://localhost:8000/api/stats

# Search
curl http://localhost:8000/api/search?q=book

# Filter by type
curl http://localhost:8000/api/recommendations?type=book
```

---

## 📊 API Endpoints Available

| Endpoint | Description |
|----------|-------------|
| `GET /api/podcasts` | List all podcasts |
| `GET /api/podcasts/{id}` | Get podcast details |
| `GET /api/episodes` | List episodes |
| `GET /api/recommendations` | List recommendations (with filters) |
| `GET /api/recommendations/{id}` | Get recommendation details |
| `GET /api/search?q=query` | Search recommendations |
| `GET /api/stats` | Get overall statistics |

**Filter Options for `/api/recommendations`:**
- `?type=book` - Only books
- `?type=movie` - Only movies
- `?podcast_id=xxx` - From specific podcast
- `?limit=10&offset=0` - Pagination

---

## 🔧 Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "No transcript available"
- Video may not have captions
- Try a different episode
- Check video ID is correct

### "Claude API Error"
- Check your API key in `.env`
- Make sure you have credits in your Anthropic account
- Check: https://console.anthropic.com/settings/billing

### "Database connection error"
- Use SQLite instead of PostgreSQL for testing:
  - Update DATABASE_URL in `.env` to `sqlite:///./podcast_recs.db`

---

## 💰 Cost Estimate

For processing 5 episodes:
- **Transcripts**: Free (YouTube Transcript API)
- **Claude API**: ~$2-5 (depends on transcript length)
- **Google Books/TMDB**: Free (within rate limits)

**Total**: ~$2-5 for the test

---

## 🎯 What Happens Next

After successfully processing episodes:

1. **Backend is running** at http://localhost:8000
2. **Database has real data** from Lenny's Podcast
3. **Frontend can connect** to the backend API
4. **Replace mock data** in Next.js with real API calls

---

## 📝 Quick Start Example

Here's the fastest way to test:

```bash
# 1. Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Use SQLite (easier than PostgreSQL)
# Edit .env and change DATABASE_URL to:
# DATABASE_URL=sqlite:///./podcast_recs.db

# 3. Add one episode URL to scripts/process_lenny.py
# Just test with 1 episode first!

# 4. Uncomment main() at the bottom of process_lenny.py

# 5. Run it
python scripts/process_lenny.py

# 6. Start API
uvicorn app.main:app --reload --port 8000

# 7. Test
curl http://localhost:8000/api/recommendations
```

---

## ✅ Success Indicators

You'll know it's working when:
- ✅ Processing script completes without errors
- ✅ You see "Successfully processed episode" message
- ✅ API returns recommendations: `GET /api/recommendations`
- ✅ Stats show real data: `GET /api/stats`

---

## Need Help?

Common issues and solutions are in the Troubleshooting section above.

Next: Connect the Next.js frontend to use the real API instead of mock data!
