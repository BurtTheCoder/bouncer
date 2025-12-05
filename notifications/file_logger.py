"""
File Logger Notifier
Logs bouncer results to JSON files
"""

import json
import logging
from .formatter import NotificationFormatter
from pathlib import Path
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


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
        
        # Append to log
        try:
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())
            
            logs.append(log_entry)
            
            log_file.write_text(json.dumps(logs, indent=2))
            logger.debug(f"📝 Logged to: {log_file}")
        
        except Exception as e:
            logger.error(f"❌ Failed to write log: {e}")
    
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
