"""
Notifications Setup Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Label
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


NOTIFIER_INFO = {
    'slack': {
        'name': 'Slack',
        'description': 'Send notifications to Slack channels',
        'env_var': 'SLACK_WEBHOOK_URL',
    },
    'discord': {
        'name': 'Discord',
        'description': 'Send notifications to Discord channels',
        'env_var': 'DISCORD_WEBHOOK_URL',
    },
    'email': {
        'name': 'Email',
        'description': 'Send email notifications via SMTP',
        'env_var': 'SMTP_HOST, SMTP_USER, SMTP_PASSWORD',
    },
    'teams': {
        'name': 'Microsoft Teams',
        'description': 'Send notifications to Teams channels',
        'env_var': 'TEAMS_WEBHOOK_URL',
    },
    'webhook': {
        'name': 'Custom Webhook',
        'description': 'Send JSON to custom webhook endpoint',
        'env_var': 'GENERIC_WEBHOOK_URL',
    },
    'file_log': {
        'name': 'File Logger',
        'description': 'Log to .bouncer/logs (JSON format)',
        'env_var': None,
    }
}


class NotificationsScreen(Screen):
    """Screen for configuring notifications"""

    def compose(self) -> ComposeResult:
        """Create notification configuration widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 6 of 12:[/bold cyan] Configure Notifications",
                classes="section-title"
            )
            yield Static(
                "Choose which notification channels to enable.\n"
                "[dim]File Logger is enabled by default for local auditing.[/dim]",
                classes="help-text"
            )

            with ScrollableContainer(classes="notification-list"):
                for notifier_id, info in NOTIFIER_INFO.items():
                    env_var_text = f"Requires: {info['env_var']}" if info['env_var'] else 'No setup required'
                    yield Checkbox(
                        f"[bold]{info['name']}[/bold] - {info['description']}\n"
                        f"  [dim]{env_var_text}[/dim]",
                        value=(notifier_id == 'file_log'),
                        id=f"notifier-{notifier_id}"
                    )

            yield Static(
                "\n[bold yellow]Environment Variables:[/bold yellow]\n"
                "Set webhook URLs and credentials as environment variables.\n"
                "[dim]Example: export SLACK_WEBHOOK_URL=https://hooks.slack.com/...[/dim]",
                classes="help-text"
            )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        app = self.app
        notifications_config = app.get_config_value('notifications', {})

        # Set states from config
        for notifier_id in NOTIFIER_INFO:
            notifier_cfg = notifications_config.get(notifier_id, {})
            checkbox = self.query_one(f"#notifier-{notifier_id}", Checkbox)
            checkbox.value = notifier_cfg.get('enabled', notifier_id == 'file_log')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()

        elif event.button.id == "continue":
            # Save notification configurations
            if 'notifications' not in self.app.config_data:
                self.app.config_data['notifications'] = {}

            for notifier_id, info in NOTIFIER_INFO.items():
                if notifier_id not in self.app.config_data['notifications']:
                    self.app.config_data['notifications'][notifier_id] = {}

                notifier_cfg = self.app.config_data['notifications'][notifier_id]

                # Get checkbox value
                checkbox = self.query_one(f"#notifier-{notifier_id}", Checkbox)
                notifier_cfg['enabled'] = checkbox.value

                # Set sensible defaults
                notifier_cfg.setdefault('min_severity', 'warning')
                notifier_cfg.setdefault('detail_level', 'summary')

                # Set default values based on notifier type
                # Webhook URLs will be collected in the next screen
                if notifier_id == 'discord':
                    notifier_cfg.setdefault('username', 'Bouncer Bot')
                elif notifier_id == 'email':
                    notifier_cfg.setdefault('smtp_port', 587)
                    notifier_cfg.setdefault('use_tls', True)
                    notifier_cfg.setdefault('min_severity', 'error')
                    notifier_cfg.setdefault('detail_level', 'detailed')
                elif notifier_id == 'webhook':
                    notifier_cfg.setdefault('method', 'POST')
                    notifier_cfg.setdefault('include_timestamp', True)
                    notifier_cfg.setdefault('min_severity', 'info')
                    notifier_cfg.setdefault('detail_level', 'detailed')
                elif notifier_id == 'file_log':
                    notifier_cfg.setdefault('log_dir', '.bouncer/logs')
                    notifier_cfg.setdefault('rotation', 'daily')
                    notifier_cfg.setdefault('min_severity', 'info')
                    notifier_cfg.setdefault('detail_level', 'full_transcript')

            # Move to notification details screen
            from .notification_details import NotificationDetailsScreen
            self.app.push_screen(NotificationDetailsScreen())
