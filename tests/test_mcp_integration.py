"""
Tests for MCP (Model Context Protocol) integration

Tests cover:
- MCPManager configuration and validation
- IntegrationActions with structured output parsing
- Integration with core orchestrator
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch


class TestMCPManager:
    """Tests for MCPManager"""

    def test_init_with_empty_config(self):
        """Test MCPManager initialization with empty config"""
        from integrations.mcp_manager import MCPManager

        manager = MCPManager({})

        assert manager.enabled_integrations == []
        assert manager.get_mcp_servers() == {}

    def test_init_with_disabled_integrations(self):
        """Test that disabled integrations are not enabled"""
        from integrations.mcp_manager import MCPManager

        config = {
            'github': {'enabled': False},
            'gitlab': {'enabled': False},
        }
        manager = MCPManager(config)

        assert manager.enabled_integrations == []

    def test_init_with_enabled_integrations(self):
        """Test that enabled integrations are tracked"""
        from integrations.mcp_manager import MCPManager

        config = {
            'github': {'enabled': True},
            'gitlab': {'enabled': True},
            'linear': {'enabled': False},
        }
        manager = MCPManager(config)

        assert 'github' in manager.enabled_integrations
        assert 'gitlab' in manager.enabled_integrations
        assert 'linear' not in manager.enabled_integrations

    def test_is_integration_enabled(self):
        """Test is_integration_enabled method"""
        from integrations.mcp_manager import MCPManager

        config = {
            'github': {'enabled': True},
            'gitlab': {'enabled': False},
        }
        manager = MCPManager(config)

        assert manager.is_integration_enabled('github') is True
        assert manager.is_integration_enabled('gitlab') is False
        assert manager.is_integration_enabled('unknown') is False

    def test_get_integration_config(self):
        """Test getting integration-specific config"""
        from integrations.mcp_manager import MCPManager

        config = {
            'github': {
                'enabled': True,
                'auto_create_pr': True,
                'default_labels': ['bouncer', 'automated']
            },
        }
        manager = MCPManager(config)

        github_config = manager.get_integration_config('github')
        assert github_config['auto_create_pr'] is True
        assert github_config['default_labels'] == ['bouncer', 'automated']

        # Unknown integration returns empty dict
        assert manager.get_integration_config('unknown') == {}

    @patch.dict('os.environ', {'GITHUB_PERSONAL_ACCESS_TOKEN': 'test-token'})
    def test_get_mcp_servers_with_valid_env(self):
        """Test MCP server config generation with valid environment"""
        from integrations.mcp_manager import MCPManager

        config = {'github': {'enabled': True}}
        manager = MCPManager(config)

        servers = manager.get_mcp_servers()

        assert 'github' in servers
        assert servers['github']['command'] == 'npx'
        assert '@modelcontextprotocol/server-github' in servers['github']['args']

    @patch.dict('os.environ', {}, clear=True)
    def test_get_mcp_servers_without_env(self):
        """Test MCP server config when env vars are missing"""
        from integrations.mcp_manager import MCPManager

        config = {'github': {'enabled': True}}
        manager = MCPManager(config)

        servers = manager.get_mcp_servers()

        # Should not include github since GITHUB_PERSONAL_ACCESS_TOKEN is not set
        assert 'github' not in servers

    def test_get_allowed_tools_all(self):
        """Test getting all allowed tools for an integration"""
        from integrations.mcp_manager import MCPManager

        config = {'github': {'enabled': True}}
        manager = MCPManager(config)

        tools = manager.get_allowed_tools(integration='github')

        assert len(tools) > 0
        assert all(t.startswith('mcp__github__') for t in tools)
        assert 'mcp__github__create_pull_request' in tools
        assert 'mcp__github__create_issue' in tools

    def test_get_allowed_tools_filtered(self):
        """Test getting specific allowed tools"""
        from integrations.mcp_manager import MCPManager

        config = {'github': {'enabled': True}}
        manager = MCPManager(config)

        tools = manager.get_allowed_tools(
            integration='github',
            tool_names=['create_issue', 'create_pull_request']
        )

        assert len(tools) == 2
        assert 'mcp__github__create_issue' in tools
        assert 'mcp__github__create_pull_request' in tools

    @patch.dict('os.environ', {'GITHUB_PERSONAL_ACCESS_TOKEN': 'token'})
    def test_validate_environment_valid(self):
        """Test environment validation with valid credentials"""
        from integrations.mcp_manager import MCPManager

        config = {'github': {'enabled': True}}
        manager = MCPManager(config)

        validation = manager.validate_environment()

        assert validation['github'] is True

    @patch.dict('os.environ', {}, clear=True)
    def test_validate_environment_missing(self):
        """Test environment validation with missing credentials"""
        from integrations.mcp_manager import MCPManager

        config = {'github': {'enabled': True}}
        manager = MCPManager(config)

        validation = manager.validate_environment()

        assert validation['github'] is False

    @patch.dict('os.environ', {}, clear=True)
    def test_get_missing_credentials(self):
        """Test getting list of missing credentials"""
        from integrations.mcp_manager import MCPManager

        config = {
            'github': {'enabled': True},
            'gitlab': {'enabled': True},
        }
        manager = MCPManager(config)

        missing = manager.get_missing_credentials()

        assert 'github' in missing
        assert 'gitlab' in missing

    def test_get_required_env_var(self):
        """Test getting required environment variable for integration"""
        from integrations.mcp_manager import MCPManager

        assert MCPManager.get_required_env_var('github') == 'GITHUB_PERSONAL_ACCESS_TOKEN'
        assert MCPManager.get_required_env_var('gitlab') == 'GITLAB_PERSONAL_ACCESS_TOKEN'
        assert MCPManager.get_required_env_var('linear') == 'LINEAR_API_KEY'
        assert MCPManager.get_required_env_var('jira') == 'JIRA_API_TOKEN'
        assert MCPManager.get_required_env_var('unknown') is None

    def test_get_available_integrations(self):
        """Test getting all available integrations"""
        from integrations.mcp_manager import MCPManager

        integrations = MCPManager.get_available_integrations()

        assert 'github' in integrations
        assert 'gitlab' in integrations
        assert 'linear' in integrations
        assert 'jira' in integrations


class TestIntegrationResponseSchema:
    """Tests for structured output response parsing"""

    def test_schema_structure(self):
        """Test that the response schema has required fields"""
        from integrations.actions import INTEGRATION_RESPONSE_SCHEMA

        assert INTEGRATION_RESPONSE_SCHEMA['type'] == 'object'
        assert 'success' in INTEGRATION_RESPONSE_SCHEMA['properties']
        assert 'url' in INTEGRATION_RESPONSE_SCHEMA['properties']
        assert 'message' in INTEGRATION_RESPONSE_SCHEMA['properties']
        assert 'error' in INTEGRATION_RESPONSE_SCHEMA['properties']
        assert 'success' in INTEGRATION_RESPONSE_SCHEMA['required']
        assert 'message' in INTEGRATION_RESPONSE_SCHEMA['required']


class TestIntegrationActions:
    """Tests for IntegrationActions"""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mock MCP manager"""
        manager = MagicMock()
        manager.is_integration_enabled.return_value = True
        manager.get_mcp_servers.return_value = {
            'github': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-github']
            }
        }
        manager.get_integration_config.return_value = {
            'default_labels': ['bouncer', 'automated']
        }
        manager.get_allowed_tools.return_value = ['mcp__github__create_issue']
        return manager

    @pytest.fixture
    def integration_actions(self, mock_mcp_manager, temp_dir):
        """Create IntegrationActions instance"""
        from integrations.actions import IntegrationActions
        return IntegrationActions(mock_mcp_manager, temp_dir)

    @pytest.fixture
    def mock_bouncer_result(self, temp_dir):
        """Create a mock bouncer result"""
        from bouncer.core import BouncerResult
        return BouncerResult(
            bouncer_name='test_bouncer',
            file_path=temp_dir / 'test.py',
            status='denied',
            issues_found=tuple([
                {'severity': 'high', 'description': 'Security issue found'},
                {'severity': 'medium', 'description': 'Code quality issue'}
            ]),
            fixes_applied=tuple([
                {'description': 'Fixed security issue'}
            ]),
            messages=tuple(['Issues found during check']),
            timestamp=12345.0
        )

    def test_parse_structured_response_success(self, integration_actions):
        """Test parsing successful structured response"""
        response = json.dumps({
            'success': True,
            'url': 'https://github.com/test/repo/issues/123',
            'id': '123',
            'message': 'Issue created successfully'
        })

        result = integration_actions._parse_structured_response(response, 'issue_url')

        assert result['success'] is True
        assert result['url'] == 'https://github.com/test/repo/issues/123'
        assert result['issue_url'] == 'https://github.com/test/repo/issues/123'  # Backward compat
        assert result['id'] == '123'
        assert result['message'] == 'Issue created successfully'

    def test_parse_structured_response_failure(self, integration_actions):
        """Test parsing failed structured response"""
        response = json.dumps({
            'success': False,
            'message': 'Failed to create issue',
            'error': 'Authentication failed'
        })

        result = integration_actions._parse_structured_response(response, 'issue_url')

        assert result['success'] is False
        assert result['error'] == 'Authentication failed'
        assert result['message'] == 'Failed to create issue'

    def test_parse_structured_response_invalid_json(self, integration_actions):
        """Test parsing invalid JSON response"""
        response = "This is not valid JSON"

        result = integration_actions._parse_structured_response(response, 'issue_url')

        assert result['success'] is False
        assert 'Could not parse response as JSON' in result['error']
        assert 'raw_response' in result

    @pytest.mark.asyncio
    async def test_create_github_issue_disabled(self, integration_actions, mock_bouncer_result):
        """Test creating issue when GitHub is disabled"""
        integration_actions.mcp_manager.is_integration_enabled.return_value = False

        result = await integration_actions.create_github_issue(mock_bouncer_result)

        assert result['success'] is False
        assert 'not enabled' in result['error']

    @pytest.mark.asyncio
    async def test_create_github_pr_disabled(self, integration_actions, mock_bouncer_result):
        """Test creating PR when GitHub is disabled"""
        integration_actions.mcp_manager.is_integration_enabled.return_value = False

        result = await integration_actions.create_github_pr(mock_bouncer_result)

        assert result['success'] is False
        assert 'not enabled' in result['error']

    @pytest.mark.asyncio
    async def test_create_gitlab_mr_disabled(self, integration_actions, mock_bouncer_result):
        """Test creating MR when GitLab is disabled"""
        integration_actions.mcp_manager.is_integration_enabled.return_value = False

        result = await integration_actions.create_gitlab_mr(mock_bouncer_result)

        assert result['success'] is False
        assert 'not enabled' in result['error']

    @pytest.mark.asyncio
    async def test_create_gitlab_issue_disabled(self, integration_actions, mock_bouncer_result):
        """Test creating issue when GitLab is disabled"""
        integration_actions.mcp_manager.is_integration_enabled.return_value = False

        result = await integration_actions.create_gitlab_issue(mock_bouncer_result)

        assert result['success'] is False
        assert 'not enabled' in result['error']

    @pytest.mark.asyncio
    async def test_create_linear_issue_disabled(self, integration_actions, mock_bouncer_result):
        """Test creating issue when Linear is disabled"""
        integration_actions.mcp_manager.is_integration_enabled.return_value = False

        result = await integration_actions.create_linear_issue(mock_bouncer_result)

        assert result['success'] is False
        assert 'not enabled' in result['error']

    @pytest.mark.asyncio
    async def test_create_jira_ticket_disabled(self, integration_actions, mock_bouncer_result):
        """Test creating ticket when Jira is disabled"""
        integration_actions.mcp_manager.is_integration_enabled.return_value = False

        result = await integration_actions.create_jira_ticket(mock_bouncer_result)

        assert result['success'] is False
        assert 'not enabled' in result['error']

    @pytest.mark.asyncio
    async def test_create_github_pr_no_server(self, integration_actions, mock_bouncer_result):
        """Test creating PR when MCP server is not configured"""
        integration_actions.mcp_manager.get_mcp_servers.return_value = {}

        result = await integration_actions.create_github_pr(mock_bouncer_result)

        assert result['success'] is False
        assert 'not configured' in result['error']

    def test_build_pr_prompt(self, integration_actions, mock_bouncer_result):
        """Test PR prompt generation"""
        prompt = integration_actions._build_pr_prompt(
            mock_bouncer_result,
            'bouncer/test/20240101-120000',
            {'default_labels': ['bouncer']}
        )

        assert 'test_bouncer' in prompt
        assert 'bouncer/test/20240101-120000' in prompt
        assert 'Fixed security issue' in prompt
        assert 'Required Response Format' in prompt
        assert '"success"' in prompt

    def test_build_issue_prompt(self, integration_actions, mock_bouncer_result):
        """Test issue prompt generation"""
        prompt = integration_actions._build_issue_prompt(
            mock_bouncer_result,
            {'default_labels': ['bouncer', 'automated']}
        )

        assert 'test_bouncer' in prompt
        assert 'Security issue found' in prompt
        assert 'bouncer, automated' in prompt
        assert 'Required Response Format' in prompt

    def test_build_gitlab_mr_prompt(self, integration_actions, mock_bouncer_result):
        """Test GitLab MR prompt generation"""
        prompt = integration_actions._build_gitlab_mr_prompt(
            mock_bouncer_result,
            'bouncer/test/20240101-120000',
            {}
        )

        assert 'GitLab Merge Request' in prompt
        assert 'test_bouncer' in prompt
        assert 'bouncer/test/20240101-120000' in prompt

    def test_build_gitlab_issue_prompt(self, integration_actions, mock_bouncer_result):
        """Test GitLab issue prompt generation"""
        prompt = integration_actions._build_gitlab_issue_prompt(
            mock_bouncer_result,
            {}
        )

        assert 'GitLab issue' in prompt
        assert 'test_bouncer' in prompt

    def test_build_linear_issue_prompt(self, integration_actions, mock_bouncer_result):
        """Test Linear issue prompt generation"""
        prompt = integration_actions._build_linear_issue_prompt(
            mock_bouncer_result,
            {'project_id': 'PROJ-1', 'team_id': 'TEAM-1'}
        )

        assert 'Linear issue' in prompt
        assert 'PROJ-1' in prompt
        assert 'TEAM-1' in prompt

    def test_build_jira_ticket_prompt(self, integration_actions, mock_bouncer_result):
        """Test Jira ticket prompt generation"""
        prompt = integration_actions._build_jira_ticket_prompt(
            mock_bouncer_result,
            {'project_key': 'TEST', 'default_issue_type': 'Bug'}
        )

        assert 'Jira ticket' in prompt
        assert 'TEST' in prompt
        assert 'Bug' in prompt


