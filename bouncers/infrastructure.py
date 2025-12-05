"""
Infrastructure Bouncer
Checks infrastructure-as-code files for best practices
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class InfrastructureBouncer(BaseBouncer):
    """
    Infrastructure bouncer - checks for:
    - Dockerfile best practices
    - Kubernetes manifest validation
    - Terraform/CloudFormation syntax
    - Environment variable security
    - Resource limits and quotas
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.checks = config.get('checks', ['dockerfile', 'k8s', 'terraform'])
    
    async def check(self, event):
        """Check infrastructure files"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        
        logger.info(f"🏗️  Infrastructure Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            allowed_tools=["Read", "Write", "Bash"],
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
            logger.error(f"Error in Infrastructure Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during infrastructure check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for infrastructure checking"""
        return f"""
You are an Infrastructure Bouncer - a DevOps and IaC expert.

Your job:
1. Read the infrastructure file that changed
2. Check for best practices and security issues
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure production-ready infrastructure

Infrastructure checks:

**Dockerfile:**
- Use specific base image tags (not :latest)
- Run as non-root user
- Multi-stage builds for smaller images
- Proper layer caching
- No secrets in build args
- Security scanning

**Kubernetes:**
- Resource limits and requests
- Security contexts (non-root, read-only filesystem)
- Liveness and readiness probes
- Network policies
- RBAC configuration
- Secret management

**Terraform/CloudFormation:**
- Syntax validation
- Security group rules (no 0.0.0.0/0 for SSH)
- Encryption at rest
- IAM least privilege
- Tagging standards
- State file security

**General:**
- Environment variable security
- No hardcoded credentials
- Proper error handling
- Resource naming conventions

When you find issues:
- Describe the security/reliability impact
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Reference best practices

Build secure, reliable infrastructure.
"""
    
    def _build_prompt(self, event) -> str:
        """Build infrastructure check prompt"""
        file_type = self._detect_file_type(event.path)
        
        return f"""
Infrastructure file changed: {event.path.name}
File type: {file_type}
Event type: {event.event_type}

Please review this infrastructure file for best practices and security issues.

Checks to perform: {', '.join(self.checks)}
Auto-fix enabled: {self.auto_fix}

For {file_type} files, check:
1. Security best practices
2. Resource configuration
3. Performance optimization
4. Production readiness

Provide a report of:
1. Issues found (with severity)
2. Fixes applied (if auto-fix is enabled)
3. Recommendations for improvement
"""
    
    def _detect_file_type(self, path) -> str:
        """Detect infrastructure file type"""
        name = path.name.lower()
        
        if 'dockerfile' in name:
            return 'Dockerfile'
        elif path.suffix in ['.yaml', '.yml']:
            if 'k8s' in name or 'kubernetes' in name:
                return 'Kubernetes'
            return 'YAML'
        elif path.suffix == '.tf':
            return 'Terraform'
        elif path.suffix in ['.json', '.template']:
            return 'CloudFormation'
        else:
            return 'Unknown'
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse infrastructure check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'issue', 'security', 'best practice', 'warning', 'error'
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
