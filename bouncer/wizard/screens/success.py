"""
Success Screen - Configuration Complete
"""

import platform
import subprocess
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Container, Vertical, Horizontal

from .scheduling import generate_launchd_plist, generate_cron_entry, install_launchd_plist


class SuccessScreen(Screen):
    """Success screen shown after configuration is saved"""

    def compose(self) -> ComposeResult:
        """Create success screen widgets"""
        scheduling_info = self._get_scheduling_info()

        with Container(id="welcome-container"):
            with Vertical():
                yield Static(
                    "\n\n"
                    "╔═══════════════════════════════════════════╗\n"
                    "║                                           ║\n"
                    "║   ✅  Configuration Saved Successfully!   ║\n"
                    "║                                           ║\n"
                    "╚═══════════════════════════════════════════╝\n",
                    classes="success-message"
                )

                yield Static(
                    f"\n[bold]Configuration saved to:[/bold] {self.app.config_path}\n\n"
                    "[bold cyan]Next Steps:[/bold cyan]\n\n"
                    "[bold]1. Set your Anthropic API key:[/bold]\n",
                    classes="command-box"
                )

                yield Static(
                    "   export ANTHROPIC_API_KEY=\"your-api-key-here\"\n",
                    classes="command-box"
                )

                yield Static(
                    "\n[bold]2. Start Bouncer in monitor mode:[/bold]\n",
                    classes="command-box"
                )

                yield Static(
                    "   bouncer start\n",
                    classes="command-box"
                )

                yield Static(
                    "\n[bold]3. Or run a batch scan:[/bold]\n",
                    classes="command-box"
                )

                yield Static(
                    "   bouncer scan /path/to/project\n",
                    classes="command-box"
                )

                if scheduling_info:
                    yield Static(
                        f"\n[bold green]4. Scheduled scans configured![/bold green]\n"
                        f"{scheduling_info}\n",
                        classes="command-box"
                    )

                yield Static(
                    "\n[dim]For more information, see the documentation:\n"
                    "• README.md - Getting started guide\n"
                    "• docs/DEPLOYMENT.md - Deployment options\n"
                    "• docs/MCP_INTEGRATIONS.md - Integration setup[/dim]\n",
                    classes="help-text"
                )

            with Horizontal(classes="nav-buttons"):
                yield Button("Finish", variant="primary", id="finish")

    def _get_scheduling_info(self) -> str:
        """Get scheduling status info"""
        scheduling = getattr(self.app, 'scheduling_config', None)
        if not scheduling or not scheduling.get('enabled'):
            return ""

        system = platform.system()

        # Get paths
        bouncer_path = Path.cwd()
        python_path = Path(subprocess.check_output(['which', 'python3']).decode().strip())
        target_dir = Path(self.app.config_data.get('watch_dir', '.'))

        freq = scheduling.get('frequency', 'daily')
        max_files = scheduling.get('max_files', 10)
        random_sample = scheduling.get('random_sample', True)
        report_only = scheduling.get('report_only', False)

        if system == "Darwin":
            # macOS - generate and install launchd plist
            plist_content = generate_launchd_plist(
                bouncer_path=bouncer_path,
                python_path=python_path,
                target_dir=target_dir,
                frequency=freq,
                max_files=max_files,
                random_sample=random_sample,
                report_only=report_only
            )
            plist_path = install_launchd_plist(plist_content)

            # Try to load the plist
            try:
                subprocess.run(['launchctl', 'unload', str(plist_path)], capture_output=True)
                subprocess.run(['launchctl', 'load', str(plist_path)], check=True, capture_output=True)
                return (
                    f"   [green]✓[/green] LaunchAgent installed: {plist_path}\n"
                    f"   [green]✓[/green] Service loaded and running\n"
                    f"   [dim]To stop: launchctl unload {plist_path}[/dim]"
                )
            except subprocess.CalledProcessError:
                return (
                    f"   [yellow]![/yellow] LaunchAgent created: {plist_path}\n"
                    f"   [dim]To start: launchctl load {plist_path}[/dim]"
                )
        else:
            # Linux/other - generate cron entry
            cron_entry = generate_cron_entry(
                bouncer_path=bouncer_path,
                python_path=python_path,
                target_dir=target_dir,
                frequency=freq,
                max_files=max_files,
                random_sample=random_sample,
                report_only=report_only
            )
            return (
                f"   Add this to your crontab (crontab -e):\n"
                f"   [cyan]{cron_entry}[/cyan]"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "finish":
            self.app.exit()
