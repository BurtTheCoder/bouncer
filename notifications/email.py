"""
Email Notifier
Sends bouncer results via email (SMTP)
"""

import smtplib
import logging
from .formatter import NotificationFormatter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Send notifications via email"""
    
    def __init__(self, config: Dict[str, Any]):
        self.detail_level = config.get('detail_level', 'summary')
        self.formatter = NotificationFormatter(self.detail_level)
        self.enabled = config.get('enabled', False)
        self.smtp_host = config.get('smtp_host')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password')
        self.from_email = config.get('from_email')
        self.to_emails = config.get('to_emails', [])
        self.use_tls = config.get('use_tls', True)
        self.min_severity = config.get('min_severity', 'warning')
        
        if self.enabled:
            if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.from_email]):
                logger.warning("Email notifications enabled but missing required config")
                self.enabled = False
            if not self.to_emails:
                logger.warning("Email notifications enabled but no to_emails provided")
                self.enabled = False
    
    def send(self, result: Dict[str, Any]):
        """Send notification via email"""
        if not self.enabled:
            return
        
        # Check severity threshold
        severity = result.get('severity', 'info')
        if not self._should_notify(severity):
            return
        
        try:
            msg = self._create_email(result)
            
            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.debug(f"📧 Email notification sent for {result.get('file_path')}")
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _create_email(self, result: Dict[str, Any]) -> MIMEMultipart:
        """Create email from result"""
        severity = result.get('severity', 'info')
        bouncer = result.get('bouncer', 'Unknown')
        file_path = result.get('file_path', 'Unknown')
        action = result.get('action', 'checked')
        
        # Emoji based on severity
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'denied': '❌',
            'error': '🚨',
            'fixed': '✅'
        }
        emoji = emoji_map.get(severity, '📋')
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{emoji} Bouncer: {severity.upper()} - {file_path}'
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        
        # Plain text version
        text_content = self._create_text_content(result)
        
        # HTML version
        html_content = self._create_html_content(result)
        
        # Attach both versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        return msg
    
    def _create_text_content(self, result: Dict[str, Any]) -> str:
        """Create plain text email content"""
        severity = result.get('severity', 'info')
        bouncer = result.get('bouncer', 'Unknown')
        file_path = result.get('file_path', 'Unknown')
        action = result.get('action', 'checked')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        content = f"""
Bouncer Report
==============

Timestamp: {timestamp}
Severity: {severity.upper()}
Bouncer: {bouncer}
File: {file_path}
Action: {action}

"""
        
        # Add issues
        issues = result.get('issues', [])
        if issues:
            content += "Issues Found:\n"
            for issue in issues:
                content += f"  • {issue}\n"
            content += "\n"
        
        # Add fixes
        fixes = result.get('fixes', [])
        if fixes:
            content += "Fixes Applied:\n"
            for fix in fixes:
                content += f"  ✓ {fix}\n"
            content += "\n"
        
        # Add message
        message = result.get('message')
        if message:
            content += f"Message:\n{message}\n"
        
        content += "\n---\nSent by Bouncer - Quality control at the door\n"
        
        return content
    
    def _create_html_content(self, result: Dict[str, Any]) -> str:
        """Create HTML email content"""
        severity = result.get('severity', 'info')
        bouncer = result.get('bouncer', 'Unknown')
        file_path = result.get('file_path', 'Unknown')
        action = result.get('action', 'checked')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Color based on severity
        color_map = {
            'info': '#3498db',
            'warning': '#f39c12',
            'denied': '#e74c3c',
            'error': '#c0392b',
            'fixed': '#2ecc71'
        }
        color = color_map.get(severity, '#95a5a6')
        
        html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
        .field {{ margin-bottom: 15px; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .issues, .fixes {{ background-color: white; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        .issue {{ color: #e74c3c; margin: 5px 0; }}
        .fix {{ color: #2ecc71; margin: 5px 0; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🚪 Bouncer Report</h2>
            <p>{severity.upper()}</p>
        </div>
        <div class="content">
            <div class="field">
                <span class="label">⏰ Timestamp:</span>
                <span class="value">{timestamp}</span>
            </div>
            <div class="field">
                <span class="label">🚪 Bouncer:</span>
                <span class="value">{bouncer}</span>
            </div>
            <div class="field">
                <span class="label">📁 File:</span>
                <span class="value"><code>{file_path}</code></span>
            </div>
            <div class="field">
                <span class="label">🎯 Action:</span>
                <span class="value">{action}</span>
            </div>
"""
        
        # Add issues
        issues = result.get('issues', [])
        if issues:
            html += '<div class="issues"><h3>🔍 Issues Found</h3>'
            for issue in issues:
                html += f'<div class="issue">• {issue}</div>'
            html += '</div>'
        
        # Add fixes
        fixes = result.get('fixes', [])
        if fixes:
            html += '<div class="fixes"><h3>🔧 Fixes Applied</h3>'
            for fix in fixes:
                html += f'<div class="fix">✓ {fix}</div>'
            html += '</div>'
        
        # Add message
        message = result.get('message')
        if message:
            html += f'<div class="field" style="margin-top: 15px;"><p>{message}</p></div>'
        
        html += """
        </div>
        <div class="footer">
            Sent by Bouncer - Quality control at the door
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _should_notify(self, severity: str) -> bool:
        """Check if severity meets threshold"""
        severity_levels = ['info', 'warning', 'denied', 'error']
        
        try:
            min_level = severity_levels.index(self.min_severity)
            current_level = severity_levels.index(severity)
            return current_level >= min_level
        except ValueError:
            return True
