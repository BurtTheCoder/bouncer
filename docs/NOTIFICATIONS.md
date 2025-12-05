# Notification Configuration

Bouncer supports a wide range of notification channels to keep you informed about file quality checks. This guide explains how to configure each channel and customize the level of detail in your notifications.

## Supported Channels

- **Slack**: Real-time team collaboration
- **Discord**: Community projects and gaming teams
- **Email (SMTP)**: Formal reports and summaries
- **Microsoft Teams**: Enterprise Microsoft 365 environments
- **Generic Webhook**: Custom integrations (IFTTT, Zapier, etc.)
- **File Logger (JSON)**: Auditing and log ingestion (ELK, Splunk)

## Notification Detail Levels

All notification channels support three detail levels, configurable in `bouncer.yaml` or via environment variables.

### 1. `summary` (Default)

Provides a concise overview of the check.

**Content:**
- File path and event type
- Overall status (approved, denied, fixed, warning)
- Total issue and fix counts
- Top 3 most severe issues
- Summary of each bouncer that ran

**Best for:**
- Real-time channels (Slack, Discord, Teams)
- Quick, scannable updates
- Getting a high-level overview

### 2. `detailed`

Includes all information from `summary` plus full details of all issues and fixes.

**Content:**
- Everything from `summary`
- **All issues** with full descriptions, severity, and suggestions
- **All fixes** with descriptions of what was changed
- **Smart suggestions** from each bouncer

**Best for:**
- Email reports
- Generic webhooks for custom dashboards
- When you need to see all the details without the full transcript

### 3. `full_transcript`

Provides the complete conversation transcript from the Claude agent, including its thought process.

**Content:**
- Everything from `detailed`
- **Full conversation transcript**
- Agent's thought process and reasoning
- Tool calls made and their results
- Intermediate steps and analysis

**Best for:**
- Debugging bouncer behavior
- Understanding why the agent made certain decisions
- Training and fine-tuning models
- Archival and compliance purposes

## Configuration

### `bouncer.yaml`

Configure each notification channel under the `notifications` section:

```yaml
notifications:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    min_severity: warning
    detail_level: summary  # summary, detailed, or full_transcript
  
  email:
    enabled: false
    smtp_host: ${SMTP_HOST}
    min_severity: error
    detail_level: detailed
  
  file_log:
    enabled: true
    log_dir: .bouncer/logs
    detail_level: full_transcript  # Log everything for auditing
```

### Environment Variables

You can override the detail level for each channel using environment variables:

```bash
# .env
BOUNCER_SLACK_DETAIL_LEVEL=detailed
BOUNCER_EMAIL_DETAIL_LEVEL=full_transcript
BOUNCER_FILE_LOG_DETAIL_LEVEL=summary
```

## Channel-Specific Setup

### Slack

1.  **Create a Slack App** in your workspace.
2.  Enable **Incoming Webhooks**.
3.  Create a new webhook for your desired channel.
4.  Set the `SLACK_WEBHOOK_URL` environment variable.

### Discord

1.  Go to **Server Settings > Integrations > Webhooks**.
2.  Create a new webhook.
3.  Copy the webhook URL.
4.  Set the `DISCORD_WEBHOOK_URL` environment variable.

### Email (SMTP)

Configure your SMTP server details in `bouncer.yaml` or via environment variables:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `FROM_EMAIL`
- `TO_EMAILS` (comma-separated)

**Note:** For Gmail, you may need to use an [App Password](https://support.google.com/accounts/answer/185833).

### Microsoft Teams

1.  In your Teams channel, click **... > Connectors**.
2.  Search for **Incoming Webhook** and configure it.
3.  Copy the webhook URL.
4.  Set the `TEAMS_WEBHOOK_URL` environment variable.

### Generic Webhook

- **`GENERIC_WEBHOOK_URL`**: The endpoint to send POST/PUT requests to.
- **`WEBHOOK_SECRET`**: A secret token sent in the `Authorization` header (`Bearer <token>`).

### File Logger

- **`log_dir`**: Directory to store JSON log files.
- **`rotation`**: How often to rotate log files (daily, weekly, monthly, or none).

## Example Notifications

### Summary (Slack)

> 🚪 **Bouncer Report: WARNING**
> **File:** `src/main.py`
> **Event:** modified
> 
> **Top Issues:**
> • 🔴 Hardcoded API key on line 42
> • ⚠️ Unused import on line 5
> • ⚠️ Function too complex on line 120
> 
> **Bouncers:**
> • ✅ Code Quality: fixed (1 issue, 1 fix)
> • ⚠️ Security: warning (2 issues, 0 fixes)
> • ✅ Documentation: approved

### Detailed (Email)

> **Subject: ⚠️ Bouncer Report: WARNING - src/main.py**
> 
> **File:** `src/main.py`
> **Status:** WARNING
> 
> **Security Bouncer**
> - **Issue:** Hardcoded API key on line 42
>   - **Severity:** critical
>   - **Suggestion:** Use environment variables or a secret manager.
> - **Issue:** Potential SQL injection on line 67
>   - **Severity:** high
>   - **Suggestion:** Use parameterized queries.
> 
> **Code Quality Bouncer**
> - **Fix:** Refactored complex loop on line 120 to use list comprehension.

### Full Transcript (File Log)

```json
{
  "format": "full_transcript",
  "file_path": "src/main.py",
  "overall_status": "warning",
  "results": [...], // Detailed results
  "transcript": {
    "conversation": [
      {
        "role": "user",
        "content": "Please review this file..."
      },
      {
        "role": "assistant",
        "content": "[thinking] I will check for security issues..."
      },
      {
        "role": "assistant",
        "content": "[tool_use] Reading file..."
      },
      {
        "role": "assistant",
        "content": "[tool_result] File content..."
      },
      {
        "role": "assistant",
        "content": "[thinking] I found a hardcoded API key..."
      },
      {
        "role": "assistant",
        "content": "[text] Final summary..."
      }
    ]
  }
}
```
