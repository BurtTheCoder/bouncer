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
        
        options = ClaudeAgentOptions(
            cwd=str(event.path.parent),
            allowed_tools=["Read", "Write", "Bash"],
            permission_mode="acceptEdits" if self.auto_fix else "plan",
            system_prompt=self._get_system_prompt(),
            structured_output=get_bouncer_schema("obsidian")
        )
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                prompt = self._build_prompt(event)
                await client.query(prompt)
                
                # With structured_output, we get clean JSON
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                # Only keep the last text block (final JSON output)
                                response_text = block.text
                
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
        return f"""
You are an Obsidian Bouncer - a knowledge management and PKM (Personal Knowledge Management) expert.

Your job:
1. Read the Obsidian markdown note that changed
2. Check for knowledge management best practices
3. {'Fix issues automatically when safe' if self.auto_fix else 'Report issues without fixing'}
4. Ensure notes are well-connected and valuable

Obsidian-Specific Checks:

**1. Wikilinks & Connections:**
- Broken [[wikilinks]] (check: {self.check_broken_links})
- Orphaned notes (min connections: {self.min_connections})
- Suggest related connections (enabled: {self.suggest_connections})
- Validate link syntax
- Check for circular dependencies

**2. Frontmatter (YAML):**
- Required fields: {', '.join(self.required_fields)}
- Valid YAML syntax
- Consistent metadata schema
- Date format validation
- Tag presence and format

**3. Tags:**
- Tag format: {self.tag_format}
- Max tags per note: {self.max_tags}
- Duplicate/similar tags
- Tag hierarchy validation (#parent/child)
- Orphaned tags

**4. Content Quality:**
- Min note length: {self.min_note_length} characters
- Require headings: {self.require_headings}
- Empty or stub notes
- Proper heading hierarchy (H1 → H2 → H3)
- Markdown syntax validity

**5. Obsidian Syntax:**
- `![[embeds]]` and transclusions
- `^block-references`
- Dataview queries (if present)
- Callouts: `> [!note]`, `> [!warning]`, etc.
- Code block language tags

**6. Knowledge Graph:**
- Note isolation (no incoming/outgoing links)
- Over-connected hub notes (>50 links)
- Suggest MOCs (Maps of Content)
- Bidirectional linking

**7. Vault Structure:**
- Attachment folder: {self.attachment_folder}
- Template folder: {self.template_folder}
- Daily notes folder: {self.daily_notes_folder}
- Proper file organization

**8. Smart Suggestions:**
- Related notes based on content
- Missing connections to MOCs
- Tag consolidation opportunities
- Note splitting recommendations (if too long)

When you find issues:
- Describe the knowledge management impact
- {'Fix it if safe to do so' if self.auto_fix else 'Explain how to fix it'}
- Suggest improvements for better knowledge organization
- Recommend connections to related notes

Build a well-connected, valuable knowledge base.
"""
    
    def _build_prompt(self, event) -> str:
        """Build Obsidian check prompt"""
        # Check if it's a daily note
        is_daily_note = self.daily_notes_folder in str(event.path)
        
        # Check if it's a template
        is_template = self.template_folder in str(event.path)
        
        return f"""
Obsidian note changed: {event.path.name}
Location: {event.path.parent}
Event type: {event.event_type}
Is daily note: {is_daily_note}
Is template: {is_template}

Please review this Obsidian note for knowledge management best practices.

Configuration:
- Required frontmatter fields: {', '.join(self.required_fields)}
- Tag format: {self.tag_format}
- Max tags: {self.max_tags}
- Check broken links: {self.check_broken_links}
- Suggest connections: {self.suggest_connections}
- Min connections: {self.min_connections}
- Min note length: {self.min_note_length} characters
- Require headings: {self.require_headings}
- Auto-fix enabled: {self.auto_fix}

Check for:
1. Frontmatter validity and completeness
2. Broken wikilinks and orphaned notes
3. Tag quality and consistency
4. Content quality and structure
5. Obsidian-specific syntax (embeds, callouts, etc.)
6. Knowledge graph connections
7. File organization

Provide a report of:
1. Issues found (with severity and type)
2. Fixes applied (if auto-fix is enabled)
3. Smart suggestions for improving this note
4. Recommended connections to other notes

Focus on making this note a valuable part of the knowledge base.
"""
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse Obsidian check response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Detect common issues from text
            has_issues = any(keyword in response_text.lower() for keyword in [
                'broken', 'missing', 'orphaned', 'invalid', 'empty', 'stub'
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
