"""
Obsidian Bouncer
Checks Obsidian markdown notes for knowledge management best practices
"""

from .base import BaseBouncer
from .schemas import get_bouncer_schema
import logging
import json

logger = logging.getLogger(__name__)


class ObsidianBouncer(BaseBouncer):
    """
    Obsidian bouncer - checks for:
    - Broken wikilinks and orphaned notes
    - Frontmatter validation
    - Tag management and consistency
    - Content quality and completeness
    - Obsidian-specific syntax (embeds, block references, callouts)
    - Knowledge graph health
    - Daily notes and template compliance
    - Attachment management
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.required_fields = config.get('required_fields', ['tags', 'created'])
        self.tag_format = config.get('tag_format', 'kebab-case')
        self.max_tags = config.get('max_tags', 10)
        self.check_broken_links = config.get('check_broken_links', True)
        self.suggest_connections = config.get('suggest_connections', True)
        self.min_connections = config.get('min_connections', 1)
        self.min_note_length = config.get('min_note_length', 50)
        self.require_headings = config.get('require_headings', True)
        self.attachment_folder = config.get('attachment_folder', 'attachments')
        self.template_folder = config.get('template_folder', 'templates')
        self.daily_notes_folder = config.get('daily_notes_folder', 'daily')
    
    async def check(self, event):
        """Check Obsidian markdown note"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
        
        logger.info(f"🧠 Obsidian Bouncer checking: {event.path.name}")
        
        # Build options dict
        options_kwargs = {
            'cwd': str(event.path.parent),
            'allowed_tools': ["Read", "Write", "Bash"],
            'permission_mode': "acceptEdits" if self.auto_fix else "plan",
            'system_prompt': self._get_system_prompt(),
            'output_format': get_bouncer_schema("obsidian")
        }

        # Add hooks if configured
        hooks_config = self.get_hooks_config()
        if hooks_config:
            options_kwargs['hooks'] = hooks_config

        options = ClaudeAgentOptions(**options_kwargs)
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                prompt = self._build_prompt(event)
                logger.debug(f"Sending prompt to agent for: {event.path.name}")
                await client.query(prompt)

                # Collect agent responses and log activity
                all_text_responses = []
                message_count = 0
                async for msg in client.receive_response():
                    message_count += 1
                    msg_type = type(msg).__name__

                    # Log message type for debugging
                    logger.debug(f"    Message {message_count}: {msg_type}")

                    # Check for tool use in different message formats
                    # Format 1: msg.type == 'tool_use'
                    if hasattr(msg, 'type') and msg.type == 'tool_use':
                        tool_name = getattr(msg, 'name', 'unknown')
                        logger.info(f"    🔧 Agent using tool: {tool_name}")

                    # Format 2: msg has tool_use content blocks
                    if hasattr(msg, 'content') and msg.content:
                        for block in msg.content:
                            block_type = getattr(block, 'type', None)
                            if block_type == 'tool_use':
                                tool_name = getattr(block, 'name', 'unknown')
                                logger.info(f"    🔧 Agent using tool: {tool_name}")
                            elif block_type == 'text':
                                text = getattr(block, 'text', '')
                                if text:
                                    all_text_responses.append(text)

                    # Format 3: Check for tool_calls attribute
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_name = getattr(tc, 'name', str(tc))
                            logger.info(f"    🔧 Agent calling tool: {tool_name}")

                    # Format 4: Direct text attribute
                    if hasattr(msg, 'text') and msg.text:
                        all_text_responses.append(msg.text)

                    # Format 5: ResultMessage with result attribute
                    if hasattr(msg, 'result') and msg.result:
                        all_text_responses.append(str(msg.result))

                logger.debug(f"Agent finished with {message_count} messages")

                # Combine all text responses
                response_text = "\n\n".join(all_text_responses)
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
            logger.error(f"Error in Obsidian Bouncer: {e}")
            return self._create_result(
                event=event,
                status='warning',
                messages=[f"Error during Obsidian check: {str(e)}"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Obsidian checking"""
        fix_instructions = """
IMPORTANT - AUTO-FIX IS ENABLED:
You MUST use the Write tool to save your fixes to the file. Do not just report what you would fix.

Steps:
1. Read the file with the Read tool
2. Identify issues
3. Fix the issues in the content
4. Use the Write tool to save the fixed content back to the SAME file path
5. Report what you fixed

If you don't use the Write tool, your fixes will NOT be applied!
""" if self.auto_fix else """
AUTO-FIX IS DISABLED:
Report issues but do NOT modify the file. Explain what should be fixed.
"""

        return f"""
You are an Obsidian Bouncer - a knowledge management and PKM (Personal Knowledge Management) expert.

{fix_instructions}

Your job:
1. Read the Obsidian markdown note using the Read tool
2. List the vault's folder structure using Bash: ls -d */  (in the vault root)
3. Check for knowledge management best practices
4. {'Use the Write tool to fix issues and save the file' if self.auto_fix else 'Report issues without modifying files'}
5. Ensure notes are well-connected and in the correct folder

Obsidian-Specific Checks:

**1. Folder Organization (IMPORTANT):**
- Check if the note is in the correct folder based on its content
- Use `ls` to see what folders exist in the vault
- A note about a person should be in People/
- A note about a project should be in Projects/
- A note about a topic/concept should be in a relevant topic folder
- Daily notes should be in the daily notes folder
- If misplaced, recommend moving the file (but don't move it automatically)

**2. Frontmatter (YAML):**
- Required fields: {', '.join(self.required_fields)}
- Valid YAML syntax
- Date format validation
- Tag presence and format

**3. Tags:**
- Tag format: {self.tag_format}
- Max tags per note: {self.max_tags}
- Tags should be in frontmatter, not inline

**4. Wikilinks & Connections:**
- Valid [[wikilinks]] syntax
- Min connections: {self.min_connections}
- Suggest related connections: {self.suggest_connections}

**5. Content Quality:**
- Min note length: {self.min_note_length} characters
- Require headings: {self.require_headings}
- Proper heading hierarchy

**6. Obsidian Syntax:**
- Callouts: `> [!note]`, `> [!warning]`, etc.
- Code block language tags (should be in fence, not above it)
- Embeds and transclusions

When you find issues:
{'1. Fix the content\n2. Use Write tool to save the fixed file\n3. Report what you fixed' if self.auto_fix else '1. Report what is wrong\n2. Explain how to fix it'}

Build a well-connected, valuable knowledge base.
"""
    
    def _build_prompt(self, event) -> str:
        """Build Obsidian check prompt"""
        # Check if it's a daily note
        is_daily_note = self.daily_notes_folder in str(event.path)

        # Check if it's a template
        is_template = self.template_folder in str(event.path)

        file_path = str(event.path)

        # Get vault root (parent of the file's directory structure)
        # Walk up until we find the vault root (where .obsidian folder is)
        vault_root = event.path.parent
        while vault_root.parent != vault_root:
            if (vault_root / '.obsidian').exists():
                break
            vault_root = vault_root.parent

        # Get current folder relative to vault
        try:
            current_folder = event.path.parent.relative_to(vault_root)
        except ValueError:
            current_folder = event.path.parent.name

        fix_action = f"""
ACTION REQUIRED:
1. First, use Bash to list vault folders: ls -d */ in {vault_root}
2. Use the Read tool to read: {file_path}
3. Analyze the content and check if the file is in the correct folder
4. If content issues found, fix them
5. Use the Write tool to save the fixed content to: {file_path}
6. Provide your JSON report of what you fixed and any folder recommendations
""" if self.auto_fix else """
ACTION REQUIRED:
1. Use Bash to list vault folders
2. Use the Read tool to read the file
3. Analyze and report issues including folder placement (do NOT modify the file)
"""

        return f"""
Obsidian note changed: {event.path.name}
Full path: {file_path}
Vault root: {vault_root}
Current folder: {current_folder}
Event type: {event.event_type}
Is daily note: {is_daily_note}
Is template: {is_template}

{fix_action}

Configuration:
- Required frontmatter fields: {', '.join(self.required_fields)}
- Tag format: {self.tag_format} (use hyphens, not spaces)
- Auto-fix enabled: {self.auto_fix}

Check for:
1. FOLDER PLACEMENT: Is this note in the right folder based on its content?
   - List folders with: ls -d */ (in vault root)
   - Person notes → People/
   - Project notes → Projects/
   - Topic notes → relevant topic folder
   - If misplaced, recommend the correct folder (don't move automatically)

2. Missing or invalid YAML frontmatter (must have --- delimiters)
3. Missing required fields: {', '.join(self.required_fields)}
4. Inline tags (#tag) should be moved to frontmatter
5. Code blocks should have language in fence (```python) not as text above

{'REMEMBER: You MUST use the Write tool to save content fixes!' if self.auto_fix else 'Report issues only, do not modify.'}
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse Obsidian check response"""
        import re

        # First try direct JSON parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
            r'\{[\s\S]*"status"[\s\S]*\}',   # Raw JSON object with status
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response_text)
            for match in matches:
                try:
                    # Clean up the match
                    json_str = match.strip()
                    if not json_str.startswith('{'):
                        # Find the JSON object within the match
                        start = json_str.find('{')
                        if start >= 0:
                            json_str = json_str[start:]
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        # Ensure we have the required fields
                        if 'messages' not in parsed:
                            parsed['messages'] = [response_text]
                        return parsed
                except json.JSONDecodeError:
                    continue

        # Fallback: extract information from text
        has_issues = any(keyword in response_text.lower() for keyword in [
            'broken', 'missing', 'orphaned', 'invalid', 'empty', 'stub',
            'issue', 'error', 'fix', 'problem'
        ])

        has_fixes = any(keyword in response_text.lower() for keyword in [
            'fixed', 'applied', 'corrected', 'updated', 'added frontmatter',
            'added tags', 'added wikilinks'
        ])

        return {
            'status': 'fixed' if has_fixes else ('issues_found' if has_issues else 'clean'),
            'issues': [],
            'fixes': [],
            'messages': [response_text] if response_text else ['No response from agent']
        }
    
    def _determine_status(self, result_data: dict) -> str:
        """Determine status from result data"""
        issues = result_data.get('issues', [])
        
        if not issues:
            return 'approved'
        
        # Check for critical issues (broken links, invalid frontmatter)
        critical_issues = [
            i for i in issues 
            if i.get('severity') in ['critical', 'high']
        ]
        
        if critical_issues and not self.auto_fix:
            return 'denied'
        elif result_data.get('status') == 'fixed':
            return 'fixed'
        else:
            return 'warning'
