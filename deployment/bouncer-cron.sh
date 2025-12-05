#!/bin/bash
#
# Bouncer Cron Wrapper Script
#
# This script is designed to be run by cron for scheduled Bouncer execution.
# It sets up the environment, runs Bouncer in batch mode, and logs output.
#

# Exit on error
set -e

# Configuration
BOUNCER_DIR="/path/to/bouncer"  # CHANGE THIS
VENV_DIR="$BOUNCER_DIR/venv"
LOG_DIR="$BOUNCER_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/bouncer_cron_$TIMESTAMP.log"

# Scan mode: "full" or "incremental"
# - full: Scan all files (good for periodic audits)
# - incremental: Only scan files changed since last run (faster, uses git)
SCAN_MODE="${SCAN_MODE:-full}"  # Default to full scan

# For incremental mode: time window to check (e.g., "24 hours ago", "1 day ago")
TIME_WINDOW="${TIME_WINDOW:-24 hours ago}"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log start time
echo "=== Bouncer Cron Job Started at $(date) ===" >> "$LOG_FILE"

# Change to bouncer directory
cd "$BOUNCER_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Load environment variables
if [ -f "$BOUNCER_DIR/.env" ]; then
    export $(cat "$BOUNCER_DIR/.env" | grep -v '^#' | xargs)
fi

# Run Bouncer in batch mode
echo "Running Bouncer scan (mode: $SCAN_MODE)..." >> "$LOG_FILE"

if [ "$SCAN_MODE" = "incremental" ]; then
    # Incremental: only check files changed since TIME_WINDOW
    echo "Checking files modified since: $TIME_WINDOW" >> "$LOG_FILE"
    python -m bouncer.main scan "$BOUNCER_DIR" --git-diff --since="$TIME_WINDOW" >> "$LOG_FILE" 2>&1
else
    # Full: scan all files
    echo "Running full scan of all files" >> "$LOG_FILE"
    python -m bouncer.main scan "$BOUNCER_DIR" >> "$LOG_FILE" 2>&1
fi

# Log completion
echo "=== Bouncer Cron Job Completed at $(date) ===" >> "$LOG_FILE"

# Optional: Clean up old logs (keep last 30 days)
find "$LOG_DIR" -name "bouncer_cron_*.log" -mtime +30 -delete

# Optional: Send notification on completion
# curl -X POST -H 'Content-type: application/json' \
#   --data "{\"text\":\"Bouncer cron job completed at $(date)\"}" \
#   "$SLACK_WEBHOOK_URL"

exit 0
