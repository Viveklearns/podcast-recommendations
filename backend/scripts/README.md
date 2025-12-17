# Backend Scripts Directory

This directory contains scripts for processing podcast episodes and managing the recommendation database.

## Directory Structure

```
scripts/
├── active/           # Primary scripts for production use
├── archive/          # Legacy/one-time scripts (kept for reference)
│   ├── migrations/   # Database migration scripts (already applied)
│   ├── experiments/  # Model comparison & experimental scripts
│   ├── bootstrap/    # Initial data loading scripts (already run)
│   ├── old_versions/ # Superseded script versions
│   └── docs/         # Historical documentation
└── utils/            # Debug and utility scripts
```

---

## Active Scripts (Use These)

### `active/process_all_pending.py`
**Main processing pipeline** - Processes pending podcast episodes and extracts recommendations.

```bash
# Process all pending episodes
python active/process_all_pending.py

# Process limited number of episodes
python active/process_all_pending.py --limit 10
```

**What it does:**
1. Fetches transcripts from YouTube
2. Extracts guest names from episode titles
3. Uses Claude Sonnet 4 to extract recommendations
4. Enriches books with Google Books API metadata
5. Stores everything in SQLite database

**Status tracking:**
- Checks `episodes.processing_status`
- Only processes episodes with status = 'pending' or 'failed'
- Updates status to 'completed' or 'failed'

---

### `active/auto_retry.sh`
**Automatic retry system** - Monitors and retries failed episodes every 15 minutes.

```bash
# Start auto-retry in background
./active/auto_retry.sh

# Monitor progress
tail -f auto_retry_monitor.log
```

**What it does:**
- Runs `process_all_pending.py --limit 5` every 15 minutes
- Useful for handling temporary YouTube API failures
- Logs to `auto_retry_monitor.log`

**When to use:**
- After bulk episode imports
- When YouTube blocks transcript access temporarily
- For unattended overnight processing

---

### `active/fix_guest_names.py`
**Re-extract guest names** - Updates guest names for all episodes by parsing titles.

```bash
python active/fix_guest_names.py
```

**What it does:**
- Reads all episode titles from database
- Extracts guest names using regex pattern
- Updates `episodes.guest_names` field
- Handles Lenny's Podcast format: "Topic | Guest Name (title)"

**When to use:**
- After fixing guest name extraction logic
- When episode titles change
- To backfill guest data for old episodes

---

### `active/add_lenny_episodes.py`
**Add new episodes** - Discovers and adds new Lenny's Podcast episodes to database.

```bash
python active/add_lenny_episodes.py
```

**What it does:**
- Uses YouTube Discovery Service to find recent episodes
- Filters by publication date
- Adds new episodes with status='pending'
- Avoids duplicates (checks by YouTube video ID)

**When to use:**
- Weekly/monthly to add new podcast episodes
- Before running bulk processing

---

### `active/show_metrics_table.py`
**View processing metrics** - Displays database statistics in formatted tables.

```bash
python active/show_metrics_table.py
```

**What it does:**
- Shows episode count by status (pending, completed, failed)
- Displays recommendation count by type
- Shows enrichment statistics
- Formatted output using tabulate

**When to use:**
- Check processing progress
- Debug data quality issues
- Generate status reports

---

## Utility Scripts

### `utils/view_metadata.py`
View detailed metadata for specific recommendations.

```bash
python utils/view_metadata.py
```

**Use case:** Debug Google Books enrichment data, check ISBN/cover URLs

---

### `utils/view_phase_metrics.py`
View processing phase metrics (transcript quality, Claude API usage, etc.)

```bash
python utils/view_phase_metrics.py
```

**Use case:** Analyze processing costs, check transcript coverage

---

## Archive (Reference Only)

### `archive/migrations/`
Database schema migration scripts - **already applied to production database**.

- `migrate_add_metadata_fields.py` - Added `extra_metadata` JSONB column
- `migrate_add_processing_metrics.py` - Added `processing_metrics` table
- `migrate_add_video_duration_url.py` - Added duration/URL fields to episodes

**When to use:** Only if rebuilding database from scratch

---

### `archive/experiments/`
One-time experimental scripts for research/comparison.

- `compare_models.py` - Claude Sonnet vs Opus comparison
- `compare_sonnet_haiku.py` - Sonnet vs Haiku comparison
- `discover_episodes.py` - Early YouTube discovery logic (replaced by service)

**Results:** Claude Sonnet 4 chosen for best accuracy/cost ratio

---

### `archive/bootstrap/`
Initial data loading scripts - **already executed**.

- `save_lenny_from_playlist.py` - Loaded first batch of episodes
- `save_lenny_full_playlist.py` - Loaded complete playlist (294 episodes)
- `save_lenny_recent_episodes.py` - Old version of episode discovery

**When to use:** Only for adding new podcast sources

---

### `archive/old_versions/`
Superseded script versions kept for reference.

