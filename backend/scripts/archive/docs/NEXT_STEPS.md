# Next Steps - Backend is Ready!

## Backend Setup Complete ✅

All backend components are working:
- ✅ SQLite database configured
- ✅ FastAPI application ready
- ✅ Claude API integration working
- ✅ YouTube transcript service configured
- ✅ All dependencies installed
- ✅ Test pipeline passed

## What You Need to Do Now

### Step 1: Get Lenny's Podcast YouTube URLs

1. Go to: https://www.youtube.com/@LennysPodcast/videos
2. Find the 5 most recent episodes
3. Copy each YouTube URL (they look like: `https://www.youtube.com/watch?v=VIDEO_ID`)

### Step 2: Update the Processing Script

Edit the file: `backend/scripts/process_lenny.py`

Replace the `REPLACE_WITH_VIDEO_ID_X` placeholders with the actual video IDs:

```python
# Around line 38-73
LENNY_EPISODES = [
    {
        "title": "What most people miss about marketing | Rory Sutherland",
        "youtube_url": "https://www.youtube.com/watch?v=ACTUAL_VIDEO_ID_HERE",
        # ... update all 5 episodes
    },
    # ... 4 more episodes
]
```

**Example:**
If the YouTube URL is `https://www.youtube.com/watch?v=dQw4w9WgXcQ`, then:
```python
"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
```

### Step 3: Run the Processing Script

```bash
cd /Users/vivekgupta/Desktop/podcast/backend

# Activate virtual environment
source venv/bin/activate

# Run the processing script
python scripts/process_lenny.py
```

This will:
1. ✅ Fetch transcripts from YouTube
2. ✅ Extract recommendations using Claude AI
3. ✅ Save everything to the database

**Expected output:**
```
================================================================================
Processing: Episode Title
================================================================================

Fetching transcript...
Transcript length: 45231 characters
Extracting recommendations with Claude API...
Extracted 8 recommendations

Recommendation 1/8:
  Type: book
  Title: The Lean Startup
  Confidence: 0.85
  Enriching with external APIs...

✅ Successfully processed episode: Episode Title
   Saved 8 recommendations
```

### Step 4: Start the API Server

In a new terminal:

```bash
cd /Users/vivekgupta/Desktop/podcast/backend

# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 5: Test the API

Open your browser or use curl:

```bash
# Get all recommendations
curl http://localhost:8000/api/recommendations

# Get stats
curl http://localhost:8000/api/stats

# Search for books
curl http://localhost:8000/api/recommendations?type=book
```

## Troubleshooting

### "No transcript available"
- The video might not have captions
- Try a different episode
- Make sure the video ID is correct

### "Claude API Error"
- Your API key is already configured correctly
- Check your Anthropic account has credits: https://console.anthropic.com/settings/billing

### Script taking too long
- Each episode takes ~30-60 seconds to process
- For 5 episodes, expect ~5 minutes total

## Cost Estimate

Processing 5 episodes of Lenny's Podcast:
- **YouTube Transcripts**: Free
- **Claude API**: ~$2-5 (depends on episode length)
- **Total**: ~$2-5

## Files Modified in This Session

### Backend Files Created/Updated:
1. `/Users/vivekgupta/Desktop/podcast/backend/requirements.txt` - Updated for Python 3.13
2. `/Users/vivekgupta/Desktop/podcast/backend/.env` - Added your API key, configured for SQLite
3. `/Users/vivekgupta/Desktop/podcast/backend/scripts/process_lenny.py` - Updated with recent episode templates
4. `/Users/vivekgupta/Desktop/podcast/backend/scripts/test_pipeline.py` - Created for testing
5. `/Users/vivekgupta/Desktop/podcast/backend/app/models/recommendation.py` - Fixed `metadata` → `extra_metadata`
6. `/Users/vivekgupta/Desktop/podcast/backend/app/models/episode.py` - Fixed `ARRAY` → `JSON` for SQLite
7. `/Users/vivekgupta/Desktop/podcast/backend/app/services/claude_service.py` - Fixed markdown code block parsing

## What Happens Next

After processing the episodes:
1. Backend will have real podcast recommendations in the database
2. You can test the API endpoints
3. Next phase: Connect the Next.js frontend to the backend API
4. Replace mock data in the frontend with real API calls

## Quick Reference

**Backend directory:** `/Users/vivekgupta/Desktop/podcast/backend`
**Frontend directory:** `/Users/vivekgupta/Desktop/podcast/podcast-app`
**Database file:** `/Users/vivekgupta/Desktop/podcast/backend/podcast_recs.db`

**Key URLs:**
- API Server: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend (Next.js): http://localhost:3000

---

Ready to process real podcast data! 🎉
