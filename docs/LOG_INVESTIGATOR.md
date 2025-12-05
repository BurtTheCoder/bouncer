# 🔍 Log Investigator Bouncer

The **Log Investigator** is a specialized bouncer that monitors application logs for errors, automatically investigates the codebase to find root causes, and suggests fixes.

This is particularly useful for:
- **Production monitoring** - Automatically investigate errors as they occur
- **Post-deployment checks** - Scan logs after releases to catch new issues
- **Historical analysis** - Investigate accumulated errors in log files
- **Development debugging** - Auto-investigate errors during testing

---

## 🎯 How It Works

The Log Investigator follows a systematic approach:

### 1. **Log Parsing**
Scans log files and extracts error entries with:
- Error level (ERROR, CRITICAL, EXCEPTION, FATAL)
- Error message
- Timestamp
- Stack traces
- File paths and line numbers

### 2. **Error Deduplication**
Tracks previously investigated errors to avoid duplicate work. Uses a hash based on:
- Error message
- File location
- Line number

### 3. **Codebase Investigation**
For each new error, the bouncer:
- Locates the relevant source code
- Reads the context around the error
- Analyzes the root cause
- Identifies patterns (null checks, error handling, race conditions)

### 4. **Fix Suggestions**
Generates structured output with:
- **Issues found** - Description, severity, location
- **Suggested fixes** - Code changes with explanations
- **Investigation summary** - What was checked and why

---

## ⚙️ Configuration

Add the Log Investigator to your `bouncer.yaml`:

```yaml
bouncers:
  log_investigator:
    enabled: true
    auto_fix: false  # Recommend manual review
    
    # Log configuration
    log_dir: "/var/log/myapp"
    log_patterns:
      - "*.log"
      - "error*.log"
    
    # Codebase configuration
    codebase_dir: "/path/to/codebase"
    
    # Error detection
    error_levels:
      - "ERROR"
      - "CRITICAL"
      - "EXCEPTION"
      - "FATAL"
    
    # Performance tuning
    max_errors_per_scan: 10
    lookback_hours: 24
    track_fixed_errors: true
```

### Configuration Options

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `log_dir` | string | `/var/log` | Directory containing log files |
| `codebase_dir` | string | `.` | Root directory of codebase to investigate |
| `log_patterns` | array | `["*.log"]` | Glob patterns for log files to monitor |
| `error_levels` | array | `["ERROR", "CRITICAL", ...]` | Log levels to investigate |
| `max_errors_per_scan` | int | `10` | Maximum errors to investigate per scan |
| `lookback_hours` | int | `24` | Only check errors from last N hours |
| `track_fixed_errors` | bool | `true` | Remember investigated errors |

---

## 🚀 Usage Examples

### Example 1: Continuous Monitoring

Monitor logs in real-time and investigate new errors as they appear.

```bash
# Start Bouncer in monitor mode
bouncer start --config log_investigator_config.yaml
```

**Use case:** Production monitoring - get instant notifications when errors occur with investigation results.

---

### Example 2: Scheduled Scans

Run periodic scans of log files (e.g., hourly or daily).

```bash
# Scan logs once
bouncer scan /var/log/myapp --config log_investigator_config.yaml

# Or use cron for hourly scans
0 * * * * bouncer scan /var/log/myapp --config log_investigator_config.yaml
```

**Use case:** Regular health checks - catch errors that accumulated over time.

---

### Example 3: Post-Deployment Investigation

Scan logs after a deployment to catch new issues.

```bash
# Scan logs from last 2 hours (since deployment)
bouncer scan /var/log/myapp --git-diff --since="2 hours ago"
```

**Use case:** Deployment validation - ensure new code didn't introduce errors.

---

### Example 4: Historical Analysis

Investigate all errors in existing log files.

```yaml
# Temporarily disable tracking to re-investigate all errors
log_investigator:
  track_fixed_errors: false
  max_errors_per_scan: 100
```

```bash
bouncer scan /var/log/myapp
```

**Use case:** Onboarding a new codebase - understand existing error patterns.

---

## 📊 Supported Log Formats

The Log Investigator can parse various log formats:

### Python Logging
```
2024-12-05 10:30:45 ERROR Failed to process request
Traceback (most recent call last):
  File "/app/main.py", line 123, in process_request
    result = process_data(data)
ValueError: Invalid data format
```

### JavaScript/Node.js
```
[2024-12-05 10:30:45] ERROR: Unhandled promise rejection
    at /app/server.js:45:12
    at processTicksAndRejections (internal/process/task_queues.js:93:5)
Error: Database connection failed
```

### Java
```
2024-12-05 10:30:45 FATAL [main] com.example.App - Application startup failed
java.lang.NullPointerException: Cannot invoke method on null object
    at com.example.Service.initialize(Service.java:67)
    at com.example.App.main(App.java:23)
```

### Generic Format
```
ERROR: User authentication failed for user@example.com
  at auth.js:89
  Cause: Invalid password
```

---

## 🎯 Best Practices

### 1. **Start Conservative**

Begin with a low `max_errors_per_scan` to avoid overwhelming the system:

```yaml
max_errors_per_scan: 5  # Start small
lookback_hours: 1       # Recent errors only
```

### 2. **Use Report-Only Mode**

Always review fixes before applying them:

