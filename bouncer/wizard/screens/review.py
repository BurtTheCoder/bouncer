"""
Review Configuration Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, TextArea
from textual.containers import Container, Vertical, Horizontal
import yaml


class ReviewScreen(Screen):
    """Screen for reviewing configuration before saving"""
    
    def compose(self) -> ComposeResult:
        """Create review widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 7 of 8:[/bold cyan] Review Configuration",
                classes="section-title"
            )
            yield Static(
                "Review your configuration. You can edit it directly or go back.",
                classes="help-text"
            )

            yield TextArea(
                "",
                language="yaml",
                theme="monokai",
                id="config-preview",
                classes="config-preview"
            )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Save & Continue →", variant="primary", id="save")
    
    def on_mount(self) -> None:
        """Display current configuration"""
        # Generate YAML preview
        config_yaml = yaml.dump(
            self.app.config_data,
            default_flow_style=False,
            sort_keys=False
        )
        
        # Update text area
        text_area = self.query_one("#config-preview", TextArea)
        text_area.text = config_yaml
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        
        elif event.button.id == "save":
            # Get edited config from text area
            text_area = self.query_one("#config-preview", TextArea)
            config_yaml = text_area.text
            
            # Try to parse YAML
            try:
                self.app.config_data = yaml.safe_load(config_yaml) or {}
            except yaml.YAMLError as e:
                self.app.notify(
                    f"Invalid YAML: {e}",
                    severity="error",
                    timeout=10
                )
                return
            
            # Save configuration
            if self.app.save_config():
                # Move to success screen
                from .success import SuccessScreen
                self.app.push_screen(SuccessScreen())
            else:
                self.app.notify(
                    "Failed to save configuration. Please check the file path and permissions.",
                    severity="error",
                    timeout=10
                )
