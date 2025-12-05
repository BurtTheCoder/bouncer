"""
Notifications Setup Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Input, Label
from textual.containers import Container, Vertical, ScrollableContainer


NOTIFIER_INFO = {
    'slack': {
        'name': 'Slack',
        'description': 'Send notifications to Slack channels',
        'env_var': 'SLACK_WEBHOOK_URL'
    },
    'discord': {
        'name': 'Discord',
        'description': 'Send notifications to Discord channels',
        'env_var': 'DISCORD_WEBHOOK_URL'
    },
    'email': {
        'name': 'Email',
        'description': 'Send email notifications',
        'env_var': 'SMTP_SERVER'
    },
    'teams': {
        'name': 'Microsoft Teams',
        'description': 'Send notifications to Teams channels',
        'env_var': 'TEAMS_WEBHOOK_URL'
    },
    'webhook': {
        'name': 'Custom Webhook',
        'description': 'Send notifications to custom webhook',
        'env_var': 'WEBHOOK_URL'
    },
    'file_log': {
        'name': 'File Logger',
        'description': 'Log notifications to .bouncer/notifications.log',
        'env_var': None
    }
}


class NotificationsScreen(Screen):
    """Screen for configuring notifications"""
    
    def compose(self) -> ComposeResult:
        """Create notification configuration widgets"""
        with Container(classes="content-container"):
            with Vertical():
                yield Static(
                    "[bold cyan]Step 3 of 6:[/bold cyan] Configure Notifications",
                    classes="section-title"
                )
                yield Static(
                    "Choose how you want to be notified about bouncer findings.\n"
                    "[dim]Tip: File Logger is enabled by default and requires no setup.[/dim]",
                    classes="help-text"
                )
                
                with ScrollableContainer(classes="bouncer-list"):
                    for notifier_id, info in NOTIFIER_INFO.items():
                        with Vertical():
                            env_var_text = f"Requires: {info['env_var']}" if info['env_var'] else 'No configuration needed'
                            yield Checkbox(
                                f"[bold]{info['name']}[/bold]\n"
                                f"  {info['description']}\n"
                                f"  [dim]{env_var_text}[/dim]",
                                value=(notifier_id == 'file_log'),  # File logger enabled by default
                                id=f"notifier-{notifier_id}"
                            )
                
                yield Static(
                    "\n[bold yellow]Note:[/bold yellow] Webhook URLs and credentials should be set as environment variables.\n"
                    "See the documentation for details on setting up each notifier.",
                    classes="help-text"
                )
                
                with Container(classes="nav-buttons"):
                    yield Button("← Back", variant="default", id="back")
                    yield Button("Continue →", variant="primary", id="continue")
    
    def on_mount(self) -> None:
        """Initialize with saved config"""
        app = self.app
        notifications_config = app.get_config_value('notifications', {})
        
        # Set checkbox states from config
        for notifier_id in NOTIFIER_INFO.keys():
            checkbox = self.query_one(f"#notifier-{notifier_id}", Checkbox)
            notifier_cfg = notifications_config.get(notifier_id, {})
            checkbox.value = notifier_cfg.get('enabled', notifier_id == 'file_log')
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        
        elif event.button.id == "continue":
            # Save notification selections to config
            if 'notifications' not in self.app.config_data:
                self.app.config_data['notifications'] = {}
            
            for notifier_id in NOTIFIER_INFO.keys():
                checkbox = self.query_one(f"#notifier-{notifier_id}", Checkbox)
                
                if notifier_id not in self.app.config_data['notifications']:
                    self.app.config_data['notifications'][notifier_id] = {}
                
                self.app.config_data['notifications'][notifier_id]['enabled'] = checkbox.value
            
            # Move to next screen
            from .integrations import IntegrationsScreen
            self.app.push_screen(IntegrationsScreen())
