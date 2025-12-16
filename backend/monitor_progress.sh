#!/bin/bash
# Monitor batch processing progress

DB="podcast_recs.db"
LOGFILE="processing_batch.log"

echo "==================================================================="
echo "Batch Processing Monitor - Started at $(date)"
echo "==================================================================="
echo ""

while true; do
    # Get current stats from database
    STATS=$(sqlite3 $DB "SELECT
        (SELECT COUNT(*) FROM episodes WHERE processing_status='completed') as completed,
        (SELECT COUNT(*) FROM episodes WHERE processing_status='pending') as pending,
        (SELECT COUNT(*) FROM episodes WHERE processing_status='failed') as failed,
        (SELECT COUNT(*) FROM recommendations) as recs
    ;")

    COMPLETED=$(echo $STATS | cut -d'|' -f1)
    PENDING=$(echo $STATS | cut -d'|' -f2)
    FAILED=$(echo $STATS | cut -d'|' -f3)
    RECS=$(echo $STATS | cut -d'|' -f4)
    TOTAL=$((COMPLETED + PENDING + FAILED))

    # Check if process is still running
    if pgrep -f "process_all_pending.py" > /dev/null; then
        STATUS="✓ RUNNING"
    else
        STATUS="✗ STOPPED"
    fi

    # Calculate progress percentage
    if [ $TOTAL -gt 0 ]; then
        PERCENT=$((COMPLETED * 100 / TOTAL))
    else
        PERCENT=0
    fi

    # Display progress
    echo "[$(date '+%H:%M:%S')] $STATUS | Episodes: $COMPLETED/$TOTAL ($PERCENT%) | Pending: $PENDING | Failed: $FAILED | Recommendations: $RECS"

    # Check if we've hit a 20-episode milestone
    MILESTONE=$((COMPLETED / 20 * 20))
    if [ -f ".last_milestone" ]; then
        LAST_MILESTONE=$(cat .last_milestone)
    else
        LAST_MILESTONE=0
    fi

    if [ $MILESTONE -gt $LAST_MILESTONE ] && [ $((COMPLETED % 20)) -eq 0 ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🎯 MILESTONE: $COMPLETED episodes processed!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   Progress: $PERCENT% complete"
        echo "   Recommendations extracted: $RECS"
        echo "   Failed episodes: $FAILED"
        echo "   Remaining: $PENDING episodes"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo $MILESTONE > .last_milestone
    fi

    # Exit if processing is complete
    if [ $PENDING -eq 0 ] && [ "$STATUS" = "✗ STOPPED" ]; then
        echo ""
        echo "==================================================================="
        echo "✅ PROCESSING COMPLETE!"
        echo "==================================================================="
        echo "Final Stats:"
        echo "  - Episodes completed: $COMPLETED"
        echo "  - Episodes failed: $FAILED"
        echo "  - Total recommendations: $RECS"
        echo "==================================================================="
        rm -f .last_milestone
        break
    fi

    # Wait 60 seconds before next check
    sleep 60
done
