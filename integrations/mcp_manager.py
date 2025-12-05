"""
MCP Manager - Handles Model Context Protocol server configuration
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class MCPManager:
    """
    Manages MCP server configuration and tool permissions.
    
    Dynamically configures MCP servers based on enabled integrations
    and provides the configuration to Claude Agent SDK.
    """
    
    # Available MCP servers and their configurations
    MCP_SERVERS = {
        'github': {
            'package': '@modelcontextprotocol/server-github',
            'env_var': 'GITHUB_PERSONAL_ACCESS_TOKEN',
            'tools': [
                'create_or_update_file',
                'push_files',
                'create_pull_request',
                'create_issue',
                'search_repositories',
                'get_file_contents',
                'list_commits',
                'fork_repository',
                'create_repository'
            ]
        },
        'gitlab': {
            'package': '@modelcontextprotocol/server-gitlab',
            'env_var': 'GITLAB_PERSONAL_ACCESS_TOKEN',
            'tools': [
                'create_merge_request',
                'create_issue',
                'update_file',
                'get_file',
                'list_projects'
            ]
        },
        'linear': {
            'package': '@modelcontextprotocol/server-linear',
            'env_var': 'LINEAR_API_KEY',
            'tools': [
                'create_issue',
                'update_issue',
                'search_issues',
                'get_issue',
                'add_comment'
            ]
        },
        'jira': {
            'package': '@modelcontextprotocol/server-jira',
            'env_var': 'JIRA_API_TOKEN',
            'tools': [
                'create_issue',
                'update_issue',
                'search_issues',
                'add_comment',
                'transition_issue'
            ]
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP Manager with integration configuration.
        
        Args:
            config: Integration configuration from bouncer.yaml
        """
        self.config = config
        self.enabled_integrations = self._get_enabled_integrations()
        
    def _get_enabled_integrations(self) -> List[str]:
        """Get list of enabled integrations from config"""
        enabled = []
        for integration, settings in self.config.items():
            if isinstance(settings, dict) and settings.get('enabled', False):
                enabled.append(integration)
        return enabled
    
    def get_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get MCP server configurations for enabled integrations.
        
        Returns:
            Dict of MCP server configurations ready for ClaudeAgentOptions
        """
        mcp_servers = {}
        
        for integration in self.enabled_integrations:
            if integration not in self.MCP_SERVERS:
                logger.warning(f"Unknown integration: {integration}")
                continue
            
            server_info = self.MCP_SERVERS[integration]
            env_var = server_info['env_var']
            
            # Check if authentication token is available
            if not os.getenv(env_var):
                logger.warning(
                    f"Skipping {integration} integration: "
                    f"{env_var} not set in environment"
                )
                continue
            
            # Configure MCP server
            mcp_servers[integration] = {
                'command': 'npx',
                'args': ['-y', server_info['package']],
                'env': {
                    env_var: f"${{{env_var}}}"
                }
            }
            
            logger.info(f"✅ Configured MCP server: {integration}")
        
        return mcp_servers
    
    def get_allowed_tools(self, 
                         integration: Optional[str] = None,
                         tool_names: Optional[List[str]] = None) -> List[str]:
        """
        Get list of allowed MCP tools.
        
        Args:
            integration: Specific integration to get tools for (or None for all)
            tool_names: Specific tool names to allow (or None for all)
        
        Returns:
            List of fully-qualified MCP tool names
        """
        allowed_tools = []
        
        # Determine which integrations to include
        integrations = [integration] if integration else self.enabled_integrations
        
        for integ in integrations:
            if integ not in self.MCP_SERVERS:
                continue
            
            server_info = self.MCP_SERVERS[integ]
            
            # Filter tools if specific names provided
            if tool_names:
                tools = [t for t in server_info['tools'] if t in tool_names]
            else:
                tools = server_info['tools']
            
            # Add fully-qualified tool names
            for tool in tools:
                allowed_tools.append(f"mcp__{integ}__{tool}")
        
        return allowed_tools
    
    def is_integration_enabled(self, integration: str) -> bool:
        """Check if a specific integration is enabled"""
        return integration in self.enabled_integrations
    
    def get_integration_config(self, integration: str) -> Dict[str, Any]:
        """Get configuration for a specific integration"""
        return self.config.get(integration, {})
    
    def validate_environment(self) -> Dict[str, bool]:
        """
        Validate that required environment variables are set.
        
        Returns:
            Dict mapping integration names to validation status
        """
        validation = {}
        
        for integration in self.enabled_integrations:
            if integration not in self.MCP_SERVERS:
                validation[integration] = False
                continue
            
            env_var = self.MCP_SERVERS[integration]['env_var']
            validation[integration] = bool(os.getenv(env_var))
        
        return validation
    
    def get_missing_credentials(self) -> List[str]:
        """
        Get list of integrations with missing credentials.
        
        Returns:
            List of integration names that are enabled but missing credentials
        """
        missing = []
        validation = self.validate_environment()
        
        for integration, is_valid in validation.items():
            if not is_valid:
                missing.append(integration)
        
        return missing
    
    @staticmethod
    def get_required_env_var(integration: str) -> Optional[str]:
        """Get the required environment variable for an integration"""
        if integration in MCPManager.MCP_SERVERS:
            return MCPManager.MCP_SERVERS[integration]['env_var']
        return None
    
    @staticmethod
    def get_available_integrations() -> List[str]:
        """Get list of all available integrations"""
        return list(MCPManager.MCP_SERVERS.keys())
