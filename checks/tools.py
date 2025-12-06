"""
Path validation and security tools for Bouncer
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global allowed directories for path validation (set by orchestrator)
_allowed_directories: list[Path] = []


def set_allowed_directories(directories: list[Path]) -> None:
    """Set the allowed directories for path validation"""
    global _allowed_directories
    _allowed_directories = [Path(d).resolve() for d in directories]


def validate_file_path(file_path: str, allowed_dirs: Optional[list[Path]] = None) -> Path:
    """
    Validate and sanitize a file path to prevent path traversal attacks.

    Args:
        file_path: The file path to validate
        allowed_dirs: Optional list of allowed directories. Uses global if not provided.

    Returns:
        Resolved Path object if valid

    Raises:
        ValueError: If path is invalid or outside allowed directories
    """
    if allowed_dirs is None:
        allowed_dirs = _allowed_directories

    # Convert to Path and resolve to absolute path (eliminates .. and symlinks)
    try:
        resolved_path = Path(file_path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {file_path}") from e

    # Check for null bytes (common attack vector)
    if '\x00' in str(file_path):
        raise ValueError("Invalid file path: contains null bytes")

    # If allowed directories are set, verify path is within them
    if allowed_dirs:
        is_allowed = False
        for allowed_dir in allowed_dirs:
            try:
                resolved_path.relative_to(allowed_dir)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            raise ValueError(f"File path outside allowed directories: {file_path}")

    # Verify file exists
    if not resolved_path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    # Verify it's a file, not a directory
    if not resolved_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return resolved_path
