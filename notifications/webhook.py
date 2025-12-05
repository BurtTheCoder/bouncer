"""
Generic Webhook Notifier
Sends bouncer results to any webhook endpoint
"""

import requests
import logging
from .formatter import NotificationFormatter
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Send notifications to generic webhook endpoints"""
    
    def __init__(self, config: Dict[str, Any]):
        self.detail_level = config.get('detail_level', 'summary')
        self.formatter = NotificationFormatter(self.detail_level)
        self.enabled = config.get('enabled', False)
        self.webhook_url = config.get('webhook_url')
        self.method = config.get('method', 'POST').upper()
        self.headers = config.get('headers', {})
        self.min_severity = config.get('min_severity', 'info')
        self.include_timestamp = config.get('include_timestamp', True)
        
        if self.enabled and not self.webhook_url:
            logger.warning("Webhook notifications enabled but no webhook_url provided")
            self.enabled = False
    
    def send(self, result: Dict[str, Any]):
        """Send notification to webhook"""
        if not self.enabled:
            return
        
        # Check severity threshold
        severity = result.get('severity', 'info')
        if not self._should_notify(severity):
            return
        
        try:
            payload = self._create_payload(result)
            
            if self.method == 'POST':
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
            elif self.method == 'PUT':
                response = requests.put(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
            else:
                logger.error(f"Unsupported HTTP method: {self.method}")
                return
            
            response.raise_for_status()
            
            logger.debug(f"📤 Webhook notification sent for {result.get('file_path')}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    def _create_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook payload from result"""
        payload = {
            'bouncer': result.get('bouncer', 'Unknown'),
            'file_path': result.get('file_path', 'Unknown'),
            'severity': result.get('severity', 'info'),
            'action': result.get('action', 'checked'),
            'issues': result.get('issues', []),
            'fixes': result.get('fixes', []),
            'message': result.get('message', '')
        }
        
        if self.include_timestamp:
            payload['timestamp'] = datetime.utcnow().isoformat()
        
        return payload
    
    def _should_notify(self, severity: str) -> bool:
        """Check if severity meets threshold"""
        severity_levels = ['info', 'warning', 'denied', 'error']
        
        try:
            min_level = severity_levels.index(self.min_severity)
            current_level = severity_levels.index(severity)
            return current_level >= min_level
        except ValueError:
            return True
