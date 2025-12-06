"""
Custom Tools for Bouncer
Implemented as SDK MCP servers for in-process execution
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
import subprocess
import json
import re
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


# Linting Tools

@tool(
    name="run_pylint",
    description="Run pylint on a Python file and return issues",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to Python file"}
        },
        "required": ["file_path"]
    }
)
async def run_pylint(args):
    """Run pylint and return structured results"""
    try:
        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])
        file_path_str = str(validated_path)

        result = subprocess.run(
            ["pylint", "--output-format=json", file_path_str],
            capture_output=True,
            text=True,
            timeout=30
        )

        issues = json.loads(result.stdout) if result.stdout else []

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": file_path_str,
                    "linter": "pylint",
                    "issues": issues,
                    "count": len(issues)
                }, indent=2)
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except subprocess.TimeoutExpired:
        return {"content": [{"type": "text", "text": "Linting timed out"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    name="run_eslint",
    description="Run ESLint on a JavaScript/TypeScript file",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to JS/TS file"}
        },
        "required": ["file_path"]
    }
)
async def run_eslint(args):
    """Run ESLint and return results"""
    try:
        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])
        file_path_str = str(validated_path)

        result = subprocess.run(
            ["eslint", "--format=json", file_path_str],
            capture_output=True,
            text=True,
            timeout=30
        )

        issues = json.loads(result.stdout) if result.stdout else []

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": file_path_str,
                    "linter": "eslint",
                    "issues": issues
                }, indent=2)
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Formatting Tools

@tool(
    name="format_python",
    description="Format Python code using Black",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to Python file"}
        },
        "required": ["file_path"]
    }
)
async def format_python(args):
    """Format Python code with Black"""
    try:
        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])
        file_path_str = str(validated_path)

        result = subprocess.run(
            ["black", file_path_str],
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "content": [{
                "type": "text",
                "text": f"Formatted {file_path_str} with Black\n{result.stdout}"
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    name="format_javascript",
    description="Format JavaScript/TypeScript code using Prettier",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to JS/TS file"}
        },
        "required": ["file_path"]
    }
)
async def format_javascript(args):
    """Format JS/TS code with Prettier"""
    try:
        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])
        file_path_str = str(validated_path)

        result = subprocess.run(
            ["prettier", "--write", file_path_str],
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "content": [{
                "type": "text",
                "text": f"Formatted {file_path_str} with Prettier\n{result.stdout}"
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Security Scanning Tools

@tool(
    name="scan_secrets",
    description="Scan file for hardcoded secrets using basic patterns",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to file to scan"}
        },
        "required": ["file_path"]
    }
)
async def scan_secrets(args):
    """Scan for hardcoded secrets"""
    try:
        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])

        content = validated_path.read_text()

        # Comprehensive pattern matching for common secrets
        patterns = {
            "API Key": r"api[_-]?key\s*[=:]\s*['\"][^'\"]+['\"]",
            "Password": r"password\s*[=:]\s*['\"][^'\"]+['\"]",
            "Secret Key": r"secret[_-]?key\s*[=:]\s*['\"][^'\"]+['\"]",
            "Token": r"token\s*[=:]\s*['\"][^'\"]+['\"]",
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "AWS Secret Key": r"(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*['\"][^'\"]+['\"]",
            "Private Key": r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH)?\s*PRIVATE KEY-----",
            "JWT Token": r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_.+/]*",
            "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
            "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
            "Slack Token": r"xox[baprs]-[0-9A-Za-z-]+",
            "Database URL": r"(?i)(?:postgres|mysql|mongodb|redis):\/\/[^\s'\"]+",
            "Bearer Token": r"(?i)bearer\s+[A-Za-z0-9-_.]+",
        }

        findings = []
        for secret_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                findings.append({
                    "type": secret_type,
                    "line": line_num,
                    "severity": "high"
                })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(validated_path),
                    "findings": findings,
                    "count": len(findings)
                }, indent=2)
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Data Validation Tools

@tool(
    name="validate_json",
    description="Validate JSON file syntax and formatting",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to JSON file"}
        },
        "required": ["file_path"]
    }
)
async def validate_json(args):
    """Validate JSON file"""
    try:
        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])

        content = validated_path.read_text()
        data = json.loads(content)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(validated_path),
                    "valid": True,
                    "message": "JSON is valid",
                    "size": len(data) if isinstance(data, (list, dict)) else 1
                }, indent=2)
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except json.JSONDecodeError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": args.get("file_path", "unknown"),
                    "valid": False,
                    "error": str(e),
                    "line": e.lineno if hasattr(e, 'lineno') else None
                }, indent=2)
            }]
        }
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    name="validate_yaml",
    description="Validate YAML file syntax and formatting",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to YAML file"}
        },
        "required": ["file_path"]
    }
)
async def validate_yaml(args):
    """Validate YAML file"""
    try:
        import yaml

        # Validate and sanitize file path
        validated_path = validate_file_path(args["file_path"])

        content = validated_path.read_text()
        data = yaml.safe_load(content)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(validated_path),
                    "valid": True,
                    "message": "YAML is valid"
                }, indent=2)
            }]
        }
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Path validation error: {str(e)}"}]}
    except yaml.YAMLError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": args.get("file_path", "unknown"),
                    "valid": False,
                    "error": str(e)
                }, indent=2)
            }]
        }
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Create SDK MCP server with all tools
bouncer_tools_server = create_sdk_mcp_server(
    name="bouncer-tools",
    version="1.0.0",
    tools=[
        run_pylint,
        run_eslint,
        format_python,
        format_javascript,
        scan_secrets,
        validate_json,
        validate_yaml
    ]
)


def get_tools_server():
    """Get the bouncer tools MCP server"""
    return bouncer_tools_server
