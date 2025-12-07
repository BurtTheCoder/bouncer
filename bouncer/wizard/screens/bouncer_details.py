"""
Bouncer Details Screen - Configure per-bouncer settings
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Input, Label, Checkbox, Select
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


# Default file types for each bouncer
BOUNCER_FILE_TYPES = {
    'code_quality': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.rs'],
    'security': ['.py', '.js', '.ts', '.java', '.go', '.env', '.yaml', '.yml'],
    'documentation': ['.md', '.rst', '.txt', '.adoc'],
    'data_validation': ['.json', '.yaml', '.yml', '.csv', '.xml'],
    'performance': ['.py', '.js', '.ts', '.java', '.go'],
    'accessibility': ['.html', '.jsx', '.tsx', '.vue', '.svelte'],
    'license': ['.py', '.js', '.ts', '.java', '.go', '.rs', '.rb'],
    'infrastructure': ['.yaml', '.yml', '.tf', '.json', 'Dockerfile', '.dockerfile'],
    'api_contract': ['.yaml', '.yml', '.json', '.graphql'],
    'dependency': ['package.json', 'requirements.txt', 'Pipfile', 'go.mod', 'Cargo.toml', 'Gemfile'],
    'obsidian': ['.md'],
    'log_investigator': ['.log'],
}


class BouncerDetailsScreen(Screen):
    """Screen for configuring per-bouncer details"""

    def compose(self) -> ComposeResult:
        """Create bouncer details widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 4 of 12:[/bold cyan] Bouncer Settings",
                classes="section-title"
            )
            yield Static(
                "Configure settings for each enabled bouncer.\n"
                "[dim]Only showing bouncers you enabled in the previous step.[/dim]",
                classes="help-text"
            )

            with ScrollableContainer(classes="notification-list"):
                # We'll populate this dynamically in on_mount
                yield Static("", id="bouncer-settings-container")

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Build the bouncer settings dynamically"""
        container = self.query_one("#bouncer-settings-container", Static)

        # Get enabled bouncers
        bouncers = self.app.config_data.get('bouncers', {})
        enabled_bouncers = [b for b, cfg in bouncers.items() if cfg.get('enabled', False)]

        if not enabled_bouncers:
            container.update("[yellow]No bouncers enabled. Go back and enable some bouncers.[/yellow]")
            return

        # Build settings for each enabled bouncer
        self._build_bouncer_widgets(enabled_bouncers)

    def _build_bouncer_widgets(self, enabled_bouncers: list) -> None:
        """Build widgets for each enabled bouncer"""
        # Remove the placeholder
        container = self.query_one("#bouncer-settings-container", Static)
        container.remove()

        # Get the scrollable container
        scroll = self.query_one(ScrollableContainer)

        for bouncer_id in enabled_bouncers:
            bouncer_cfg = self.app.config_data.get('bouncers', {}).get(bouncer_id, {})

            # Bouncer header
            scroll.mount(Static(f"\n[bold cyan]{bouncer_id.replace('_', ' ').title()}[/bold cyan]"))

            # Auto-fix toggle
            auto_fix = bouncer_cfg.get('auto_fix', True)
            scroll.mount(Checkbox(
                "Auto-fix issues",
                value=auto_fix,
                id=f"autofix-{bouncer_id}"
            ))

            # File types
            default_types = BOUNCER_FILE_TYPES.get(bouncer_id, [])
            current_types = bouncer_cfg.get('file_types', default_types)
            scroll.mount(Label(f"File types (comma-separated):"))
            scroll.mount(Input(
                value=", ".join(current_types),
                id=f"filetypes-{bouncer_id}"
            ))

            # Bouncer-specific settings
            if bouncer_id == 'security':
                severity = bouncer_cfg.get('severity_threshold', 'medium')
                scroll.mount(Label("Severity threshold:"))
                scroll.mount(Select(
                    [("Low", "low"), ("Medium", "medium"), ("High", "high"), ("Critical", "critical")],
                    value=severity,
                    id=f"severity-{bouncer_id}",
                    allow_blank=False
                ))

            elif bouncer_id == 'license':
                license_type = bouncer_cfg.get('project_license', 'MIT')
                scroll.mount(Label("Project license:"))
                scroll.mount(Input(
                    value=license_type,
                    placeholder="MIT, Apache-2.0, GPL-3.0, etc.",
                    id=f"license-{bouncer_id}"
                ))

            elif bouncer_id == 'accessibility':
                wcag = bouncer_cfg.get('wcag_level', 'AA')
                scroll.mount(Label("WCAG Level:"))
                scroll.mount(Select(
                    [("A - Minimum", "A"), ("AA - Standard", "AA"), ("AAA - Enhanced", "AAA")],
                    value=wcag,
                    id=f"wcag-{bouncer_id}",
                    allow_blank=False
                ))

            elif bouncer_id == 'performance':
                max_file = bouncer_cfg.get('max_file_size', 1000000)
                scroll.mount(Label("Max file size (bytes):"))
                scroll.mount(Input(
                    value=str(max_file),
                    id=f"maxfile-{bouncer_id}"
                ))

            elif bouncer_id == 'log_investigator':
                log_dir = bouncer_cfg.get('log_dir', '/var/log')
                scroll.mount(Label("Log directory:"))
                scroll.mount(Input(
                    value=log_dir,
                    id=f"logdir-{bouncer_id}"
                ))
                lookback = bouncer_cfg.get('lookback_hours', 24)
                scroll.mount(Label("Lookback hours:"))
                scroll.mount(Input(
                    value=str(lookback),
                    id=f"lookback-{bouncer_id}"
                ))

            scroll.mount(Static("[dim]─────────────────────────────────[/dim]"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "continue":
            self._save_and_continue()

    def _save_and_continue(self) -> None:
        """Save bouncer details and continue"""
        bouncers = self.app.config_data.get('bouncers', {})

        for bouncer_id, cfg in bouncers.items():
            if not cfg.get('enabled', False):
                continue

            # Auto-fix
            try:
                autofix_cb = self.query_one(f"#autofix-{bouncer_id}", Checkbox)
                cfg['auto_fix'] = autofix_cb.value
            except Exception:
                pass

            # File types
            try:
                filetypes_input = self.query_one(f"#filetypes-{bouncer_id}", Input)
                types = [t.strip() for t in filetypes_input.value.split(',') if t.strip()]
                if types:
                    cfg['file_types'] = types
            except Exception:
                pass

            # Bouncer-specific
            if bouncer_id == 'security':
                try:
                    severity = self.query_one(f"#severity-{bouncer_id}", Select)
                    cfg['severity_threshold'] = severity.value
                except Exception:
                    pass

            elif bouncer_id == 'license':
                try:
                    license_input = self.query_one(f"#license-{bouncer_id}", Input)
                    cfg['project_license'] = license_input.value
                except Exception:
                    pass

            elif bouncer_id == 'accessibility':
                try:
                    wcag = self.query_one(f"#wcag-{bouncer_id}", Select)
                    cfg['wcag_level'] = wcag.value
                except Exception:
                    pass

            elif bouncer_id == 'performance':
                try:
                    maxfile = self.query_one(f"#maxfile-{bouncer_id}", Input)
                    cfg['max_file_size'] = int(maxfile.value)
                except Exception:
                    pass

            elif bouncer_id == 'log_investigator':
                try:
                    logdir = self.query_one(f"#logdir-{bouncer_id}", Input)
                    cfg['log_dir'] = logdir.value
                    lookback = self.query_one(f"#lookback-{bouncer_id}", Input)
                    cfg['lookback_hours'] = int(lookback.value)
                except Exception:
                    pass

        # Check if Obsidian is enabled - go to Obsidian screen
        if bouncers.get('obsidian', {}).get('enabled', False):
            from .obsidian_settings import ObsidianSettingsScreen
            self.app.push_screen(ObsidianSettingsScreen())
        else:
            from .notifications import NotificationsScreen
            self.app.push_screen(NotificationsScreen())
