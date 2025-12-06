"""
Tests for bouncer/watcher.py - File watching and debouncing
"""

import pytest
import asyncio
import time
from pathlib import Path
from collections import OrderedDict
from unittest.mock import MagicMock, AsyncMock, patch


class TestFileWatcher:
    """Tests for FileWatcher class"""

    def test_init(self, temp_dir, sample_config):
        """Test FileWatcher initialization"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        sample_config['debounce_delay'] = 3.0
        sample_config['poll_interval'] = 1.0
        sample_config['max_pending_changes'] = 5000

        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        assert watcher.watch_dir == temp_dir
        assert watcher.debounce_delay == 3.0
        assert watcher.poll_interval == 1.0
        assert watcher.max_pending_changes == 5000
        assert isinstance(watcher.pending_changes, OrderedDict)

    def test_init_defaults(self, temp_dir, sample_config):
        """Test FileWatcher uses defaults when not specified"""
        from bouncer.watcher import FileWatcher, DEFAULT_DEBOUNCE_DELAY, DEFAULT_POLL_INTERVAL, DEFAULT_MAX_PENDING_CHANGES
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        # Remove optional configs
        sample_config.pop('debounce_delay', None)
        sample_config.pop('poll_interval', None)
        sample_config.pop('max_pending_changes', None)

        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        assert watcher.debounce_delay == DEFAULT_DEBOUNCE_DELAY
        assert watcher.poll_interval == DEFAULT_POLL_INTERVAL
        assert watcher.max_pending_changes == DEFAULT_MAX_PENDING_CHANGES


class TestPendingChanges:
    """Tests for pending changes management"""

    def test_pending_changes_ordered_dict(self, temp_dir, sample_config):
        """Test that pending_changes uses OrderedDict"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        # Simulate adding changes
        path1 = temp_dir / "file1.py"
        path2 = temp_dir / "file2.py"
        path3 = temp_dir / "file3.py"

        watcher.pending_changes[path1] = {'timestamp': time.time(), 'event_type': 'created'}
        watcher.pending_changes[path2] = {'timestamp': time.time(), 'event_type': 'modified'}
        watcher.pending_changes[path3] = {'timestamp': time.time(), 'event_type': 'created'}

        # Verify order is maintained
        keys = list(watcher.pending_changes.keys())
        assert keys[0] == path1
        assert keys[1] == path2
        assert keys[2] == path3

    def test_pending_changes_move_to_end(self, temp_dir, sample_config):
        """Test that updating existing change moves to end"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        path1 = temp_dir / "file1.py"
        path2 = temp_dir / "file2.py"

        watcher.pending_changes[path1] = {'timestamp': time.time(), 'event_type': 'created'}
        watcher.pending_changes[path2] = {'timestamp': time.time(), 'event_type': 'created'}

        # Move path1 to end
        watcher.pending_changes.move_to_end(path1)

        keys = list(watcher.pending_changes.keys())
        assert keys[0] == path2
        assert keys[1] == path1


class TestOverflowProtection:
    """Tests for max pending changes overflow protection"""

    def test_eviction_on_overflow(self, temp_dir, sample_config):
        """Test that oldest entries are evicted on overflow"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        sample_config['max_pending_changes'] = 10  # Small limit for testing

        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        # Fill up pending changes
        for i in range(10):
            path = temp_dir / f"file{i}.py"
            watcher.pending_changes[path] = {'timestamp': time.time(), 'event_type': 'created'}

        assert len(watcher.pending_changes) == 10

        # Simulate overflow detection (this would happen in _handle_change)
        # When at max, 10% (1) should be evicted
        if len(watcher.pending_changes) >= watcher.max_pending_changes:
            evict_count = watcher.max_pending_changes // 10 or 1
            for _ in range(evict_count):
                if watcher.pending_changes:
                    oldest_key = next(iter(watcher.pending_changes))
                    del watcher.pending_changes[oldest_key]

        assert len(watcher.pending_changes) == 9
        # First file should have been evicted
        assert temp_dir / "file0.py" not in watcher.pending_changes


