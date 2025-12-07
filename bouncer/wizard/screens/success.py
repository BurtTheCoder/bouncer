"""
Success Screen - Configuration Complete
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Container, Vertical, Horizontal


class SuccessScreen(Screen):
    """Success screen shown after configuration is saved"""
    
    def compose(self) -> ComposeResult:
        """Create success screen widgets"""
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
                
                yield Static(
                    "\n[dim]For more information, see the documentation:\n"
                    "• README.md - Getting started guide\n"
                    "• docs/DEPLOYMENT.md - Deployment options\n"
                    "• docs/MCP_INTEGRATIONS.md - Integration setup[/dim]\n",
                    classes="help-text"
                )
                
            with Horizontal(classes="nav-buttons"):
                yield Button("Finish", variant="primary", id="finish")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "finish":
            self.app.exit()
