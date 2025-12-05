"""
Code Quality Bouncer
Checks code files for quality issues using Claude Agent SDK
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class CodeQualityBouncer(BaseBouncer):
    """
    Code quality bouncer - checks code for:
    - Syntax errors
    - Linting issues
    - Formatting problems
    - Best practices
    - Code complexity
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.checks = config.get('checks', ['syntax', 'linting', 'formatting'])
    
    async def check(self, event):
        """Check code quality using Claude Agent SDK"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        
        logger.info(f"👔 Code Bouncer checking: {event.path.name}")
        
        # Configure Claude SDK with subagent
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            allowed_tools=["Read", "Write", "Bash"],
            permission_mode="acceptEdits" if self.auto_fix else "plan",
            system_prompt=self._get_system_prompt(),
            structured_output=self._get_output_schema()
        )
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                # Build prompt
                prompt = self._build_prompt(event)
                
                # Query the agent
                await client.query(prompt)
                
                # Collect response
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text  # Only keep last message (structured JSON)
                
                # Parse response
                result_data = self._parse_response(response_text)
                
                # Determine status
                status = self._determine_status(result_data)
                
                return self._create_result(
                    event=event,
                    status=status,
                    issues_found=result_data.get('issues', []),
                    fixes_applied=result_data.get('fixes', []),
                    messages=result_data.get('messages', [])
                )
        
        except Exception as e:
            logger.error(f"Error in Code Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the code quality agent"""
        return f"""
You are a Code Quality Bouncer - a strict but helpful code reviewer.

Your job:
1. Read the file that changed
2. Check for these issues: {', '.join(self.checks)}
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Provide clear, actionable feedback

Quality standards:
- Code must be properly formatted
- No syntax errors
- Follow language best practices
- Reasonable complexity
- Proper error handling

When you find issues:
- Describe each issue clearly
- Specify line numbers
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Prioritize by severity

Output your findings in a structured format.
"""
    
    def _get_output_schema(self) -> dict:
        """Get structured output schema"""
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["clean", "issues_found", "fixed", "error"]
                },
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "severity": {"type": "string", "enum": ["error", "warning", "info"]},
                            "type": {"type": "string"},
                            "line": {"type": "number"},
                            "description": {"type": "string"},
                            "fixed": {"type": "boolean"}
                        },
                        "required": ["severity", "type", "description", "fixed"]
                    }
                },
                "fixes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "line": {"type": "number"}
                        },
                        "required": ["description"]
                    }
                },
                "messages": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["status", "issues", "messages"]
        }
    
    def _build_prompt(self, event) -> str:
        """Build prompt for the agent"""
        return f"""
File changed: {event.path.name}
Event type: {event.event_type}

Please review this file for code quality issues.

Checks to perform: {', '.join(self.checks)}
Auto-fix enabled: {self.auto_fix}

Provide a detailed report of:
1. Issues found (with severity, line numbers, descriptions)
2. Fixes applied (if auto-fix is enabled)
3. Overall assessment

Be thorough but concise.
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse agent response into structured data"""
        try:
            # Try to parse as JSON (if structured output worked)
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: parse text response
            return {
                'status': 'issues_found' if 'issue' in response_text.lower() else 'clean',
                'issues': [],
                'fixes': [],
                'messages': [response_text]
            }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine overall status from result data"""
        status_map = {
            'clean': 'approved',
            'issues_found': 'denied' if not self.auto_fix else 'warning',
            'fixed': 'fixed',
            'error': 'warning'
        }
        
        return status_map.get(result_data.get('status', 'error'), 'warning')
