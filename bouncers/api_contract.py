"""
API Contract Bouncer
Checks API specifications and contracts for validity and breaking changes
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class APIContractBouncer(BaseBouncer):
    """
    API Contract bouncer - checks for:
    - OpenAPI/Swagger spec validation
    - Breaking API changes
    - GraphQL schema validation
    - API versioning compliance
    - Response schema consistency
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.api_type = config.get('api_type', 'openapi')  # openapi, graphql, grpc
        self.allow_breaking_changes = config.get('allow_breaking_changes', False)
    
    async def check(self, event):
        """Check API contract files"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        
        logger.info(f"🔌 API Contract Bouncer checking: {event.path.name}")
        
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
            logger.error(f"Error in API Contract Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during API contract check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for API contract checking"""
        return f"""
You are an API Contract Bouncer - an API design and versioning expert.

Your job:
1. Read the API specification file that changed
2. Validate the API contract
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure API consistency and backwards compatibility

API contract checks:

**OpenAPI/Swagger:**
- Valid OpenAPI 3.0/3.1 syntax
- Required fields present (paths, info, openapi version)
- Schema definitions complete
- Response codes documented
- Security schemes defined
- Examples provided

**GraphQL:**
- Valid GraphQL schema syntax
- Type definitions complete
- Resolver coverage
- Deprecation annotations
- Query complexity limits

**Breaking Changes:**
- Removed endpoints
- Changed request/response schemas
- Removed required fields
- Changed field types
- Removed enum values

**Best Practices:**
- Semantic versioning
- Deprecation warnings
- Clear error messages
- Pagination support
- Rate limiting documented

Allow breaking changes: {self.allow_breaking_changes}

When you find issues:
- Describe the API impact
- Identify breaking vs non-breaking changes
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Suggest versioning strategy

Maintain stable, well-documented APIs.
"""
    
    def _build_prompt(self, event) -> str:
        """Build API contract check prompt"""
        return f"""
API specification file changed: {event.path.name}
API type: {self.api_type}
Event type: {event.event_type}

Please review this API specification for validity and breaking changes.

Allow breaking changes: {self.allow_breaking_changes}
Auto-fix enabled: {self.auto_fix}

Check for:
1. Syntax validity
2. Breaking changes
3. Missing documentation
4. Schema completeness
5. Best practices compliance

Provide a report of:
1. Issues found (breaking vs non-breaking)
2. Fixes applied (if auto-fix is enabled)
3. Recommendations for API design
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse API contract check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'breaking', 'invalid', 'missing', 'error', 'deprecated'
            ])
            
            return {
                'status': 'issues_found' if has_issues else 'clean',
                'issues': [],
                'fixes': [],
                'messages': [response_text]
            }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine status from result data"""
        issues = result_data.get('issues', [])
        
        # Check for breaking changes
        has_breaking = any(
            'breaking' in issue.get('type', '').lower()
            for issue in issues
        )
        
        if not issues:
            return 'approved'
        elif has_breaking and not self.allow_breaking_changes:
            return 'denied'
        elif result_data.get('status') == 'fixed':
            return 'fixed'
        else:
            return 'warning'
