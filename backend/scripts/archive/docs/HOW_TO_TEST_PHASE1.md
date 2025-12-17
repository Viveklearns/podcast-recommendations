# How to Test Phase 1 Improvements

## Where Are Checks Captured?

Phase 1 data quality checks are captured in **TWO places**:

### 1. 📋 **Logging Output** (Real-time)
- Console output during processing
- Saved to `processing_all.log` file
- Visible immediately during processing

### 2. 💾 **Database** (Permanent Storage)
- `episodes.transcript_metadata` - JSON field
- `episodes.claude_processing_metadata` - JSON field
- Queryable after processing

---

## Quick Start: Run the Demo

```bash
cd backend
source venv/bin/activate
python scripts/demo_phase1.py
```

**This shows:**
- ✅ Transcript verification checks
- ✅ Claude chunk processing checks
- ✅ What gets stored in database
- ✅ All quality verifications

**Output:**
```
🔍 QUALITY CHECKS:
   ✓ Total segments captured: 884
   ✓ Character count: 32,962
   ✓ Word count: 5,686
   ✓ Duration covered: 35.1 minutes
   ✓ Gaps detected: 0
   ✓ Is complete: YES ✅

📍 COVERAGE VERIFICATION:
   Expected to send: 7,960 chars
   Actually sent: 7,960 chars
   Match: YES ✅
```

---

## Testing Methods

### Method 1: View Demo (No Processing)
Shows what Phase 1 captures without processing a real episode:

```bash
python scripts/demo_phase1.py
```

- ⏱️ Time: 30 seconds
- 💰 Cost: $0.005 (1 Claude API call)
- Shows all checks in action

---

### Method 2: View Logs (Real-time)
Process an episode and watch the logs:

```bash
python scripts/process_all_pending.py --limit 1
```

**You'll see logs like:**
```
Transcript verification for abc123:
  - Total segments: 1,234
  - First timestamp: 0.00s
  - Last timestamp: 3600.50s
  - Duration covered: 3600.50s (60.0 minutes)
  - Character count: 125,432
  - Word count: 23,456
  - Gaps found: 2

=== CHUNK PROCESSING START ===
Total chunks to process: 16

Processing chunk 1/16:
  Position: 0 - 8,000
  Length: 8,000 characters
  Starts: 'Welcome to the podcast...'
  Ends: '...and that's how it works.'
  Found 3 recommendations in this chunk

=== CHUNK PROCESSING COMPLETE ===
First chunk started at position: 0
Last chunk ended at position: 125,432
Total characters processed: 125,432
Coverage verification: True
```

---

### Method 3: Query Database (Permanent)
View stored metadata after processing:

```bash
python scripts/view_metadata.py
```

**Shows:**
- Episode information
- Full transcript metadata
- Full Claude processing metadata
- Quality check summary

**Or query specific episode:**
```bash
python scripts/view_metadata.py --episode-id <id>
```

---

### Method 4: List All Episodes
See which episodes have metadata:

```bash
python scripts/view_metadata.py --list
```

**Output:**
```
Status       Metadata        Title                           Recs
-------------------------------------------------------------------
completed    ✅ T  ✅ C      New Episode with Phase 1        15
completed    ❌ T  ❌ C      Old Episode (no metadata)       12
```

Legend:
- ✅ T = Has transcript metadata
- ✅ C = Has Claude metadata

---

## What You'll See in Each Location

### 📋 In Logs (During Processing)

**Transcript Verification:**
```
INFO - Transcript verification for abc123:
INFO -   - Total segments: 884
INFO -   - First timestamp: 0.24s
INFO -   - Last timestamp: 2106.26s
INFO -   - Duration covered: 2106.02s (35.1 minutes)
INFO -   - Character count: 32,962
INFO -   - Word count: 5,686
INFO -   - Gaps found: 0
```

**Chunk Processing:**
```
INFO - === CHUNK PROCESSING START ===
INFO - Total chunks to process: 5
INFO - Processing chunk 1/5:
INFO -   Position: 0 - 7,960
INFO -   Length: 7,960 characters
INFO -   Starts: 'Welcome to...'
INFO -   Ends: '...and so forth.'
INFO -   Found 0 recommendations in this chunk
INFO - === CHUNK PROCESSING COMPLETE ===
INFO - Coverage verification: True
```

---

### 💾 In Database (After Processing)

