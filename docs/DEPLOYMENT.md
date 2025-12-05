# 🚀 Bouncer Deployment Guide

This guide covers different ways to deploy and run Bouncer in production.

---

## 📋 Table of Contents

- [Operation Modes](#operation-modes)
- [Linux (systemd)](#linux-systemd)
- [macOS (launchd)](#macos-launchd)
- [Windows (Task Scheduler)](#windows-task-scheduler)
- [Docker](#docker)
- [Cloud Deployment](#cloud-deployment)

---

## 🎛️ Operation Modes

Bouncer supports different operation modes to fit your workflow.

### 1. **Monitor Mode** (Default)

Continuously watches a directory for file changes and processes them in real-time.

```bash
bouncer start
```

**Use when:**
- You want real-time quality control
- You're actively developing
- You want immediate feedback

---

### 2. **Report-Only Mode**

Checks files and reports issues **without making any changes**.

**Configuration:**

Set `auto_fix: false` for all bouncers in `bouncer.yaml`:

```yaml
bouncers:
  code_quality:
    enabled: true
    auto_fix: false  # Report only, no fixes
  
  security:
    enabled: true
    auto_fix: false
  
  # ... repeat for all bouncers
```

**Or use the CLI flag:**

```bash
bouncer start --report-only
```

**Use when:**
- You want to review all changes manually
- You're testing Bouncer on a new project
- You have strict change control requirements
- You're using Bouncer in CI/CD (review before merge)

---

### 3. **Batch Mode**

Scan an entire directory once and generate a comprehensive report.

```bash
bouncer scan /path/to/project
```

**Use when:**
- You want to audit an existing codebase
- You're onboarding a new project
- You want a one-time quality assessment

---

### 4. **Diff Mode**

Only check files that have changed (git diff).

```bash
bouncer start --diff-only
```

**Use when:**
- You have a large codebase
- You only care about new changes
- You want faster checks

---

## 🐧 Linux (systemd)

Run Bouncer as a system service that starts automatically on boot.

### 1. Install Bouncer

```bash
git clone https://github.com/BurtTheCoder/bouncer.git
cd bouncer
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Configure Bouncer

Edit `bouncer.yaml` and `.env` with your settings.

### 3. Create Service File

Copy the provided service file:

```bash
sudo cp deployment/bouncer.service /etc/systemd/system/
```

Edit the service file to match your setup:

```bash
sudo nano /etc/systemd/system/bouncer.service
```

Update these paths:
- `User=YOUR_USERNAME` → Your Linux username
- `WorkingDirectory=/path/to/bouncer` → Full path to bouncer directory
- `Environment="PATH=/path/to/bouncer/venv/bin"` → Full path to venv
- `EnvironmentFile=/path/to/bouncer/.env` → Full path to .env file
- `ExecStart=/path/to/bouncer/venv/bin/python ...` → Full path to python

### 4. Enable and Start Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable bouncer

# Start the service now
sudo systemctl start bouncer

# Check status
sudo systemctl status bouncer
```

### 5. View Logs

```bash
# Follow logs in real-time
sudo journalctl -u bouncer -f

# View recent logs
sudo journalctl -u bouncer -n 100
```

### 6. Manage Service

```bash
# Stop service
sudo systemctl stop bouncer

# Restart service
sudo systemctl restart bouncer

# Disable service (don't start on boot)
sudo systemctl disable bouncer
```

---

## 🍎 macOS (launchd)

Run Bouncer as a launch agent that starts automatically when you log in.

### 1. Install Bouncer

```bash
git clone https://github.com/BurtTheCoder/bouncer.git
cd bouncer
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Configure Bouncer

Edit `bouncer.yaml` and `.env` with your settings.

### 3. Create Launch Agent

Copy the provided plist file:

```bash
cp deployment/com.bouncer.agent.plist ~/Library/LaunchAgents/
```

Edit the plist file:

```bash
nano ~/Library/LaunchAgents/com.bouncer.agent.plist
```

Update these values:
- `/path/to/bouncer/venv/bin/python` → Full path to your venv python
- `/path/to/bouncer` → Full path to bouncer directory
- `YOUR_API_KEY_HERE` → Your Anthropic API key
- `YOUR_WEBHOOK_URL_HERE` → Your Slack webhook URL

### 4. Load and Start

```bash
# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.bouncer.agent.plist

# Start the agent
launchctl start com.bouncer.agent
```

### 5. View Logs

```bash
# View standard output
tail -f /tmp/bouncer.log

# View errors
tail -f /tmp/bouncer.error.log
```

### 6. Manage Service

```bash
# Stop the agent
launchctl stop com.bouncer.agent

# Unload the agent (disable)
launchctl unload ~/Library/LaunchAgents/com.bouncer.agent.plist

# Reload after making changes
launchctl unload ~/Library/LaunchAgents/com.bouncer.agent.plist
launchctl load ~/Library/LaunchAgents/com.bouncer.agent.plist
```

---

## 🪟 Windows (Task Scheduler)

Run Bouncer as a scheduled task that starts automatically.

### 1. Install Bouncer

```powershell
git clone https://github.com/BurtTheCoder/bouncer.git
cd bouncer
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

### 2. Configure Bouncer

Edit `bouncer.yaml` and `.env` with your settings.

### 3. Create Batch Script

Create `start-bouncer.bat` in the bouncer directory:

```batch
@echo off
cd /d C:\path\to\bouncer
call venv\Scripts\activate.bat
python -m bouncer.main start
```

### 4. Create Scheduled Task

1. Open **Task Scheduler**
2. Click **Create Task** (not "Create Basic Task")
3. **General tab:**
   - Name: `Bouncer`
   - Description: `AI-powered file monitoring agent`
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"

4. **Triggers tab:**
   - Click **New**
   - Begin the task: **At startup**
   - Click **OK**

5. **Actions tab:**
   - Click **New**
   - Action: **Start a program**
   - Program/script: `C:\path\to\bouncer\start-bouncer.bat`
   - Start in: `C:\path\to\bouncer`
   - Click **OK**

6. **Conditions tab:**
   - Uncheck "Start the task only if the computer is on AC power"

7. **Settings tab:**
   - Check "Allow task to be run on demand"
   - Check "If the task fails, restart every: 1 minute"
   - Set "Attempt to restart up to: 3 times"

8. Click **OK** to save

### 5. Start Task

Right-click the task and select **Run**.

### 6. View Logs

Check `bouncer.log` in the bouncer directory.

---

## 🐳 Docker

Run Bouncer in a container for isolation and portability.

### 1. Using Docker Compose (Recommended)

```bash
# Edit docker-compose.yml to mount your project directory
nano docker-compose.yml

# Start Bouncer
docker-compose up -d

# View logs
docker-compose logs -f

# Stop Bouncer
docker-compose down
```

### 2. Using Docker Directly

```bash
# Build image
docker build -t bouncer:latest .

# Run container
docker run -d \
  --name bouncer \
  -v /path/to/your/project:/app/watch:ro \
  -e ANTHROPIC_API_KEY=your_key \
  -e SLACK_WEBHOOK_URL=your_webhook \
  bouncer:latest

# View logs
docker logs -f bouncer

# Stop container
docker stop bouncer
```

### 3. Docker with Report-Only Mode

```bash
docker run -d \
  --name bouncer \
  -v /path/to/your/project:/app/watch:ro \
  -e ANTHROPIC_API_KEY=your_key \
  -e SLACK_WEBHOOK_URL=your_webhook \
  bouncer:latest \
  bouncer start --report-only
```

---

## ☁️ Cloud Deployment

### AWS (EC2)

1. Launch an EC2 instance (t3.small or larger)
2. Install Bouncer following the Linux instructions
3. Set up systemd service
4. Configure security groups to allow outbound HTTPS
5. Use IAM roles for secrets management (optional)

### Google Cloud (Compute Engine)

1. Create a Compute Engine instance
2. Install Bouncer following the Linux instructions
3. Set up systemd service
4. Use Secret Manager for API keys (optional)

### Azure (Virtual Machines)

1. Create an Azure VM
2. Install Bouncer following the Linux instructions
3. Set up systemd service
4. Use Azure Key Vault for secrets (optional)

---

## 🔧 Advanced Configuration

### Report-Only Mode for Specific Bouncers

You can mix report-only and auto-fix modes:

```yaml
bouncers:
  code_quality:
    enabled: true
    auto_fix: true  # Auto-fix safe issues
  
  security:
    enabled: true
    auto_fix: false  # NEVER auto-fix security issues
  
  infrastructure:
    enabled: true
    auto_fix: false  # Require review for infrastructure changes
```

### Notification-Only Mode

Disable all bouncers and only send notifications:

```yaml
bouncers:
  # All bouncers disabled
  code_quality:
    enabled: false

notifications:
  slack:
    enabled: true
```

### Dry-Run Mode

Test Bouncer without making changes or sending notifications:

```bash
bouncer start --dry-run
```

---

## 🐛 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
# Linux
sudo journalctl -u bouncer -n 50

# macOS
tail -f /tmp/bouncer.error.log

# Windows
Check bouncer.log in the bouncer directory
```

**Common issues:**
- Incorrect paths in service file
- Missing API key in .env
- Python virtual environment not activated
- Permissions issues

### High CPU Usage

- Enable `diff-only` mode to reduce checks
- Increase `debounce_delay` in config
- Disable resource-intensive bouncers

### Missing File Changes

- Check `ignore_patterns` in config
- Verify file watcher is working: `bouncer test-watch`
- Check file system permissions

---

## 📊 Monitoring

### Health Check Endpoint

If running as a service, Bouncer exposes a health check:

```bash
curl http://localhost:8080/health
```

### Metrics

View Bouncer metrics:

```bash
bouncer stats
```

Shows:
- Files processed
- Issues found
- Fixes applied
- Bouncer performance

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` as a template
2. **Use read-only mounts** in Docker (`/app/watch:ro`)
3. **Run as non-root user** in production
4. **Restrict file system access** to only watched directories
5. **Use secrets management** (AWS Secrets Manager, Azure Key Vault, etc.)
6. **Enable report-only mode** for sensitive repositories
7. **Review auto-fixes** before enabling them

---

## 📚 Additional Resources

- [Configuration Guide](../bouncer.yaml)
- [Obsidian Bouncer Guide](OBSIDIAN_BOUNCER.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [GitHub Repository](https://github.com/BurtTheCoder/bouncer)

---

**Questions?** Open an issue on GitHub!


---

## ⏰ Scheduled Execution (Cron & Task Scheduler)

While Bouncer excels at real-time monitoring, you can also run it on a schedule for periodic audits, batch processing, or off-hours scanning. This is ideal for environments where continuous monitoring is unnecessary or resource-intensive.

Scheduled execution uses **Batch Mode** (`bouncer scan`) to check an entire directory at specified intervals. You can choose between two scan modes:

- **Full Scan (default):** Scans every file in the target directory. Ideal for comprehensive periodic audits.
- **Incremental Scan:** Scans only the files that have changed since the last run. Faster and more resource-efficient, making it perfect for frequent checks.

### When to Use Scheduled Execution vs. Continuous Monitoring

| Use Case | Continuous Monitoring (`bouncer start`) | Scheduled Execution (`bouncer scan`) |
| :--- | :--- | :--- |
| **Real-time Feedback** | ✅ **Ideal** | ❌ **Not suitable** |
| **Active Development** | ✅ **Ideal** | ❌ **Too slow** |
| **CI/CD Integration** | ✅ **On commit/PR** | ❌ **Too slow** |
| **Scheduled Audits** | ❌ **Overkill** | ✅ **Ideal** |
| **Off-hours Scanning** | ❌ **Inefficient** | ✅ **Ideal** |
| **Batch Processing** | ❌ **Not designed for it** | ✅ **Ideal** |
| **Low-resource Environments** | ❌ **Can be resource-intensive** | ✅ **Resource-friendly** |
| **Legacy Codebases** | ❌ **Can be noisy** | ✅ **Good for periodic checks** |

---

### Scan Modes: Full vs. Incremental

| Scan Mode | Best For | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Full Scan** | Periodic deep audits | Catches everything, simple to configure | Can be slow and resource-intensive on large projects |
| **Incremental Scan** | Frequent, fast checks | Lightweight, efficient, faster feedback | Relies on Git history, may miss non-Git changes |

**Best Practice:** Use a hybrid approach. Run **incremental scans** frequently (e.g., hourly or daily) and a **full scan** periodically (e.g., weekly or monthly) to ensure complete coverage.

---

### 🐧 Linux & macOS (cron)

Use `cron` to run Bouncer at any interval you choose. We provide a wrapper script to handle the environment and logging.

#### 1. Configure the Cron Script

Edit `deployment/bouncer-cron.sh` and set the `BOUNCER_DIR` variable to the absolute path of your Bouncer installation.

```bash
# In deployment/bouncer-cron.sh
BOUNCER_DIR="/home/ubuntu/bouncer"  # <-- CHANGE THIS
```

#### 2. Set Up Your Crontab

You can control the scan mode using environment variables in your crontab file.

- `SCAN_MODE=full`: (Default) Runs a full scan.
- `SCAN_MODE=incremental`: Runs an incremental scan.
- `TIME_WINDOW="<timespan>"`: Specifies the lookback period for incremental scans (e.g., "1 hour ago", "2 days ago").

Open your crontab for editing:


Open your crontab for editing:

```bash
crontab -e
```

Add a new line to schedule the `bouncer-cron.sh` script. See `deployment/crontab.example` for a full list of examples.

**Example: Full Scan (Daily Audit)**

This runs a full scan every day at 2:00 AM.

```crontab
# Run a full Bouncer scan every day at 2:00 AM
0 2 * * * SCAN_MODE=full /home/ubuntu/bouncer/deployment/bouncer-cron.sh
```

**Example: Incremental Scan (Hourly Check)**

This runs an incremental scan every hour, checking only files that have changed in the last hour.

```crontab
# Run an incremental Bouncer scan every hour
0 * * * * SCAN_MODE=incremental TIME_WINDOW="1 hour ago" /home/ubuntu/bouncer/deployment/bouncer-cron.sh
```

**Example: Hybrid Approach**

Run an incremental scan every 4 hours and a full scan every Sunday at 3:00 AM.

```crontab
# Incremental scan every 4 hours
0 */4 * * * SCAN_MODE=incremental TIME_WINDOW="4 hours ago" /home/ubuntu/bouncer/deployment/bouncer-cron.sh

# Full scan weekly on Sunday at 3 AM
0 3 * * 0 SCAN_MODE=full /home/ubuntu/bouncer/deployment/bouncer-cron.sh
```

See `deployment/crontab.example` for more examples and patterns.

#### 3. Logging

Logs for each cron run are saved to the `logs` directory within your Bouncer project (e.g., `/home/ubuntu/bouncer/logs/bouncer_cron_20251205_103000.log`). The script will automatically clean up logs older than 30 days.

---

### 🪟 Windows (Task Scheduler)

For Windows, you can set the `SCAN_MODE` and `TIME_WINDOW` as environment variables in the Task Scheduler UI or directly within the PowerShell script.

Use Windows Task Scheduler with the provided PowerShell script for powerful, scheduled execution.

#### 1. Configure the PowerShell Script

Edit `deployment/bouncer-scheduled.ps1` and set the `$BouncerDir` variable to the absolute path of your Bouncer installation.

```powershell
# In deployment/bouncer-scheduled.ps1
$BouncerDir = "C:\Users\YourUser\bouncer"  # <-- CHANGE THIS
```

#### 2. Create a Scheduled Task (Incremental Scan Example)

This example sets up a daily incremental scan.

1.  Open **Task Scheduler**.
2.  Click **Create Task**.
3.  **General Tab:** Name it `Bouncer Incremental Scan`.
4.  **Triggers Tab:** Set it to run daily at your desired time.
5.  **Actions Tab:**
    *   Action: **Start a program**.
    *   Program/script: `powershell.exe`
    *   Add arguments: `-ExecutionPolicy Bypass -File "C:\path\to\bouncer\deployment\bouncer-scheduled.ps1"`
    *   Start in: `C:\path\to\bouncer`
6.  **Environment Variables (Optional):** To configure the scan mode, you can add environment variables to the task. This is the cleanest method.
    *   In the task properties, go to the **Actions** tab and edit your action.
    *   In the `Start a program` settings, you can't directly add environment variables. Instead, you can create a wrapper batch file or modify the PowerShell script to accept parameters.

**Recommended Method: Modify the PowerShell script to accept parameters for more robust control.**

Alternatively, for simplicity, you can directly set the variables at the top of the `bouncer-scheduled.ps1` script:

```powershell
# In deployment/bouncer-scheduled.ps1
$ScanMode = "incremental"
$TimeWindow = "24 hours ago"
```

1.  Open **Task Scheduler**.
2.  Click **Create Task** in the Actions pane.
3.  **General Tab:**
    *   Name: `Bouncer Scheduled Scan`
    *   Select "Run whether user is logged on or not".
4.  **Triggers Tab:**
    *   Click **New**.
    *   Choose a schedule (e.g., **Daily**, **Weekly**).
    *   Set the desired time and recurrence.
    *   Click **OK**.
5.  **Actions Tab:**
    *   Click **New**.
    *   Action: **Start a program**.
    *   Program/script: `powershell.exe`
    *   Add arguments: `-ExecutionPolicy Bypass -File "C:\Users\YourUser\bouncer\deployment\bouncer-scheduled.ps1"` (use the correct path).
    *   Start in: `C:\Users\YourUser\bouncer`
    *   Click **OK**.
6.  **Conditions Tab:**
    *   Adjust power settings as needed (e.g., uncheck "Start the task only if the computer is on AC power").
7.  **Settings Tab:**
    *   Configure failure behavior (e.g., "If the task fails, restart every: 10 minutes").
8.  Click **OK** to save the task. You will be prompted for your user password.

#### 3. Logging

Logs for each scheduled run are saved to the `logs` directory within your Bouncer project (e.g., `C:\Users\YourUser\bouncer\logs\bouncer_scheduled_20251205_103000.log`).

---

### 🐳 Docker (cron)

For containerized environments, you can use the provided Docker setup to run Bouncer on a schedule.

This setup uses a dedicated `Dockerfile.cron` to build an image with `cron` installed and configured to run Bouncer.

#### 1. Configure Docker Compose

Edit `deployment/docker-compose.cron.yml` to set up your environment.

*   **Volumes:** Mount the directory you want to scan into the container (e.g., `- ./my-project:/watch:ro`).
*   **Environment:** Set your notification webhooks and other Bouncer settings.

```yaml
# In deployment/docker-compose.cron.yml
services:
  bouncer-cron:
    build:
      context: ..
      dockerfile: deployment/Dockerfile.cron
    volumes:
      # Mount the directory to watch (read-only is safer)
      - /path/to/your/codebase:/watch:ro
      # Persist logs
      - ./logs:/app/logs
    environment:
      # Set your notification webhook
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      # Customize the cron schedule (optional, defaults to hourly)
      # This example runs at 4:05 AM every day
      - CRON_SCHEDULE="5 4 * * *"
```

#### 2. Build and Run

Use `docker-compose` to manage the cron container.

```bash
# Build and start the container in the background
docker-compose -f deployment/docker-compose.cron.yml up --build -d

# View logs
docker-compose -f deployment/docker-compose.cron.yml logs -f

# Stop the container
docker-compose -f deployment/docker-compose.cron.yml down
```

By default, the cron job runs every hour. You can customize this by setting the `CRON_SCHEDULE` environment variable in the `docker-compose.cron.yml` file.
