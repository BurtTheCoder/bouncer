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
echo "Running Bouncer scan..." >> "$LOG_FILE"
python -m bouncer.main scan "$BOUNCER_DIR" >> "$LOG_FILE" 2>&1

# Log completion
echo "=== Bouncer Cron Job Completed at $(date) ===" >> "$LOG_FILE"

# Optional: Clean up old logs (keep last 30 days)
find "$LOG_DIR" -name "bouncer_cron_*.log" -mtime +30 -delete

# Optional: Send notification on completion
# curl -X POST -H 'Content-type: application/json' \
#   --data "{\"text\":\"Bouncer cron job completed at $(date)\"}" \
#   "$SLACK_WEBHOOK_URL"

exit 0
