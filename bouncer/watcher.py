"""
File watcher for Bouncer
Monitors directory for file changes and queues events
"""

import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_PENDING_CHANGES = 10000
DEFAULT_DEBOUNCE_DELAY = 2.0
DEFAULT_POLL_INTERVAL = 0.5


class FileWatcher:
    """
    Watches directory for file changes
    Debounces rapid changes and queues events for processing
    """

    def __init__(self, watch_dir: Path, orchestrator):
        self.watch_dir = watch_dir
        self.orchestrator = orchestrator
        # Use OrderedDict to maintain insertion order for LRU eviction
        self.pending_changes: OrderedDict = OrderedDict()
        self.debounce_delay = orchestrator.config.get('debounce_delay', DEFAULT_DEBOUNCE_DELAY)
        self.poll_interval = orchestrator.config.get('poll_interval', DEFAULT_POLL_INTERVAL)
        # Max pending changes to prevent unbounded memory growth
        self.max_pending_changes = orchestrator.config.get('max_pending_changes', DEFAULT_MAX_PENDING_CHANGES)
    
    async def start(self):
        """Start watching the directory"""
        from .core import FileChangeEvent
        
        class ChangeHandler(FileSystemEventHandler):
            """Handles file system events from watchdog"""
            
            def __init__(self, watcher):
                self.watcher = watcher
            
            def on_modified(self, event):
                """Handle file modification events"""
                if not event.is_directory:
                    self._handle_change(event.src_path, 'modified')
            
            def on_created(self, event):
                """Handle file creation events"""
                if not event.is_directory:
                    self._handle_change(event.src_path, 'created')
            
            def on_deleted(self, event):
                """Handle file deletion events"""
                if not event.is_directory:
                    self._handle_change(event.src_path, 'deleted')
            
            def _handle_change(self, path_str: str, event_type: str):
                path = Path(path_str)

                # Ignore certain files
                if self.watcher.orchestrator.should_ignore(path):
                    return

                # Check if we've exceeded max pending changes
                if len(self.watcher.pending_changes) >= self.watcher.max_pending_changes:
                    # Evict oldest entries (first 10% of max)
                    evict_count = self.watcher.max_pending_changes // 10
                    for _ in range(evict_count):
                        if self.watcher.pending_changes:
                            oldest_key = next(iter(self.watcher.pending_changes))
                            del self.watcher.pending_changes[oldest_key]
                            logger.warning(f"Evicted pending change due to overflow: {oldest_key}")

                # Update pending changes (move to end if already exists)
                if path in self.watcher.pending_changes:
                    self.watcher.pending_changes.move_to_end(path)
                self.watcher.pending_changes[path] = {
                    'timestamp': time.time(),
                    'event_type': event_type
                }
        
        # Start watchdog observer
        event_handler = ChangeHandler(self)
        observer = Observer()
        observer.schedule(
            event_handler,
            str(self.watch_dir),
            recursive=True
        )
        observer.start()
        
        logger.info(f"👁️  File watcher started")
        
        # Debounce loop
        try:
            while self.orchestrator.running:
                await asyncio.sleep(self.poll_interval)

                current_time = time.time()
                to_process = []

                # Find changes that have settled
                for path, info in list(self.pending_changes.items()):
                    if current_time - info['timestamp'] >= self.debounce_delay:
                        to_process.append((path, info))
                        del self.pending_changes[path]

                # Queue settled changes
                for path, info in to_process:
                    event = FileChangeEvent(
                        path=path,
                        event_type=info['event_type'],
                        timestamp=info['timestamp']
                    )
                    try:
                        # Use put_nowait with fallback to avoid blocking indefinitely
                        self.orchestrator.event_queue.put_nowait(event)
                        logger.debug(f"📬 Queued: {path.name}")
                    except asyncio.QueueFull:
                        logger.warning(f"Event queue full, dropping event for: {path.name}")
        
        finally:
            observer.stop()
            observer.join()
            logger.info("👁️  File watcher stopped")
