# /dbtable API Endpoint

## Overview

New endpoint to view all Phase 1 processing metrics in JSON format.

---

## Endpoints

Both URLs work:
- `http://localhost:8000/dbtable`
- `http://localhost:8000/api/dbtable`

---

## Response Format

```json
{
  "total": 2,
  "metrics": [
    {
      "id": "uuid",
      "episodeId": "uuid",
      "phase": "phase_1",
      "processingDate": "2025-11-11T21:41:41.078304",

      "transcriptQuality": {
        "totalSegments": 884,
        "characterCount": 32962,
        "wordCount": 5686,
        "startTime": 0.24,
        "endTime": 2106.26,
        "durationCoveredSeconds": 2106.02,
        "videoDurationSeconds": 4320.0,
        "coveragePercent": 48.8,
        "gapsDetected": 0,
        "isComplete": true
      },

      "claudeProcessing": {
        "totalChunks": 5,
        "charactersSent": 32962,
        "firstChunkPosition": 0,
        "lastChunkPosition": 25002,
        "coverageVerified": true
      },

      "recommendations": {
        "totalFound": 8,
        "unique": 5,
        "books": 2,
        "movies": 1,
        "products": 2
      },

      "performance": {
        "aiModel": "claude-sonnet-4-20250514",
        "estimatedCostUSD": 0.0247,
        "processingTimeSeconds": 142.5,
        "processingTimeMinutes": 2.4
      },

      "hadErrors": false,
      "errorMessage": null,
      "createdAt": "2025-11-11T21:41:41.079169",

      "youtubeUrl": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
  ]
}
```

---

## Usage

### Using curl
```bash
curl http://localhost:8000/dbtable
```

### Using browser
Open: http://localhost:8000/dbtable

### Pretty formatted
```bash
curl -s http://localhost:8000/dbtable | python3 -m json.tool
```

---

## What You See

All Phase 1 quality checks:

**Transcript Quality:**
- Total segments captured
- Character/word count
- Start/end timestamps
- Duration covered (transcript timestamps)
- Video duration (actual from YouTube)
- Coverage percentage (how much of video has transcript)
- Gaps detected
- Completeness flag

**Claude Processing:**
- Total chunks processed
- Characters sent to AI
- First/last chunk positions
- Coverage verification

**Results:**
- Total recommendations found
- Unique after deduplication
- Breakdown by type (books, movies, products)

**Performance:**
- AI model used
- Estimated cost in USD
- Processing time (seconds and minutes)
- Error flags

---

## Start the Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Then access: **http://localhost:8000/dbtable**

---

## Process a Video

To add new data to the table:

```bash
python scripts/process_single_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

This will:
1. Fetch and verify transcript
2. Process with Claude AI
3. Save metrics to database
4. Immediately visible at /dbtable

---

## Example: Complete Workflow

### Step 1: Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Step 2: Process Video
```bash
python scripts/process_single_video.py "https://www.youtube.com/watch?v=1sClhfuCxP0"
```

### Step 3: View Data
Open: http://localhost:8000/dbtable

Or:
```bash
curl http://localhost:8000/dbtable | python3 -m json.tool
```

---

## Features

✅ **All Phase 1 metrics** - Every quality check captured
✅ **JSON format** - Easy to parse and use
✅ **Real-time** - Updates immediately after processing
✅ **Sorted** - Most recent first
✅ **Complete data** - All fields included
✅ **Time units** - Seconds and minutes for processing time

---

## Integration with Frontend

```javascript
// Fetch metrics
const response = await fetch('http://localhost:8000/dbtable');
const data = await response.json();

console.log(`Total metrics: ${data.total}`);

data.metrics.forEach(m => {
  console.log(`Phase: ${m.phase}`);
  console.log(`Characters: ${m.transcriptQuality.characterCount}`);
  console.log(`Cost: $${m.performance.estimatedCostUSD}`);
  console.log(`Time: ${m.performance.processingTimeMinutes} minutes`);
});
```

---

## Current Data

As of now, you have 1 metric in the database (sample data).

After processing `https://www.youtube.com/watch?v=1sClhfuCxP0`, you'll see 2 metrics.

---

**The /dbtable endpoint is live and ready!** ✅

Access it at: **http://localhost:8000/dbtable**
