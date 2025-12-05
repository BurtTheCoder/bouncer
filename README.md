# 🚪 Bouncer

**Quality control at the door.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Bouncer is an AI-powered file monitoring agent that keeps your repository clean by checking every file change for quality issues before they get in.

Think of it as a bouncer at a club - only quality gets past the door.

---

## ✨ Features

- **🎯 11 Specialized Bouncers**: Expert agents for Code Quality, Security, Documentation, Data, Performance, Accessibility, License, Infrastructure, API Contracts, Dependencies, and Obsidian knowledge management.
- **🔧 Auto-Fix**: Automatically fixes formatting, linting, and other safe-to-fix issues.
- **🚨 Real-time Alerts**: Instant notifications via Slack, with more options coming soon.
- **🎛️ Fully Configurable**: Fine-tune everything with a simple `bouncer.yaml` file.
- **🐳 Easy Deployment**: Run as a standalone script or as a Docker container.
- **🛡️ Security First**: Pre-write hooks prevent dangerous changes and hardcoded secrets.
- **🧩 Modular by Design**: Easily extend Bouncer with your own bouncers and checks.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- `pip` and `venv`
- An [Anthropic API key](https://console.anthropic.com/dashboard) for Claude

### 1. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/your-username/bouncer.git
cd bouncer

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Bouncer and its dependencies
pip install -e .
```

### 2. Configuration

Bouncer uses a `bouncer.yaml` file for configuration.

```bash
# Create a default configuration file
cp bouncer.yaml.example bouncer.yaml
```

Now, edit `bouncer.yaml`:

- Set `watch_dir` to the directory you want to monitor.
- Enable/disable bouncers and configure their behavior.
- Set up your Slack webhook URL for notifications.

#### Authentication Setup

Create a `.env` file for your secrets:

```bash
cp .env.example .env
```

Bouncer supports **multiple authentication methods**. Choose one:

**Option 1: Anthropic API Key** (Recommended)
```
ANTHROPIC_API_KEY=your_api_key_here
SLACK_WEBHOOK_URL=your_webhook_url
```

**Option 2: AWS Bedrock**
```
USE_BEDROCK=true
AWS_REGION=us-east-1
SLACK_WEBHOOK_URL=your_webhook_url
```

**Option 3: Google Vertex AI**
```
USE_VERTEX=true
GOOGLE_CLOUD_PROJECT=your-project
SLACK_WEBHOOK_URL=your_webhook_url
```

**Option 4: Microsoft Foundry**
```
USE_FOUNDRY=true
SLACK_WEBHOOK_URL=your_webhook_url
```

**📚 Full authentication guide:** [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)

### 3. Run Bouncer

That's it! Your bouncer is now on duty.

```bash
bouncer start
```

Bouncer will now watch the specified directory for file changes and start checking them.

---

## 🎯 Real-World Use Cases

Bouncer is a versatile quality control system that can be adapted to many different workflows. Here are some real-world examples:

### 1. **Solo Developer: The Personal Code Guardian** 👨‍💻

Maintain high code quality on your side projects without manual reviews.

**Setup:** Run Bouncer locally while you code. Enable Code, Security, Docs, and Dependency bouncers with `auto_fix: true`.

**Result:** Your codebase stays clean and secure automatically. Focus on building features while Bouncer handles quality control.

---

### 2. **Startup Team: The Automated PR Reviewer** 🚀

Automate tedious code review tasks so your team can focus on architecture and business logic.

**Setup:** Integrate Bouncer into your CI/CD pipeline (GitHub Actions, GitLab CI). Run on every pull request.

**Result:** Bouncer posts detailed PR comments with findings. Catches issues before human review, saving hours per PR. Enforces consistent standards across the team.

**Example PR Comment:**
```
🚪 Bouncer Report

✅ 12 checks passed
⚠️ 3 issues found

• Performance: large_image.png is 1.2MB (limit: 500KB)
• Accessibility: Missing alt text on user_avatar.jsx
• Security: Hardcoded API key found in config.py
```

---

### 3. **Knowledge Worker: The Obsidian Gardener** 🧠

Keep your Obsidian vault organized, connected, and valuable over time.

**Setup:** Point Bouncer at your Obsidian vault. Enable the Obsidian bouncer with frontmatter requirements and tag formatting.

**Result:** Automatically fixes broken wikilinks, standardizes tags, adds missing metadata, and suggests connections. Your knowledge base stays healthy without manual maintenance.

**Example Notification:**
```
🧠 Obsidian Bouncer Report

Note: New Machine Learning Idea.md

Fixes Applied:
• Added created: 2024-12-05
• Standardized tag #ML to #machine-learning

Suggestions:
• Link to [[Machine Learning MOC]]
• This note is a stub (35 words). Consider expanding.
```

---

### 4. **DevOps Team: The Infrastructure Guardian** 🏗️

Prevent misconfigurations and enforce security best practices in infrastructure-as-code.

**Setup:** Watch your IaC repository. Enable Infrastructure and Security bouncers with `auto_fix: false` (require human review).

**Result:** Catches dangerous configurations before they reach production. Creates tickets for issues. Your infrastructure is more secure and reliable.

**Example Alert:**
```
🚨 Critical Issue in production.tf

Type: Insecure Security Group
Severity: Critical

Details: aws_security_group_rule allows ingress from 
0.0.0.0/0 on port 22 (SSH).

Please review and remediate immediately.
```

---

### 5. **Open Source Project: The Community Maintainer** 🌍

Ensure contributions meet quality standards without spending all your time on nitpicks.

**Setup:** Run Bouncer on all PRs from external contributors.

**Result:** Contributors get fast, helpful feedback. You spend less time on tedious reviews and more time on meaningful contributions. Your project maintains high quality standards.

**Example PR Comment:**
```
👋 Hello! Thanks for your contribution!

I'm Bouncer, the automated quality assistant. I've found 
a few things that need attention:

• Code Style: Run `npm run format` to fix formatting
• Documentation: README.md needs updating
• License Header: new_feature.js is missing MIT header

Once these are addressed, the maintainers will review. 
Thanks again! 🚀
```

---

## 🎯 Operation Modes

Bouncer supports different operation modes to fit your workflow:

### 1. **Monitor Mode** (Default)
Continuously watches a directory for file changes in real-time.
```bash
bouncer start
```

### 2. **Report-Only Mode**
Checks files and reports issues **without making any changes**.

**Option A:** Set `auto_fix: false` for all bouncers in `bouncer.yaml`:
```yaml
bouncers:
  code_quality:
    auto_fix: false  # Report only, no fixes
  security:
    auto_fix: false
  # ... repeat for all bouncers
```

**Option B:** Use CLI flag:
```bash
bouncer start --report-only
```

**Use when:**
- You want to review all changes manually
- Testing Bouncer on a new project
- Strict change control requirements
- Using in CI/CD pipelines

### 3. **Batch Mode**
Scan an entire directory once and generate a report.
```bash
bouncer scan /path/to/project
```

### 4. **Diff Mode**
Only check files that have changed (git diff).
```bash
bouncer start --diff-only
```

---

## 🚪 Running as a Service

Run Bouncer as a background service that starts automatically.

### Linux (systemd)

1. Copy the service file:
   ```bash
   sudo cp deployment/bouncer.service /etc/systemd/system/
   sudo nano /etc/systemd/system/bouncer.service  # Edit paths
   ```

2. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bouncer
   sudo systemctl start bouncer
   sudo systemctl status bouncer
   ```

3. View logs:
   ```bash
   sudo journalctl -u bouncer -f
   ```

### macOS (launchd)

1. Copy the plist file:
   ```bash
   cp deployment/com.bouncer.agent.plist ~/Library/LaunchAgents/
   nano ~/Library/LaunchAgents/com.bouncer.agent.plist  # Edit paths
   ```

2. Load and start:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.bouncer.agent.plist
   launchctl start com.bouncer.agent
   ```

3. View logs:
   ```bash
   tail -f /tmp/bouncer.log
   ```

### Windows (Task Scheduler)

1. Create `start-bouncer.bat`:
   ```batch
   @echo off
   cd /d C:\path\to\bouncer
   call venv\Scripts\activate.bat
   python -m bouncer.main start
   ```

2. Open Task Scheduler and create a new task:
   - Trigger: At startup
   - Action: Run `start-bouncer.bat`
   - Settings: Restart on failure

**📚 Full deployment guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🐳 Docker Deployment

For a more isolated and production-ready setup, use Docker.

1.  **Configure `docker-compose.yml`**: Mount the directory you want to watch.

    ```yaml
    volumes:
      # Mount your project directory to watch (read-only is safer)
      - /path/to/your/project:/app/watch:ro
    ```

2.  **Build and Run**:

    ```bash
    docker-compose up --build -d
    ```

3.  **View Logs**:

    ```bash
    docker-compose logs -f
    ```

---

## 🎛️ Configuration

All configuration is done in `bouncer.yaml`.

- **`watch_dir`**: The directory Bouncer monitors.
- **`ignore_patterns`**: A list of file/directory patterns to ignore.
- **`bouncers`**: Enable, disable, and configure each specialized bouncer.
    - `enabled`: `true` or `false`.
    - `file_types`: Which file extensions this bouncer checks.
    - `auto_fix`: `true` to allow the bouncer to fix issues automatically.
- **`notifications`**: Configure where Bouncer sends reports.
    - `slack`: Send rich notifications to a Slack channel.
    - `file_log`: Keep a detailed JSON log of all activity.

---

## 🛡️ The Bouncers

Bouncer uses a team of specialized sub-agents to check different types of files.

### 👔 Code Bouncer

- **Checks**: Syntax, linting, formatting, best practices.
- **Fixes**: Automatically formats code and fixes simple linting issues.
- **Tools**: `pylint`, `eslint`, `black`, `prettier`.

### 🕵️ Security Bouncer

- **Checks**: Hardcoded secrets, SQL injection, XSS, insecure dependencies.
- **Fixes**: Never auto-fixes. Reports all findings for human review.
- **Tools**: `bandit`, `semgrep` (via custom tools), pattern matching.

### 📚 Docs Bouncer

- **Checks**: Broken links, spelling, grammar, formatting.
- **Fixes**: Automatically corrects spelling and formatting.

### 📊 Data Bouncer

- **Checks**: JSON/YAML/CSV schema and syntax validation.
- **Fixes**: Automatically formats JSON and YAML files.

### ⚡ Performance Bouncer

- **Checks**: Code complexity, large files, unoptimized images, memory leaks, N+1 queries.
- **Fixes**: Optimizes images and refactors inefficient code patterns.

### ♿ Accessibility Bouncer

- **Checks**: WCAG compliance, missing alt text, color contrast, ARIA labels.
- **Fixes**: Adds alt text, ARIA labels, and improves accessibility.

### ⚖️ License Bouncer

- **Checks**: Missing copyright headers, license compatibility, GDPR compliance.
- **Fixes**: Adds copyright headers and ensures license compliance.

### 🏗️ Infrastructure Bouncer

- **Checks**: Dockerfile best practices, Kubernetes manifests, Terraform/CloudFormation.
- **Fixes**: Improves infrastructure configuration and security.

### 🔌 API Contract Bouncer

- **Checks**: OpenAPI/Swagger validation, breaking API changes, GraphQL schemas.
- **Fixes**: Validates API contracts and prevents breaking changes.

### 📦 Dependency Bouncer

- **Checks**: Known CVEs, outdated dependencies, license conflicts.
- **Fixes**: Reports vulnerabilities (never auto-updates dependencies).

### 🧠 Obsidian Bouncer

- **Checks**: Broken wikilinks, frontmatter validation, tag management, orphaned notes, knowledge graph health.
- **Fixes**: Fixes broken links, adds missing frontmatter, standardizes tags, suggests connections.
- **[Full Documentation](docs/OBSIDIAN_BOUNCER.md)** - Complete guide to Obsidian Bouncer features

---

## 📖 Documentation

- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** - Configuration overrides via env vars
- **[Authentication](docs/AUTHENTICATION.md)** - API keys and cloud provider setup
- **[Deployment](docs/DEPLOYMENT.md)** - Running as a service
- **[Obsidian Bouncer Guide](docs/OBSIDIAN_BOUNCER.md)** - Specialized guide for Obsidian vaults

---

## 🧩 Extensibility

Bouncer is designed to be easily extended.

1.  **Create a new Bouncer**: Inherit from `BaseBouncer` in `bouncers/base.py`.
2.  **Add Custom Checks**: Add new functions to `checks/tools.py` using the `@tool` decorator.
3.  **Register your Bouncer**: Add it to the `main.py` factory function.

---

## 🤝 Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for details on how to get started.

## 📄 License

Bouncer is licensed under the [MIT License](LICENSE).
