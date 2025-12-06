"""
Tests for path validation security functions in checks/tools.py
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestValidateFilePath:
    """Tests for validate_file_path function"""

    def test_valid_path_in_allowed_dir(self, temp_dir):
        """Test that valid paths in allowed directories pass"""
        from checks.tools import validate_file_path

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # Resolve temp_dir to handle macOS /var -> /private/var symlink
        resolved_temp_dir = temp_dir.resolve()

        # Should succeed with explicit allowed_dirs
        result = validate_file_path(str(test_file), allowed_dirs=[resolved_temp_dir])
        assert result == test_file.resolve()

    def test_path_outside_allowed_dir(self, temp_dir):
        """Test that paths outside allowed directories are rejected"""
        from checks.tools import validate_file_path

        resolved_temp_dir = temp_dir.resolve()

        # Try to access /etc/passwd (outside allowed dir)
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_file_path("/etc/passwd", allowed_dirs=[resolved_temp_dir])

    def test_path_traversal_attack(self, temp_dir):
        """Test that path traversal attacks are blocked"""
        from checks.tools import validate_file_path

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        resolved_temp_dir = temp_dir.resolve()

        # Try path traversal
        traversal_path = str(temp_dir / ".." / ".." / "etc" / "passwd")
        with pytest.raises(ValueError):
            validate_file_path(traversal_path, allowed_dirs=[resolved_temp_dir])

    def test_null_byte_injection(self, temp_dir):
        """Test that null byte injection is blocked"""
        from checks.tools import validate_file_path

        resolved_temp_dir = temp_dir.resolve()

        # Try null byte injection - this should fail either at validation or path resolution
        with pytest.raises((ValueError, OSError)):
            validate_file_path(str(temp_dir) + "/test.py\x00.txt", allowed_dirs=[resolved_temp_dir])

    def test_nonexistent_file(self, temp_dir):
        """Test that nonexistent files are rejected"""
        from checks.tools import validate_file_path

        resolved_temp_dir = temp_dir.resolve()

        with pytest.raises(ValueError, match="does not exist"):
            validate_file_path(str(temp_dir / "nonexistent.py"), allowed_dirs=[resolved_temp_dir])

    def test_directory_not_file(self, temp_dir):
        """Test that directories are rejected"""
        from checks.tools import validate_file_path

        resolved_temp_dir = temp_dir.resolve()

        # temp_dir is a directory, not a file
        with pytest.raises(ValueError, match="not a file"):
            validate_file_path(str(temp_dir), allowed_dirs=[resolved_temp_dir])

    def test_empty_allowed_dirs(self, temp_dir):
        """Test behavior with no allowed directories set"""
        from checks.tools import validate_file_path

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # Should still work with empty allowed_dirs (no restriction)
        result = validate_file_path(str(test_file), allowed_dirs=[])
        assert result == test_file.resolve()

    def test_custom_allowed_dirs(self, temp_dir):
        """Test passing custom allowed_dirs parameter"""
        from checks.tools import validate_file_path

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        resolved_temp_dir = temp_dir.resolve()

        # Pass custom allowed dirs (resolved)
        result = validate_file_path(str(test_file), allowed_dirs=[resolved_temp_dir])
        assert result == test_file.resolve()

    def test_symlink_resolution(self, temp_dir):
        """Test that symlinks are resolved properly"""
        from checks.tools import validate_file_path

        # Create a test file
        test_file = temp_dir / "actual.py"
        test_file.write_text("print('hello')")

        # Create a symlink
        symlink = temp_dir / "link.py"
        try:
            symlink.symlink_to(test_file)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

        resolved_temp_dir = temp_dir.resolve()

        # Symlink should resolve to actual file
        result = validate_file_path(str(symlink), allowed_dirs=[resolved_temp_dir])
        assert result == test_file.resolve()

    def test_symlink_escape_attack(self, temp_dir):
        """Test that symlinks pointing outside allowed dirs are blocked"""
        from checks.tools import validate_file_path

        # Create a subdir as allowed
        subdir = temp_dir / "allowed"
        subdir.mkdir()

        # Create a file outside allowed dir
        outside_file = temp_dir / "outside.py"
        outside_file.write_text("print('outside')")

        # Create a symlink inside allowed dir pointing outside
        symlink = subdir / "escape.py"
        try:
            symlink.symlink_to(outside_file)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

        resolved_subdir = subdir.resolve()

        # Should fail because resolved path is outside allowed dir
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_file_path(str(symlink), allowed_dirs=[resolved_subdir])


class TestSetAllowedDirectories:
    """Tests for set_allowed_directories function"""

    def test_set_single_directory(self, temp_dir):
        """Test setting a single allowed directory"""
        from checks.tools import set_allowed_directories, validate_file_path

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # Set allowed directories
        set_allowed_directories([temp_dir])

        # Should work using the global setting (no explicit allowed_dirs)
        result = validate_file_path(str(test_file))
        assert result == test_file.resolve()

    def test_set_multiple_directories(self, temp_dir):
        """Test setting multiple allowed directories"""
        from checks.tools import set_allowed_directories, validate_file_path

        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Create files in both directories
        file1 = dir1 / "test1.py"
        file2 = dir2 / "test2.py"
        file1.write_text("print('test1')")
        file2.write_text("print('test2')")

        set_allowed_directories([dir1, dir2])

        # Both should be accessible
        result1 = validate_file_path(str(file1))
        result2 = validate_file_path(str(file2))
        assert result1 == file1.resolve()
        assert result2 == file2.resolve()

    def test_clear_allowed_directories(self, temp_dir):
        """Test clearing allowed directories"""
        from checks.tools import set_allowed_directories, validate_file_path

        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        # First set, then clear
        set_allowed_directories([temp_dir])
        set_allowed_directories([])

        # With empty allowed dirs, any valid path should work
        result = validate_file_path(str(test_file))
        assert result == test_file.resolve()
