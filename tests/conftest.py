"""
Pytest configuration and fixtures for Bouncer tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'watch_dir': '.',
        'debounce_delay': 2,
        'ignore_patterns': ['.git', '__pycache__', '*.pyc'],
        'bouncers': {
            'code_quality': {
                'enabled': True,
                'file_types': ['.py', '.js'],
                'auto_fix': False,
                'checks': ['syntax', 'linting']
            },
            'security': {
                'enabled': True,
                'file_types': ['.py', '.js'],
                'auto_fix': False,
                'severity_threshold': 'medium'
            }
        },
        'notifications': {
            'file_log': {
                'enabled': True,
                'log_dir': '.bouncer/logs',
                'rotation': 'daily'
            }
        }
    }


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing"""
    file_path = temp_dir / "sample.py"
    file_path.write_text('''
def hello_world():
    """A simple function"""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
''')
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing"""
    file_path = temp_dir / "sample.json"
    file_path.write_text('{"name": "test", "value": 123}')
    return file_path


@pytest.fixture
def sample_yaml_file(temp_dir):
    """Create a sample YAML file for testing"""
    file_path = temp_dir / "sample.yaml"
    file_path.write_text('name: test\nvalue: 123\n')
    return file_path


@pytest.fixture
def mock_claude_client():
    """Mock Claude SDK client for testing without API calls"""
    with patch('claude_agent_sdk.ClaudeSDKClient') as mock_client:
        # Create async context manager mock
        async_cm = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=async_cm)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock query method
        async_cm.query = AsyncMock()

        # Mock receive_response to return structured JSON
        async def mock_response():
            mock_msg = MagicMock()
            mock_block = MagicMock()
            mock_block.text = '{"status": "clean", "issues": [], "fixes": [], "messages": ["All checks passed"]}'
            mock_msg.content = [mock_block]
            yield mock_msg

        async_cm.receive_response = mock_response

        yield mock_client


@pytest.fixture
def file_change_event(sample_python_file):
    """Create a sample FileChangeEvent"""
    from bouncer.core import FileChangeEvent
    import time

    return FileChangeEvent(
        path=sample_python_file,
        event_type='modified',
        timestamp=time.time()
    )