**Query in Python:**
```python
from app.database import SessionLocal
from app.models.episode import Episode

db = SessionLocal()
episode = db.query(Episode).first()

# Transcript metadata
print(episode.transcript_metadata)
# {
#   "total_segments": 884,
#   "start_time": 0.24,
#   "end_time": 2106.26,
#   "duration_covered_seconds": 2106.02,
#   "character_count": 32962,
#   "word_count": 5686,
#   "gaps_detected": 0,
#   "is_complete": true,
#   "gaps": []
# }

# Claude metadata
print(episode.claude_processing_metadata)
# {
#   "total_chunks": 5,
#   "total_characters_sent": 32962,
#   "first_chunk": {...},
#   "last_chunk": {...},
#   "chunks": [...],
#   "total_recommendations_found": 8,
#   "unique_recommendations": 5
# }
```

---

## Example: Full Testing Flow

### Step 1: Run Demo
```bash
python scripts/demo_phase1.py
```
**Result:** See what checks are performed ✅

### Step 2: Check Current Status
```bash
python scripts/view_metadata.py --list
```
**Result:** See that no episodes have metadata yet ⚠️

### Step 3: Process New Episode
```bash
# Pick one pending episode to process
python scripts/process_all_pending.py --limit 1
```
**Result:** Watch logs in real-time, see all checks ✅

### Step 4: View Stored Metadata
```bash
python scripts/view_metadata.py
```
**Result:** See metadata stored in database ✅

### Step 5: Verify Everything Works
```bash
python scripts/view_metadata.py --list
```
**Result:** See the new episode has ✅ T ✅ C ✅

---

## Testing Without Processing Episodes

If you don't want to process a full episode (costs $0.20), use the test script:

```bash
python scripts/test_verification.py
```

**This:**
- Fetches transcript (free)
- Processes only 1 chunk with Claude ($0.005)
- Shows all verification working
- Doesn't save to database

**Perfect for:**
- Testing before production
- Verifying changes work
- Quick validation

---

## Common Questions

### Q: Why don't my existing episodes have metadata?
**A:** They were processed before Phase 1. The metadata fields are NULL for old episodes.

**Solution:** Re-process them:
```bash
# Reset one episode to pending
python -c "
from app.database import SessionLocal
from app.models.episode import Episode
db = SessionLocal()
ep = db.query(Episode).first()
ep.processing_status = 'pending'
db.commit()
"

# Process it
python scripts/process_all_pending.py --limit 1
```

---

### Q: How do I see logs from past processing?
**A:** Check the log file:
```bash
tail -f processing_all.log
```

Or for specific episode:
```bash
grep "episode_id_here" processing_all.log
```

---

### Q: Can I query metadata via API?
**A:** Yes! The Episode model's `to_dict()` includes the metadata fields.

```bash
# Start API
uvicorn app.main:app --reload

# Query episode
curl http://localhost:8000/api/episodes/{id}
```

**Response includes:**
```json
{
  "id": "...",
  "title": "...",
  "transcriptMetadata": {
    "total_segments": 884,
    "character_count": 32962,
    ...
  },
  "claudeProcessingMetadata": {
    "total_chunks": 5,
    "total_characters_sent": 32962,
    ...
  }
}
```

---

### Q: How do I monitor quality over time?
**A:** Query database for quality metrics:

```python
from app.database import SessionLocal
from app.models.episode import Episode

db = SessionLocal()

# Find incomplete transcripts
incomplete = db.query(Episode).filter(
    Episode.transcript_metadata['is_complete'].astext == 'false'
).all()

print(f"Incomplete transcripts: {len(incomplete)}")

# Find episodes with gaps
episodes = db.query(Episode).filter(
    Episode.transcript_metadata.isnot(None)
).all()

for ep in episodes:
    gaps = ep.transcript_metadata.get('gaps_detected', 0)
    if gaps > 0:
        print(f"{ep.title}: {gaps} gaps")
```

---

## Summary

### ✅ Quick Test (30 seconds)
```bash
python scripts/demo_phase1.py
```

### ✅ View Current Status
```bash
python scripts/view_metadata.py --list
```

### ✅ Process & Capture
```bash
python scripts/process_all_pending.py --limit 1
```

### ✅ View Results
```bash
python scripts/view_metadata.py
```

---

## All Available Scripts

| Script | Purpose | Cost | Time |
|--------|---------|------|------|
| `demo_phase1.py` | Show what Phase 1 does | $0.005 | 30s |
| `test_verification.py` | Test verification working | $0.005 | 30s |
| `view_metadata.py` | View stored metadata | Free | 1s |
| `view_metadata.py --list` | List all episodes | Free | 2s |
| `process_all_pending.py --limit 1` | Process with metadata | $0.20 | 2-3min |

---

**Phase 1 is fully implemented and tested!** ✅

All checks are captured in logs and database. You can verify everything works without processing full episodes.
