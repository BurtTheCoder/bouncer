# Notification Channels

Bouncer supports multiple notification channels to keep you informed about file quality checks. You can enable as many channels as you need.

## How It Works

1. **Enable Channels**: In `bouncer.yaml`, enable the notification channels you want to use.
2. **Configure Settings**: Provide the necessary credentials and settings for each channel (e.g., webhook URLs, API keys).
3. **Set Severity Threshold**: Each channel can have a `min_severity` to filter which notifications it receives.

---

## Supported Channels

### 1. Slack

**Best for:** Real-time team collaboration

**Features:**
- Rich, formatted messages
- Color-coded by severity
- Deep linking to files

#### Configuration

**bouncer.yaml:**
```yaml
notifications:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#bouncer-alerts"
    min_severity: warning  # info, warning, denied, error
```

**.env:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Setup

1. Go to **Slack App Directory** > **Build** > **Create New App**.
2. Select **From scratch**.
3. Name your app (e.g., "Bouncer") and choose your workspace.
4. Go to **Incoming Webhooks** and activate it.
5. Click **Add New Webhook to Workspace**.
6. Choose a channel and click **Allow**.
7. Copy the **Webhook URL** and add it to your `.env` file.

#### Example Notification

```
🚪 Bouncer Report

✅ 12 checks passed
⚠️ 3 issues found

• Performance: large_image.png is 1.2MB (limit: 500KB)
• Accessibility: Missing alt text on user_avatar.jsx
• Security: Hardcoded API key found in config.py
```

---

### 2. Discord

**Best for:** Community projects, gaming-focused teams

**Features:**
- Rich embed messages
- Color-coded by severity
- Customizable username

#### Configuration

**bouncer.yaml:**
```yaml
notifications:
  discord:
    enabled: true
    webhook_url: ${DISCORD_WEBHOOK_URL}
    username: "Bouncer Bot"
    min_severity: warning
```

**.env:**
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

#### Setup

1. In Discord, go to **Server Settings** > **Integrations** > **Webhooks**.
2. Click **New Webhook**.
3. Name the webhook (e.g., "Bouncer") and choose a channel.
4. Copy the **Webhook URL** and add it to your `.env` file.

#### Example Notification

(Similar to Slack, but with Discord embed formatting)

---

### 3. Email (SMTP)

**Best for:** Formal reports, summaries, non-real-time notifications

**Features:**
- HTML and plain text emails
- Customizable subject lines
- Multiple recipients
- Secure SMTP with TLS

#### Configuration

**bouncer.yaml:**
```yaml
notifications:
  email:
    enabled: true
    smtp_host: ${SMTP_HOST}
    smtp_port: 587
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from_email: "bouncer@your-domain.com"
    to_emails:
      - "team@your-domain.com"
      - "manager@your-domain.com"
    use_tls: true
    min_severity: error
```

**.env:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Setup

- Use your email provider's SMTP settings.
- For Gmail, you may need to create an **App Password**.
- Ensure your firewall allows outbound connections on the SMTP port.

#### Example Notification

(HTML email with tables and formatting)

---

### 4. Microsoft Teams

**Best for:** Enterprise environments using Microsoft 365

**Features:**
- Adaptive Cards for rich, interactive messages
- Color-coded by severity

#### Configuration

**bouncer.yaml:**
```yaml
notifications:
  teams:
    enabled: true
    webhook_url: ${TEAMS_WEBHOOK_URL}
    min_severity: warning
```

**.env:**
```bash
TEAMS_WEBHOOK_URL=https://your-tenant.webhook.office.com/webhookb2/...
```

#### Setup

1. In your Teams channel, click **...** > **Connectors**.
2. Find **Incoming Webhook** and click **Add**.
3. Click **Configure**, provide a name, and click **Create**.
4. Copy the **Webhook URL** and add it to your `.env` file.

#### Example Notification

(Adaptive Card with facts and actions)

---

### 5. Generic Webhook

**Best for:** Integrating with custom systems, IFTTT, Zapier, etc.

**Features:**
- Send JSON payloads to any URL
- Customizable HTTP method (POST/PUT)
- Custom headers for authentication

#### Configuration

**bouncer.yaml:**
```yaml
notifications:
  webhook:
    enabled: true
    webhook_url: ${GENERIC_WEBHOOK_URL}
    method: POST
    headers:
      Authorization: "Bearer ${WEBHOOK_SECRET}"
      X-Custom-Header: "Bouncer"
    min_severity: info
```

**.env:**
```bash
GENERIC_WEBHOOK_URL=https://your-service.com/api/bouncer
WEBHOOK_SECRET=your-secret-token
```

#### Setup

- Point to any endpoint that accepts JSON.
- Use headers for authentication.

#### Example Payload

```json
{
  "bouncer": "code_quality",
  "file_path": "src/main.py",
  "severity": "warning",
  "action": "checked",
  "issues": [
    "Unused import: os",
    "Line too long (121/100)"
  ],
  "fixes": [],
  "message": "Found 2 issues",
  "timestamp": "2024-12-05T04:20:00.123Z"
}
```

---

### 6. File Logger (JSON)

**Best for:** Auditing, local debugging, feeding into other systems (ELK, Splunk)

**Features:**
- Detailed JSON logs
- Log rotation (daily, weekly, monthly)
- Structured data for easy parsing

#### Configuration

**bouncer.yaml:**
```yaml
notifications:
  file_log:
    enabled: true
    log_dir: ".bouncer/logs"
    rotation: daily
```

#### Setup

- No external setup needed.
- Just ensure the directory is writable.

#### Example Log Entry

```json
{
  "timestamp": "2024-12-05T04:20:00.123Z",
  "bouncer": "code_quality",
  "file_path": "src/main.py",
  "severity": "warning",
  "action": "checked",
  "issues": [
    "Unused import: os",
    "Line too long (121/100)"
  ],
  "fixes": []
}
```

---

## Configuration Priority

1. **Environment Variables**: Override all other settings.
2. **bouncer.yaml**: Your main configuration file.
3. **Default values**: Hardcoded fallbacks.

### Example

**bouncer.yaml:**
```yaml
notifications:
  slack:
    enabled: true
    min_severity: warning
```

**.env:**
```bash
BOUNCER_SLACK_ENABLED=false
BOUNCER_SLACK_MIN_SEVERITY=error
```

**Result:** Slack notifications are **disabled** and would only trigger on `error` if they were enabled.

---

## Adding New Notifiers

Bouncer is designed to be easily extensible:

1. **Create a new notifier class** in `bouncer/notifications/`.
2. **Inherit from a base class** (or implement `__init__` and `send` methods).
3. **Add it to `notifications/__init__.py`**.
4. **Update the orchestrator** in `bouncer/core.py` to load and call your new notifier.

---

## See Also

- [Environment Variables](ENVIRONMENT_VARIABLES.md) - Configuration overrides
- [Authentication](AUTHENTICATION.md) - API keys and cloud provider setup
- [Deployment](DEPLOYMENT.md) - Running Bouncer as a service
