"""
Hooks Configuration Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Label, Input
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


class HooksScreen(Screen):
    """Screen for configuring hooks (validation and logging)"""

    def compose(self) -> ComposeResult:
        """Create hooks configuration widgets"""
        with Container(classes="content-container"):
            with Vertical():
                yield Static(
                    "[bold cyan]Step 5 of 8:[/bold cyan] Configure Hooks",
                    classes="section-title"
                )
                yield Static(
                    "Hooks provide pre-tool validation and post-tool logging.\n"
                    "[dim]These are optional security and auditing features.[/dim]",
                    classes="help-text"
                )

                with ScrollableContainer(classes="bouncer-list"):
                    # Master enable switch
                    yield Checkbox(
                        "[bold]Enable Hooks[/bold]\n"
                        "  Master switch to enable the hooks system",
                        value=False,
                        id="hooks-enabled"
                    )

                    # Validation section
                    yield Static("\n[bold yellow]Validation Hooks[/bold yellow]", classes="subsection-title")
                    yield Static(
                        "[dim]Run checks before tools execute (e.g., block writes to .env files)[/dim]",
                        classes="help-text"
                    )

                    yield Checkbox(
                        "[bold]Enable Validation[/bold]\n"
                        "  Pre-tool validation checks",
                        value=True,
                        id="validation-enabled"
                    )

                    yield Checkbox(
                        "Block Protected Files\n"
                        "  [dim]Prevent writes to .env, secrets, credentials files[/dim]",
                        value=True,
                        id="block-protected-files"
                    )

                    yield Checkbox(
                        "Block Hardcoded Secrets\n"
                        "  [dim]Detect and block writes containing API keys, passwords[/dim]",
                        value=True,
                        id="block-hardcoded-secrets"
                    )

                    yield Checkbox(
                        "Block Dangerous Code Patterns\n"
                        "  [dim]Block eval(), exec(), and other dangerous code[/dim]",
                        value=True,
                        id="block-dangerous-code"
                    )

                    yield Checkbox(
                        "Block Dangerous Commands\n"
                        "  [dim]Block rm -rf, dd, and other destructive commands[/dim]",
                        value=True,
                        id="block-dangerous-commands"
                    )

                    # Logging section
                    yield Static("\n[bold yellow]Logging Hooks[/bold yellow]", classes="subsection-title")
                    yield Static(
                        "[dim]Log tool usage for audit trails[/dim]",
                        classes="help-text"
                    )

                    yield Checkbox(
                        "[bold]Enable Logging[/bold]\n"
                        "  Post-tool logging for audit trails",
                        value=True,
                        id="logging-enabled"
                    )

                    yield Checkbox(
                        "Log File Writes\n"
                        "  [dim]Log all Write tool usage[/dim]",
                        value=True,
                        id="log-writes"
                    )

                    yield Checkbox(
                        "Log Bash Commands\n"
                        "  [dim]Log all Bash tool usage[/dim]",
                        value=True,
                        id="log-bash"
                    )

                    yield Checkbox(
                        "Log All Tools\n"
                        "  [dim]Log usage of all tools (verbose)[/dim]",
                        value=False,
                        id="log-all-tools"
                    )

                    yield Static("\n[dim]Audit Directory: .bouncer/audit[/dim]", classes="help-text")

                yield Static(
                    "\n[bold yellow]Note:[/bold yellow] Hooks add overhead to each tool call.\n"
                    "Enable only what you need for your security/audit requirements.",
                    classes="help-text"
                )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Skip", variant="default", id="skip")
                yield Button("Continue →", variant="primary", id="continue")

    def on_mount(self) -> None:
        """Initialize with saved config"""
        app = self.app
        hooks_config = app.get_config_value('hooks', {})
        validation_config = hooks_config.get('validation', {})
        logging_config = hooks_config.get('logging', {})

        # Set checkbox states from config
        self.query_one("#hooks-enabled", Checkbox).value = hooks_config.get('enabled', False)

        # Validation settings
        self.query_one("#validation-enabled", Checkbox).value = validation_config.get('enabled', True)
        self.query_one("#block-protected-files", Checkbox).value = validation_config.get('block_protected_files', True)
        self.query_one("#block-hardcoded-secrets", Checkbox).value = validation_config.get('block_hardcoded_secrets', True)
        self.query_one("#block-dangerous-code", Checkbox).value = validation_config.get('block_dangerous_code', True)
        self.query_one("#block-dangerous-commands", Checkbox).value = validation_config.get('block_dangerous_commands', True)

        # Logging settings
        self.query_one("#logging-enabled", Checkbox).value = logging_config.get('enabled', True)
        self.query_one("#log-writes", Checkbox).value = logging_config.get('log_writes', True)
        self.query_one("#log-bash", Checkbox).value = logging_config.get('log_bash', True)
        self.query_one("#log-all-tools", Checkbox).value = logging_config.get('log_all_tools', False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()

        elif event.button.id == "skip":
            # Skip hooks, move to scheduling
            from .scheduling import SchedulingScreen
            self.app.push_screen(SchedulingScreen())

        elif event.button.id == "continue":
            # Save hooks configuration
            hooks_enabled = self.query_one("#hooks-enabled", Checkbox).value

            self.app.config_data['hooks'] = {
                'enabled': hooks_enabled,
                'validation': {
                    'enabled': self.query_one("#validation-enabled", Checkbox).value,
                    'block_protected_files': self.query_one("#block-protected-files", Checkbox).value,
                    'protected_file_patterns': ['.env', 'secrets', 'credentials', '.pem', '.key'],
                    'block_hardcoded_secrets': self.query_one("#block-hardcoded-secrets", Checkbox).value,
                    'secret_patterns': ['api_key', 'password', 'secret', 'token', 'private_key'],
                    'block_dangerous_code': self.query_one("#block-dangerous-code", Checkbox).value,
                    'blocked_code_patterns': ['eval(', 'exec('],
                    'warning_code_patterns': ['os.system(', 'subprocess.Popen(', '__import__'],
                    'file_size_limit': 1000000,
                    'block_dangerous_commands': self.query_one("#block-dangerous-commands", Checkbox).value,
                    'dangerous_commands': ['rm -rf', 'dd if=', ':(){:|:&};:', 'mkfs', 'wipefs'],
                    'warning_commands': ['sudo', 'apt-get', 'pip install', 'npm install']
                },
                'logging': {
                    'enabled': self.query_one("#logging-enabled", Checkbox).value,
                    'audit_dir': '.bouncer/audit',
                    'log_writes': self.query_one("#log-writes", Checkbox).value,
                    'log_bash': self.query_one("#log-bash", Checkbox).value,
                    'log_all_tools': self.query_one("#log-all-tools", Checkbox).value
                }
            }

            # Move to scheduling screen
            from .scheduling import SchedulingScreen
            self.app.push_screen(SchedulingScreen())