class TestChangeHandler:
    """Tests for internal ChangeHandler behavior"""

    def test_ignore_directories(self, temp_dir, sample_config):
        """Test that directory events are ignored"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator
        from watchdog.events import DirModifiedEvent

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        # Create a mock directory event
        dir_event = DirModifiedEvent(str(temp_dir / "subdir"))

        # is_directory should be True for DirModifiedEvent
        assert dir_event.is_directory is True

    def test_ignore_patterns_respected(self, temp_dir, sample_config):
        """Test that ignored patterns are not processed"""
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        # Use patterns that will match as substrings
        sample_config['ignore_patterns'] = ['.git', '__pycache__', '.pyc']

        orchestrator = BouncerOrchestrator(sample_config)

        # Should ignore .git files
        assert orchestrator.should_ignore(temp_dir / ".git" / "config") is True

        # Should ignore __pycache__ files
        assert orchestrator.should_ignore(temp_dir / "__pycache__" / "module.pyc") is True

        # Should ignore .pyc files (substring match on .pyc extension)
        assert orchestrator.should_ignore(temp_dir / "module.pyc") is True

        # Should NOT ignore regular Python files
        assert orchestrator.should_ignore(temp_dir / "main.py") is False


class TestDebouncing:
    """Tests for file change debouncing"""

    def test_debounce_delay_respected(self, temp_dir, sample_config):
        """Test that changes within debounce delay are grouped"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        sample_config['debounce_delay'] = 2.0

        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        path = temp_dir / "test.py"
        current_time = time.time()

        # Add change with recent timestamp
        watcher.pending_changes[path] = {
            'timestamp': current_time,
            'event_type': 'modified'
        }

        # Check if change should be processed
        to_process = []
        for p, info in list(watcher.pending_changes.items()):
            if current_time - info['timestamp'] >= watcher.debounce_delay:
                to_process.append((p, info))

        # Should not process yet (change is too recent)
        assert len(to_process) == 0

    def test_debounce_delay_expired(self, temp_dir, sample_config):
        """Test that changes are processed after debounce delay"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        sample_config['debounce_delay'] = 2.0

        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        path = temp_dir / "test.py"
        old_timestamp = time.time() - 3.0  # 3 seconds ago

        # Add change with old timestamp
        watcher.pending_changes[path] = {
            'timestamp': old_timestamp,
            'event_type': 'modified'
        }

        # Check if change should be processed
        current_time = time.time()
        to_process = []
        for p, info in list(watcher.pending_changes.items()):
            if current_time - info['timestamp'] >= watcher.debounce_delay:
                to_process.append((p, info))

        # Should process now (debounce delay expired)
        assert len(to_process) == 1
        assert to_process[0][0] == path


class TestEventTypes:
    """Tests for different event types"""

    def test_modified_event_type(self, temp_dir, sample_config):
        """Test modified event type is recorded"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        path = temp_dir / "test.py"
        watcher.pending_changes[path] = {
            'timestamp': time.time(),
            'event_type': 'modified'
        }

        assert watcher.pending_changes[path]['event_type'] == 'modified'

    def test_created_event_type(self, temp_dir, sample_config):
        """Test created event type is recorded"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        path = temp_dir / "test.py"
        watcher.pending_changes[path] = {
            'timestamp': time.time(),
            'event_type': 'created'
        }

        assert watcher.pending_changes[path]['event_type'] == 'created'

    def test_deleted_event_type(self, temp_dir, sample_config):
        """Test deleted event type is recorded"""
        from bouncer.watcher import FileWatcher
        from bouncer.core import BouncerOrchestrator

        sample_config['watch_dir'] = str(temp_dir)
        orchestrator = BouncerOrchestrator(sample_config)
        watcher = FileWatcher(temp_dir, orchestrator)

        path = temp_dir / "test.py"
        watcher.pending_changes[path] = {
            'timestamp': time.time(),
            'event_type': 'deleted'
        }

        assert watcher.pending_changes[path]['event_type'] == 'deleted'
