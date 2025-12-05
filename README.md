# 🚪 Bouncer

**Quality control at the door.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Bouncer is an AI-powered file monitoring agent that keeps your repository clean by checking every file change for quality issues before they get in.

Think of it as a bouncer at a club - only quality gets past the door.

---

## ✨ Features

- **🎯 10 Specialized Bouncers**: Expert agents for Code Quality, Security, Documentation, Data, Performance, Accessibility, License, Infrastructure, API Contracts, and Dependencies.
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

Create a `.env` file for your secrets:

```bash
cp .env.example .env
```

Edit `.env` and add your `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL`.

### 3. Run Bouncer

That's it! Your bouncer is now on duty.

```bash
bouncer start
```

Bouncer will now watch the specified directory for file changes and start checking them.

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
