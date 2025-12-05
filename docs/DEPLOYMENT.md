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
