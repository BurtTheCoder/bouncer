"""
Discord Notifier
Sends bouncer results to Discord via webhooks
"""

import aiohttp
import logging
from .formatter import NotificationFormatter
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Send notifications to Discord via webhooks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.detail_level = config.get('detail_level', 'summary')
        self.formatter = NotificationFormatter(self.detail_level)
        self.enabled = config.get('enabled', False)
        self.webhook_url = config.get('webhook_url')
        self.username = config.get('username', 'Bouncer')
        self.min_severity = config.get('min_severity', 'warning')
        
        if self.enabled and not self.webhook_url:
            logger.warning("Discord notifications enabled but no webhook_url provided")
            self.enabled = False
    
    async def send(self, result: Dict[str, Any]):
        """Send notification to Discord (async)"""
        if not self.enabled:
            return

        # Check severity threshold
        severity = result.get('severity', 'info')
        if not self._should_notify(severity):
            return

        try:
            embed = self._create_embed(result)
            payload = {
                'username': self.username,
                'embeds': [embed]
            }
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as response:
                    response.raise_for_status()

            logger.debug(f"📤 Discord notification sent for {result.get('file_path')}")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending Discord notification: {e}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    def _create_embed(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create Discord embed from result"""
        severity = result.get('severity', 'info')
        bouncer = result.get('bouncer', 'Unknown')
        file_path = result.get('file_path', 'Unknown')
        action = result.get('action', 'checked')
        
        # Color based on severity
        color_map = {
            'info': 0x3498db,      # Blue
            'warning': 0xf39c12,   # Orange
            'denied': 0xe74c3c,    # Red
            'error': 0xc0392b,     # Dark red
            'fixed': 0x2ecc71      # Green
        }
        color = color_map.get(severity, 0x95a5a6)
        
        # Emoji based on severity
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'denied': '❌',
            'error': '🚨',
            'fixed': '✅'
        }
        emoji = emoji_map.get(severity, '📋')
        
        embed = {
            'title': f'{emoji} Bouncer Report',
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'fields': [
                {
                    'name': '🚪 Bouncer',
                    'value': bouncer,
                    'inline': True
                },
                {
                    'name': '📁 File',
                    'value': f'`{file_path}`',
                    'inline': True
                },
                {
                    'name': '🎯 Action',
                    'value': action.capitalize(),
                    'inline': True
                }
            ]
        }
        
        # Add issues if present
        issues = result.get('issues', [])
        if issues:
            issues_text = '\n'.join([f"• {issue}" for issue in issues[:5]])
            if len(issues) > 5:
                issues_text += f"\n... and {len(issues) - 5} more"
            embed['fields'].append({
                'name': '🔍 Issues Found',
                'value': issues_text,
                'inline': False
            })
        
        # Add fixes if present
        fixes = result.get('fixes', [])
        if fixes:
            fixes_text = '\n'.join([f"✓ {fix}" for fix in fixes[:5]])
            if len(fixes) > 5:
                fixes_text += f"\n... and {len(fixes) - 5} more"
            embed['fields'].append({
                'name': '🔧 Fixes Applied',
                'value': fixes_text,
                'inline': False
            })
        
        # Add message if present
        message = result.get('message')
        if message:
            embed['description'] = message
        
        return embed
    
    def _should_notify(self, severity: str) -> bool:
        """Check if severity meets threshold"""
        severity_levels = ['info', 'warning', 'denied', 'error']
        
        try:
            min_level = severity_levels.index(self.min_severity)
            current_level = severity_levels.index(severity)
            return current_level >= min_level
        except ValueError:
            return True
