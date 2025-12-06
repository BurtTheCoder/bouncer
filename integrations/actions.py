"""
Integration Actions - Create PRs, issues, and tickets using MCP
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Structured output schema for integration responses
INTEGRATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether the operation was successful"
        },
        "url": {
            "type": "string",
            "description": "URL of the created resource (PR, issue, ticket)"
        },
        "id": {
            "type": "string",
            "description": "ID of the created resource"
        },
        "message": {
            "type": "string",
            "description": "Human-readable status message"
        },
        "error": {
            "type": "string",
            "description": "Error message if operation failed"
        }
    },
    "required": ["success", "message"]
}


class IntegrationActions:
    """
    Performs integration actions like creating PRs, issues, and tickets.

    Uses Claude Agent SDK with MCP servers to interact with external services.
    """

    def __init__(self, mcp_manager, codebase_dir: Path):
        """
        Initialize Integration Actions.

        Args:
            mcp_manager: MCPManager instance
            codebase_dir: Root directory of the codebase
        """
        self.mcp_manager = mcp_manager
        self.codebase_dir = codebase_dir

    async def create_github_pr(self,
                               bouncer_result,
                               branch_name: Optional[str] = None,
                               auto_create: bool = False) -> Dict[str, Any]:
        """
        Create a GitHub Pull Request with fixes from bouncer results.

        Args:
            bouncer_result: BouncerResult with fixes to apply
            branch_name: Custom branch name (or auto-generated)
            auto_create: If True, create without confirmation

        Returns:
            Dict with PR details or error information
        """
        if not self.mcp_manager.is_integration_enabled('github'):
            return {'success': False, 'error': 'GitHub integration not enabled'}

        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Generate branch name if not provided
        if not branch_name:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            branch_name = f"bouncer/{bouncer_result.bouncer_name}/{timestamp}"

        # Get MCP configuration
        mcp_servers = self.mcp_manager.get_mcp_servers()
        if 'github' not in mcp_servers:
            return {'success': False, 'error': 'GitHub MCP server not configured'}

        # Get GitHub integration config
        github_config = self.mcp_manager.get_integration_config('github')

        # Configure Claude Agent SDK with GitHub MCP and structured output
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='github',
                tool_names=['create_or_update_file', 'push_files', 'create_pull_request']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan',
            output_format=INTEGRATION_RESPONSE_SCHEMA
        )

        # Build prompt for PR creation
        prompt = self._build_pr_prompt(bouncer_result, branch_name, github_config)

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text

                # Parse structured response
                result = self._parse_structured_response(response_text, 'pr_url')

                if result.get('success'):
                    logger.info(f"Created GitHub PR: {result.get('url')}")
                else:
                    logger.error(f"Failed to create PR: {result.get('error')}")

                return result

        except Exception as e:
            logger.error(f"Failed to create GitHub PR: {e}")
            return {'success': False, 'error': str(e)}

    async def create_github_issue(self,
                                  bouncer_result,
                                  auto_create: bool = False) -> Dict[str, Any]:
        """
        Create a GitHub Issue for bouncer findings.

        Args:
            bouncer_result: BouncerResult with issues found
            auto_create: If True, create without confirmation

        Returns:
            Dict with issue details or error information
        """
        if not self.mcp_manager.is_integration_enabled('github'):
            return {'success': False, 'error': 'GitHub integration not enabled'}

        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Get MCP configuration
        mcp_servers = self.mcp_manager.get_mcp_servers()
        if 'github' not in mcp_servers:
            return {'success': False, 'error': 'GitHub MCP server not configured'}

        # Get GitHub integration config
        github_config = self.mcp_manager.get_integration_config('github')

        # Configure Claude Agent SDK with structured output
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='github',
                tool_names=['create_issue']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan',
            output_format=INTEGRATION_RESPONSE_SCHEMA
        )

        # Build prompt for issue creation
        prompt = self._build_issue_prompt(bouncer_result, github_config)

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text

                # Parse structured response
                result = self._parse_structured_response(response_text, 'issue_url')

                if result.get('success'):
                    logger.info(f"Created GitHub issue: {result.get('url')}")
                else:
                    logger.error(f"Failed to create issue: {result.get('error')}")

                return result

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return {'success': False, 'error': str(e)}

    async def create_gitlab_mr(self,
                               bouncer_result,
                               branch_name: Optional[str] = None,
                               auto_create: bool = False) -> Dict[str, Any]:
        """
        Create a GitLab Merge Request with fixes from bouncer results.

        Args:
            bouncer_result: BouncerResult with fixes to apply
            branch_name: Custom branch name (or auto-generated)
            auto_create: If True, create without confirmation

        Returns:
            Dict with MR details or error information
        """
        if not self.mcp_manager.is_integration_enabled('gitlab'):
            return {'success': False, 'error': 'GitLab integration not enabled'}

        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Generate branch name if not provided
        if not branch_name:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            branch_name = f"bouncer/{bouncer_result.bouncer_name}/{timestamp}"

        # Get MCP configuration
        mcp_servers = self.mcp_manager.get_mcp_servers()
        if 'gitlab' not in mcp_servers:
            return {'success': False, 'error': 'GitLab MCP server not configured'}

        # Get GitLab integration config
        gitlab_config = self.mcp_manager.get_integration_config('gitlab')

        # Configure Claude Agent SDK with structured output
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='gitlab',
                tool_names=['update_file', 'create_merge_request']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan',
            output_format=INTEGRATION_RESPONSE_SCHEMA
        )

        # Build prompt for MR creation
        prompt = self._build_gitlab_mr_prompt(bouncer_result, branch_name, gitlab_config)

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text

                # Parse structured response
                result = self._parse_structured_response(response_text, 'mr_url')

                if result.get('success'):
                    logger.info(f"Created GitLab MR: {result.get('url')}")
                else:
                    logger.error(f"Failed to create MR: {result.get('error')}")

                return result

        except Exception as e:
            logger.error(f"Failed to create GitLab MR: {e}")
            return {'success': False, 'error': str(e)}

    async def create_gitlab_issue(self,
                                  bouncer_result,
                                  auto_create: bool = False) -> Dict[str, Any]:
        """
        Create a GitLab Issue for bouncer findings.

        Args:
            bouncer_result: BouncerResult with issues found
            auto_create: If True, create without confirmation

        Returns:
            Dict with issue details or error information
        """
        if not self.mcp_manager.is_integration_enabled('gitlab'):
            return {'success': False, 'error': 'GitLab integration not enabled'}

        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Get MCP configuration
        mcp_servers = self.mcp_manager.get_mcp_servers()
        if 'gitlab' not in mcp_servers:
            return {'success': False, 'error': 'GitLab MCP server not configured'}

        # Get GitLab integration config
        gitlab_config = self.mcp_manager.get_integration_config('gitlab')

        # Configure Claude Agent SDK with structured output
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='gitlab',
                tool_names=['create_issue']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan',
            output_format=INTEGRATION_RESPONSE_SCHEMA
        )

        # Build prompt for issue creation
        prompt = self._build_gitlab_issue_prompt(bouncer_result, gitlab_config)

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text

                # Parse structured response
                result = self._parse_structured_response(response_text, 'issue_url')

                if result.get('success'):
                    logger.info(f"Created GitLab issue: {result.get('url')}")
                else:
                    logger.error(f"Failed to create issue: {result.get('error')}")

                return result

        except Exception as e:
            logger.error(f"Failed to create GitLab issue: {e}")
            return {'success': False, 'error': str(e)}

    async def create_linear_issue(self,
                                  bouncer_result,
                                  auto_create: bool = False) -> Dict[str, Any]:
        """
        Create a Linear Issue for bouncer findings.

        Args:
            bouncer_result: BouncerResult with issues found
            auto_create: If True, create without confirmation

        Returns:
            Dict with issue details or error information
        """
        if not self.mcp_manager.is_integration_enabled('linear'):
            return {'success': False, 'error': 'Linear integration not enabled'}

        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Get MCP configuration
        mcp_servers = self.mcp_manager.get_mcp_servers()
        if 'linear' not in mcp_servers:
            return {'success': False, 'error': 'Linear MCP server not configured'}

        # Get Linear integration config
        linear_config = self.mcp_manager.get_integration_config('linear')

        # Configure Claude Agent SDK with structured output
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='linear',
                tool_names=['create_issue']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan',
            output_format=INTEGRATION_RESPONSE_SCHEMA
        )

        # Build prompt for issue creation
        prompt = self._build_linear_issue_prompt(bouncer_result, linear_config)

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text

                # Parse structured response
                result = self._parse_structured_response(response_text, 'issue_url')

                if result.get('success'):
                    logger.info(f"Created Linear issue: {result.get('url')}")
                else:
                    logger.error(f"Failed to create issue: {result.get('error')}")

                return result

        except Exception as e:
            logger.error(f"Failed to create Linear issue: {e}")
            return {'success': False, 'error': str(e)}

    async def create_jira_ticket(self,
                                 bouncer_result,
                                 auto_create: bool = False) -> Dict[str, Any]:
        """
        Create a Jira ticket for bouncer findings.

        Args:
            bouncer_result: BouncerResult with issues found
            auto_create: If True, create without confirmation

        Returns:
            Dict with ticket details or error information
        """
        if not self.mcp_manager.is_integration_enabled('jira'):
            return {'success': False, 'error': 'Jira integration not enabled'}

        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # Get MCP configuration
        mcp_servers = self.mcp_manager.get_mcp_servers()
        if 'jira' not in mcp_servers:
            return {'success': False, 'error': 'Jira MCP server not configured'}

        # Get Jira integration config
        jira_config = self.mcp_manager.get_integration_config('jira')

        # Configure Claude Agent SDK with structured output
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='jira',
                tool_names=['create_issue']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan',
            output_format=INTEGRATION_RESPONSE_SCHEMA
        )

        # Build prompt for ticket creation
        prompt = self._build_jira_ticket_prompt(bouncer_result, jira_config)

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                response_text = block.text

                # Parse structured response
                result = self._parse_structured_response(response_text, 'ticket_url')

                if result.get('success'):
                    logger.info(f"Created Jira ticket: {result.get('url')}")
                else:
                    logger.error(f"Failed to create ticket: {result.get('error')}")

                return result

        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return {'success': False, 'error': str(e)}

    def _parse_structured_response(self, response: str, url_key: str) -> Dict[str, Any]:
        """
        Parse structured JSON response from Claude.

        Args:
            response: JSON response string
            url_key: Key name for backward compatibility in result dict

        Returns:
            Dict with success, url, message, and optionally error
        """
        try:
            data = json.loads(response)
            result = {
                'success': data.get('success', False),
                'message': data.get('message', ''),
            }

            # Include URL if present
            if data.get('url'):
                result['url'] = data['url']
                result[url_key] = data['url']  # Backward compatibility

            # Include ID if present
            if data.get('id'):
                result['id'] = data['id']

            # Include error if present
            if data.get('error'):
                result['error'] = data['error']

            return result

        except json.JSONDecodeError:
            # Fallback: try to extract useful info from non-JSON response
            return {
                'success': False,
                'error': 'Could not parse response as JSON',
                'raw_response': response[:500]  # Truncate for logging
            }

    def _build_pr_prompt(self,
                        bouncer_result,
                        branch_name: str,
                        github_config: Dict[str, Any]) -> str:
        """Build prompt for GitHub PR creation"""

        # Format fixes
        fixes_summary = "\n".join([
            f"- {fix.get('description', fix.get('message', 'Fix applied'))}"
            for fix in bouncer_result.fixes_applied
        ]) or "- Automated fixes applied"

        return f"""Create a GitHub Pull Request with fixes from the {bouncer_result.bouncer_name} bouncer.

