"""
MCP Integrations Setup Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Label
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


INTEGRATION_INFO = {
    'github': {
        'name': 'GitHub',
        'description': 'Auto-create PRs and issues from bouncer findings',
        'env_var': 'GITHUB_PERSONAL_ACCESS_TOKEN',
        'features': ['Create PRs', 'Create Issues', 'Custom branch naming']
    },
    'gitlab': {
        'name': 'GitLab',
        'description': 'Auto-create MRs and issues from bouncer findings',
        'env_var': 'GITLAB_PERSONAL_ACCESS_TOKEN',
        'features': ['Create MRs', 'Create Issues', 'Project targeting']
    },
    'linear': {
        'name': 'Linear',
        'description': 'Create Linear issues from bouncer findings',
        'env_var': 'LINEAR_API_KEY',
        'features': ['Create Issues', 'Team targeting', 'Priority levels']
    },
    'jira': {
        'name': 'Jira',
        'description': 'Create Jira tickets from bouncer findings',
        'env_var': 'JIRA_API_TOKEN',
        'features': ['Create Tickets', 'Project targeting', 'Issue types']
    }
}


class IntegrationsScreen(Screen):
    """Screen for configuring MCP integrations"""
    
    def compose(self) -> ComposeResult:
        """Create integration configuration widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 4 of 8:[/bold cyan] Configure Integrations",
                classes="section-title"
            )
            yield Static(
                "Enable integrations to automatically create PRs, issues, and tickets.\n"
                "[dim]These are optional - skip if you don't need integrations.[/dim]",
                classes="help-text"
            )

            with ScrollableContainer(classes="notification-list"):
                for integration_id, info in INTEGRATION_INFO.items():
                    yield Checkbox(
                        f"[bold]{info['name']}[/bold] - {info['description']}\n"
                        f"  [dim]Requires: {info['env_var']}[/dim]",
                        value=False,
                        id=f"integration-{integration_id}"
                    )

            yield Static(
                "\n[dim]API tokens should be set as environment variables.[/dim]",
                classes="help-text"
            )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Skip", variant="default", id="skip")
                yield Button("Continue →", variant="primary", id="continue")
    
    def on_mount(self) -> None:
        """Initialize with saved config"""
        app = self.app
        integrations_config = app.get_config_value('integrations', {})
        
        # Set checkbox states from config
        for integration_id in INTEGRATION_INFO.keys():
            checkbox = self.query_one(f"#integration-{integration_id}", Checkbox)
            integration_cfg = integrations_config.get(integration_id, {})
            checkbox.value = integration_cfg.get('enabled', False)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        
        elif event.button.id == "skip":
            # Skip integrations, move to hooks
            from .hooks import HooksScreen
            self.app.push_screen(HooksScreen())
        
        elif event.button.id == "continue":
            # Save integration selections to config
            if 'integrations' not in self.app.config_data:
                self.app.config_data['integrations'] = {}
            
            for integration_id in INTEGRATION_INFO.keys():
                checkbox = self.query_one(f"#integration-{integration_id}", Checkbox)
                
                if checkbox.value:
                    if integration_id not in self.app.config_data['integrations']:
                        self.app.config_data['integrations'][integration_id] = {}
                    
                    self.app.config_data['integrations'][integration_id]['enabled'] = True
                    
                    # Set default values
                    if integration_id == 'github':
                        self.app.config_data['integrations'][integration_id].update({
                            'auto_create_pr': False,
                            'auto_create_issue': False,
                            'branch_prefix': 'bouncer'
                        })
                    elif integration_id == 'gitlab':
                        self.app.config_data['integrations'][integration_id].update({
                            'auto_create_mr': False,
                            'auto_create_issue': False
                        })
                    elif integration_id == 'linear':
                        self.app.config_data['integrations'][integration_id].update({
                            'auto_create_issue': False
                        })
                    elif integration_id == 'jira':
                        self.app.config_data['integrations'][integration_id].update({
                            'auto_create_ticket': False
                        })
            
            # Move to next screen
            from .hooks import HooksScreen
            self.app.push_screen(HooksScreen())
