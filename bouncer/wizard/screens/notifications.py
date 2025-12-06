"""
Notifications Setup Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Select, Label
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


NOTIFIER_INFO = {
    'slack': {
        'name': 'Slack',
        'description': 'Send notifications to Slack channels',
        'env_var': 'SLACK_WEBHOOK_URL',
        'default_severity': 'warning',
        'default_detail': 'summary'
    },
    'discord': {
        'name': 'Discord',
        'description': 'Send notifications to Discord channels',
        'env_var': 'DISCORD_WEBHOOK_URL',
        'default_severity': 'warning',
        'default_detail': 'summary'
    },
    'email': {
        'name': 'Email',
        'description': 'Send email notifications via SMTP',
        'env_var': 'SMTP_HOST, SMTP_USER, SMTP_PASSWORD',
        'default_severity': 'error',
        'default_detail': 'detailed'
    },
    'teams': {
        'name': 'Microsoft Teams',
        'description': 'Send notifications to Teams channels',
        'env_var': 'TEAMS_WEBHOOK_URL',
        'default_severity': 'warning',
        'default_detail': 'summary'
    },
    'webhook': {
        'name': 'Custom Webhook',
        'description': 'Send JSON to custom webhook endpoint',
        'env_var': 'GENERIC_WEBHOOK_URL',
        'default_severity': 'info',
        'default_detail': 'detailed'
    },
    'file_log': {
        'name': 'File Logger',
        'description': 'Log to .bouncer/logs (JSON format)',
        'env_var': None,
        'default_severity': 'info',
        'default_detail': 'full_transcript'
    }
}

SEVERITY_OPTIONS = [
    ("info", "Info - All notifications"),
    ("warning", "Warning - Warnings and above"),
    ("denied", "Denied - Critical issues only"),
    ("error", "Error - Errors only"),
]

DETAIL_OPTIONS = [
    ("summary", "Summary - Concise overview"),
    ("detailed", "Detailed - Full issue details"),
    ("full_transcript", "Full - Complete agent transcript"),
]

ROTATION_OPTIONS = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("none", "No rotation"),
]


class NotificationsScreen(Screen):
    """Screen for configuring notifications"""

    def compose(self) -> ComposeResult:
        """Create notification configuration widgets"""
        with Container(classes="content-container"):
            with Vertical():
                yield Static(
                    "[bold cyan]Step 3 of 7:[/bold cyan] Configure Notifications",
                    classes="section-title"
                )
                yield Static(
                    "Choose notification channels and customize their settings.\n"
                    "[dim]File Logger is enabled by default for local auditing.[/dim]",
                    classes="help-text"
                )

                with ScrollableContainer(classes="bouncer-list"):
                    for notifier_id, info in NOTIFIER_INFO.items():
                        with Vertical(classes="notifier-section"):
                            # Notifier checkbox
                            env_var_text = f"Requires: {info['env_var']}" if info['env_var'] else 'No setup required'
                            yield Checkbox(
                                f"[bold]{info['name']}[/bold] - {info['description']}\n"
                                f"  [dim]{env_var_text}[/dim]",
                                value=(notifier_id == 'file_log'),
                                id=f"notifier-{notifier_id}"
                            )

                            # Settings row (indented)
                            with Horizontal(classes="notifier-settings"):
                                yield Label("  Severity:", classes="setting-label")
                                yield Select(
                                    SEVERITY_OPTIONS,
                                    value=info['default_severity'],
                                    id=f"severity-{notifier_id}",
                                    allow_blank=False
                                )

                                yield Label("  Detail:", classes="setting-label")
                                yield Select(
                                    DETAIL_OPTIONS,
                                    value=info['default_detail'],
                                    id=f"detail-{notifier_id}",
                                    allow_blank=False
                                )

                            # File logger specific: rotation setting
                            if notifier_id == 'file_log':
                                with Horizontal(classes="notifier-settings"):
                                    yield Label("  Rotation:", classes="setting-label")
                                    yield Select(
                                        ROTATION_OPTIONS,
                                        value="daily",
                                        id="rotation-file_log",
                                        allow_blank=False
                                    )

                yield Static(
                    "\n[bold yellow]Environment Variables:[/bold yellow]\n"
                    "Set webhook URLs and credentials as environment variables.\n"
                    "[dim]Example: export SLACK_WEBHOOK_URL=https://hooks.slack.com/...[/dim]\n\n"
                    "[bold]Severity Levels:[/bold]\n"
                    "• [green]info[/green] - All notifications\n"
                    "• [yellow]warning[/yellow] - Warnings and critical only\n"
                    "• [red]denied/error[/red] - Critical issues only",
                    classes="help-text"
                )

                with Container(classes="nav-buttons"):
                    yield Button("← Back", variant="default", id="back")
                    yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        app = self.app
        notifications_config = app.get_config_value('notifications', {})

        # Set states from config
        for notifier_id, info in NOTIFIER_INFO.items():
            notifier_cfg = notifications_config.get(notifier_id, {})

            # Enabled checkbox
            checkbox = self.query_one(f"#notifier-{notifier_id}", Checkbox)
            checkbox.value = notifier_cfg.get('enabled', notifier_id == 'file_log')

            # Severity select
            severity_select = self.query_one(f"#severity-{notifier_id}", Select)
            severity_select.value = notifier_cfg.get('min_severity', info['default_severity'])

            # Detail level select
            detail_select = self.query_one(f"#detail-{notifier_id}", Select)
            detail_select.value = notifier_cfg.get('detail_level', info['default_detail'])

        # File logger rotation
        file_log_cfg = notifications_config.get('file_log', {})
        rotation_select = self.query_one("#rotation-file_log", Select)
        rotation_select.value = file_log_cfg.get('rotation', 'daily')

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

                # Get severity
                severity_select = self.query_one(f"#severity-{notifier_id}", Select)
                notifier_cfg['min_severity'] = severity_select.value

                # Get detail level
                detail_select = self.query_one(f"#detail-{notifier_id}", Select)
                notifier_cfg['detail_level'] = detail_select.value

                # Set default values based on notifier type
                if notifier_id == 'slack':
                    notifier_cfg.setdefault('webhook_url', '${SLACK_WEBHOOK_URL}')
                    notifier_cfg.setdefault('channel', '#bouncer')
                elif notifier_id == 'discord':
                    notifier_cfg.setdefault('webhook_url', '${DISCORD_WEBHOOK_URL}')
                    notifier_cfg.setdefault('username', 'Bouncer Bot')
                elif notifier_id == 'email':
                    notifier_cfg.setdefault('smtp_host', '${SMTP_HOST}')
                    notifier_cfg.setdefault('smtp_port', 587)
                    notifier_cfg.setdefault('smtp_user', '${SMTP_USER}')
                    notifier_cfg.setdefault('smtp_password', '${SMTP_PASSWORD}')
                    notifier_cfg.setdefault('from_email', 'bouncer@example.com')
                    notifier_cfg.setdefault('to_emails', ['team@example.com'])
                    notifier_cfg.setdefault('use_tls', True)
                elif notifier_id == 'teams':
                    notifier_cfg.setdefault('webhook_url', '${TEAMS_WEBHOOK_URL}')
                elif notifier_id == 'webhook':
                    notifier_cfg.setdefault('webhook_url', '${GENERIC_WEBHOOK_URL}')
                    notifier_cfg.setdefault('method', 'POST')
                    notifier_cfg.setdefault('include_timestamp', True)
                elif notifier_id == 'file_log':
                    notifier_cfg.setdefault('log_dir', '.bouncer/logs')
                    # Get rotation
                    rotation_select = self.query_one("#rotation-file_log", Select)
                    notifier_cfg['rotation'] = rotation_select.value

            # Move to next screen
            from .integrations import IntegrationsScreen
            self.app.push_screen(IntegrationsScreen())