## Fixes to Apply
{fixes_summary}

## PR Details
- Branch name: {branch_name}
- Title: Fix: Issues found by {bouncer_result.bouncer_name}
- File: {bouncer_result.file_path}

## Instructions
1. Create a new branch: `{branch_name}`
2. Apply the fixes to the file
3. Commit with message: "fix: {bouncer_result.bouncer_name} automated fixes"
4. Create a pull request

Use the GitHub MCP tools to complete these steps.

## Required Response Format
You MUST respond with a JSON object:
{{
  "success": true/false,
  "url": "https://github.com/...",
  "id": "123",
  "message": "Pull request created successfully"
}}
"""

    def _build_issue_prompt(self,
                           bouncer_result,
                           github_config: Dict[str, Any]) -> str:
        """Build prompt for GitHub issue creation"""

        # Format issues
        issues_summary = "\n".join([
            f"- **{issue.get('severity', 'medium')}**: {issue.get('description', issue.get('message', 'Issue found'))}"
            for issue in bouncer_result.issues_found
        ]) or "- Issues detected by bouncer"

        labels = github_config.get('default_labels', ['bouncer', 'automated'])
        labels_str = ', '.join(labels)

        return f"""Create a GitHub issue for problems found by the {bouncer_result.bouncer_name} bouncer.

