"""
Scheduling Screen - Set up automated scans
"""

import platform
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Input, Label, Select
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


FREQUENCY_OPTIONS = [
    ("Every 6 hours", "6h"),
    ("Every 12 hours", "12h"),
    ("Daily (9am)", "daily"),
    ("Twice daily (9am, 6pm)", "twice"),
    ("Weekly (Sunday 9am)", "weekly"),
]


class SchedulingScreen(Screen):
    """Screen for setting up scheduled scans"""

    def compose(self) -> ComposeResult:
        """Create scheduling configuration widgets"""
        system = platform.system()
        scheduler_type = "launchd" if system == "Darwin" else "cron"

        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 10 of 12:[/bold cyan] Schedule Automated Scans",
                classes="section-title"
            )
            yield Static(
                "Set up automated scans to keep your vault/project healthy.\n"
                f"[dim]Detected system: {system} ({scheduler_type})[/dim]",
                classes="help-text"
            )

            yield Checkbox(
                "[bold]Enable scheduled scans[/bold]",
                value=False,
                id="enable-scheduling"
            )

            with ScrollableContainer(classes="notification-list", id="scheduling-options"):
                yield Label("\nScan Frequency:")
                yield Select(
                    [(label, value) for label, value in FREQUENCY_OPTIONS],
                    value="daily",
                    id="frequency",
                    allow_blank=False
                )

                yield Label("\nFiles per scan:")
                yield Input(
                    placeholder="10",
                    value="10",
                    id="max-files"
                )
                yield Static(
                    "[dim]Limit files per scan to avoid long-running jobs[/dim]",
                    classes="help-text"
                )

                yield Checkbox(
                    "[bold]Random sampling[/bold] - Scan random files each run",
                    value=True,
                    id="random-sample"
                )

                yield Checkbox(
                    "[bold]Report only[/bold] - Don't auto-fix, just report issues",
                    value=False,
                    id="report-only"
                )

                yield Static(
                    f"\n[bold yellow]What will be created:[/bold yellow]\n"
                    f"{'~/Library/LaunchAgents/com.bouncer.scan.plist' if system == 'Darwin' else 'Cron entry in your crontab'}\n",
                    classes="help-text"
                )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Skip", variant="default", id="skip")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        # Disable options by default until scheduling is enabled
        self._toggle_options(False)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes"""
        if event.checkbox.id == "enable-scheduling":
            self._toggle_options(event.value)

    def _toggle_options(self, enabled: bool) -> None:
        """Enable/disable scheduling options"""
        options_container = self.query_one("#scheduling-options", ScrollableContainer)
        options_container.disabled = not enabled

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "skip":
            self.app.scheduling_config = None
            from .ignore_patterns import IgnorePatternsScreen
            self.app.push_screen(IgnorePatternsScreen())
        elif event.button.id == "continue":
            self._save_and_continue()

    def _save_and_continue(self) -> None:
        """Save scheduling config and continue"""
        enable_scheduling = self.query_one("#enable-scheduling", Checkbox).value

        if not enable_scheduling:
            self.app.scheduling_config = None
        else:
            try:
                max_files = int(self.query_one("#max-files", Input).value or "10")
            except ValueError:
                max_files = 10

            self.app.scheduling_config = {
                'enabled': True,
                'frequency': self.query_one("#frequency", Select).value,
                'max_files': max_files,
                'random_sample': self.query_one("#random-sample", Checkbox).value,
                'report_only': self.query_one("#report-only", Checkbox).value,
            }

        from .ignore_patterns import IgnorePatternsScreen
        self.app.push_screen(IgnorePatternsScreen())


def generate_cron_entry(
    bouncer_path: Path,
    python_path: Path,
    target_dir: Path,
    frequency: str,
    max_files: int,
    random_sample: bool,
    report_only: bool
) -> str:
    """Generate a cron entry for scheduled scans"""
    # Build the command
    cmd_parts = [
        f"cd {bouncer_path}",
        "&&",
        str(python_path),
        "main.py",
        "scan",
        str(target_dir),
        f"--max-files {max_files}",
    ]

    if random_sample:
        cmd_parts.append("--random")
    if report_only:
        cmd_parts.append("--report-only")

    cmd = " ".join(cmd_parts)

    # Determine schedule
    schedules = {
        "6h": "0 */6 * * *",      # Every 6 hours
        "12h": "0 */12 * * *",    # Every 12 hours
        "daily": "0 9 * * *",     # Daily at 9am
        "twice": "0 9,18 * * *",  # 9am and 6pm
        "weekly": "0 9 * * 0",    # Sunday at 9am
    }
    schedule = schedules.get(frequency, "0 9 * * *")

    return f"{schedule} {cmd} >> ~/.bouncer/scan.log 2>&1"


def generate_launchd_plist(
    bouncer_path: Path,
    python_path: Path,
    target_dir: Path,
    frequency: str,
    max_files: int,
    random_sample: bool,
    report_only: bool
) -> str:
    """Generate a launchd plist for scheduled scans on macOS"""
    # Build program arguments
    args = [
        str(python_path),
        str(bouncer_path / "main.py"),
        "scan",
        str(target_dir),
        "--max-files",
        str(max_files),
    ]

    if random_sample:
        args.append("--random")
    if report_only:
        args.append("--report-only")

    args_xml = "\n        ".join(f"<string>{arg}</string>" for arg in args)

    # Determine interval in seconds
    intervals = {
        "6h": 21600,      # 6 hours
        "12h": 43200,     # 12 hours
        "daily": 86400,   # 24 hours
        "twice": 43200,   # 12 hours (approximation)
        "weekly": 604800, # 7 days
    }
    interval = intervals.get(frequency, 86400)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bouncer.scan</string>
    <key>ProgramArguments</key>
    <array>
        {args_xml}
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>StandardOutPath</key>
    <string>/tmp/bouncer-scan.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/bouncer-scan.err</string>
    <key>WorkingDirectory</key>
    <string>{bouncer_path}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
'''


def install_launchd_plist(plist_content: str) -> Path:
    """Install launchd plist and return the path"""
    plist_path = Path.home() / "Library/LaunchAgents/com.bouncer.scan.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)
    return plist_path
