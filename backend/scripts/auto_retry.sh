#!/bin/bash

# Auto-retry script for processing pending episodes
# Retries every 15 minutes until all episodes are processed

cd /Users/vivekgupta/Desktop/podcast/backend

echo "==================================================================="
echo "Auto-retry script started at $(date)"
echo "Will retry processing every 15 minutes"
echo "==================================================================="

while true; do
    # Check how many pending episodes remain
    PENDING=$(sqlite3 podcast_recs.db "SELECT COUNT(*) FROM episodes WHERE processing_status = 'pending'")

    echo ""
    echo "$(date): Checking status..."
    echo "Pending episodes: $PENDING"

    if [ "$PENDING" -eq 0 ]; then
        echo "$(date): All episodes processed! Exiting."
        break
    fi

    echo "$(date): Starting processing batch..."

    # Run processing script
    source venv/bin/activate
    python scripts/process_all_pending.py > "processing_retry_$(date +%Y%m%d_%H%M%S).log" 2>&1

    # Check results
    COMPLETED=$(sqlite3 podcast_recs.db "SELECT COUNT(*) FROM episodes WHERE processing_status = 'completed'")
    FAILED=$(sqlite3 podcast_recs.db "SELECT COUNT(*) FROM episodes WHERE processing_status = 'failed'")
    RECS=$(sqlite3 podcast_recs.db "SELECT COUNT(*) FROM recommendations")

    echo "$(date): Batch complete"
    echo "  Completed: $COMPLETED/294"
    echo "  Failed: $FAILED"
    echo "  Recommendations: $RECS"

    # Reset failed episodes back to pending for next retry
    if [ "$FAILED" -gt 0 ]; then
        echo "$(date): Resetting $FAILED failed episodes to pending"
        sqlite3 podcast_recs.db "UPDATE episodes SET processing_status = 'pending' WHERE processing_status = 'failed'"
    fi

    # Wait 15 minutes before next retry
    echo "$(date): Waiting 15 minutes before next retry..."
    sleep 900  # 15 minutes = 900 seconds
done

echo ""
echo "==================================================================="
echo "Processing complete at $(date)"
echo "==================================================================="
