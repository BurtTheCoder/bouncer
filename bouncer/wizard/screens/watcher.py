"""
Watcher Settings Screen - Configure file watching behavior
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Input, Label, Checkbox
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


class WatcherScreen(Screen):
    """Screen for configuring file watcher settings"""

    def compose(self) -> ComposeResult:
        """Create watcher configuration widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 2 of 12:[/bold cyan] Watcher Settings",
                classes="section-title"
            )
            yield Static(
                "Configure how Bouncer monitors your files.",
                classes="help-text"
            )

            with ScrollableContainer(classes="notification-list"):
                yield Label("\n[bold]Debounce Delay (seconds):[/bold]")
                yield Input(
                    placeholder="10",
                    value="10",
                    id="debounce-delay"
                )
                yield Static(
                    "[dim]Wait this many seconds after the last file change before processing.\n"
                    "Higher values prevent conflicts during active editing.\n"
                    "Recommended: 2-5 for code, 10+ for Obsidian/notes.[/dim]",
                    classes="help-text"
                )

                yield Label("\n[bold]Poll Interval (seconds):[/bold]")
                yield Input(
                    placeholder="0.5",
                    value="0.5",
                    id="poll-interval"
                )
                yield Static(
                    "[dim]How often to check for settled changes.\n"
                    "Lower = more responsive, higher = less CPU usage.[/dim]",
                    classes="help-text"
                )

                yield Label("\n[bold]Queue Settings:[/bold]")
                yield Input(
                    placeholder="1000",
                    value="1000",
                    id="event-queue-size"
                )
                yield Static(
                    "[dim]Maximum pending events before oldest are dropped.\n"
                    "Default 1000 is fine for most use cases.[/dim]",
                    classes="help-text"
                )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        debounce = self.app.config_data.get('debounce_delay', 10)
        poll = self.app.config_data.get('poll_interval', 0.5)
        queue_size = self.app.config_data.get('event_queue_size', 1000)

        self.query_one("#debounce-delay", Input).value = str(debounce)
        self.query_one("#poll-interval", Input).value = str(poll)
        self.query_one("#event-queue-size", Input).value = str(queue_size)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "continue":
            self._save_and_continue()

    def _save_and_continue(self) -> None:
        """Save watcher config and continue"""
        try:
            debounce = float(self.query_one("#debounce-delay", Input).value or "10")
        except ValueError:
            debounce = 10

        try:
            poll = float(self.query_one("#poll-interval", Input).value or "0.5")
        except ValueError:
            poll = 0.5

        try:
            queue_size = int(self.query_one("#event-queue-size", Input).value or "1000")
        except ValueError:
            queue_size = 1000

        self.app.config_data['debounce_delay'] = debounce
        self.app.config_data['poll_interval'] = poll
        self.app.config_data['event_queue_size'] = queue_size

        from .bouncers import BouncersScreen
        self.app.push_screen(BouncersScreen())
