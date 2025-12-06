"""
Custom Bouncer Template

Copy this file to create your own custom bouncer.
Follow the instructions in docs/CREATING_BOUNCERS.md for detailed guidance.
"""

from pathlib import Path
from typing import Dict, Any
import logging
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from .schemas import BOUNCER_OUTPUT_SCHEMA

logger = logging.getLogger(__name__)


class CustomBouncer:
    """
    Template for creating custom bouncers
    
    Replace 'Custom' with your bouncer name (e.g., 'Jupyter', 'LaTeX', 'Video')
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the bouncer with configuration
        
        Args:
            config: Configuration dictionary from bouncer.yaml
        """
        self.enabled = config.get('enabled', False)
        self.file_types = config.get('file_types', [])
        self.auto_fix = config.get('auto_fix', False)
        
        # Add your custom configuration options here
        # Example:
        # self.max_size = config.get('max_size', 1000000)
        # self.check_option = config.get('check_option', True)
    
    def should_check(self, file_path: Path) -> bool:
        """
        Determine if this bouncer should check the given file
        
        Args:
            file_path: Path to the file that changed
            
        Returns:
            True if this bouncer should check the file
        """
        if not self.enabled:
            return False
        
        # Check file extension
        if self.file_types:
            return any(str(file_path).endswith(ext) for ext in self.file_types)
        
        return False
    
    async def check(self, file_path: Path, event_type: str) -> Dict[str, Any]:
        """
        Check the file and return results
        
        Args:
            file_path: Path to the file that changed
            event_type: Type of event ('created', 'modified', 'deleted')
            
        Returns:
            Dictionary with check results following BOUNCER_OUTPUT_SCHEMA
        """
        logger.info(f"🎯 Custom Bouncer checking: {file_path}")
        
        try:
            # Build the system prompt for Claude
            system_prompt = self._build_system_prompt()
            
            # Build the user prompt with file context
            user_prompt = self._build_user_prompt(file_path, event_type)
            
            # Configure Claude Agent SDK options
            options = ClaudeAgentOptions(
                cwd=str(file_path.parent),
                allowed_tools=["Read", "Write"] if self.auto_fix else ["Read"],
                permission_mode="acceptEdits" if self.auto_fix else "plan",
                output_format=BOUNCER_OUTPUT_SCHEMA
            )
            
            # Query Claude
            async with ClaudeSDKClient(options=options) as client:
                await client.query(
                    prompt=f"{system_prompt}\n\n{user_prompt}"
                )
                
                # Collect response
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text += block.text
                
                # Parse structured output
                import json
                result = json.loads(response_text)
                
                logger.info(f"✅ Custom Bouncer completed: {result['status']}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Custom Bouncer error: {e}")
            return {
                "status": "error",
                "issues": [{
                    "category": "error",
                    "type": "bouncer_error",
                    "message": str(e),
                    "severity": "high"
                }],
                "fixes": [],
                "suggestions": {},
                "messages": [f"Bouncer error: {str(e)}"]
            }
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt that defines the bouncer's role
        
        Returns:
            System prompt string
        """
        auto_fix_instruction = "Fix issues automatically when safe" if self.auto_fix else "Report issues without fixing"
        
        return f"""You are a Custom Bouncer - an expert in [YOUR DOMAIN].

Your job:
1. Read the file that changed
2. Check for [SPECIFIC QUALITY CRITERIA]
3. {auto_fix_instruction}
4. Ensure files meet [YOUR STANDARDS]

When you find issues:
- Describe the impact clearly
- {"Fix it if safe to do so" if self.auto_fix else "Explain how to fix it"}
- Suggest improvements
- Provide actionable recommendations

Focus on [YOUR SPECIFIC GOALS].
"""
    
    def _build_user_prompt(self, file_path: Path, event_type: str) -> str:
        """
        Build the user prompt with file context
        
        Args:
            file_path: Path to the file
            event_type: Type of event
            
        Returns:
            User prompt string
        """
        return f"""File changed: {file_path.name}
Location: {file_path.parent}
Event type: {event_type}

Please review this file for [YOUR QUALITY CRITERIA].

Configuration:
- Auto-fix enabled: {self.auto_fix}
- File types: {', '.join(self.file_types)}

Check for:
1. [First check category]
2. [Second check category]
3. [Third check category]
4. [Additional checks...]

Provide a report of:
1. Issues found (with severity, category, and type)
2. Fixes applied (if auto-fix is enabled)
3. Suggestions for improvement
4. Actionable recommendations

Return your analysis in the structured JSON format.
"""