## Issues Found
{issues_summary}

## Issue Details
- Title: [{bouncer_result.bouncer_name}] Issues found in {bouncer_result.file_path.name}
- File: `{bouncer_result.file_path}`
- Labels: {labels_str}

Use the GitHub MCP `create_issue` tool to create an issue with the above details.

## Required Response Format
You MUST respond with a JSON object:
{{
  "success": true/false,
  "url": "https://github.com/.../issues/123",
  "id": "123",
  "message": "Issue created successfully"
}}
"""

    def _build_gitlab_mr_prompt(self,
                                bouncer_result,
                                branch_name: str,
                                gitlab_config: Dict[str, Any]) -> str:
        """Build prompt for GitLab merge request creation"""

        # Format fixes
        fixes_summary = "\n".join([
            f"- {fix.get('description', fix.get('message', 'Fix applied'))}"
            for fix in bouncer_result.fixes_applied
        ]) or "- Automated fixes applied"

        return f"""Create a GitLab Merge Request with fixes from the {bouncer_result.bouncer_name} bouncer.

## Fixes to Apply
{fixes_summary}

## MR Details
- Branch name: {branch_name}
- Title: Fix: Issues found by {bouncer_result.bouncer_name}
- File: {bouncer_result.file_path}

## Instructions
1. Create a new branch: `{branch_name}`
2. Update the file with fixes
3. Create a merge request

