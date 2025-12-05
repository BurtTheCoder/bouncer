"""
License & Legal Bouncer
Checks files for license compliance and legal issues
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class LicenseBouncer(BaseBouncer):
    """
    License bouncer - checks for:
    - Missing copyright headers
    - License compatibility issues
    - Dependency license conflicts
    - GDPR/privacy compliance
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.project_license = config.get('project_license', 'MIT')
        self.require_headers = config.get('require_headers', True)
    
    async def check(self, event):
        """Check for license and legal issues"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        logger.info(f"⚖️  License Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent,
            structured_output=BOUNCER_OUTPUT_SCHEMA),
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
            logger.error(f"Error in License Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during license check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for license checking"""
        return f"""
You are a License & Legal Bouncer - a licensing compliance expert.

Your job:
1. Read the file that changed
2. Check for license and legal issues
3. {'Add copyright headers when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure license compliance

License checks:
- Missing copyright headers (required: {self.require_headers})
- Incompatible licenses in dependencies
- GPL contamination in non-GPL projects
- Missing license attribution
- GDPR/privacy compliance issues
- Personal data handling in code

Project license: {self.project_license}

Compatible licenses with {self.project_license}:
- MIT: Compatible with most licenses
- Apache-2.0: Compatible with most, requires attribution
- BSD: Compatible with most licenses
- GPL: Only compatible with GPL (copyleft)

When you find issues:
- Describe the legal risk
- Reference license terms
- {'Add headers if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Suggest compatible alternatives

Protect the project from legal issues.
"""
    
    def _build_prompt(self, event) -> str:
        """Build license check prompt"""
        return f"""
File changed: {event.path.name}
Event type: {event.event_type}

Please review this file for license and legal issues.

Project license: {self.project_license}
Require copyright headers: {self.require_headers}
Auto-fix enabled: {self.auto_fix}

Check for:
1. Missing copyright headers
2. License compatibility issues
3. Dependency license conflicts
4. GDPR/privacy compliance
5. Personal data handling

Provide a report of:
1. Issues found (with legal risk level)
2. Fixes applied (if auto-fix is enabled)
3. Recommendations for compliance
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse license check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'license', 'copyright', 'legal', 'gpl', 'compliance'
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
            return 'warning'
