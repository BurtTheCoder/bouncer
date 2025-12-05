"""
Documentation Bouncer
Checks documentation files for quality and completeness
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class DocumentationBouncer(BaseBouncer):
    """
    Documentation bouncer - checks docs for:
    - Broken links
    - Spelling and grammar
    - Clarity and completeness
    - Code example accuracy
    - Formatting consistency
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.checks = config.get('checks', ['links', 'spelling', 'formatting'])
    
    async def check(self, event):
        """Check documentation quality"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        logger.info(f"📚 Docs Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            structured_output=BOUNCER_OUTPUT_SCHEMA,
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
            logger.error(f"Error in Docs Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during docs check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for documentation checking"""
        return f"""
You are a Documentation Bouncer - a technical writing expert.

Your job:
1. Read the documentation file that changed
2. Check for quality issues: {', '.join(self.checks)}
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure documentation is clear and helpful

Quality standards:
- No broken links
- Correct spelling and grammar
- Clear, concise writing
- Accurate code examples
- Consistent formatting
- Proper structure (headings, lists, etc.)

When you find issues:
- Describe each issue clearly
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Prioritize readability and accuracy

Be helpful and constructive.
"""
    
    def _build_prompt(self, event) -> str:
        """Build documentation check prompt"""
        return f"""
Documentation file changed: {event.path.name}
Event type: {event.event_type}

Please review this documentation for quality issues.

Checks to perform: {', '.join(self.checks)}
Auto-fix enabled: {self.auto_fix}

Provide a report of:
1. Issues found (broken links, spelling errors, unclear sections, etc.)
2. Fixes applied (if auto-fix is enabled)
3. Suggestions for improvement

Focus on making the documentation clear and helpful.
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse documentation check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'issue', 'error', 'broken', 'unclear', 'fix'
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
