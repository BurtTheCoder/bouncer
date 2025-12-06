"""
Dependency Bouncer
Checks dependency files for security vulnerabilities and updates
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class DependencyBouncer(BaseBouncer):
    """
    Dependency bouncer - checks for:
    - Known vulnerabilities (CVEs)
    - Outdated dependencies
    - Unused dependencies
    - License compatibility
    - Dependency conflicts
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.severity_threshold = config.get('severity_threshold', 'medium')
        self.check_updates = config.get('check_updates', True)
    
    async def check(self, event):
        """Check dependency files"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        logger.info(f"📦 Dependency Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            output_format=BOUNCER_OUTPUT_SCHEMA,
            allowed_tools=["Read", "Write", "Bash"],
            permission_mode="plan",  # Never auto-update dependencies without approval
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
                    issues_found=result_data.get('vulnerabilities', []),
                    messages=result_data.get('messages', [])
                )
        
        except Exception as e:
            logger.error(f"Error in Dependency Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during dependency check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for dependency checking"""
        return f"""
You are a Dependency Bouncer - a dependency security and maintenance expert.

Your job:
1. Read the dependency file that changed
2. Check for security vulnerabilities and outdated packages
3. NEVER auto-update dependencies (requires human approval)
4. Report all findings for review

Dependency checks:

**Security:**
- Known CVEs (Common Vulnerabilities and Exposures)
- Malicious packages
- Compromised dependencies
- Transitive vulnerabilities

**Maintenance:**
- Outdated dependencies (check: {self.check_updates})
- Deprecated packages
- Unmaintained packages
- Version conflicts

**Optimization:**
- Unused dependencies
- Duplicate dependencies
- Bundle size impact

**License:**
- License compatibility
- GPL contamination
- Missing licenses

Severity levels:
- CRITICAL: Actively exploited vulnerabilities
- HIGH: Known exploits available
- MEDIUM: Vulnerabilities without known exploits
- LOW: Outdated but no known vulnerabilities

Severity threshold: {self.severity_threshold}

When you find issues:
- Describe the security risk
- Provide CVE numbers if available
- Suggest safe update versions
- NEVER update automatically

Protect the project from vulnerable dependencies.
"""
    
    def _build_prompt(self, event) -> str:
        """Build dependency check prompt"""
        file_type = self._detect_dependency_type(event.path)
        
        return f"""
Dependency file changed: {event.path.name}
File type: {file_type}
Event type: {event.event_type}

Please review this dependency file for security vulnerabilities and updates.

Severity threshold: {self.severity_threshold}
Check for updates: {self.check_updates}

Check for:
1. Known CVEs and vulnerabilities
2. Outdated dependencies
3. Unused dependencies
4. License compatibility
5. Dependency conflicts

Provide a report of:
1. Vulnerabilities found (with CVE numbers)
2. Outdated packages (with recommended versions)
3. Recommendations for updates

DO NOT update dependencies automatically.
"""
    
    def _detect_dependency_type(self, path) -> str:
        """Detect dependency file type"""
        name = path.name.lower()
        
        if name == 'package.json':
            return 'npm'
        elif name == 'package-lock.json':
            return 'npm-lock'
        elif name == 'requirements.txt':
            return 'pip'
        elif name == 'pipfile' or name == 'pipfile.lock':
            return 'pipenv'
        elif name == 'poetry.lock' or name == 'pyproject.toml':
            return 'poetry'
        elif name == 'go.mod' or name == 'go.sum':
            return 'go'
        elif name == 'cargo.toml' or name == 'cargo.lock':
            return 'rust'
        elif name == 'gemfile' or name == 'gemfile.lock':
            return 'ruby'
        else:
            return 'unknown'
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse dependency check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'vulnerability', 'cve', 'outdated', 'security', 'risk'
            ])
            
            return {
                'status': 'vulnerabilities_found' if has_issues else 'clean',
                'vulnerabilities': [],
                'messages': [response_text]
            }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine status from result data"""
        vulnerabilities = result_data.get('vulnerabilities', [])
        
        if not vulnerabilities:
            return 'approved'
        
        # Check severity
        severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        threshold = severity_levels.get(self.severity_threshold.lower(), 2)
        
        critical_found = any(
            severity_levels.get(v.get('severity', '').lower(), 0) >= threshold
            for v in vulnerabilities
        )
        
        return 'denied' if critical_found else 'warning'
