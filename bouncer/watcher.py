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

logger = logging.getLogger(__name__)


class FileWatcher:
    """
    Watches directory for file changes
    Debounces rapid changes and queues events for processing
    """
    
    def __init__(self, watch_dir: Path, orchestrator):
        self.watch_dir = watch_dir
        self.orchestrator = orchestrator
        self.pending_changes = {}  # path -> timestamp
        self.debounce_delay = 2.0  # seconds
    
    async def start(self):
        """Start watching the directory"""
        from .core import FileChangeEvent
        
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, watcher):
                self.watcher = watcher
            
            def on_modified(self, event):
                if not event.is_directory:
                    self._handle_change(event.src_path, 'modified')
            
            def on_created(self, event):
                if not event.is_directory:
                    self._handle_change(event.src_path, 'created')
            
            def on_deleted(self, event):
                if not event.is_directory:
                    self._handle_change(event.src_path, 'deleted')
            
            def _handle_change(self, path_str: str, event_type: str):
                path = Path(path_str)
                
                # Ignore certain files
                if self.watcher.orchestrator.should_ignore(path):
                    return
                
                # Update pending changes
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
                await asyncio.sleep(0.5)
                
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
                    await self.orchestrator.event_queue.put(event)
                    logger.debug(f"📬 Queued: {path.name}")
        
        finally:
            observer.stop()
            observer.join()
            logger.info("👁️  File watcher stopped")
