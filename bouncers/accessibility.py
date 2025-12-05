"""
Accessibility Bouncer
Checks files for accessibility issues (WCAG compliance)
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class AccessibilityBouncer(BaseBouncer):
    """
    Accessibility bouncer - checks for:
    - Missing alt text on images
    - Color contrast issues
    - ARIA labels and roles
    - Keyboard navigation support
    - Screen reader compatibility
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.wcag_level = config.get('wcag_level', 'AA')  # A, AA, or AAA
    
    async def check(self, event):
        """Check for accessibility issues"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        
        logger.info(f"♿ Accessibility Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            allowed_tools=["Read", "Write"],
            permission_mode="acceptEdits" if self.auto_fix else "plan",
            system_prompt=self._get_system_prompt()
        )
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                prompt = self._build_prompt(event)
                await client.query(prompt)
                
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text  # Only keep last message (structured JSON)
                
                result_data = self._parse_response(response_text)
                status = self._determine_status(result_data)
                
                return self._create_result(
                    event=event,
                    status=status,
                    issues_found=result_data.get('issues', []),
                    fixes_applied=result_data.get('fixes', []),
                    messages=result_data.get('messages', [])
                )
        
        except Exception as e:
            logger.error(f"Error in Accessibility Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during accessibility check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for accessibility checking"""
        return f"""
You are an Accessibility Bouncer - a WCAG compliance expert.

Your job:
1. Read the file that changed (HTML, JSX, Vue, etc.)
2. Check for accessibility issues
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure WCAG {self.wcag_level} compliance

Accessibility checks:
- Missing alt text on images
- Missing ARIA labels and roles
- Insufficient color contrast
- Missing form labels
- Keyboard navigation issues
- Missing skip links
- Improper heading hierarchy
- Missing lang attribute
- Inaccessible interactive elements

WCAG {self.wcag_level} requirements:
- Level A: Basic accessibility
- Level AA: Recommended standard (4.5:1 contrast)
- Level AAA: Enhanced accessibility (7:1 contrast)

When you find issues:
- Describe the accessibility impact
- Reference WCAG guidelines
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Consider screen reader users

Make the web accessible for everyone.
"""
    
    def _build_prompt(self, event) -> str:
        """Build accessibility check prompt"""
        return f"""
File changed: {event.path.name}
Event type: {event.event_type}

Please review this file for accessibility issues.

WCAG Level: {self.wcag_level}
Auto-fix enabled: {self.auto_fix}

Check for:
1. Missing alt text on images
2. Missing ARIA labels
3. Color contrast issues
4. Keyboard navigation support
5. Form accessibility
6. Semantic HTML usage

Provide a report of:
1. Issues found (with WCAG reference)
2. Fixes applied (if auto-fix is enabled)
3. Recommendations for improvement
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse accessibility check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'accessibility', 'wcag', 'aria', 'alt', 'contrast'
            ])
            
            return {
                'status': 'issues_found' if has_issues else 'clean',
                'issues': [],
                'fixes': [],
                'messages': [response_text]
            }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine status from result data"""
        status = result_data.get('status', 'clean')
        
        if status == 'clean':
            return 'approved'
        elif status == 'fixed':
            return 'fixed'
        else:
            return 'warning' if self.auto_fix else 'denied'
