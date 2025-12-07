"""
Bouncer Selection Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Checkbox, Label
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer


BOUNCER_INFO = {
    'code_quality': {
        'name': 'Code Quality',
        'description': 'Checks code style, complexity, and best practices',
        'file_types': ['.py', '.js', '.ts', '.java', '.go', '.rs']
    },
    'security': {
        'name': 'Security',
        'description': 'Scans for security vulnerabilities and sensitive data',
        'file_types': ['.py', '.js', '.ts', '.java', '.env', '.config']
    },
    'documentation': {
        'name': 'Documentation',
        'description': 'Ensures code has proper documentation and comments',
        'file_types': ['.py', '.js', '.ts', '.java', '.go', '.rs']
    },
    'data_validation': {
        'name': 'Data Validation',
        'description': 'Validates data schemas, JSON, and API contracts',
        'file_types': ['.json', '.yaml', '.yml', '.xml', '.csv']
    },
    'performance': {
        'name': 'Performance',
        'description': 'Identifies performance bottlenecks and inefficiencies',
        'file_types': ['.py', '.js', '.ts', '.java', '.sql']
    },
    'accessibility': {
        'name': 'Accessibility',
        'description': 'Checks web accessibility (WCAG compliance)',
        'file_types': ['.html', '.jsx', '.tsx', '.vue', '.svelte']
    },
    'license': {
        'name': 'License',
        'description': 'Validates license headers and compliance',
        'file_types': ['.py', '.js', '.ts', '.java', '.go', '.rs']
    },
    'infrastructure': {
        'name': 'Infrastructure',
        'description': 'Checks infrastructure-as-code and configs',
        'file_types': ['.tf', '.yaml', '.yml', 'Dockerfile', '.sh']
    },
    'api_contract': {
        'name': 'API Contract',
        'description': 'Validates API schemas and OpenAPI specs',
        'file_types': ['.yaml', '.yml', '.json']
    },
    'dependency': {
        'name': 'Dependency',
        'description': 'Checks for outdated or vulnerable dependencies',
        'file_types': ['requirements.txt', 'package.json', 'Cargo.toml']
    },
    'obsidian': {
        'name': 'Obsidian',
        'description': 'Validates Obsidian markdown notes and links',
        'file_types': ['.md']
    },
    'log_investigator': {
        'name': 'Log Investigator',
        'description': 'Monitors logs for errors and suggests fixes',
        'file_types': ['.log']
    }
}


class BouncersScreen(Screen):
    """Screen for selecting which bouncers to enable"""
    
    def compose(self) -> ComposeResult:
        """Create bouncer selection widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 2 of 8:[/bold cyan] Select Bouncers",
                classes="section-title"
            )
            yield Static(
                "Choose which bouncers to enable. You can always change this later.",
                classes="help-text"
            )

            with Horizontal():
                yield Button("Select All", variant="default", id="select-all")
                yield Button("Deselect All", variant="default", id="deselect-all")

            with ScrollableContainer(classes="bouncer-list"):
                for bouncer_id, info in BOUNCER_INFO.items():
                    yield Checkbox(
                        f"[bold]{info['name']}[/bold] - {info['description']}",
                        value=True,
                        id=f"bouncer-{bouncer_id}"
                    )

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")
    
    def on_mount(self) -> None:
        """Initialize with saved config"""
        app = self.app
        bouncers_config = app.get_config_value('bouncers', {})
        
        # Set checkbox states from config
        for bouncer_id in BOUNCER_INFO.keys():
            checkbox = self.query_one(f"#bouncer-{bouncer_id}", Checkbox)
            bouncer_cfg = bouncers_config.get(bouncer_id, {})
            checkbox.value = bouncer_cfg.get('enabled', True)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "select-all":
            for bouncer_id in BOUNCER_INFO.keys():
                checkbox = self.query_one(f"#bouncer-{bouncer_id}", Checkbox)
                checkbox.value = True
        
        elif event.button.id == "deselect-all":
            for bouncer_id in BOUNCER_INFO.keys():
                checkbox = self.query_one(f"#bouncer-{bouncer_id}", Checkbox)
                checkbox.value = False
        
        elif event.button.id == "back":
            self.app.pop_screen()
        
        elif event.button.id == "continue":
            # Save bouncer selections to config
            if 'bouncers' not in self.app.config_data:
                self.app.config_data['bouncers'] = {}
            
            for bouncer_id in BOUNCER_INFO.keys():
                checkbox = self.query_one(f"#bouncer-{bouncer_id}", Checkbox)
                
                if bouncer_id not in self.app.config_data['bouncers']:
                    self.app.config_data['bouncers'][bouncer_id] = {}
                
                self.app.config_data['bouncers'][bouncer_id]['enabled'] = checkbox.value
                
                # Set default auto_fix
                if 'auto_fix' not in self.app.config_data['bouncers'][bouncer_id]:
                    self.app.config_data['bouncers'][bouncer_id]['auto_fix'] = True
            
            # Move to next screen
            from .notifications import NotificationsScreen
            self.app.push_screen(NotificationsScreen())
