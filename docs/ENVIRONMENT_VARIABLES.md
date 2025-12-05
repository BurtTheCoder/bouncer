# Environment Variables

Bouncer supports environment variable overrides for flexible deployment across different environments (development, staging, production).

## How It Works

1. **Base Configuration**: Define your default settings in `bouncer.yaml`
2. **Environment Overrides**: Use environment variables to override specific settings
3. **Priority**: Environment variables always take precedence over `bouncer.yaml` settings

This approach allows you to:
- Commit `bouncer.yaml` to version control with sensible defaults
- Use `.env` files for environment-specific overrides (not committed)
- Easily configure Bouncer in Docker, CI/CD, or cloud deployments

---

## Available Environment Variables

### Core Configuration

#### `BOUNCER_WATCH_DIR`
**Purpose:** Override the directory to monitor

**Format:** Absolute or relative path

**Example:**
```bash
BOUNCER_WATCH_DIR=/app/src
```

**Use case:** Different watch directories per environment
```bash
# Development
BOUNCER_WATCH_DIR=.

# Production
BOUNCER_WATCH_DIR=/app/src
```

---

#### `BOUNCER_RECURSIVE`
**Purpose:** Enable or disable recursive monitoring of subdirectories

**Format:** `true` or `false`

**Default:** `true`

**Example:**
```bash
BOUNCER_RECURSIVE=false  # Only monitor top-level directory
```

**Use case:** Shallow monitoring for performance

---

#### `BOUNCER_DEBOUNCE_DELAY`
**Purpose:** Override the debounce delay (seconds to wait before processing file changes)

**Format:** Number (float)

**Default:** `2`

**Example:**
```bash
BOUNCER_DEBOUNCE_DELAY=5  # Wait 5 seconds
```

**Use case:** Adjust for fast-changing files or slow systems

---

### Operation Modes

#### `BOUNCER_REPORT_ONLY`
**Purpose:** Enable report-only mode (no automatic changes)

**Format:** `true` or `false`

**Default:** `false`

**Example:**
```bash
BOUNCER_REPORT_ONLY=true
```

**Use case:** CI/CD pipelines, code review, testing
```bash
# CI environment
BOUNCER_REPORT_ONLY=true  # Never modify files in CI

# Development
BOUNCER_REPORT_ONLY=false  # Allow auto-fixes
```

---

#### `BOUNCER_AUTO_FIX`
**Purpose:** Global override for all bouncer `auto_fix` settings

**Format:** `true` or `false`

**Example:**
```bash
BOUNCER_AUTO_FIX=false  # Disable all auto-fixes
```

**Use case:** Temporarily disable all auto-fixes without editing YAML
```bash
# Production - be cautious
BOUNCER_AUTO_FIX=false

# Development - allow fixes
BOUNCER_AUTO_FIX=true
```

---

### Logging & Debugging

#### `BOUNCER_LOG_LEVEL`
**Purpose:** Set logging verbosity

**Format:** `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Default:** `INFO`

**Example:**
```bash
BOUNCER_LOG_LEVEL=DEBUG  # Verbose logging
```

**Use case:** Debugging issues
```bash
# Development
BOUNCER_LOG_LEVEL=DEBUG

# Production
BOUNCER_LOG_LEVEL=WARNING
```

---

### Performance

#### `BOUNCER_MAX_FILE_SIZE`
**Purpose:** Skip files larger than this size (in bytes)

**Format:** Integer (bytes)

**Default:** No limit

**Example:**
```bash
BOUNCER_MAX_FILE_SIZE=10485760  # 10MB
```

**Use case:** Avoid processing very large files
```bash
# Skip files > 5MB
BOUNCER_MAX_FILE_SIZE=5242880
```

---

### Bouncer Selection

#### `BOUNCER_ENABLED_BOUNCERS`
**Purpose:** Override which bouncers are enabled

**Format:** Comma-separated list of bouncer names

**Example:**
```bash
BOUNCER_ENABLED_BOUNCERS=code_quality,security,documentation
```

**Available bouncers:**
- `code_quality`
- `security`
- `documentation`
- `data_validation`
- `performance`
- `accessibility`
- `license`
- `infrastructure`
- `api_contract`
- `dependency`
- `obsidian`

**Use case:** Enable only specific bouncers per environment
```bash
# CI - only security and code quality
BOUNCER_ENABLED_BOUNCERS=code_quality,security

