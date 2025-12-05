"""
Integration Actions - Create PRs, issues, and tickets using MCP
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


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
        
        # Configure Claude Agent SDK with GitHub MCP
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='github',
                tool_names=['create_or_update_file', 'push_files', 'create_pull_request']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan'
        )
        
        # Build prompt for PR creation
        prompt = self._build_pr_prompt(bouncer_result, branch_name, github_config)
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        response_text += msg.content
                
                # Parse response
                result = self._parse_pr_response(response_text)
                
                if result.get('success'):
                    logger.info(f"✅ Created GitHub PR: {result.get('pr_url')}")
                else:
                    logger.error(f"❌ Failed to create PR: {result.get('error')}")
                
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
        
        # Configure Claude Agent SDK
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='github',
                tool_names=['create_issue']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan'
        )
        
        # Build prompt for issue creation
        prompt = self._build_issue_prompt(bouncer_result, github_config)
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        response_text += msg.content
                
                # Parse response
                result = self._parse_issue_response(response_text)
                
                if result.get('success'):
                    logger.info(f"✅ Created GitHub issue: {result.get('issue_url')}")
                else:
                    logger.error(f"❌ Failed to create issue: {result.get('error')}")
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
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
        
        # Configure Claude Agent SDK
        options = ClaudeAgentOptions(
            cwd=str(self.codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=self.mcp_manager.get_allowed_tools(
                integration='linear',
                tool_names=['create_issue']
            ),
            permission_mode='acceptEdits' if auto_create else 'plan'
        )
        
        # Build prompt for issue creation
        prompt = self._build_linear_issue_prompt(bouncer_result, linear_config)
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                
                response_text = ""
                async for msg in client.receive_response():
                    if hasattr(msg, 'content'):
                        response_text += msg.content
                
                # Parse response
                result = self._parse_linear_response(response_text)
                
                if result.get('success'):
                    logger.info(f"✅ Created Linear issue: {result.get('issue_url')}")
                else:
                    logger.error(f"❌ Failed to create issue: {result.get('error')}")
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to create Linear issue: {e}")
            return {'success': False, 'error': str(e)}
    
    def _build_pr_prompt(self, 
                        bouncer_result, 
                        branch_name: str,
                        github_config: Dict[str, Any]) -> str:
        """Build prompt for GitHub PR creation"""
        
        # Get branch prefix from config
        branch_prefix = github_config.get('branch_prefix', 'bouncer')
        
        # Format fixes
        fixes_summary = "\n".join([
            f"- {fix.get('description', 'Fix applied')}"
            for fix in bouncer_result.fixes_applied
        ])
        
        prompt = f"""# Create GitHub Pull Request

You need to create a GitHub Pull Request with fixes from the {bouncer_result.bouncer_name} bouncer.

## Fixes to Apply

{fixes_summary}

## PR Details

**Branch name:** {branch_name}
**Title:** Fix: Issues found by {bouncer_result.bouncer_name}
**Description:**

This PR addresses issues found by the {bouncer_result.bouncer_name} bouncer:

{fixes_summary}

**File:** {bouncer_result.file_path}

## Steps

1. Create a new branch: `{branch_name}`
2. Apply the fixes to the appropriate files
3. Commit the changes with a descriptive message
4. Push the branch
5. Create a pull request with the title and description above

Use the GitHub MCP tools to complete these steps.
"""
        
        return prompt
    
    def _build_issue_prompt(self,
                           bouncer_result,
                           github_config: Dict[str, Any]) -> str:
        """Build prompt for GitHub issue creation"""
        
        # Format issues
        issues_summary = "\n".join([
            f"- **{issue.get('severity', 'medium')}**: {issue.get('description', 'Issue found')}"
            for issue in bouncer_result.issues_found
        ])
        
        prompt = f"""# Create GitHub Issue

You need to create a GitHub issue for problems found by the {bouncer_result.bouncer_name} bouncer.

## Issues Found

{issues_summary}

## Issue Details

**Title:** [{bouncer_result.bouncer_name}] Issues found in {bouncer_result.file_path.name}

**Description:**

The {bouncer_result.bouncer_name} bouncer found the following issues:

{issues_summary}

**File:** `{bouncer_result.file_path}`

**Labels:** bouncer, {bouncer_result.bouncer_name}, automated

## Steps

Use the GitHub MCP `create_issue` tool to create an issue with the above details.
"""
        
        return prompt
    
    def _build_linear_issue_prompt(self,
                                   bouncer_result,
                                   linear_config: Dict[str, Any]) -> str:
        """Build prompt for Linear issue creation"""
        
        # Get project/team from config
        project_id = linear_config.get('project_id', '')
        team_id = linear_config.get('team_id', '')
        
        # Format issues
        issues_summary = "\n".join([
            f"- **{issue.get('severity', 'medium')}**: {issue.get('description', 'Issue found')}"
            for issue in bouncer_result.issues_found
        ])
        
        prompt = f"""# Create Linear Issue

You need to create a Linear issue for problems found by the {bouncer_result.bouncer_name} bouncer.

## Issues Found

{issues_summary}

## Issue Details

**Title:** [{bouncer_result.bouncer_name}] Issues in {bouncer_result.file_path.name}

**Description:**

The {bouncer_result.bouncer_name} bouncer found the following issues:

{issues_summary}

**File:** `{bouncer_result.file_path}`

**Project:** {project_id}
**Team:** {team_id}

## Steps

Use the Linear MCP `create_issue` tool to create an issue with the above details.
"""
        
        return prompt
    
    def _parse_pr_response(self, response: str) -> Dict[str, Any]:
        """Parse PR creation response"""
        # Try to extract PR URL from response
        # This is a simplified parser - actual implementation would be more robust
        try:
            if 'pull' in response.lower() and 'http' in response:
                # Extract URL (simplified)
                import re
                url_match = re.search(r'https://github\.com/[^\s]+', response)
                if url_match:
                    return {
                        'success': True,
                        'pr_url': url_match.group(0),
                        'message': 'Pull request created successfully'
                    }
            
            return {
                'success': False,
                'error': 'Could not parse PR response',
                'raw_response': response
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_issue_response(self, response: str) -> Dict[str, Any]:
        """Parse issue creation response"""
        try:
            if 'issue' in response.lower() and 'http' in response:
                import re
                url_match = re.search(r'https://github\.com/[^\s]+', response)
                if url_match:
                    return {
                        'success': True,
                        'issue_url': url_match.group(0),
                        'message': 'Issue created successfully'
                    }
            
            return {
                'success': False,
                'error': 'Could not parse issue response',
                'raw_response': response
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_linear_response(self, response: str) -> Dict[str, Any]:
        """Parse Linear issue creation response"""
        try:
            if 'issue' in response.lower() and 'http' in response:
                import re
                url_match = re.search(r'https://linear\.app/[^\s]+', response)
                if url_match:
                    return {
                        'success': True,
                        'issue_url': url_match.group(0),
                        'message': 'Linear issue created successfully'
                    }
            
            return {
                'success': False,
                'error': 'Could not parse Linear response',
                'raw_response': response
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
