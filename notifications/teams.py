"""
Microsoft Teams Notifier
Sends bouncer results to Microsoft Teams via webhooks
"""

import aiohttp
import logging
from .formatter import NotificationFormatter
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TeamsNotifier:
    """Send notifications to Microsoft Teams via webhooks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.detail_level = config.get('detail_level', 'summary')
        self.formatter = NotificationFormatter(self.detail_level)
        self.enabled = config.get('enabled', False)
        self.webhook_url = config.get('webhook_url')
        self.min_severity = config.get('min_severity', 'warning')
        
        if self.enabled and not self.webhook_url:
            logger.warning("Teams notifications enabled but no webhook_url provided")
            self.enabled = False
    
    async def send(self, result: Dict[str, Any]):
        """Send notification to Microsoft Teams (async)"""
        if not self.enabled:
            return

        # Check severity threshold
        severity = result.get('severity', 'info')
        if not self._should_notify(severity):
            return

        try:
            card = self._create_adaptive_card(result)
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.webhook_url,
                    json=card
                ) as response:
                    response.raise_for_status()

            logger.debug(f"📤 Teams notification sent for {result.get('file_path')}")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending Teams notification: {e}")
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
    
    def _create_adaptive_card(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create Microsoft Teams Adaptive Card from result"""
        severity = result.get('severity', 'info')
        bouncer = result.get('bouncer', 'Unknown')
        file_path = result.get('file_path', 'Unknown')
        action = result.get('action', 'checked')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Color based on severity
        color_map = {
            'info': 'accent',
            'warning': 'warning',
            'denied': 'attention',
            'error': 'attention',
            'fixed': 'good'
        }
        theme_color = color_map.get(severity, 'default')
        
        # Emoji based on severity
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'denied': '❌',
            'error': '🚨',
            'fixed': '✅'
        }
        emoji = emoji_map.get(severity, '📋')
        
        # Build adaptive card
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "Container",
                                "style": theme_color,
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": f"{emoji} Bouncer Report",
                                        "weight": "bolder",
                                        "size": "large",
                                        "color": "light"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": severity.upper(),
                                        "weight": "bolder",
                                        "color": "light"
                                    }
                                ]
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "⏰ Timestamp:",
                                        "value": timestamp
                                    },
                                    {
                                        "title": "🚪 Bouncer:",
                                        "value": bouncer
                                    },
                                    {
                                        "title": "📁 File:",
                                        "value": file_path
                                    },
                                    {
                                        "title": "🎯 Action:",
                                        "value": action.capitalize()
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        body = card["attachments"][0]["content"]["body"]
        
        # Add issues if present
        issues = result.get('issues', [])
        if issues:
            body.append({
                "type": "TextBlock",
                "text": "🔍 Issues Found",
                "weight": "bolder",
                "spacing": "medium"
            })
            
            issues_text = "\n".join([f"• {issue}" for issue in issues[:5]])
            if len(issues) > 5:
                issues_text += f"\n... and {len(issues) - 5} more"
            
            body.append({
                "type": "TextBlock",
                "text": issues_text,
                "wrap": True,
                "color": "attention"
            })
        
        # Add fixes if present
        fixes = result.get('fixes', [])
        if fixes:
            body.append({
                "type": "TextBlock",
                "text": "🔧 Fixes Applied",
                "weight": "bolder",
                "spacing": "medium"
            })
            
            fixes_text = "\n".join([f"✓ {fix}" for fix in fixes[:5]])
            if len(fixes) > 5:
                fixes_text += f"\n... and {len(fixes) - 5} more"
            
            body.append({
                "type": "TextBlock",
                "text": fixes_text,
                "wrap": True,
                "color": "good"
            })
        
        # Add message if present
        message = result.get('message')
        if message:
            body.append({
                "type": "TextBlock",
                "text": message,
                "wrap": True,
                "spacing": "medium"
            })
        
        return card
    
    def _should_notify(self, severity: str) -> bool:
        """Check if severity meets threshold"""
        severity_levels = ['info', 'warning', 'denied', 'error']
        
        try:
            min_level = severity_levels.index(self.min_severity)
            current_level = severity_levels.index(severity)
            return current_level >= min_level
        except ValueError:
            return True
