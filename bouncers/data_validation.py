"""
Data Validation Bouncer
Validates data files (JSON, YAML, CSV)
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class DataValidationBouncer(BaseBouncer):
    """
    Data validation bouncer - checks data files for:
    - Schema compliance
    - Data type correctness
    - Required fields
    - Formatting consistency
    - Duplicate entries
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.checks = config.get('checks', ['schema', 'formatting'])
    
    async def check(self, event):
        """Validate data file"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        logger.info(f"📊 Data Bouncer checking: {event.path.name}")
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            output_format=BOUNCER_OUTPUT_SCHEMA,
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
            logger.error(f"Error in Data Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during data validation: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for data validation"""
        return f"""
You are a Data Validation Bouncer - a data quality expert.

Your job:
1. Read the data file that changed
2. Validate data quality: {', '.join(self.checks)}
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure data integrity

Quality standards:
- Valid JSON/YAML/CSV syntax
- Consistent formatting
- No duplicate entries
- Required fields present
- Correct data types
- Logical data values

When you find issues:
- Describe each issue clearly
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Ensure data integrity is maintained

Be thorough and precise.
"""
    
    def _build_prompt(self, event) -> str:
        """Build data validation prompt"""
        file_type = event.path.suffix
        
        return f"""
Data file changed: {event.path.name}
File type: {file_type}
Event type: {event.event_type}

Please validate this data file.

Checks to perform: {', '.join(self.checks)}
Auto-fix enabled: {self.auto_fix}

For {file_type} files, check:
1. Syntax validity
2. Formatting consistency
3. Data integrity
4. Schema compliance (if applicable)

Provide a report of:
1. Issues found
2. Fixes applied (if auto-fix is enabled)
3. Data quality assessment
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse data validation response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            has_issues = any(keyword in response_text.lower() for keyword in [
                'invalid', 'error', 'missing', 'duplicate', 'incorrect'
            ])
            
            return {
                'status': 'issues_found' if has_issues else 'valid',
                'issues': [],
                'fixes': [],
                'messages': [response_text]
            }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine status from result data"""
        status = result_data.get('status', 'valid')
        
        if status == 'valid':
            return 'approved'
        elif status == 'fixed':
            return 'fixed'
        else:
            return 'warning' if self.auto_fix else 'denied'
