"""
Bouncer - Quality control at the door
Core orchestrator that manages file watching and bouncer coordination
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileChangeEvent:
    """Represents a file change event"""
    path: Path
    event_type: str  # 'created', 'modified', 'deleted'
    timestamp: float
    metadata: Dict[str, Any] = None


@dataclass
class BouncerResult:
    """Result from a bouncer check"""
    bouncer_name: str
    file_path: Path
    status: str  # 'approved', 'denied', 'fixed', 'warning'
    issues_found: List[Dict[str, Any]]
    fixes_applied: List[Dict[str, Any]]
    messages: List[str]
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
        self.watch_dir = Path(config['watch_dir'])
        self.event_queue = asyncio.Queue()
        self.results_queue = asyncio.Queue()
        self.bouncers = {}
        self.notifiers = []
        self.running = False
        
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
        
        return results
    
    async def _notify(self, event: FileChangeEvent, results: List[BouncerResult]):
        """Send notifications about bouncer results"""
        for notifier in self.notifiers:
            try:
                await notifier.notify(event, results)
            except Exception as e:
                logger.error(f"Notification error: {e}")
    
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
