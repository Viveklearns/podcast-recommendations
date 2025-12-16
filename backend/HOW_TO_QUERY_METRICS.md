# How to Query Processing Metrics

## Quick Reference

**Database File:** `podcast_recs.db` (in backend directory)
**Table:** `processing_metrics`
**Time Unit:** `processing_time_seconds` is in **seconds**

---

## Using CLI Tool (Easiest)

```bash
cd backend
source venv/bin/activate

# View Phase 1 summary
python scripts/view_phase_metrics.py --phase phase_1

# List all metrics
python scripts/view_phase_metrics.py --list

# Compare phases
python scripts/view_phase_metrics.py --compare phase_1 phase_2
```

**Output includes units:**
```
⏱️  Performance Metrics:
  Avg processing time: 142.5 seconds (2.4 minutes)
```

---

## Using SQLite Directly

### Basic Query with Units

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  character_count,
  estimated_cost AS cost_usd,
  processing_time_seconds AS time_sec,
  ROUND(processing_time_seconds/60.0, 1) AS time_min
FROM processing_metrics;
"
```

**Output:**
```
phase    character_count  cost_usd  time_sec  time_min
-------  ---------------  --------  --------  --------
phase_1  32962            0.0247    142.5     2.4
```

### All Metrics with Units

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  total_segments,
  character_count,
  gaps_detected,
  is_complete,
  total_chunks,
  unique_recommendations AS recs,
  estimated_cost AS 'cost ($)',
  processing_time_seconds AS 'time (sec)',
  ROUND(processing_time_seconds/60.0, 1) AS 'time (min)'
FROM processing_metrics;
"
```

### Average Time by Phase

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  COUNT(*) as episodes,
  ROUND(AVG(processing_time_seconds), 1) AS 'avg_time_sec',
  ROUND(AVG(processing_time_seconds)/60.0, 1) AS 'avg_time_min'
FROM processing_metrics
GROUP BY phase;
"
```

### Find Slow Episodes (> 3 minutes)

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  episode_id,
  processing_time_seconds AS time_sec,
  ROUND(processing_time_seconds/60.0, 1) AS time_min
FROM processing_metrics
WHERE processing_time_seconds > 180
ORDER BY processing_time_seconds DESC;
"
```

---

## Using Python

```python
from app.database import SessionLocal
from app.models.processing_metrics import ProcessingMetrics

db = SessionLocal()

# Query metrics
metrics = db.query(ProcessingMetrics).all()

for m in metrics:
    time_sec = m.processing_time_seconds
    time_min = time_sec / 60.0

    print(f"Phase: {m.phase}")
    print(f"  Time: {time_sec:.1f} seconds ({time_min:.1f} minutes)")
    print(f"  Cost: ${m.estimated_cost:.4f}")
    print(f"  Complete: {m.is_complete}")
    print()

db.close()
```

---

## Useful Queries

### Total Processing Time by Phase

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  COUNT(*) as episodes,
  SUM(processing_time_seconds) AS total_sec,
  ROUND(SUM(processing_time_seconds)/60.0, 1) AS total_min,
  ROUND(SUM(processing_time_seconds)/3600.0, 2) AS total_hours
FROM processing_metrics
GROUP BY phase;
"
```

### Cost per Minute of Processing

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  ROUND(AVG(estimated_cost / (processing_time_seconds/60.0)), 4) AS cost_per_minute
FROM processing_metrics
WHERE processing_time_seconds > 0
GROUP BY phase;
"
```

### Quality vs Speed Analysis

```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  is_complete,
  COUNT(*) as episodes,
  ROUND(AVG(processing_time_seconds), 1) AS avg_time_sec,
  ROUND(AVG(unique_recommendations), 1) AS avg_recs
FROM processing_metrics
GROUP BY phase, is_complete;
"
```

---

## Column Reference

| Column | Unit | Description |
|--------|------|-------------|
| `processing_time_seconds` | seconds | Total processing time |
| `estimated_cost` | USD ($) | Estimated API cost |
| `character_count` | count | Total characters processed |
| `total_segments` | count | Transcript segments |
| `duration_covered_seconds` | seconds | Video duration covered |
| `start_time` | seconds | First transcript timestamp |
| `end_time` | seconds | Last transcript timestamp |

---

## Quick Conversions

### Seconds to Minutes
```sql
SELECT processing_time_seconds / 60.0 AS minutes
```

### Seconds to Hours
```sql
SELECT processing_time_seconds / 3600.0 AS hours
```

### Cost per Hour
```sql
SELECT estimated_cost / (processing_time_seconds / 3600.0) AS cost_per_hour
```

---

## Examples with Real Data

### Current Data
```
phase_1 | 142.5 seconds = 2.4 minutes
```

### When You Have More Data
```bash
sqlite3 -header -column podcast_recs.db "
SELECT
  phase,
  MIN(processing_time_seconds) AS min_sec,
  MAX(processing_time_seconds) AS max_sec,
  AVG(processing_time_seconds) AS avg_sec,
  ROUND(AVG(processing_time_seconds)/60.0, 1) AS avg_min
FROM processing_metrics
GROUP BY phase;
"
```

**Output Example:**
```
phase    min_sec  max_sec  avg_sec  avg_min
-------  -------  -------  -------  -------
phase_1  120.3    180.5    142.5    2.4
phase_2  110.2    165.3    130.1    2.2
```

---

## Summary

- **Time is stored in SECONDS** in `processing_time_seconds`
- **CLI tool shows both seconds and minutes**
- **Use SQL to convert:** `seconds / 60.0` for minutes, `seconds / 3600.0` for hours
- **Column names include units** for clarity (e.g., `duration_covered_seconds`)

**All time values are in seconds unless otherwise specified!** ⏱️
