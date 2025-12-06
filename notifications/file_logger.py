"""
File Logger Notifier
Logs bouncer results to JSON files
"""

import json
import logging
import asyncio
import sys
from contextlib import contextmanager
from .formatter import NotificationFormatter
from pathlib import Path
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

# Cross-platform file locking
if sys.platform == 'win32':
    import msvcrt

    @contextmanager
    def file_lock(f):
        """Windows file locking using msvcrt"""
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            yield
        finally:
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
else:
    import fcntl

    @contextmanager
    def file_lock(f):
        """Unix file locking using fcntl"""
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class FileLoggerNotifier:
    """Log bouncer results to JSON files"""
    
    def __init__(self, config: dict):
        self.log_dir = Path(config.get('log_dir', '.bouncer/logs'))
        self.rotation = config.get('rotation', 'daily')
        self.detail_level = config.get('detail_level', 'summary')
        self.formatter = NotificationFormatter(self.detail_level)
        self.enabled = config.get('enabled', True)
        
        # Create log directory
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    async def notify(self, event, results: List):
        """Log results to file"""
        if not self.enabled:
            return
        
        # Build log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file": str(event.path),
            "event_type": event.event_type,
            "results": []
        }
        
        for result in results:
            log_entry["results"].append({
                "bouncer": result.bouncer_name,
                "status": result.status,
                "issues_found": len(result.issues_found),
                "fixes_applied": len(result.fixes_applied),
                "issues": result.issues_found,
                "fixes": result.fixes_applied,
                "messages": result.messages
            })
        
        # Determine log file based on rotation
        log_file = self._get_log_file()

        # Append to log with file locking to prevent race conditions
        try:
            await self._write_log_entry_safe(log_file, log_entry)
            logger.debug(f"📝 Logged to: {log_file}")

        except Exception as e:
            logger.error(f"❌ Failed to write log: {e}")

    async def _write_log_entry_safe(self, log_file: Path, log_entry: dict):
        """Write log entry with proper file locking to prevent race conditions"""
        def _write_with_lock():
            # Open file in read-write mode, create if doesn't exist
            with open(log_file, 'a+') as f:
                # Acquire exclusive lock using cross-platform context manager
                with file_lock(f):
                    # Move to beginning to read existing content
                    f.seek(0)
                    content = f.read()

                    # Parse existing logs or start with empty list
                    if content.strip():
                        try:
                            logs = json.loads(content)
                        except json.JSONDecodeError:
                            logger.warning(f"Corrupted log file, starting fresh: {log_file}")
                            logs = []
                    else:
                        logs = []

                    # Append new entry
                    logs.append(log_entry)

                    # Truncate and write updated content
                    f.seek(0)
                    f.truncate()
                    f.write(json.dumps(logs, indent=2))
                    f.flush()

        # Run blocking I/O in thread pool
        await asyncio.to_thread(_write_with_lock)
    
    def _get_log_file(self) -> Path:
        """Get log file path based on rotation"""
        if self.rotation == 'daily':
            filename = f"{datetime.now():%Y-%m-%d}.json"
        elif self.rotation == 'weekly':
            filename = f"{datetime.now():%Y-W%W}.json"
        elif self.rotation == 'monthly':
            filename = f"{datetime.now():%Y-%m}.json"
        else:
            filename = "bouncer.json"
        
        return self.log_dir / filename
