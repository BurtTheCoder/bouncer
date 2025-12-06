"""
Bouncer - Quality control at the door
Core orchestrator that manages file watching and bouncer coordination
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Constants for queue size limits
DEFAULT_EVENT_QUEUE_SIZE = 1000
DEFAULT_RESULTS_QUEUE_SIZE = 1000


@dataclass
class FileChangeEvent:
    """Represents a file change event"""
    path: Path
    event_type: str  # 'created', 'modified', 'deleted'
    timestamp: float
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class BouncerResult:
    """Result from a bouncer check (immutable)"""
    bouncer_name: str
    file_path: Path
    status: str  # 'approved', 'denied', 'fixed', 'warning'
    issues_found: tuple  # Using tuple for immutability
    fixes_applied: tuple  # Using tuple for immutability
    messages: tuple  # Using tuple for immutability
    timestamp: float


class BouncerOrchestrator:
    """
    Main Bouncer orchestrator
    
    Manages:
    - File watching
    - Routing to specialized bouncers
    - Aggregating results
    - Sending notifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.watch_dir = Path(config['watch_dir']).resolve()

        # Initialize path validation with allowed directories for security
        try:
            from checks.tools import set_allowed_directories
            set_allowed_directories([self.watch_dir])
            logger.debug(f"🔒 Path validation initialized for: {self.watch_dir}")
        except ImportError:
            logger.debug("Path validation not available (checks.tools not found)")

        # Add queue size limits to prevent unbounded memory growth
        event_queue_size = config.get('event_queue_size', DEFAULT_EVENT_QUEUE_SIZE)
        results_queue_size = config.get('results_queue_size', DEFAULT_RESULTS_QUEUE_SIZE)
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=event_queue_size)
        self.results_queue: asyncio.Queue = asyncio.Queue(maxsize=results_queue_size)
        self.bouncers: Dict[str, Any] = {}
        self.notifiers: List[Any] = []
        self.running = False
        self.mcp_manager = None
        self.integration_actions = None
        
        # Initialize MCP integrations if configured
        integrations_config = config.get('integrations', {})
        if integrations_config:
            try:
                from integrations import MCPManager, IntegrationActions
                self.mcp_manager = MCPManager(integrations_config)
                self.integration_actions = IntegrationActions(
                    self.mcp_manager,
                    self.watch_dir
                )
                logger.info("✅ MCP integrations initialized")
                
                # Validate credentials
                missing = self.mcp_manager.get_missing_credentials()
                if missing:
                    logger.warning(f"⚠️  Missing credentials for: {', '.join(missing)}")
            except ImportError:
                logger.warning("⚠️  MCP integrations not available (missing dependencies)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize MCP integrations: {e}")
        
        logger.info(f"🚪 Bouncer initialized for: {self.watch_dir}")
    
    def register_bouncer(self, name: str, bouncer):
        """Register a specialized bouncer"""
        self.bouncers[name] = bouncer
        logger.info(f"✅ Registered bouncer: {name}")
    
    def register_notifier(self, notifier):
        """Register a notification handler"""
        self.notifiers.append(notifier)
        logger.info(f"✅ Registered notifier: {notifier.__class__.__name__}")
    
    async def process_event(self, event: FileChangeEvent) -> List[BouncerResult]:
        """
        Process a file change event through applicable bouncers
        
        Returns list of results from all bouncers that checked the file
        """
        logger.info(f"📝 Processing: {event.path.name} ({event.event_type})")
        
        results = []
        
        # Route to applicable bouncers
        for bouncer_name, bouncer in self.bouncers.items():
            if await bouncer.should_check(event):
                logger.info(f"  → Checking with {bouncer_name}")
                
                try:
                    result = await bouncer.check(event)
                    results.append(result)
                    
                    # Log result
                    status_emoji = {
                        'approved': '✅',
                        'denied': '❌',
                        'fixed': '🔧',
                        'warning': '⚠️'
                    }
                    emoji = status_emoji.get(result.status, '❓')
                    logger.info(f"  {emoji} {bouncer_name}: {result.status}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error in {bouncer_name}: {e}")
        
        # Send notifications
        await self._notify(event, results)
        
        # Handle MCP integrations (create PRs/issues if configured)
        if self.integration_actions:
            await self._handle_integrations(results)
        
        return results
    
    async def _notify(self, event: FileChangeEvent, results: List[BouncerResult]):
        """Send notifications about bouncer results"""
        for notifier in self.notifiers:
            try:
                await notifier.notify(event, results)
            except Exception as e:
                logger.error(f"Notification error: {e}")
    
    async def _handle_integrations(self, results: List[BouncerResult]):
        """Handle MCP integrations (create PRs/issues based on results)"""
        if not self.integration_actions or not self.mcp_manager:
            return
        
        for result in results:
            # Skip if no issues or fixes
            if not result.issues_found and not result.fixes_applied:
                continue
            
            try:
                # Check if GitHub integration is enabled
                if self.mcp_manager.is_integration_enabled('github'):
                    github_config = self.mcp_manager.get_integration_config('github')
                    
                    # Create PR if fixes were applied and auto_create_pr is enabled
                    if result.fixes_applied and github_config.get('auto_create_pr', False):
                        logger.info(f"🔗 Creating GitHub PR for {result.bouncer_name} fixes...")
                        pr_result = await self.integration_actions.create_github_pr(
                            result,
                            auto_create=True
                        )
                        if pr_result.get('success'):
                            logger.info(f"✅ PR created: {pr_result.get('pr_url')}")
                        else:
                            logger.error(f"❌ PR creation failed: {pr_result.get('error')}")
                    
                    # Create issue if problems found and auto_create_issue is enabled
                    if result.issues_found and github_config.get('auto_create_issue', False):
                        logger.info(f"🔗 Creating GitHub issue for {result.bouncer_name} findings...")
                        issue_result = await self.integration_actions.create_github_issue(
                            result,
                            auto_create=True
                        )
                        if issue_result.get('success'):
                            logger.info(f"✅ Issue created: {issue_result.get('issue_url')}")
                        else:
                            logger.error(f"❌ Issue creation failed: {issue_result.get('error')}")
                
                # Check if Linear integration is enabled
                if self.mcp_manager.is_integration_enabled('linear'):
                    linear_config = self.mcp_manager.get_integration_config('linear')
                    
                    # Create Linear issue if auto_create_issue is enabled
                    if result.issues_found and linear_config.get('auto_create_issue', False):
                        logger.info(f"🔗 Creating Linear issue for {result.bouncer_name} findings...")
                        linear_result = await self.integration_actions.create_linear_issue(
                            result,
                            auto_create=True
                        )
                        if linear_result.get('success'):
                            logger.info(f"✅ Linear issue created: {linear_result.get('issue_url')}")
                        else:
                            logger.error(f"❌ Linear issue creation failed: {linear_result.get('error')}")
                
            except Exception as e:
                logger.error(f"❌ Integration error for {result.bouncer_name}: {e}")
    
    async def event_processor_loop(self):
        """Main loop that processes events from queue"""
        logger.info("🔄 Event processor started")
        
        while self.running:
            try:
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                results = await self.process_event(event)
                await self.results_queue.put((event, results))
                self.event_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")
    
    def should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = self.config.get('ignore_patterns', [
            '.git', 'node_modules', '__pycache__', '.pyc',
            'venv', '.env', '.bouncer'
        ])
        
        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)
    
    async def start(self):
        """Start the bouncer"""
        self.running = True
        logger.info("🚪 Bouncer is now on duty!")
        logger.info(f"👀 Watching: {self.watch_dir}")
        logger.info(f"🎯 Active bouncers: {', '.join(self.bouncers.keys())}")
        
        # Start event processor
        processor_task = asyncio.create_task(self.event_processor_loop())
        
        # Start file watcher
        from .watcher import FileWatcher
        watcher = FileWatcher(self.watch_dir, self)
        watcher_task = asyncio.create_task(watcher.start())
        
        # Wait for tasks
        await asyncio.gather(processor_task, watcher_task)
    
    async def stop(self):
        """Stop the bouncer"""
        logger.info("🛑 Bouncer stopping...")
        self.running = False
        await asyncio.sleep(1)  # Allow cleanup
        logger.info("👋 Bouncer stopped")

    async def scan(self, target_dir: Path, git_diff: bool = False, since: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan a directory in batch mode
        
        Args:
            target_dir: Directory to scan
            git_diff: If True, only scan files in git diff
            since: Time window for git diff (e.g., "1 hour ago", "24 hours ago")
        
        Returns:
            Dictionary with scan results and summary
        """
        logger.info("🔍 Starting batch scan...")
        logger.info(f"📁 Target: {target_dir}")
        logger.info(f"🎯 Active bouncers: {', '.join(self.bouncers.keys())}")
        
        # Get files to scan
        if git_diff:
            logger.info(f"📊 Mode: Incremental (git diff since {since or 'last commit'})")
            files = await self._get_git_changed_files(target_dir, since)
        else:
            logger.info("📊 Mode: Full scan")
            files = await self._get_all_files(target_dir)
        
        if not files:
            logger.info("✅ No files to scan")
            return {
                'status': 'success',
                'files_scanned': 0,
                'issues_found': 0,
                'fixes_applied': 0,
                'results': []
            }
        
        logger.info(f"📝 Found {len(files)} files to scan")
        
        # Process each file
        all_results = []
        total_issues = 0
        total_fixes = 0
        
        for file_path in files:
            # Create a file change event
            event = FileChangeEvent(
                path=file_path,
                event_type='modified',
                timestamp=datetime.now().timestamp(),
                metadata={'scan_mode': 'batch'}
            )
            
            # Process through bouncers
            results = await self.process_event(event)
            all_results.extend(results)
            
            # Count issues and fixes
            for result in results:
                total_issues += len(result.issues_found)
                total_fixes += len(result.fixes_applied)
        
        # Generate summary
        summary = {
            'status': 'success',
            'files_scanned': len(files),
            'issues_found': total_issues,
            'fixes_applied': total_fixes,
            'results': all_results
        }
        
        logger.info("✅ Scan complete!")
        logger.info(f"📊 Files scanned: {len(files)}")
        logger.info(f"⚠️  Issues found: {total_issues}")
        logger.info(f"🔧 Fixes applied: {total_fixes}")
        
        return summary
    
    async def _get_all_files(self, target_dir: Path) -> List[Path]:
        """Get all files in directory (excluding ignored patterns) - async version"""
        # Use asyncio.to_thread to avoid blocking the event loop for large directories
        def _scan_directory():
            files = []
            for path in target_dir.rglob('*'):
                if path.is_file() and not self.should_ignore(path):
                    files.append(path)
            return files

        return await asyncio.to_thread(_scan_directory)

    @staticmethod
    def _validate_git_since_param(since: str) -> bool:
        """
        Validate the 'since' parameter to prevent command injection.

        Allows patterns like:
        - "1 hour ago"
        - "24 hours ago"
        - "2 days ago"
        - "1 week ago"
        - "2023-01-01"
        - "yesterday"
        """
        if not since:
            return False

        # Define allowed patterns
        allowed_patterns = [
            r'^\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago$',  # "N units ago"
            r'^yesterday$',
            r'^today$',
            r'^\d{4}-\d{2}-\d{2}$',  # ISO date format
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(:\d{2})?$',  # ISO datetime format
        ]

        for pattern in allowed_patterns:
            if re.match(pattern, since.strip(), re.IGNORECASE):
                return True

        return False

    async def _get_git_changed_files(self, target_dir: Path, since: Optional[str] = None) -> List[Path]:
        """Get files changed in git since a specific time"""
        import subprocess

        try:
            # Validate and sanitize 'since' parameter to prevent command injection
            if since:
                if not self._validate_git_since_param(since):
                    logger.error(f"Invalid 'since' parameter format: {since}")
                    logger.warning("Falling back to full scan")
                    return await self._get_all_files(target_dir)
                # Use a safer git log approach instead of @{} syntax
                cmd = ['git', '-C', str(target_dir), 'log', '--name-only', '--pretty=format:', f'--since={since}']
            else:
                # Get files changed since last commit
                cmd = ['git', '-C', str(target_dir), 'diff', '--name-only', 'HEAD~1', 'HEAD']

            # Run git command in a thread to avoid blocking
            def _run_git():
                return subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60  # Add timeout for safety
                )

            result = await asyncio.to_thread(_run_git)

            # Parse output
            files = []
            seen = set()  # Deduplicate file paths
            for line in result.stdout.strip().split('\n'):
                if line and line not in seen:
                    seen.add(line)
                    file_path = target_dir / line.strip()
                    if file_path.exists() and file_path.is_file() and not self.should_ignore(file_path):
                        files.append(file_path)

            return files

        except subprocess.TimeoutExpired:
            logger.error("Git command timed out")
            logger.warning("Falling back to full scan")
            return await self._get_all_files(target_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            logger.warning("Falling back to full scan")
            return await self._get_all_files(target_dir)
        except Exception as e:
            logger.error(f"Error getting git changed files: {e}")
            logger.warning("Falling back to full scan")
            return await self._get_all_files(target_dir)