```yaml
auto_fix: false  # Manual review required
```

### 3. **Configure Notifications**

Get notified when errors are investigated:

```yaml
notifications:
  slack:
    enabled: true
    detail_level: "detailed"  # Include investigation details
```

### 4. **Combine with Scheduled Scans**

Use a hybrid approach:
- **Real-time monitoring** during business hours
- **Scheduled scans** overnight to catch accumulated errors

```crontab
# Scan logs every 6 hours
0 */6 * * * bouncer scan /var/log/myapp
```

### 5. **Separate Log and Codebase Directories**

Keep logs and code in different locations for better organization:

```yaml
log_dir: "/var/log/myapp"      # Production logs
codebase_dir: "/app/src"       # Application code
```

---

## 🔧 Advanced Features

### Error Tracking

The bouncer maintains a tracking file (`.bouncer/fixed_errors.json`) to remember investigated errors:

```json
{
  "ValueError|/app/main.py|123": {
    "timestamp": "2024-12-05T10:30:45",
    "message": "Invalid data format"
  }
}
```

To re-investigate all errors, delete this file or set `track_fixed_errors: false`.

### Custom Error Patterns

Add custom error levels for your logging framework:

```yaml
error_levels:
  - "ERROR"
  - "CRITICAL"
  - "SEVERE"      # Java
  - "PANIC"       # Go
  - "ALERT"       # Custom
```

### Integration with CI/CD

Use the exit code to fail builds if errors are found:

```bash
# In your CI/CD pipeline
bouncer scan /var/log/app
if [ $? -ne 0 ]; then
  echo "Errors found in logs!"
  exit 1
fi
```

---

## 🐛 Troubleshooting

### No Errors Detected

**Problem:** Bouncer doesn't find errors in logs.

**Solutions:**
- Check `error_levels` matches your log format
- Verify `log_patterns` matches your log file names
- Check `lookback_hours` - you might be filtering out old errors
- Examine log file encoding (use UTF-8)

### Too Many Errors

**Problem:** Bouncer finds hundreds of errors.

**Solutions:**
- Reduce `max_errors_per_scan` to process fewer errors per run
- Enable `track_fixed_errors` to avoid re-investigating
- Increase `lookback_hours` to focus on recent errors
- Use scheduled scans instead of continuous monitoring

### Investigation Fails

**Problem:** Bouncer can't find the code causing the error.

**Solutions:**
- Verify `codebase_dir` points to the correct location
- Check that file paths in stack traces are relative to `codebase_dir`
- Ensure the bouncer has read access to the codebase
- Review the investigation prompt in the logs

---

## 📈 Performance Considerations

### Resource Usage

The Log Investigator can be resource-intensive because it:
- Reads entire log files
- Calls Claude AI for each error
- Reads source code files

**Recommendations:**
- Use `max_errors_per_scan` to limit investigations per run
- Use `lookback_hours` to avoid processing old errors
- Run scheduled scans during off-peak hours
- Consider log rotation to keep files manageable

### Cost Optimization

Each error investigation uses Claude AI tokens:

**Estimated costs per error:**
- Simple error (no stack trace): ~500 tokens (~$0.004)
- Complex error (with stack trace): ~2000 tokens (~$0.015)

**Cost reduction strategies:**
- Enable `track_fixed_errors` to avoid duplicate investigations
- Use `max_errors_per_scan` to control batch size
- Filter out known/expected errors at the logging level
- Focus on CRITICAL/FATAL errors only

---

## 🎓 Example Workflow

Here's a complete workflow for using the Log Investigator:

### 1. **Initial Setup**

```bash
# Create config
cp examples/log_investigator_config.yaml bouncer.yaml

# Edit config
nano bouncer.yaml  # Set log_dir and codebase_dir

# Test with a small scan
bouncer scan /var/log/myapp --config bouncer.yaml
```

### 2. **Review Results**

Check the investigation results:
- Slack notifications (if enabled)
- `.bouncer/investigations.json` file
- Console output

### 3. **Apply Fixes**

Review suggested fixes and apply them manually:
```bash
# Review the suggested changes
cat .bouncer/investigations.json | jq '.fixes'

# Apply fixes to your codebase
# (Manual review recommended)
```

### 4. **Deploy and Monitor**

After applying fixes:
```bash
# Deploy updated code
git commit -am "Fix: Address errors found in logs"
git push

# Monitor for new errors
bouncer start --config bouncer.yaml
```

### 5. **Continuous Improvement**

Set up scheduled scans:
```crontab
# Scan logs every 6 hours
0 */6 * * * cd /app && bouncer scan /var/log/myapp
```

---

## 🔮 Future Enhancements

Planned features for the Log Investigator:

- **MCP Integration** - Automatically create GitHub issues or PRs for fixes
- **Pattern Detection** - Identify recurring error patterns across logs
- **Regression Detection** - Compare current errors to historical baselines
- **Multi-language Support** - Better parsing for Go, Rust, Ruby, etc.
- **Log Streaming** - Real-time monitoring with tail -f
- **Custom Parsers** - Plugin system for custom log formats

---

## 📚 See Also

- [Creating Custom Bouncers](CREATING_BOUNCERS.md)
- [Notification Configuration](NOTIFICATIONS.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Scheduled Execution](DEPLOYMENT.md#scheduled-execution-cron--task-scheduler)