# Development - all bouncers
# (leave unset to use bouncer.yaml settings)

# Documentation project - only docs and obsidian
BOUNCER_ENABLED_BOUNCERS=documentation,obsidian
```

---

## Configuration Priority

Bouncer loads configuration in this order (later overrides earlier):

1. **Default values** (hardcoded in `config.py`)
2. **bouncer.yaml** (your configuration file)
3. **Environment variables** (highest priority)

### Example

**bouncer.yaml:**
```yaml
watch_dir: .
debounce_delay: 2
bouncers:
  code_quality:
    enabled: true
    auto_fix: true
```

**.env:**
```bash
BOUNCER_WATCH_DIR=/app/src
BOUNCER_AUTO_FIX=false
```

**Result:**
- `watch_dir` = `/app/src` (overridden by env var)
- `debounce_delay` = `2` (from YAML)
- `code_quality.enabled` = `true` (from YAML)
- `code_quality.auto_fix` = `false` (overridden by global env var)

---

## Common Use Cases

### 1. CI/CD Pipeline

```bash
# .env.ci
BOUNCER_WATCH_DIR=/github/workspace
BOUNCER_REPORT_ONLY=true
BOUNCER_AUTO_FIX=false
BOUNCER_LOG_LEVEL=WARNING
BOUNCER_ENABLED_BOUNCERS=code_quality,security
```

### 2. Docker Deployment

```dockerfile
# Dockerfile
ENV BOUNCER_WATCH_DIR=/app
ENV BOUNCER_RECURSIVE=true
ENV BOUNCER_LOG_LEVEL=INFO
```

### 3. Development Environment

```bash
# .env.development
BOUNCER_WATCH_DIR=.
BOUNCER_LOG_LEVEL=DEBUG
BOUNCER_AUTO_FIX=true
BOUNCER_DEBOUNCE_DELAY=1
```

### 4. Production Environment

```bash
# .env.production
BOUNCER_WATCH_DIR=/app/src
BOUNCER_REPORT_ONLY=false
BOUNCER_AUTO_FIX=false
BOUNCER_LOG_LEVEL=WARNING
BOUNCER_MAX_FILE_SIZE=10485760
```

### 5. Obsidian Vault

```bash
# .env.obsidian
BOUNCER_WATCH_DIR=/path/to/vault
BOUNCER_ENABLED_BOUNCERS=obsidian,documentation
BOUNCER_AUTO_FIX=true
BOUNCER_RECURSIVE=true
```

---

## Best Practices

### 1. Version Control
- ✅ Commit `bouncer.yaml` with sensible defaults
- ❌ Never commit `.env` (add to `.gitignore`)
- ✅ Commit `.env.example` as a template

### 2. Environment-Specific Files
```bash
.env.development
.env.staging
.env.production
```

Load the appropriate file:
```bash
cp .env.production .env
bouncer start
```

### 3. Docker Compose
```yaml
services:
  bouncer:
    environment:
      - BOUNCER_WATCH_DIR=/app
      - BOUNCER_REPORT_ONLY=false
      - BOUNCER_LOG_LEVEL=INFO
```

### 4. Kubernetes
```yaml
env:
  - name: BOUNCER_WATCH_DIR
    value: "/app/src"
  - name: BOUNCER_AUTO_FIX
    value: "false"
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: bouncer-secrets
        key: api-key
```

---

## Debugging

To see which overrides are active, check the logs when Bouncer starts:

```
📋 Configuration loaded from: bouncer.yaml
🔧 Override: watch_dir = /app/src
🔧 Override: report_only = true
🔧 Override: log_level = DEBUG
```

Each override is logged with a 🔧 emoji for easy identification.

---

## See Also

- [Authentication](AUTHENTICATION.md) - API keys and cloud provider setup
- [Deployment](DEPLOYMENT.md) - Running Bouncer as a service
- [bouncer.yaml](../bouncer.yaml) - Configuration file reference
