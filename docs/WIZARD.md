# Bouncer Setup Wizard

The Bouncer Setup Wizard is a beautiful, interactive TUI (Terminal User Interface) that makes configuring Bouncer quick and easy.

---

## Features

✨ **Beautiful Interface** - Modern, colorful terminal UI powered by Textual  
🎯 **Step-by-Step** - Guided workflow through all configuration options  
✅ **Validation** - Real-time validation of inputs  
📝 **Live Preview** - See and edit your configuration before saving  
🔄 **Resume Support** - Load and modify existing configurations  
⌨️ **Keyboard Navigation** - Full keyboard support (no mouse required)  
🌐 **Web Mode** - Can also run in a web browser!

---

## Quick Start

### Launch the Wizard

```bash
# Create new configuration
bouncer wizard

# Edit existing configuration
bouncer wizard --config bouncer.yaml

# Create configuration in specific location
bouncer wizard --config /path/to/config.yaml
```

---

## Wizard Flow

The wizard guides you through **6 easy steps**:

### 1. Welcome Screen
- Introduction to Bouncer
- Overview of features
- Press Enter to continue

### 2. Directory Selection
- Choose the directory to watch
- Browse directories with arrow keys
- Or type the path directly
- Validates directory exists

### 3. Bouncer Selection
- Enable/disable each of the 12 bouncers
- See description and file types for each
- Use "Select All" or "Deselect All" buttons
- Each bouncer shows:
  - Name and description
  - File types it checks
  - Default settings

### 4. Notifications Setup
- Enable notification channels
- Options:
  - **Slack** - Webhook notifications
  - **Discord** - Webhook notifications
  - **Email** - SMTP notifications
  - **Microsoft Teams** - Webhook notifications
  - **Custom Webhook** - Any HTTP endpoint
  - **File Logger** - Local log file (enabled by default)
- Shows required environment variables

### 5. Integrations Setup
- Enable MCP integrations (optional)
- Options:
  - **GitHub** - Auto-create PRs and issues
  - **GitLab** - Auto-create MRs and issues
  - **Linear** - Create Linear issues
  - **Jira** - Create Jira tickets
- Shows required API tokens
- Can skip this step

### 6. Review & Save
- Preview complete configuration
- Edit YAML directly if needed
- Validates YAML syntax
- Saves to specified path

### 7. Success!
- Shows next steps
- Commands to run Bouncer
- Links to documentation

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Arrow Keys** | Navigate options |
| **Tab** | Move between fields |
| **Enter** | Select/Continue |
| **Space** | Toggle checkboxes |
| **Backspace** | Go back to previous screen |
| **F1** | Show help |
| **Ctrl+C** | Quit wizard |
| **Ctrl+Q** | Quit wizard |

---

## Advanced Usage

### Web Mode

Run the wizard in your web browser:

```bash
# Install textual-web (if not already installed)
pip install textual[web]

# Serve the wizard
textual serve "python main.py wizard"
```

Then open the URL shown in your browser!

### Edit Existing Config

Load an existing configuration and modify it:

```bash
bouncer wizard --config existing_config.yaml
```

The wizard will pre-populate all fields with current values.

### Quick Setup

For a minimal setup, you can:
1. Launch wizard
2. Select directory
3. Keep default bouncer selections
4. Skip notifications (File Logger is enough)
5. Skip integrations
6. Save and start using Bouncer!

---

## Configuration Output

The wizard creates a `bouncer.yaml` file with structure like:

```yaml
watch_dir: /path/to/your/project

bouncers:
  code_quality:
    enabled: true
    auto_fix: true
  security:
    enabled: true
    auto_fix: true
  # ... more bouncers

notifications:
  file_log:
    enabled: true
  slack:
    enabled: false
  # ... more notifiers

integrations:
  github:
    enabled: false
    auto_create_pr: false
    auto_create_issue: false
  # ... more integrations
```

---

## After the Wizard

Once configuration is saved, follow these steps:

### 1. Set API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 2. Set Integration Tokens (if enabled)

```bash
# GitHub
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."

# GitLab
export GITLAB_PERSONAL_ACCESS_TOKEN="glpat-..."

# Linear
export LINEAR_API_KEY="lin_api_..."

# Jira
export JIRA_API_TOKEN="..."
```

### 3. Set Notification Webhooks (if enabled)

```bash
# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Discord
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Teams
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."
```

### 4. Start Bouncer

```bash
# Monitor mode (watches for file changes)
bouncer start

# Batch scan mode
bouncer scan /path/to/project

# Incremental scan (only changed files)
bouncer scan /path/to/project --git-diff --since="1 hour ago"
```

---

## Troubleshooting

### Wizard Won't Launch

**Error:** `Textual library not installed`

**Solution:**
```bash
pip install textual
# Or reinstall requirements
pip install -r requirements.txt
```

### Display Issues

If the wizard looks broken in your terminal:

1. **Use a modern terminal:**
   - iTerm2 (macOS)
   - Windows Terminal (Windows)
   - GNOME Terminal (Linux)
   - Alacritty (cross-platform)

2. **Check terminal size:**
   - Minimum: 80x24 characters
   - Recommended: 120x40 or larger

3. **Enable true color support:**
   ```bash
   export TERM=xterm-256color
   ```

### Configuration Not Saving

**Error:** `Failed to save configuration`

**Possible causes:**
- No write permissions in directory
- Invalid file path
- Disk full

**Solution:**
```bash
# Check permissions
ls -la bouncer.yaml

# Try different location
bouncer wizard --config ~/bouncer.yaml
```

---

## Tips & Tricks

### 1. Start Simple
Don't enable everything at once. Start with:
- A few key bouncers
- File Logger only
- No integrations

Then add more as needed.

### 2. Use Integrations Wisely
Integrations are powerful but require setup:
- Start with GitHub if you use it
- Test with `auto_create_pr: false` first
- Enable auto-creation once confident

### 3. Customize Later
The wizard creates a starting point. You can:
- Edit `bouncer.yaml` directly
- Run wizard again to modify
- Add advanced settings manually

### 4. Test Configuration
After wizard completes:
```bash
# Validate configuration
bouncer validate-config

# Test with report-only mode
bouncer start --report-only
```

---

## See Also

- [README.md](../README.md) - Getting started guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment options
- [MCP_INTEGRATIONS.md](MCP_INTEGRATIONS.md) - Integration setup
- [BOUNCERS.md](BOUNCERS.md) - Bouncer documentation

---

## Feedback

Found a bug or have a suggestion for the wizard?

Open an issue: https://github.com/BurtTheCoder/bouncer/issues
