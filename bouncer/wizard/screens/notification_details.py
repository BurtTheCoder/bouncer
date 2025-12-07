"""
Notification Details Screen - Configure per-notifier settings
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Input, Label, Select
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


SEVERITY_OPTIONS = [
    ("Info - All notifications", "info"),
    ("Warning - Warnings and above", "warning"),
    ("Denied - Critical issues only", "denied"),
    ("Error - Errors only", "error"),
]

DETAIL_OPTIONS = [
    ("Summary - Concise overview", "summary"),
    ("Detailed - Full issue details", "detailed"),
    ("Full Transcript - Complete agent output", "full_transcript"),
]

ROTATION_OPTIONS = [
    ("Daily", "daily"),
    ("Weekly", "weekly"),
    ("Monthly", "monthly"),
    ("No rotation", "none"),
]


class NotificationDetailsScreen(Screen):
    """Screen for configuring notification details"""

    def compose(self) -> ComposeResult:
        """Create notification details widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 7 of 12:[/bold cyan] Notification Settings",
                classes="section-title"
            )
            yield Static(
                "Configure severity levels and detail for each notification channel.\n"
                "[dim]Only showing channels you enabled in the previous step.[/dim]",
                classes="help-text"
            )

            with ScrollableContainer(classes="notification-list"):
                yield Static("", id="notification-settings-container")

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Build notification settings dynamically"""
        container = self.query_one("#notification-settings-container", Static)

        notifications = self.app.config_data.get('notifications', {})
        enabled = [n for n, cfg in notifications.items() if cfg.get('enabled', False)]

        if not enabled:
            container.update("[yellow]No notification channels enabled.[/yellow]")
            return

        self._build_notification_widgets(enabled)

    def _build_notification_widgets(self, enabled_notifiers: list) -> None:
        """Build widgets for each enabled notifier"""
        container = self.query_one("#notification-settings-container", Static)
        container.remove()

        scroll = self.query_one(ScrollableContainer)

        for notifier_id in enabled_notifiers:
            notifier_cfg = self.app.config_data.get('notifications', {}).get(notifier_id, {})

            # Header
            scroll.mount(Static(f"\n[bold cyan]{notifier_id.replace('_', ' ').title()}[/bold cyan]"))

            # Min severity
            severity = notifier_cfg.get('min_severity', 'warning')
            scroll.mount(Label("Minimum severity:"))
            scroll.mount(Select(
                SEVERITY_OPTIONS,
                value=severity,
                id=f"severity-{notifier_id}",
                allow_blank=False
            ))

            # Detail level
            detail = notifier_cfg.get('detail_level', 'summary')
            scroll.mount(Label("Detail level:"))
            scroll.mount(Select(
                DETAIL_OPTIONS,
                value=detail,
                id=f"detail-{notifier_id}",
                allow_blank=False
            ))

            # Notifier-specific settings
            if notifier_id == 'slack':
                webhook = notifier_cfg.get('webhook_url', '')
                scroll.mount(Label("Webhook URL:"))
                scroll.mount(Input(
                    value=webhook,
                    placeholder="https://hooks.slack.com/services/...",
                    id=f"webhook-{notifier_id}"
                ))
                scroll.mount(Static(
                    "[dim]Get this from Slack → Apps → Incoming Webhooks[/dim]"
                ))

            elif notifier_id == 'discord':
                webhook = notifier_cfg.get('webhook_url', '')
                scroll.mount(Label("Webhook URL:"))
                scroll.mount(Input(
                    value=webhook,
                    placeholder="https://discord.com/api/webhooks/...",
                    id=f"webhook-{notifier_id}"
                ))
                scroll.mount(Static(
                    "[dim]Get this from Server Settings → Integrations → Webhooks[/dim]"
                ))
                username = notifier_cfg.get('username', 'Bouncer Bot')
                scroll.mount(Label("Bot username:"))
                scroll.mount(Input(value=username, id=f"username-{notifier_id}"))

            elif notifier_id == 'email':
                from_email = notifier_cfg.get('from_email', 'bouncer@your-domain.com')
                scroll.mount(Label("From email:"))
                scroll.mount(Input(value=from_email, id=f"from-{notifier_id}"))

                to_emails = notifier_cfg.get('to_emails', ['team@your-domain.com'])
                scroll.mount(Label("To emails (comma-separated):"))
                scroll.mount(Input(value=", ".join(to_emails), id=f"to-{notifier_id}"))

                smtp_host = notifier_cfg.get('smtp_host', '${SMTP_HOST}')
                scroll.mount(Label("SMTP host:"))
                scroll.mount(Input(value=smtp_host, id=f"smtp-host-{notifier_id}"))

                smtp_port = notifier_cfg.get('smtp_port', 587)
                scroll.mount(Label("SMTP port:"))
                scroll.mount(Input(value=str(smtp_port), id=f"smtp-port-{notifier_id}"))

            elif notifier_id == 'teams':
                webhook = notifier_cfg.get('webhook_url', '')
                scroll.mount(Label("Webhook URL:"))
                scroll.mount(Input(
                    value=webhook,
                    placeholder="https://outlook.office.com/webhook/...",
                    id=f"webhook-{notifier_id}"
                ))
                scroll.mount(Static(
                    "[dim]Get this from Teams channel → Connectors → Incoming Webhook[/dim]"
                ))

            elif notifier_id == 'webhook':
                webhook = notifier_cfg.get('webhook_url', '')
                scroll.mount(Label("Webhook URL:"))
                scroll.mount(Input(
                    value=webhook,
                    placeholder="https://your-endpoint.com/webhook",
                    id=f"webhook-{notifier_id}"
                ))
                method = notifier_cfg.get('method', 'POST')
                scroll.mount(Label("HTTP method:"))
                scroll.mount(Select(
                    [("POST", "POST"), ("PUT", "PUT")],
                    value=method,
                    id=f"method-{notifier_id}",
                    allow_blank=False
                ))

            elif notifier_id == 'file_log':
                log_dir = notifier_cfg.get('log_dir', '.bouncer/logs')
                scroll.mount(Label("Log directory:"))
                scroll.mount(Input(value=log_dir, id=f"logdir-{notifier_id}"))

                rotation = notifier_cfg.get('rotation', 'daily')
                scroll.mount(Label("Log rotation:"))
                scroll.mount(Select(
                    ROTATION_OPTIONS,
                    value=rotation,
                    id=f"rotation-{notifier_id}",
                    allow_blank=False
                ))

            scroll.mount(Static("[dim]─────────────────────────────────[/dim]"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "continue":
            self._save_and_continue()

    def _save_and_continue(self) -> None:
        """Save notification details and continue"""
        notifications = self.app.config_data.get('notifications', {})

        for notifier_id, cfg in notifications.items():
            if not cfg.get('enabled', False):
                continue

            # Common settings
            try:
                severity = self.query_one(f"#severity-{notifier_id}", Select)
                cfg['min_severity'] = severity.value
            except Exception:
                pass

            try:
                detail = self.query_one(f"#detail-{notifier_id}", Select)
                cfg['detail_level'] = detail.value
            except Exception:
                pass

            # Notifier-specific
            if notifier_id == 'slack':
                try:
                    webhook = self.query_one(f"#webhook-{notifier_id}", Input)
                    cfg['webhook_url'] = webhook.value
                except Exception:
                    pass

            elif notifier_id == 'discord':
                try:
                    webhook = self.query_one(f"#webhook-{notifier_id}", Input)
                    cfg['webhook_url'] = webhook.value
                    username = self.query_one(f"#username-{notifier_id}", Input)
                    cfg['username'] = username.value
                except Exception:
                    pass

            elif notifier_id == 'teams':
                try:
                    webhook = self.query_one(f"#webhook-{notifier_id}", Input)
                    cfg['webhook_url'] = webhook.value
                except Exception:
                    pass

            elif notifier_id == 'email':
                try:
                    cfg['from_email'] = self.query_one(f"#from-{notifier_id}", Input).value
                    to_str = self.query_one(f"#to-{notifier_id}", Input).value
                    cfg['to_emails'] = [e.strip() for e in to_str.split(',') if e.strip()]
                    cfg['smtp_host'] = self.query_one(f"#smtp-host-{notifier_id}", Input).value
                    cfg['smtp_port'] = int(self.query_one(f"#smtp-port-{notifier_id}", Input).value)
                except Exception:
                    pass

            elif notifier_id == 'webhook':
                try:
                    webhook = self.query_one(f"#webhook-{notifier_id}", Input)
                    cfg['webhook_url'] = webhook.value
                    method = self.query_one(f"#method-{notifier_id}", Select)
                    cfg['method'] = method.value
                except Exception:
                    pass

            elif notifier_id == 'file_log':
                try:
                    cfg['log_dir'] = self.query_one(f"#logdir-{notifier_id}", Input).value
                    rotation = self.query_one(f"#rotation-{notifier_id}", Select)
                    cfg['rotation'] = rotation.value
                except Exception:
                    pass

        from .integrations import IntegrationsScreen
        self.app.push_screen(IntegrationsScreen())