class TestIntegrationWithOrchestrator:
    """Tests for integration between MCP and BouncerOrchestrator"""

    @pytest.fixture
    def config_with_integrations(self, temp_dir):
        """Config with integrations enabled"""
        return {
            'watch_dir': str(temp_dir),
            'debounce_delay': 2,
            'ignore_patterns': ['.git'],
            'bouncers': {},
            'notifications': {},
            'integrations': {
                'github': {
                    'enabled': True,
                    'auto_create_pr': True,
                    'auto_create_issue': True
                }
            }
        }

    def test_orchestrator_initializes_mcp_manager(self, config_with_integrations, temp_dir):
        """Test that orchestrator creates MCP manager when integrations configured"""
        from bouncer.core import BouncerOrchestrator

        orchestrator = BouncerOrchestrator(config_with_integrations)

        assert orchestrator.mcp_manager is not None
        assert orchestrator.integration_actions is not None

    def test_orchestrator_without_integrations(self, sample_config, temp_dir):
        """Test orchestrator without integrations section"""
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)

        # Without integrations section, MCP manager is None
        assert orchestrator.mcp_manager is None
        assert orchestrator.integration_actions is None

    @pytest.mark.asyncio
    @patch.dict('os.environ', {'GITHUB_PERSONAL_ACCESS_TOKEN': 'test-token'})
    async def test_handle_integrations_github_pr(self, config_with_integrations, temp_dir):
        """Test handling GitHub PR creation from bouncer result"""
        from bouncer.core import BouncerOrchestrator, BouncerResult

        orchestrator = BouncerOrchestrator(config_with_integrations)

        # Create result with fixes applied
        result = BouncerResult(
            bouncer_name='test_bouncer',
            file_path=temp_dir / 'test.py',
            status='fixed',
            issues_found=tuple(),
            fixes_applied=tuple([{'description': 'Fixed issue'}]),
            messages=tuple(),
            timestamp=12345.0
        )

        # Mock the integration actions
        orchestrator.integration_actions.create_github_pr = AsyncMock(
            return_value={'success': True, 'url': 'https://github.com/test/pr/1'}
        )

        # _handle_integrations takes a list of results
        await orchestrator._handle_integrations([result])

        # Verify PR creation was called
        orchestrator.integration_actions.create_github_pr.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict('os.environ', {'GITHUB_PERSONAL_ACCESS_TOKEN': 'test-token'})
    async def test_handle_integrations_github_issue(self, config_with_integrations, temp_dir):
        """Test handling GitHub issue creation from bouncer result"""
        from bouncer.core import BouncerOrchestrator, BouncerResult

        orchestrator = BouncerOrchestrator(config_with_integrations)

        # Create result with issues found
        result = BouncerResult(
            bouncer_name='test_bouncer',
            file_path=temp_dir / 'test.py',
            status='denied',
            issues_found=tuple([{'description': 'Issue found'}]),
            fixes_applied=tuple(),
            messages=tuple(),
            timestamp=12345.0
        )

        # Mock the integration actions
        orchestrator.integration_actions.create_github_issue = AsyncMock(
            return_value={'success': True, 'url': 'https://github.com/test/issues/1'}
        )

        # _handle_integrations takes a list of results
        await orchestrator._handle_integrations([result])

        # Verify issue creation was called
        orchestrator.integration_actions.create_github_issue.assert_called_once()