- `process_lenny.py` - Old processing script (before process_all_pending.py)
- `process_single_video.py` - Old single-video processor
- `process_single_video_phase2.py` - Old version
- `demo_phase1.py` - Phase 1 development demo
- `demo_save_metrics.py` - Metrics demo
- `test_*.py` - Old test scripts
- `fix_lenny_episodes.py` - One-time episode data fix
- `update_lenny_dates.py` - One-time date fix

**Why kept:** Reference implementation details, debugging old data issues

---

### `archive/docs/`
Historical documentation and planning files.

**Markdown files:**
- API endpoint notes
- Metrics querying guides
- Testing instructions
- Milestone documentation
- Model comparison results
- Technical specifications

**Why kept:** Historical context for architectural decisions

---

## Common Workflows

### 1. Add New Episodes and Process
```bash
# Discover and add new episodes
python active/add_lenny_episodes.py

# Process all pending
python active/process_all_pending.py

# Or start auto-retry for hands-off processing
./active/auto_retry.sh
```

### 2. Check Processing Status
```bash
# View statistics
python active/show_metrics_table.py

# Check auto-retry logs
tail -f auto_retry_monitor.log
```

### 3. Fix Data Quality Issues
```bash
# Re-extract guest names
python active/fix_guest_names.py

# Reprocess specific episode (manual)
# Edit episode in DB to set status='pending'
# Then run process_all_pending.py
```

### 4. Debug Single Episode
```bash
# Option 1: Use old debug script
python archive/old_versions/process_single_video.py <video_id>

# Option 2: Set status and use main script
# UPDATE episodes SET processing_status='pending' WHERE youtube_video_id='xxx'
python active/process_all_pending.py --limit 1
```

---

## Environment Setup

All scripts require:
1. Virtual environment activated:
   ```bash
   source ../venv/bin/activate
   ```

2. Environment variables set (from `../.env`):
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   GOOGLE_BOOKS_API_KEY=AIza...  # Optional but recommended
   DATABASE_URL=sqlite:///podcast_recs.db
   ```

3. Database initialized:
   ```bash
   # Database auto-created by FastAPI on first run
   cd .. && uvicorn app.main:app
   ```

---

## Dependencies

Scripts use these backend services:
- `app.services.youtube_service` - YouTube transcript fetching
- `app.services.claude_service` - Claude AI extraction
- `app.services.google_books_service` - Book metadata enrichment
- `app.database` - SQLAlchemy database session

See `../requirements.txt` for package dependencies.

---

## Cost Estimates

### Claude API
- **Sonnet 4:** ~$0.08 per episode
- **291 episodes:** ~$17 total
- **Input:** ~$3/M tokens
- **Output:** ~$15/M tokens

### Google Books API
- **Free tier:** 1,000 requests/day
- **Current usage:** ~3-5 requests per book
- **Cost:** $0 (within free tier)

### YouTube Transcript API
- **Free** - No API key required
- Uses `youtube-transcript-api` library

---

## Troubleshooting

### Episodes stuck in 'pending' status
```bash
# Check logs
tail -f auto_retry_monitor.log

# Manually retry
python active/process_all_pending.py --limit 1
```

### "Database is locked" error
SQLite WAL mode should prevent this, but if it occurs:
```bash
# Stop all running scripts
pkill -f process_all_pending.py

# Check for zombie processes
ps aux | grep python

# Restart processing
python active/process_all_pending.py
```

### Guest names not extracting
```bash
# Re-run extraction with updated regex
python active/fix_guest_names.py

# Check episode title format in database
sqlite3 ../podcast_recs.db "SELECT title FROM episodes LIMIT 5;"
```

### Book metadata missing
- Check if Google Books API key is set
- Verify book title is not too generic
- Check `extra_metadata` field in database for API response

---

## Adding a New Podcast Source

1. **Create discovery script** (based on `add_lenny_episodes.py`):
   ```python
   # active/add_tim_ferriss_episodes.py
   from app.services.youtube_discovery_service import discover_episodes

   episodes = discover_episodes(
       query="Tim Ferriss Show podcast",
       max_results=100
   )
   # Save to database...
   ```

2. **Update guest name extraction** in `fix_guest_names.py`:
   ```python
   # Add new regex pattern for Tim Ferriss format
   if "Tim Ferriss" in title:
       # Extract guest from "Guest Name — Topic" format
       pass
   ```

3. **Test with single episode**:
   ```bash
   python active/process_all_pending.py --limit 1
   ```

4. **Process all episodes**:
   ```bash
   python active/process_all_pending.py
   ```

---

## Script Maintenance

### When to update scripts
- Guest name format changes → Update `fix_guest_names.py` regex
- New recommendation types → Update Claude prompts in `claude_service.py`
- API rate limits → Add delays/retries in service files

### When to create new scripts
- Adding new podcast source → Create `add_{podcast}_episodes.py`
- New data enrichment → Create enrichment service + migration
- Bulk data fixes → Create one-time script in `archive/old_versions/`

---

## Questions?

Check these resources:
1. Main project README: `../../README.md`
2. Technical spec: `../../spec.md`
3. API docs: Start server and visit `/docs`
4. Archived docs: `archive/docs/`
