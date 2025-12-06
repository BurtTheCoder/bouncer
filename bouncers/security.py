"""
Security Bouncer
Scans files for security vulnerabilities
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class SecurityBouncer(BaseBouncer):
    """
    Security bouncer - scans for:
    - Hardcoded secrets
    - SQL injection risks
    - XSS vulnerabilities
    - Insecure dependencies
    - Authentication issues
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.severity_threshold = config.get('severity_threshold', 'medium')
    
    async def check(self, event):
        """Check for security vulnerabilities"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        
        logger.info(f"🕵️  Security Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            allowed_tools=["Read", "Bash"],  # Never auto-fix security issues
            permission_mode="plan",  # Always require approval
            system_prompt=self._get_system_prompt(),
            output_format=self._get_output_schema()
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
                    issues_found=result_data.get('vulnerabilities', []),
                    messages=result_data.get('messages', [])
                )
        
        except Exception as e:
            logger.error(f"Error in Security Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during security scan: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for security scanning"""
        return """
You are a Security Bouncer - a vigilant security expert.

Your job:
1. Read the file that changed
2. Scan for security vulnerabilities
3. NEVER auto-fix security issues
4. Report all findings for human review

Security checks:
- Hardcoded secrets (API keys, passwords, tokens)
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Insecure cryptography
- Authentication/authorization issues
- Insecure dependencies
- Path traversal risks
- Command injection risks

Severity levels:
- CRITICAL: Immediate security risk, exploitable
- HIGH: Serious vulnerability, needs urgent fix
- MEDIUM: Potential security issue, should be addressed
- LOW: Security improvement recommended

IMPORTANT: Never modify files. Only report findings.
"""
    
    def _get_output_schema(self) -> dict:
        """Get structured output schema"""
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["secure", "vulnerabilities_found", "error"]
                },
                "vulnerabilities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low"]
                            },
                            "type": {"type": "string"},
                            "line": {"type": "number"},
                            "description": {"type": "string"},
                            "recommendation": {"type": "string"}
                        },
                        "required": ["severity", "type", "description", "recommendation"]
                    }
                },
                "messages": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["status", "vulnerabilities", "messages"]
        }
    
    def _build_prompt(self, event) -> str:
        """Build security scan prompt"""
        return f"""
File changed: {event.path.name}
Event type: {event.event_type}

Perform a comprehensive security scan of this file.

Look for:
- Hardcoded secrets or credentials
- SQL injection vulnerabilities
- XSS risks
- Insecure cryptography
- Authentication issues
- Any other security concerns

Severity threshold: {self.severity_threshold}

Report all findings with:
- Severity level
- Vulnerability type
- Line number (if applicable)
- Description
- Recommendation for fixing

Be thorough and err on the side of caution.
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse security scan response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Check for security keywords in text
            has_issues = any(keyword in response_text.lower() for keyword in [
                'vulnerability', 'security', 'risk', 'exposed', 'hardcoded'
            ])
            
            return {
                'status': 'vulnerabilities_found' if has_issues else 'secure',
                'vulnerabilities': [],
                'messages': [response_text]
            }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine status based on vulnerabilities found"""
        vulnerabilities = result_data.get('vulnerabilities', [])
        
        if not vulnerabilities:
            return 'approved'
        
        # Check severity
        critical_or_high = any(
            v.get('severity') in ['critical', 'high']
            for v in vulnerabilities
        )
        
        return 'denied' if critical_or_high else 'warning'