class TestMCPServerConfigurations:
    """Tests for MCP server configuration constants"""

    def test_all_servers_have_required_fields(self):
        """Test that all MCP server configs have required fields"""
        from integrations.mcp_manager import MCPManager

        required_fields = ['package', 'env_var', 'tools']

        for server_name, config in MCPManager.MCP_SERVERS.items():
            for field in required_fields:
                assert field in config, f"{server_name} missing {field}"
            assert len(config['tools']) > 0, f"{server_name} has no tools"

    def test_github_server_tools(self):
        """Test GitHub server has expected tools"""
        from integrations.mcp_manager import MCPManager

        github_tools = MCPManager.MCP_SERVERS['github']['tools']

        expected_tools = [
            'create_or_update_file',
            'push_files',
            'create_pull_request',
            'create_issue',
        ]

        for tool in expected_tools:
            assert tool in github_tools

    def test_gitlab_server_tools(self):
        """Test GitLab server has expected tools"""
        from integrations.mcp_manager import MCPManager

        gitlab_tools = MCPManager.MCP_SERVERS['gitlab']['tools']

        expected_tools = [
            'create_merge_request',
            'create_issue',
            'update_file',
        ]

        for tool in expected_tools:
            assert tool in gitlab_tools

    def test_linear_server_tools(self):
        """Test Linear server has expected tools"""
        from integrations.mcp_manager import MCPManager

        linear_tools = MCPManager.MCP_SERVERS['linear']['tools']

        expected_tools = ['create_issue', 'update_issue']

        for tool in expected_tools:
            assert tool in linear_tools

    def test_jira_server_tools(self):
        """Test Jira server has expected tools"""
        from integrations.mcp_manager import MCPManager

        jira_tools = MCPManager.MCP_SERVERS['jira']['tools']

        expected_tools = ['create_issue', 'update_issue', 'add_comment']

        for tool in expected_tools:
            assert tool in jira_tools
