"""
Ignore Patterns Screen - Configure files/directories to skip
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, TextArea, Label
from textual.containers import Container, Vertical, Horizontal


DEFAULT_IGNORE_PATTERNS = """# Directories
.git
.github
node_modules
__pycache__
venv
.venv
env
.bouncer

# Files
*.pyc
*.pyo
*.pyd
.pytest_cache
.mypy_cache
*.egg-info
dist
build
.DS_Store
*.tmp
*.bak
*.swp
*.swo

# Environment files
.env
.env.local
.env.*.local"""


class IgnorePatternsScreen(Screen):
    """Screen for configuring ignore patterns"""

    def compose(self) -> ComposeResult:
        """Create ignore patterns widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 11 of 12:[/bold cyan] Ignore Patterns",
                classes="section-title"
            )
            yield Static(
                "Specify files and directories to skip during monitoring.\n"
                "[dim]One pattern per line. Lines starting with # are comments.[/dim]",
                classes="help-text"
            )

            yield Label("Patterns to ignore:")
            yield TextArea(
                DEFAULT_IGNORE_PATTERNS,
                id="ignore-patterns",
                language="text"
            )

            yield Static(
                "\n[bold]Pattern Syntax:[/bold]\n"
                "• [cyan].git[/cyan] - Exact directory/file name\n"
                "• [cyan]*.pyc[/cyan] - Wildcard patterns\n"
                "• [cyan]node_modules[/cyan] - Any occurrence in path\n"
                "• [cyan]# comment[/cyan] - Ignored lines",
                classes="help-text"
            )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Finish Setup →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        patterns = self.app.config_data.get('ignore_patterns', [])
        if patterns:
            # Convert list to text
            text = "\n".join(patterns)
            self.query_one("#ignore-patterns", TextArea).text = text

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "continue":
            self._save_and_continue()

    def _save_and_continue(self) -> None:
        """Save ignore patterns and continue to review"""
        text = self.query_one("#ignore-patterns", TextArea).text

        # Parse patterns, skip comments and empty lines
        patterns = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)

        self.app.config_data['ignore_patterns'] = patterns

        from .review import ReviewScreen
        self.app.push_screen(ReviewScreen())
