"""
Obsidian Settings Screen - Configure Obsidian-specific options
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Input, Label, Checkbox, Select
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


class ObsidianSettingsScreen(Screen):
    """Screen for configuring Obsidian bouncer settings"""

    def compose(self) -> ComposeResult:
        """Create Obsidian settings widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 5 of 12:[/bold cyan] Obsidian Settings",
                classes="section-title"
            )
            yield Static(
                "Configure how the Obsidian bouncer manages your vault.",
                classes="help-text"
            )

            with ScrollableContainer(classes="notification-list"):
                # Frontmatter settings
                yield Static("\n[bold]Frontmatter Settings[/bold]")
                yield Label("Required fields (comma-separated):")
                yield Input(
                    value="tags, created",
                    placeholder="tags, created, updated",
                    id="required-fields"
                )

                # Tag settings
                yield Static("\n[bold]Tag Settings[/bold]")
                yield Label("Tag format:")
                yield Select(
                    [
                        ("kebab-case (recommended)", "kebab-case"),
                        ("camelCase", "camelCase"),
                        ("snake_case", "snake_case"),
                        ("PascalCase", "PascalCase"),
                    ],
                    value="kebab-case",
                    id="tag-format",
                    allow_blank=False
                )
                yield Label("Max tags per note:")
                yield Input(
                    value="10",
                    id="max-tags"
                )

                # Link settings
                yield Static("\n[bold]Link Settings[/bold]")
                yield Checkbox(
                    "Check for broken wikilinks",
                    value=True,
                    id="check-broken-links"
                )
                yield Checkbox(
                    "Suggest new connections",
                    value=True,
                    id="suggest-connections"
                )
                yield Label("Minimum connections per note:")
                yield Input(
                    value="1",
                    id="min-connections"
                )

                # Content settings
                yield Static("\n[bold]Content Settings[/bold]")
                yield Label("Minimum note length (characters):")
                yield Input(
                    value="50",
                    id="min-note-length"
                )
                yield Checkbox(
                    "Require headings in notes",
                    value=True,
                    id="require-headings"
                )

                # Vault structure
                yield Static("\n[bold]Vault Structure[/bold]")
                yield Label("Attachments folder:")
                yield Input(
                    value="attachments",
                    id="attachment-folder"
                )
                yield Label("Templates folder:")
                yield Input(
                    value="templates",
                    id="template-folder"
                )
                yield Label("Daily notes folder:")
                yield Input(
                    value="daily",
                    id="daily-notes-folder"
                )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        obsidian_cfg = self.app.config_data.get('bouncers', {}).get('obsidian', {})

        # Required fields
        fields = obsidian_cfg.get('required_fields', ['tags', 'created'])
        self.query_one("#required-fields", Input).value = ", ".join(fields)

        # Tag settings
        self.query_one("#tag-format", Select).value = obsidian_cfg.get('tag_format', 'kebab-case')
        self.query_one("#max-tags", Input).value = str(obsidian_cfg.get('max_tags', 10))

        # Link settings
        self.query_one("#check-broken-links", Checkbox).value = obsidian_cfg.get('check_broken_links', True)
        self.query_one("#suggest-connections", Checkbox).value = obsidian_cfg.get('suggest_connections', True)
        self.query_one("#min-connections", Input).value = str(obsidian_cfg.get('min_connections', 1))

        # Content settings
        self.query_one("#min-note-length", Input).value = str(obsidian_cfg.get('min_note_length', 50))
        self.query_one("#require-headings", Checkbox).value = obsidian_cfg.get('require_headings', True)

        # Vault structure
        self.query_one("#attachment-folder", Input).value = obsidian_cfg.get('attachment_folder', 'attachments')
        self.query_one("#template-folder", Input).value = obsidian_cfg.get('template_folder', 'templates')
        self.query_one("#daily-notes-folder", Input).value = obsidian_cfg.get('daily_notes_folder', 'daily')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "continue":
            self._save_and_continue()

    def _save_and_continue(self) -> None:
        """Save Obsidian settings and continue"""
        if 'bouncers' not in self.app.config_data:
            self.app.config_data['bouncers'] = {}
        if 'obsidian' not in self.app.config_data['bouncers']:
            self.app.config_data['bouncers']['obsidian'] = {}

        obsidian_cfg = self.app.config_data['bouncers']['obsidian']

        # Required fields
        fields_str = self.query_one("#required-fields", Input).value
        obsidian_cfg['required_fields'] = [f.strip() for f in fields_str.split(',') if f.strip()]

        # Tag settings
        obsidian_cfg['tag_format'] = self.query_one("#tag-format", Select).value
        try:
            obsidian_cfg['max_tags'] = int(self.query_one("#max-tags", Input).value)
        except ValueError:
            obsidian_cfg['max_tags'] = 10

        # Link settings
        obsidian_cfg['check_broken_links'] = self.query_one("#check-broken-links", Checkbox).value
        obsidian_cfg['suggest_connections'] = self.query_one("#suggest-connections", Checkbox).value
        try:
            obsidian_cfg['min_connections'] = int(self.query_one("#min-connections", Input).value)
        except ValueError:
            obsidian_cfg['min_connections'] = 1

        # Content settings
        try:
            obsidian_cfg['min_note_length'] = int(self.query_one("#min-note-length", Input).value)
        except ValueError:
            obsidian_cfg['min_note_length'] = 50
        obsidian_cfg['require_headings'] = self.query_one("#require-headings", Checkbox).value

        # Vault structure
        obsidian_cfg['attachment_folder'] = self.query_one("#attachment-folder", Input).value
        obsidian_cfg['template_folder'] = self.query_one("#template-folder", Input).value
        obsidian_cfg['daily_notes_folder'] = self.query_one("#daily-notes-folder", Input).value

        from .notifications import NotificationsScreen
        self.app.push_screen(NotificationsScreen())
