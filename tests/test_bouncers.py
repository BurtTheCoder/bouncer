"""
Tests for bouncers/base.py and bouncer implementations
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestBaseBouncer:
    """Tests for BaseBouncer base class"""

    def test_init_with_defaults(self):
        """Test bouncer initialization with default config"""
        from bouncers.base import BaseBouncer

        # Create a concrete implementation for testing
        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        config = {}
        bouncer = TestBouncer(config)

        assert bouncer.enabled is True
        assert bouncer.file_types == []
        assert bouncer.auto_fix is False
        assert bouncer.name == 'Test'

    def test_init_with_custom_config(self):
        """Test bouncer initialization with custom config"""
        from bouncers.base import BaseBouncer

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        config = {
            'enabled': False,
            'file_types': ['.py', '.js'],
            'auto_fix': True
        }
        bouncer = TestBouncer(config)

        assert bouncer.enabled is False
        assert bouncer.file_types == ['.py', '.js']
        assert bouncer.auto_fix is True

    @pytest.mark.asyncio
    async def test_should_check_disabled_bouncer(self, file_change_event):
        """Test that disabled bouncers return False for should_check"""
        from bouncers.base import BaseBouncer

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({'enabled': False})
        result = await bouncer.should_check(file_change_event)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_check_matching_file_type(self, sample_python_file):
        """Test should_check with matching file type"""
        from bouncers.base import BaseBouncer
        from bouncer.core import FileChangeEvent
        import time

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({
            'enabled': True,
            'file_types': ['.py']
        })

        event = FileChangeEvent(
            path=sample_python_file,
            event_type='modified',
            timestamp=time.time()
        )

        result = await bouncer.should_check(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_check_non_matching_file_type(self, sample_json_file):
        """Test should_check with non-matching file type"""
        from bouncers.base import BaseBouncer
        from bouncer.core import FileChangeEvent
        import time

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({
            'enabled': True,
            'file_types': ['.py']  # Only Python files
        })

        event = FileChangeEvent(
            path=sample_json_file,  # JSON file
            event_type='modified',
            timestamp=time.time()
        )

        result = await bouncer.should_check(event)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_check_empty_file_types(self, sample_python_file):
        """Test should_check with empty file_types (accept all)"""
        from bouncers.base import BaseBouncer
        from bouncer.core import FileChangeEvent
        import time

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({
            'enabled': True,
            'file_types': []  # Accept all files
        })

        event = FileChangeEvent(
            path=sample_python_file,
            event_type='modified',
            timestamp=time.time()
        )

        result = await bouncer.should_check(event)
        assert result is True

    def test_create_result_with_defaults(self, file_change_event):
        """Test _create_result helper with default values"""
        from bouncers.base import BaseBouncer

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({})
        result = bouncer._create_result(file_change_event, 'approved')

        assert result.bouncer_name == 'Test'
        assert result.status == 'approved'
        assert result.issues_found == ()
        assert result.fixes_applied == ()
        assert result.messages == ()

    def test_create_result_with_data(self, file_change_event):
        """Test _create_result helper with actual data"""
        from bouncers.base import BaseBouncer

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({})
        issues = [{'type': 'error', 'message': 'Test error'}]
        fixes = [{'type': 'fix', 'description': 'Fixed something'}]
        messages = ['Check completed']

        result = bouncer._create_result(
            file_change_event,
            'denied',
            issues_found=issues,
            fixes_applied=fixes,
            messages=messages
        )

        assert result.status == 'denied'
        assert len(result.issues_found) == 1
        assert result.issues_found[0]['type'] == 'error'
        assert len(result.fixes_applied) == 1
        assert len(result.messages) == 1

    def test_create_result_immutability(self, file_change_event):
        """Test that created results are immutable"""
        from bouncers.base import BaseBouncer
        from dataclasses import FrozenInstanceError

        class TestBouncer(BaseBouncer):
            async def check(self, event):
                pass

        bouncer = TestBouncer({})
        result = bouncer._create_result(file_change_event, 'approved')

        with pytest.raises(FrozenInstanceError):
            result.status = 'denied'


class TestCodeQualityBouncer:
    """Tests for CodeQualityBouncer"""

    def test_init(self):
        """Test CodeQualityBouncer initialization"""
        from bouncers.code_quality import CodeQualityBouncer

        config = {
            'enabled': True,
            'file_types': ['.py'],
            'checks': ['syntax', 'linting']
        }
        bouncer = CodeQualityBouncer(config)

        assert bouncer.enabled is True
        assert '.py' in bouncer.file_types

    @pytest.mark.asyncio
    async def test_should_check_python_file(self, sample_python_file):
        """Test that CodeQualityBouncer checks Python files"""
        from bouncers.code_quality import CodeQualityBouncer
        from bouncer.core import FileChangeEvent
        import time

        bouncer = CodeQualityBouncer({
            'enabled': True,
            'file_types': ['.py']
        })

        event = FileChangeEvent(
            path=sample_python_file,
            event_type='modified',
            timestamp=time.time()
        )

        result = await bouncer.should_check(event)
        assert result is True


class TestSecurityBouncer:
    """Tests for SecurityBouncer"""

    def test_init(self):
        """Test SecurityBouncer initialization"""
        from bouncers.security import SecurityBouncer

        config = {
            'enabled': True,
            'severity_threshold': 'medium'
        }
        bouncer = SecurityBouncer(config)

        assert bouncer.enabled is True
        assert bouncer.severity_threshold == 'medium'


class TestLicenseBouncer:
    """Tests for LicenseBouncer"""

    def test_init(self):
        """Test LicenseBouncer initialization"""
        from bouncers.license import LicenseBouncer

        config = {
            'enabled': True,
            'project_license': 'MIT',
            'require_headers': True
        }
        bouncer = LicenseBouncer(config)

        assert bouncer.project_license == 'MIT'
        assert bouncer.require_headers is True

    def test_default_license(self):
        """Test LicenseBouncer default license"""
        from bouncers.license import LicenseBouncer

        bouncer = LicenseBouncer({})
        assert bouncer.project_license == 'MIT'


class TestLogInvestigator:
    """Tests for LogInvestigator"""

    def test_init(self, temp_dir):
        """Test LogInvestigator initialization"""
        from bouncers.log_investigator import LogInvestigator

        config = {
            'log_dir': str(temp_dir),
            'codebase_dir': str(temp_dir),
            'log_patterns': ['*.log'],
            'error_levels': ['ERROR', 'CRITICAL']
        }
        bouncer = LogInvestigator(config)

        assert bouncer.log_dir == temp_dir
        assert bouncer.error_levels == ['ERROR', 'CRITICAL']

    def test_extract_timestamp(self, temp_dir):
        """Test timestamp extraction from log lines"""
        from bouncers.log_investigator import LogInvestigator

        bouncer = LogInvestigator({'log_dir': str(temp_dir)})

        # ISO format
        result = bouncer._extract_timestamp('2024-12-05 10:30:45 ERROR message')
        assert result == '2024-12-05 10:30:45'

        # Bracketed format
        result = bouncer._extract_timestamp('[2024-12-05 10:30:45] ERROR message')
        assert result == '2024-12-05 10:30:45'

    def test_extract_level(self, temp_dir):
        """Test error level extraction"""
        from bouncers.log_investigator import LogInvestigator

        bouncer = LogInvestigator({'log_dir': str(temp_dir)})

        assert bouncer._extract_level('2024-12-05 ERROR message') == 'ERROR'
        assert bouncer._extract_level('CRITICAL: something bad') == 'CRITICAL'
        assert bouncer._extract_level('normal log line') == 'ERROR'  # Default

    def test_extract_file_info_python(self, temp_dir):
        """Test file info extraction from Python stack trace"""
        from bouncers.log_investigator import LogInvestigator

        bouncer = LogInvestigator({'log_dir': str(temp_dir)})

        line = '  File "/app/main.py", line 42, in function'
        result = bouncer._extract_file_info(line)

        assert result is not None
        assert result['file'] == '/app/main.py'
        assert result['line'] == 42

    def test_extract_file_info_javascript(self, temp_dir):
        """Test file info extraction from JavaScript stack trace"""
        from bouncers.log_investigator import LogInvestigator

        bouncer = LogInvestigator({'log_dir': str(temp_dir)})

        line = '    at /app/index.js:123:45'
        result = bouncer._extract_file_info(line)

        assert result is not None
        assert result['file'] == '/app/index.js'
        assert result['line'] == 123

    def test_hash_error(self, temp_dir):
        """Test error hashing for deduplication"""
        from bouncers.log_investigator import LogInvestigator

        bouncer = LogInvestigator({'log_dir': str(temp_dir)})

        error1 = {'message': 'Test error', 'file_path': '/app/main.py', 'line_number': 42}
        error2 = {'message': 'Test error', 'file_path': '/app/main.py', 'line_number': 42}
        error3 = {'message': 'Different error', 'file_path': '/app/main.py', 'line_number': 42}

        hash1 = bouncer._hash_error(error1)
        hash2 = bouncer._hash_error(error2)
        hash3 = bouncer._hash_error(error3)

        assert hash1 == hash2  # Same error should have same hash
        assert hash1 != hash3  # Different errors should have different hashes
