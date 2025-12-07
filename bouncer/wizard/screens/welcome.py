"""
Welcome Screen - Introduction to Bouncer Wizard
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Container, Vertical, Horizontal


BOUNCER_LOGO = """
  ██████╗  ██████╗ ██╗   ██╗███╗   ██╗ ██████╗███████╗██████╗
  ██╔══██╗██╔═══██╗██║   ██║████╗  ██║██╔════╝██╔════╝██╔══██╗
  ██████╔╝██║   ██║██║   ██║██╔██╗ ██║██║     █████╗  ██████╔╝
  ██╔══██╗██║   ██║██║   ██║██║╚██╗██║██║     ██╔══╝  ██╔══██╗
  ██████╔╝╚██████╔╝╚██████╔╝██║ ╚████║╚██████╗███████╗██║  ██║
  ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═╝  ╚═╝

              Quality Control at the Door
"""


class WelcomeScreen(Screen):
    """Welcome screen with Bouncer logo and introduction"""
    
    def compose(self) -> ComposeResult:
        """Create welcome screen widgets"""
        with Container(id="welcome-container"):
            with Vertical():
                yield Static(BOUNCER_LOGO, id="logo")
                yield Static(
                    "\n[bold]Welcome to the Bouncer Setup Wizard![/bold]\n\n"
                    "This wizard will help you configure Bouncer, your AI-powered\n"
                    "quality control system for code and content.\n\n"
                    "[dim]Features:[/dim]\n"
                    "• 12 specialized bouncers for different file types\n"
                    "• Real-time monitoring and batch scanning\n"
                    "• Automatic fixes with AI reasoning\n"
                    "• Integrations with GitHub, GitLab, Linear, Jira\n"
                    "• Notifications via Slack, Discord, Email, and more\n\n"
                    "[bold cyan]Let's get started![/bold cyan]",
                    id="welcome-text"
                )
            with Horizontal(classes="nav-buttons"):
                yield Button("Continue", variant="primary", id="continue")
                yield Button("Quit", variant="default", id="quit")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "continue":
            from .directory import DirectoryScreen
            self.app.push_screen(DirectoryScreen())
        elif event.button.id == "quit":
            self.app.exit()
