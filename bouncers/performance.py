"""
Performance Bouncer
Checks files for performance issues and optimizations
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class PerformanceBouncer(BaseBouncer):
    """
    Performance bouncer - checks for:
    - Code complexity and bottlenecks
    - Large file sizes
    - Unoptimized images
    - Memory leaks patterns
    - N+1 query patterns
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.max_file_size = config.get('max_file_size', 1_000_000)  # 1MB
        self.max_image_size = config.get('max_image_size', 500_000)  # 500KB
    
    async def check(self, event):
        """Check for performance issues"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        logger.info(f"⚡ Performance Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            output_format=BOUNCER_OUTPUT_SCHEMA,
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
            logger.error(f"Error in Performance Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during performance check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for performance checking"""
        return f"""
You are a Performance Bouncer - an optimization expert.

Your job:
1. Read the file that changed
2. Check for performance issues
3. {'Optimize when safe to do so' if self.auto_fix else 'Report issues without fixing'}
4. Ensure code runs efficiently

Performance checks:
- Code complexity (cyclomatic complexity, nested loops)
- Large file sizes (max: {self.max_file_size} bytes)
- Unoptimized images (max: {self.max_image_size} bytes)
- Memory leak patterns (unclosed resources, circular references)
- N+1 query patterns in database code
- Inefficient algorithms (O(n²) when O(n) possible)
- Unnecessary computations in loops

For images:
- Check file size
- Suggest compression or format conversion (WebP)
- Recommend responsive image sizes

When you find issues:
- Describe the performance impact
- {'Optimize if safe to do so' if self.auto_fix else 'Explain how to optimize'}
- Provide before/after metrics when possible

Focus on real performance gains, not micro-optimizations.
"""
    
    def _build_prompt(self, event) -> str:
        """Build performance check prompt"""
        file_size = event.path.stat().st_size if event.path.exists() else 0
        
        return f"""
File changed: {event.path.name}
File size: {file_size} bytes
Event type: {event.event_type}

Please review this file for performance issues.

Max file size: {self.max_file_size} bytes
Max image size: {self.max_image_size} bytes
Auto-fix enabled: {self.auto_fix}

Check for:
1. Code complexity and bottlenecks
2. Large file sizes
3. Unoptimized images (if image file)
4. Memory leak patterns
5. Inefficient algorithms

Provide a report of:
1. Issues found (with performance impact)
2. Optimizations applied (if auto-fix is enabled)
3. Recommendations for improvement
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse performance check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'slow', 'performance', 'optimize', 'bottleneck', 'large'
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
