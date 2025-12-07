"""
Directory Selection Screen
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Input, Label, DirectoryTree
from textual.containers import Container, Vertical, Horizontal
from pathlib import Path


class DirectoryScreen(Screen):
    """Screen for selecting the directory to watch"""
    
    def compose(self) -> ComposeResult:
        """Create directory selection widgets"""
        with Container(classes="content-container"):
            yield Static(
                "[bold cyan]Step 1 of 12:[/bold cyan] Select Directory to Watch",
                classes="section-title"
            )
            yield Static(
                "Choose the directory where Bouncer will monitor files.\n"
                "This is typically your project root directory.",
                classes="help-text"
            )

            yield Label("Directory Path:")
            yield Input(
                placeholder="/path/to/your/project",
                value=str(Path.cwd()),
                id="directory-input"
            )

            yield Label("\nBrowse Directories:")
            yield DirectoryTree(str(Path.home()), id="directory-tree")

            with Horizontal(classes="nav-buttons"):
                yield Button("← Back", variant="default", id="back")
                yield Button("Continue →", variant="primary", id="continue")
    
    def on_mount(self) -> None:
        """Initialize with current directory or saved config"""
        app = self.app
        saved_dir = app.get_config_value('watch_dir')
        if saved_dir:
            input_widget = self.query_one("#directory-input", Input)
            input_widget.value = saved_dir
    
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Update input when directory is selected from tree"""
        input_widget = self.query_one("#directory-input", Input)
        input_widget.value = str(event.path)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back":
            self.app.pop_screen()
        
        elif event.button.id == "continue":
            # Get selected directory
            input_widget = self.query_one("#directory-input", Input)
            directory = input_widget.value.strip()
            
            # Validate directory
            if not directory:
                self.app.notify(
                    "Please enter a directory path",
                    severity="warning"
                )
                return
            
            dir_path = Path(directory)
            if not dir_path.exists():
                self.app.notify(
                    f"Directory does not exist: {directory}",
                    severity="error"
                )
                return
            
            if not dir_path.is_dir():
                self.app.notify(
                    f"Path is not a directory: {directory}",
                    severity="error"
                )
                return
            
            # Save to config
            self.app.set_config_value('watch_dir', str(dir_path.absolute()))

            # Move to watcher settings screen
            from .watcher import WatcherScreen
            self.app.push_screen(WatcherScreen())
