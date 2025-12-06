# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .  # Editable install

# Run bouncer (continuous file watching)
python main.py start
python main.py start --verbose  # Debug logging
python main.py start --report-only  # No auto-fix

# Batch scan a directory
python main.py scan /path/to/project
python main.py scan /path/to/project --git-diff  # Only changed files
python main.py scan /path/to/project --git-diff --since "1 hour ago"

# Other commands
python main.py init  # Create default bouncer.yaml
python main.py wizard  # Interactive TUI setup
python main.py validate-config  # Validate bouncer.yaml
python main.py auth-status  # Check authentication

# Run tests
pytest
pytest -v  # Verbose
pytest tests/test_specific.py::test_function  # Single test
```

## Architecture

Bouncer is an AI-powered file monitoring agent built on the Claude Agent SDK. It watches directories for file changes and routes them through specialized "bouncer" agents for quality checks.

### Core Flow

1. **FileWatcher** (`bouncer/watcher.py`) monitors directories using `watchdog` and creates `FileChangeEvent` objects
2. **BouncerOrchestrator** (`bouncer/core.py`) receives events, routes to applicable bouncers, aggregates results, sends notifications
3. **Specialized Bouncers** (`bouncers/*.py`) each inherit from `BaseBouncer` and implement `check()` for their domain
4. **Notifiers** (`notifications/*.py`) send results to Slack, Discord, email, Teams, webhooks, or file logs

### Key Classes

- `BouncerOrchestrator` - Central coordinator managing bouncers, notifiers, event queue, and MCP integrations
- `BaseBouncer` - Abstract base class all bouncers extend; defines `should_check()` and `check()` interface
- `FileChangeEvent` - Dataclass representing a file change (path, event_type, timestamp)
- `BouncerResult` - Dataclass with check results (status: approved/denied/fixed/warning, issues_found, fixes_applied)
- `ConfigLoader` - Loads bouncer.yaml with environment variable expansion and overrides

### Adding a New Bouncer

1. Create `bouncers/your_bouncer.py` inheriting from `BaseBouncer`
2. Implement `async def check(self, event) -> BouncerResult`
3. Register in `main.py` `create_orchestrator()` function
4. Add config section in `bouncer.yaml`

### Adding Custom Tools

Tools use the Claude Agent SDK `@tool` decorator in `checks/tools.py`. Create an MCP server with `create_sdk_mcp_server()`.

### Configuration

All config lives in `bouncer.yaml`. Environment variables can override settings:
- `BOUNCER_WATCH_DIR` - Directory to monitor
- `BOUNCER_REPORT_ONLY` - Disable auto-fix
- `BOUNCER_ENABLED_BOUNCERS` - Comma-separated list of enabled bouncers

### Authentication

Bouncer uses the Claude Agent SDK which supports:
1. **Claude Code OAuth** (recommended) - Uses credentials from Claude Code `/login`
2. **API Key** - Set `ANTHROPIC_API_KEY` environment variable