Use the GitLab MCP tools to complete these steps.

## Required Response Format
You MUST respond with a JSON object:
{{
  "success": true/false,
  "url": "https://gitlab.com/.../merge_requests/123",
  "id": "123",
  "message": "Merge request created successfully"
}}
"""

    def _build_gitlab_issue_prompt(self,
                                   bouncer_result,
                                   gitlab_config: Dict[str, Any]) -> str:
        """Build prompt for GitLab issue creation"""

        # Format issues
        issues_summary = "\n".join([
            f"- **{issue.get('severity', 'medium')}**: {issue.get('description', issue.get('message', 'Issue found'))}"
            for issue in bouncer_result.issues_found
        ]) or "- Issues detected by bouncer"

        return f"""Create a GitLab issue for problems found by the {bouncer_result.bouncer_name} bouncer.

## Issues Found
{issues_summary}

## Issue Details
- Title: [{bouncer_result.bouncer_name}] Issues found in {bouncer_result.file_path.name}
- File: `{bouncer_result.file_path}`
- Labels: bouncer, automated

Use the GitLab MCP `create_issue` tool to create an issue with the above details.

## Required Response Format
You MUST respond with a JSON object:
{{
  "success": true/false,
  "url": "https://gitlab.com/.../issues/123",
  "id": "123",
  "message": "Issue created successfully"
}}
"""

    def _build_linear_issue_prompt(self,
                                   bouncer_result,
                                   linear_config: Dict[str, Any]) -> str:
        """Build prompt for Linear issue creation"""

        # Get project/team from config
        project_id = linear_config.get('project_id', '')
        team_id = linear_config.get('team_id', '')
        priority = linear_config.get('default_priority', 'medium')

        # Format issues
        issues_summary = "\n".join([
            f"- **{issue.get('severity', 'medium')}**: {issue.get('description', issue.get('message', 'Issue found'))}"
            for issue in bouncer_result.issues_found
        ]) or "- Issues detected by bouncer"

        return f"""Create a Linear issue for problems found by the {bouncer_result.bouncer_name} bouncer.

## Issues Found
{issues_summary}

## Issue Details
- Title: [{bouncer_result.bouncer_name}] Issues in {bouncer_result.file_path.name}
- File: `{bouncer_result.file_path}`
- Project: {project_id}
- Team: {team_id}
- Priority: {priority}

Use the Linear MCP `create_issue` tool to create an issue with the above details.

## Required Response Format
You MUST respond with a JSON object:
{{
  "success": true/false,
  "url": "https://linear.app/.../issue/...",
  "id": "ABC-123",
  "message": "Linear issue created successfully"
}}
"""

    def _build_jira_ticket_prompt(self,
                                  bouncer_result,
                                  jira_config: Dict[str, Any]) -> str:
        """Build prompt for Jira ticket creation"""

        # Get project config
        project_key = jira_config.get('project_key', '')
        issue_type = jira_config.get('default_issue_type', 'Bug')
        priority = jira_config.get('default_priority', 'Medium')

        # Format issues
        issues_summary = "\n".join([
            f"- **{issue.get('severity', 'medium')}**: {issue.get('description', issue.get('message', 'Issue found'))}"
            for issue in bouncer_result.issues_found
        ]) or "- Issues detected by bouncer"

        return f"""Create a Jira ticket for problems found by the {bouncer_result.bouncer_name} bouncer.

## Issues Found
{issues_summary}

## Ticket Details
- Summary: [{bouncer_result.bouncer_name}] Issues in {bouncer_result.file_path.name}
- Project: {project_key}
- Issue Type: {issue_type}
- Priority: {priority}
- File: `{bouncer_result.file_path}`
- Labels: bouncer, automated

Use the Jira MCP `create_issue` tool to create a ticket with the above details.

## Required Response Format
You MUST respond with a JSON object:
{{
  "success": true/false,
  "url": "https://your-domain.atlassian.net/browse/PROJ-123",
  "id": "PROJ-123",
  "message": "Jira ticket created successfully"
}}
"""
