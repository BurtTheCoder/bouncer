"""
Tests for bouncer/core.py - Core orchestrator and data classes
"""

import pytest
import asyncio
from pathlib import Path
from dataclasses import FrozenInstanceError


class TestFileChangeEvent:
    """Tests for FileChangeEvent dataclass"""

    def test_create_event_with_defaults(self, temp_dir):
        """Test creating event with default metadata"""
        from bouncer.core import FileChangeEvent

        event = FileChangeEvent(
            path=temp_dir / "test.py",
            event_type='modified',
            timestamp=123.456
        )

        assert event.path == temp_dir / "test.py"
        assert event.event_type == 'modified'
        assert event.timestamp == 123.456
        assert event.metadata == {}  # Default empty dict

    def test_create_event_with_metadata(self, temp_dir):
        """Test creating event with custom metadata"""
        from bouncer.core import FileChangeEvent

        metadata = {'size': 1024, 'author': 'test'}
        event = FileChangeEvent(
            path=temp_dir / "test.py",
            event_type='created',
            timestamp=123.456,
            metadata=metadata
        )

        assert event.metadata == metadata


class TestBouncerResult:
    """Tests for BouncerResult dataclass"""

    def test_create_result(self, temp_dir):
        """Test creating a bouncer result"""
        from bouncer.core import BouncerResult

        result = BouncerResult(
            bouncer_name='test_bouncer',
            file_path=temp_dir / "test.py",
            status='approved',
            issues_found=tuple([{'issue': 'test'}]),
            fixes_applied=tuple(),
            messages=tuple(['Test message']),
            timestamp=123.456
        )

        assert result.bouncer_name == 'test_bouncer'
        assert result.status == 'approved'
        assert len(result.issues_found) == 1
        assert len(result.messages) == 1

    def test_result_is_immutable(self, temp_dir):
        """Test that BouncerResult is frozen/immutable"""
        from bouncer.core import BouncerResult

        result = BouncerResult(
            bouncer_name='test_bouncer',
            file_path=temp_dir / "test.py",
            status='approved',
            issues_found=tuple(),
            fixes_applied=tuple(),
            messages=tuple(),
            timestamp=123.456
        )

        with pytest.raises(FrozenInstanceError):
            result.status = 'denied'


class TestBouncerOrchestrator:
    """Tests for BouncerOrchestrator"""

    def test_init_with_config(self, sample_config, temp_dir):
        """Test orchestrator initialization"""
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)

        # watch_dir is now resolved to handle symlinks (e.g., macOS /var -> /private/var)
        assert orchestrator.watch_dir == temp_dir.resolve()
        assert orchestrator.running is False
        assert orchestrator.event_queue.maxsize == 1000  # Default
        assert orchestrator.results_queue.maxsize == 1000  # Default

    def test_init_with_custom_queue_sizes(self, sample_config, temp_dir):
        """Test orchestrator with custom queue sizes"""
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        sample_config['event_queue_size'] = 500
        sample_config['results_queue_size'] = 250

        orchestrator = BouncerOrchestrator(sample_config)

        assert orchestrator.event_queue.maxsize == 500
        assert orchestrator.results_queue.maxsize == 250

    def test_register_bouncer(self, sample_config, temp_dir):
        """Test bouncer registration"""
        from bouncer.core import BouncerOrchestrator
        from unittest.mock import MagicMock

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)

        mock_bouncer = MagicMock()
        mock_bouncer.name = 'test_bouncer'

        orchestrator.register_bouncer('test', mock_bouncer)

        assert 'test' in orchestrator.bouncers
        assert orchestrator.bouncers['test'] == mock_bouncer

    def test_should_ignore_patterns(self, sample_config, temp_dir):
        """Test file ignore patterns"""
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        # Use patterns that will match as substrings
        sample_config['ignore_patterns'] = ['.git', '__pycache__', '.pyc']
        orchestrator = BouncerOrchestrator(sample_config)

        # Should ignore .git
        assert orchestrator.should_ignore(temp_dir / ".git" / "config") is True

        # Should ignore __pycache__
        assert orchestrator.should_ignore(temp_dir / "__pycache__" / "module.pyc") is True

        # Should ignore .pyc files (pattern is substring match)
        assert orchestrator.should_ignore(temp_dir / "module.pyc") is True

        # Should NOT ignore regular Python files
        assert orchestrator.should_ignore(temp_dir / "main.py") is False


class TestGitSinceValidation:
    """Tests for git --since parameter validation"""

    def test_valid_time_ago_patterns(self):
        """Test valid 'N units ago' patterns"""
        from bouncer.core import BouncerOrchestrator

        assert BouncerOrchestrator._validate_git_since_param('1 hour ago') is True
        assert BouncerOrchestrator._validate_git_since_param('24 hours ago') is True
        assert BouncerOrchestrator._validate_git_since_param('2 days ago') is True
        assert BouncerOrchestrator._validate_git_since_param('1 week ago') is True
        assert BouncerOrchestrator._validate_git_since_param('3 months ago') is True
        assert BouncerOrchestrator._validate_git_since_param('1 year ago') is True

    def test_valid_date_patterns(self):
        """Test valid date patterns"""
        from bouncer.core import BouncerOrchestrator

        assert BouncerOrchestrator._validate_git_since_param('2023-01-01') is True
        assert BouncerOrchestrator._validate_git_since_param('2024-12-31') is True
        assert BouncerOrchestrator._validate_git_since_param('yesterday') is True
        assert BouncerOrchestrator._validate_git_since_param('today') is True

    def test_invalid_injection_attempts(self):
        """Test that injection attempts are blocked"""
        from bouncer.core import BouncerOrchestrator

        # Command injection attempts
        assert BouncerOrchestrator._validate_git_since_param('; rm -rf /') is False
        assert BouncerOrchestrator._validate_git_since_param('$(whoami)') is False
        assert BouncerOrchestrator._validate_git_since_param('`id`') is False
        assert BouncerOrchestrator._validate_git_since_param('1 hour ago; cat /etc/passwd') is False
        assert BouncerOrchestrator._validate_git_since_param('--exec=rm') is False

    def test_empty_and_none(self):
        """Test empty and None values"""
        from bouncer.core import BouncerOrchestrator

        assert BouncerOrchestrator._validate_git_since_param('') is False
        assert BouncerOrchestrator._validate_git_since_param(None) is False
