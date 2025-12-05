"""
Log Investigator Bouncer
Monitors application logs for errors and investigates the codebase for root causes and fixes
"""

from .base import BaseBouncer
from pathlib import Path
import logging
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LogInvestigator(BaseBouncer):
    """
    Log Investigator bouncer - monitors logs for errors and investigates codebase:
    - Parses log files for error entries
    - Extracts stack traces and error details
    - Investigates codebase for root causes
    - Suggests or applies fixes
    - Tracks fixed errors to avoid duplicates
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.log_dir = Path(config.get('log_dir', '/var/log'))
        self.codebase_dir = Path(config.get('codebase_dir', '.'))
        self.log_patterns = config.get('log_patterns', ['*.log'])
        self.error_levels = config.get('error_levels', ['ERROR', 'CRITICAL', 'EXCEPTION', 'FATAL'])
        self.max_errors_per_scan = config.get('max_errors_per_scan', 10)
        self.track_fixed_errors = config.get('track_fixed_errors', True)
        self.fixed_errors_file = Path('.bouncer/fixed_errors.json')
        self.lookback_hours = config.get('lookback_hours', 24)  # Only check recent errors
        
        # Create tracking file if needed
        if self.track_fixed_errors:
            self.fixed_errors_file.parent.mkdir(exist_ok=True)
            if not self.fixed_errors_file.exists():
                self.fixed_errors_file.write_text('{}')
    
    async def should_check(self, event) -> bool:
        """Check if this is a log file"""
        if not event.path.exists():
            return False
        
        # Check if it's in the log directory
        try:
            event.path.relative_to(self.log_dir)
        except ValueError:
            return False
        
        # Check if it matches log patterns
        for pattern in self.log_patterns:
            if event.path.match(pattern):
                return True
        
        return False
    
    async def check(self, event):
        """Investigate errors in log file"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        logger.info(f"🔍 Log Investigator checking: {event.path.name}")
        
        # Parse log file for errors
        errors = await self._parse_log_file(event.path)
        
        if not errors:
            logger.info(f"  ✅ No errors found in {event.path.name}")
            return self._create_result(event, 'approved', [], [], 
                                      ["No errors found in log file"])
        
        logger.info(f"  📊 Found {len(errors)} error(s) in {event.path.name}")
        
        # Filter out already-fixed errors
        if self.track_fixed_errors:
            errors = await self._filter_fixed_errors(errors)
            if not errors:
                logger.info(f"  ✅ All errors already investigated")
                return self._create_result(event, 'approved', [], [], 
                                          ["All errors have been previously investigated"])
        
        # Limit number of errors to investigate
        if len(errors) > self.max_errors_per_scan:
            logger.info(f"  ⚠️  Limiting to {self.max_errors_per_scan} errors")
            errors = errors[:self.max_errors_per_scan]
        
        # Investigate each error
        all_issues = []
        all_fixes = []
        all_messages = []
        
        for i, error in enumerate(errors, 1):
            logger.info(f"  🔎 Investigating error {i}/{len(errors)}: {error['message'][:60]}...")
            
            try:
                result = await self._investigate_error(error)
                
                if result['issues']:
                    all_issues.extend(result['issues'])
                if result['fixes']:
                    all_fixes.extend(result['fixes'])
                if result['messages']:
                    all_messages.extend(result['messages'])
                
                # Mark as investigated
                if self.track_fixed_errors:
                    await self._mark_error_investigated(error)
                    
            except Exception as e:
                logger.error(f"  ❌ Failed to investigate error: {e}")
                all_messages.append(f"Failed to investigate: {error['message'][:100]}")
        
        # Determine status
        if all_fixes:
            status = 'fixed'
        elif all_issues:
            status = 'denied'
        else:
            status = 'warning'
        
        return self._create_result(event, status, all_issues, all_fixes, all_messages)
    
    async def _parse_log_file(self, log_path: Path) -> List[Dict[str, Any]]:
        """Parse log file and extract error entries"""
        errors = []
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Common log patterns
            # Format: 2024-12-05 10:30:45 ERROR message
            # Format: [2024-12-05 10:30:45] ERROR: message
            # Format: ERROR: message (stack trace follows)
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Check if line contains error level
                if any(level in line.upper() for level in self.error_levels):
                    error = {
                        'timestamp': self._extract_timestamp(line),
                        'level': self._extract_level(line),
                        'message': self._extract_message(line),
                        'stack_trace': [],
                        'file_path': None,
                        'line_number': None,
                        'raw_lines': [line]
                    }
                    
                    # Collect stack trace (next lines that are indented or start with 'at')
                    i += 1
                    while i < len(lines):
                        next_line = lines[i].rstrip()
                        # Check if this looks like a stack trace line
                        is_stack_trace = (
                            next_line and (
                                next_line.startswith('  ') or 
                                next_line.startswith('\t') or 
                                next_line.startswith('Traceback') or
                                'at ' in next_line or
                                'File "' in next_line or
                                'line ' in next_line.lower() or
                                next_line.strip().startswith('File "') or
                                (len(next_line) > 0 and next_line[0] in ' \t')
                            )
                        )
                        
                        # Also check if line is blank (part of multi-line stack trace)
                        if is_stack_trace or (i < len(lines) - 1 and not next_line.strip()):
                            if next_line.strip():  # Don't add blank lines
                                error['stack_trace'].append(next_line)
                                error['raw_lines'].append(next_line)
                                
                                # Try to extract file and line number
                                file_info = self._extract_file_info(next_line)
                                if file_info and not error['file_path']:
                                    error['file_path'] = file_info['file']
                                    error['line_number'] = file_info['line']
                            
                            i += 1
                        else:
                            break
                    
                    errors.append(error)
                    continue
                
                i += 1
            
        except Exception as e:
            logger.error(f"Failed to parse log file {log_path}: {e}")
        
        return errors
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',  # 2024-12-05 10:30:45
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',      # 12/05/2024 10:30:45
            r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]',  # [2024-12-05 10:30:45]
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0).strip('[]')
        
        return None
    
    def _extract_level(self, line: str) -> str:
        """Extract error level from log line"""
        for level in self.error_levels:
            if level in line.upper():
                return level
        return 'ERROR'
    
    def _extract_message(self, line: str) -> str:
        """Extract error message from log line"""
        # Remove timestamp and level
        msg = line
        for level in self.error_levels:
            if level in msg.upper():
                parts = re.split(level + r'[:\s]+', msg, flags=re.IGNORECASE, maxsplit=1)
                if len(parts) > 1:
                    msg = parts[1]
                break
        
        return msg.strip()
    
    def _extract_file_info(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract file path and line number from stack trace line"""
        # Python: File "/path/to/file.py", line 123
        python_match = re.search(r'File "([^"]+)", line (\d+)', line)
        if python_match:
            return {'file': python_match.group(1), 'line': int(python_match.group(2))}
        
        # JavaScript: at /path/to/file.js:123:45
        js_match = re.search(r'at ([^\s:]+):(\d+):\d+', line)
        if js_match:
            return {'file': js_match.group(1), 'line': int(js_match.group(2))}
        
        # Java: at com.example.Class.method(File.java:123)
        java_match = re.search(r'\(([^)]+):(\d+)\)', line)
        if java_match:
            return {'file': java_match.group(1), 'line': int(java_match.group(2))}
        
        return None
    
    async def _filter_fixed_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out errors that have already been investigated"""
        try:
            fixed_errors = json.loads(self.fixed_errors_file.read_text())
        except:
            fixed_errors = {}
        
        new_errors = []
        for error in errors:
            error_hash = self._hash_error(error)
            if error_hash not in fixed_errors:
                new_errors.append(error)
        
        return new_errors
    
    def _hash_error(self, error: Dict[str, Any]) -> str:
        """Create a hash for error deduplication"""
        # Hash based on message and file location
        key_parts = [
            error['message'][:100],  # First 100 chars of message
            error.get('file_path', 'unknown'),
            str(error.get('line_number', 0))
        ]
        return '|'.join(key_parts)
    
    async def _mark_error_investigated(self, error: Dict[str, Any]):
        """Mark error as investigated"""
        try:
            fixed_errors = json.loads(self.fixed_errors_file.read_text())
        except:
            fixed_errors = {}
        
        error_hash = self._hash_error(error)
        fixed_errors[error_hash] = {
            'timestamp': datetime.now().isoformat(),
            'message': error['message'][:200]
        }
        
        self.fixed_errors_file.write_text(json.dumps(fixed_errors, indent=2))
    
    async def _investigate_error(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate a single error using Claude Agent SDK"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        from .schemas import BOUNCER_OUTPUT_SCHEMA
        
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            structured_output=BOUNCER_OUTPUT_SCHEMA,
            allowed_tools=["Read", "List", "Search"],  # No Write for investigation
            permission_mode="plan",  # Always plan mode for investigation
            system_prompt=self._get_system_prompt()
        )
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                prompt = self._build_investigation_prompt(error)
                await client.query(prompt)
                
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        response_text += msg.content
                
                # Parse structured output
                result = json.loads(response_text) if response_text else {}
                
                return {
                    'issues': result.get('issues', []),
                    'fixes': result.get('fixes', []),
                    'messages': result.get('messages', [])
                }
                
        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            return {'issues': [], 'fixes': [], 'messages': [str(e)]}
    
    def _build_investigation_prompt(self, error: Dict[str, Any]) -> str:
        """Build investigation prompt for Claude"""
        prompt = f"""# Log Error Investigation

You are investigating an error found in application logs. Your goal is to:
1. Understand what caused the error
2. Find the relevant code in the codebase
3. Suggest a fix

## Error Details

**Level:** {error['level']}
**Message:** {error['message']}
"""
        
        if error.get('timestamp'):
            prompt += f"**Timestamp:** {error['timestamp']}\n"
        
        if error.get('file_path'):
            prompt += f"**File:** {error['file_path']}\n"
        
        if error.get('line_number'):
            prompt += f"**Line:** {error['line_number']}\n"
        
        if error.get('stack_trace'):
            prompt += f"\n**Stack Trace:**\n```\n" + "\n".join(error['stack_trace']) + "\n```\n"
        
        prompt += f"""

## Investigation Steps

1. **Locate the code:** Find the file and function where the error occurred
2. **Read the context:** Understand what the code is trying to do
3. **Identify the root cause:** Determine why the error happened
4. **Suggest a fix:** Propose a code change to prevent this error

## Codebase Location

The codebase is located at: {self.codebase_dir}

## Output Format

Provide your findings in the structured output format:
- **issues**: List of problems found (description, severity, location)
- **fixes**: List of suggested fixes (description, file, changes)
- **messages**: Summary of your investigation

Focus on being thorough but concise. If you can't find the exact cause, explain what you investigated and what additional information would help.
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for log investigation"""
        return """You are an expert software debugger and log analyst. Your role is to:

1. Analyze error logs and stack traces
2. Investigate codebases to find root causes
3. Suggest precise, actionable fixes
4. Explain your reasoning clearly

When investigating errors:
- Read the relevant source files carefully
- Look for common error patterns (null checks, error handling, race conditions)
- Consider the broader context (dependencies, configuration, environment)
- Suggest defensive programming practices
- Prioritize fixes that prevent similar errors

Be thorough but efficient. Focus on the most likely causes first."""
    
    def _create_result(self, event, status: str, issues: List, fixes: List, messages: List):
        """Create a BouncerResult"""
        from bouncer.core import BouncerResult
        from datetime import datetime
        
        return BouncerResult(
            bouncer_name='log_investigator',
            file_path=event.path,
            status=status,
            issues_found=issues,
            fixes_applied=fixes,
            messages=messages,
            timestamp=datetime.now().timestamp()
        )
