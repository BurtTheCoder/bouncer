# Bouncer Scheduled Task Script for Windows
#
# This PowerShell script is designed to be run by Windows Task Scheduler
# for scheduled Bouncer execution.
#

# Configuration
$BouncerDir = "C:\path\to\bouncer"  # CHANGE THIS
$VenvDir = "$BouncerDir\venv"
$LogDir = "$BouncerDir\logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = "$LogDir\bouncer_scheduled_$Timestamp.log"

# Scan mode: "full" or "incremental"
# - full: Scan all files (good for periodic audits)
# - incremental: Only scan files changed since last run (faster, uses git)
$ScanMode = if ($env:SCAN_MODE) { $env:SCAN_MODE } else { "full" }

# For incremental mode: time window to check (e.g., "24 hours ago", "1 day ago")
$TimeWindow = if ($env:TIME_WINDOW) { $env:TIME_WINDOW } else { "24 hours ago" }

# Create log directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Start logging
"=== Bouncer Scheduled Task Started at $(Get-Date) ===" | Out-File -FilePath $LogFile -Encoding UTF8

# Change to bouncer directory
Set-Location $BouncerDir

# Activate virtual environment
& "$VenvDir\Scripts\Activate.ps1"

# Load environment variables from .env file
if (Test-Path "$BouncerDir\.env") {
    Get-Content "$BouncerDir\.env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Run Bouncer in batch mode
"Running Bouncer scan (mode: $ScanMode)..." | Out-File -FilePath $LogFile -Append -Encoding UTF8
try {
    if ($ScanMode -eq "incremental") {
        # Incremental: only check files changed since TIME_WINDOW
        "Checking files modified since: $TimeWindow" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        python -m bouncer.main scan $BouncerDir --git-diff --since="$TimeWindow" 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
    } else {
        # Full: scan all files
        "Running full scan of all files" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        python -m bouncer.main scan $BouncerDir 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
    }
    "=== Bouncer Scheduled Task Completed Successfully at $(Get-Date) ===" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    exit 0
} catch {
    "=== Bouncer Scheduled Task Failed at $(Get-Date) ===" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    "Error: $_" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    exit 1
}

# Optional: Clean up old logs (keep last 30 days)
Get-ChildItem $LogDir -Filter "bouncer_scheduled_*.log" | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-30)
} | Remove-Item

# Optional: Send notification on completion
# $body = @{ text = "Bouncer scheduled task completed at $(Get-Date)" } | ConvertTo-Json
# Invoke-RestMethod -Uri $env:SLACK_WEBHOOK_URL -Method Post -Body $body -ContentType 'application/json'
