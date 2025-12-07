"""
Bouncer Setup Wizard - Main Application
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from .screens.welcome import WelcomeScreen
from .screens.directory import DirectoryScreen
from .screens.bouncers import BouncersScreen
from .screens.notifications import NotificationsScreen
from .screens.integrations import IntegrationsScreen
from .screens.hooks import HooksScreen
from .screens.scheduling import SchedulingScreen
from .screens.review import ReviewScreen
from .screens.success import SuccessScreen


class BouncerWizard(App):
    """
    Beautiful TUI wizard for Bouncer configuration
    """
    
    CSS_PATH = "styles.tcss"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("f1", "help", "Help"),
    ]
    
    TITLE = "Bouncer Setup Wizard"
    SUB_TITLE = "Configure your quality control system"
    
    def __init__(self, config_path: Optional[Path] = None):
        super().__init__()
        self.config_path = config_path or Path("bouncer.yaml")
        self.config_data: Dict[str, Any] = {}
        self.scheduling_config: Optional[Dict[str, Any]] = None

        # Load existing config if present
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self.config_data = yaml.safe_load(f) or {}
            except Exception:
                self.config_data = {}
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield Footer()
    
    def on_mount(self) -> None:
        """Start the wizard"""
        self.push_screen(WelcomeScreen())
    
    def action_help(self) -> None:
        """Show help dialog"""
        self.notify(
            "Use arrow keys to navigate, Enter to select, "
            "Ctrl+C to quit, Backspace to go back",
            title="Help",
            timeout=5
        )
    
    def save_config(self) -> bool:
        """Save configuration to YAML file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(
                    self.config_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False
                )
            return True
        except Exception as e:
            self.notify(
                f"Failed to save config: {e}",
                title="Error",
                severity="error",
                timeout=10
            )
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
