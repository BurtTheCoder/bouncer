"""
Example: Jupyter Notebook Bouncer

This is a complete, working example of a custom bouncer that checks
Jupyter notebooks for quality and best practices.

Use this as a reference when creating your own custom bouncers.
"""

from pathlib import Path
from typing import Dict, Any
import logging
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import sys
sys.path.append(str(Path(__file__).parent.parent))
from bouncers.schemas import BOUNCER_OUTPUT_SCHEMA

logger = logging.getLogger(__name__)


class JupyterBouncer:
    """
    Jupyter Notebook Bouncer
    
    Checks Jupyter notebooks for:
    - Reproducibility issues
    - Missing documentation
    - Large outputs that bloat files
    - Cell execution order problems
    - Unused imports and variables
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Jupyter bouncer"""
        self.enabled = config.get('enabled', False)
        self.file_types = config.get('file_types', ['.ipynb'])
        self.auto_fix = config.get('auto_fix', False)
        
        # Custom configuration
        self.max_cells = config.get('max_cells', 50)
        self.clear_outputs = config.get('clear_outputs', True)
        self.check_execution_order = config.get('check_execution_order', True)
        self.require_markdown_ratio = config.get('require_markdown_ratio', 0.2)
    
    def should_check(self, file_path: Path) -> bool:
        """Check if this bouncer should process the file"""
        if not self.enabled:
            return False
        
        return any(str(file_path).endswith(ext) for ext in self.file_types)
    
    async def check(self, file_path: Path, event_type: str) -> Dict[str, Any]:
        """
        Check a Jupyter notebook
        
        Args:
            file_path: Path to the .ipynb file
            event_type: 'created', 'modified', or 'deleted'
            
        Returns:
            Dictionary with check results
        """
        logger.info(f"📓 Jupyter Bouncer checking: {file_path}")
        
        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(file_path, event_type)
            
            options = ClaudeAgentOptions(
                cwd=str(file_path.parent),
                allowed_tools=["Read", "Write"] if self.auto_fix else ["Read"],
                permission_mode="acceptEdits" if self.auto_fix else "plan",
                structured_output=BOUNCER_OUTPUT_SCHEMA
            )
            
            async with ClaudeSDKClient(options=options) as client:
                await client.query(
                    prompt=f"{system_prompt}\n\n{user_prompt}"
                )
                
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text += block.text
                
                import json
                result = json.loads(response_text)
                
                logger.info(f"✅ Jupyter Bouncer completed: {result['status']}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Jupyter Bouncer error: {e}")
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
        """Build the system prompt for Claude"""
        auto_fix_instruction = "Fix issues automatically when safe" if self.auto_fix else "Report issues without fixing"
        
        return f"""You are a Jupyter Bouncer - an expert in data science, machine learning, and notebook best practices.

Your job:
1. Read the Jupyter notebook (.ipynb) file
2. Check for reproducibility, clarity, and performance issues
3. {auto_fix_instruction}
4. Ensure notebooks are clean, documented, and easy to review

When you find issues:
- Describe the impact on reproducibility and collaboration
- {"Fix it if safe to do so (e.g., clear outputs, remove unused imports)" if self.auto_fix else "Explain how to fix it"}
- Suggest improvements for better notebook quality
- Recommend best practices

Focus on making this notebook production-ready and easy for others to understand and run.
"""
    
    def _build_user_prompt(self, file_path: Path, event_type: str) -> str:
        """Build the user prompt with file context"""
        return f"""Jupyter notebook changed: {file_path.name}
Location: {file_path.parent}
Event type: {event_type}

Please review this Jupyter notebook for quality and best practices.

Configuration:
- Auto-fix enabled: {self.auto_fix}
- Clear outputs on save: {self.clear_outputs}
- Max cells: {self.max_cells}
- Check execution order: {self.check_execution_order}
- Required markdown ratio: {self.require_markdown_ratio * 100}%

Check for:
1. **Documentation**: Missing markdown cells, unclear explanations
2. **Reproducibility**: Missing random seeds, environment dependencies
3. **Code Quality**: Unused imports, undefined variables, PEP 8 violations
4. **Cell Outputs**: Large outputs that bloat the file (images, dataframes)
5. **Execution Order**: Cells executed out of order, non-sequential numbering
6. **Structure**: Too many cells, poor organization, missing sections
7. **Performance**: Inefficient code patterns, unnecessary computations

Provide a report of:
1. Issues found (with severity, category, and specific cell numbers)
2. Fixes applied (if auto-fix is enabled)
3. Suggestions for improving notebook quality
4. Best practices recommendations

Return your analysis in the structured JSON format.
"""


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Example configuration
    config = {
        "enabled": True,
        "file_types": [".ipynb"],
        "auto_fix": True,
        "max_cells": 50,
        "clear_outputs": True,
        "check_execution_order": True,
        "require_markdown_ratio": 0.2
    }
    
    bouncer = JupyterBouncer(config)
    
    # Example check
    async def test():
        result = await bouncer.check(
            Path("example_notebook.ipynb"),
            "modified"
        )
        print("Result:", result)
    
    asyncio.run(test())
