"""
Slack Notifier
Sends bouncer results to Slack
"""

import aiohttp
import logging
from typing import List
from .formatter import NotificationFormatter

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send notifications to Slack"""
    
    def __init__(self, config: dict):
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel', '#bouncer')
        self.min_severity = config.get('min_severity', 'warning')
        self.detail_level = config.get('detail_level', 'summary')
        self.enabled = config.get('enabled', False) and self.webhook_url
        self.formatter = NotificationFormatter(self.detail_level)
    
    async def notify(self, event, results: List):
        """Send notification about bouncer results"""
        if not self.enabled:
            return
        
        # Filter by severity
        if not self._should_notify(results):
            return
        
        # Format data based on detail level
        formatted_data = self.formatter.format(event, results)
        
        # Build Slack message
        message = self._build_message(formatted_data, results)
        
        # Send to Slack
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as resp:
                    if resp.status == 200:
                        logger.debug("✅ Slack notification sent")
                    else:
                        logger.error(f"❌ Slack notification failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Slack notification error: {e}")
    
    def _should_notify(self, results: List) -> bool:
        """Determine if notification should be sent"""
        severity_levels = {
            'info': 0,
            'warning': 1,
            'denied': 2,
            'error': 3
        }
        
        min_level = severity_levels.get(self.min_severity, 1)
        
        for result in results:
            result_level = severity_levels.get(result.status, 0)
            if result_level >= min_level:
                return True
        
        return False
    
    def _build_message(self, event, results: List) -> dict:
        """Build Slack message blocks"""
        # Determine overall status
        statuses = [r.status for r in results]
        
        if 'denied' in statuses:
            overall_emoji = '❌'
            overall_status = 'DENIED'
            color = '#ff0000'
        elif 'warning' in statuses:
            overall_emoji = '⚠️'
            overall_status = 'WARNING'
            color = '#ffaa00'
        elif 'fixed' in statuses:
            overall_emoji = '🔧'
            overall_status = 'FIXED'
            color = '#00aaff'
        else:
            overall_emoji = '✅'
            overall_status = 'APPROVED'
            color = '#00ff00'
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{overall_emoji} Bouncer Report: {overall_status}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*File:*\n`{event.path.name}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Event:*\n{event.event_type}"
                    }
                ]
            }
        ]
        
        # Add results from each bouncer
        for result in results:
            bouncer_emoji = {
                'approved': '✅',
                'denied': '❌',
                'fixed': '🔧',
                'warning': '⚠️'
            }.get(result.status, '❓')
            
            result_text = f"*{bouncer_emoji} {result.bouncer_name}:* {result.status}"
            
            if result.issues_found:
                result_text += f"\n• Issues: {len(result.issues_found)}"
            
            if result.fixes_applied:
                result_text += f"\n• Fixes: {len(result.fixes_applied)}"
            
            if result.messages:
                # Add first message
                result_text += f"\n_{result.messages[0][:100]}_"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": result_text
                }
            })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        return {
            "channel": self.channel,
            "blocks": blocks,
            "attachments": [{
                "color": color,
                "footer": "Bouncer - Quality control at the door",
                "ts": int(event.timestamp)
            }]
        }
