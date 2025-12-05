"""
Custom Tools for Bouncer
Implemented as SDK MCP servers for in-process execution
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
import subprocess
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


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
    file_path = args["file_path"]
    
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        issues = json.loads(result.stdout) if result.stdout else []
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": file_path,
                    "linter": "pylint",
                    "issues": issues,
                    "count": len(issues)
                }, indent=2)
            }]
        }
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
    file_path = args["file_path"]
    
    try:
        result = subprocess.run(
            ["eslint", "--format=json", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        issues = json.loads(result.stdout) if result.stdout else []
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": file_path,
                    "linter": "eslint",
                    "issues": issues
                }, indent=2)
            }]
        }
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
    file_path = args["file_path"]
    
    try:
        result = subprocess.run(
            ["black", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "content": [{
                "type": "text",
                "text": f"Formatted {file_path} with Black\n{result.stdout}"
            }]
        }
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
    file_path = args["file_path"]
    
    try:
        result = subprocess.run(
            ["prettier", "--write", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "content": [{
                "type": "text",
                "text": f"Formatted {file_path} with Prettier\n{result.stdout}"
            }]
        }
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
    file_path = Path(args["file_path"])
    
    try:
        content = file_path.read_text()
        
        # Simple pattern matching for common secrets
        patterns = {
            "API Key": r"api[_-]?key",
            "Password": r"password\s*=\s*['\"]",
            "Secret": r"secret[_-]?key",
            "Token": r"token\s*=\s*['\"]",
            "AWS Key": r"AKIA[0-9A-Z]{16}"
        }
        
        findings = []
        for secret_type, pattern in patterns.items():
            import re
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
                    "file": str(file_path),
                    "findings": findings,
                    "count": len(findings)
                }, indent=2)
            }]
        }
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
    file_path = Path(args["file_path"])
    
    try:
        content = file_path.read_text()
        data = json.loads(content)
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(file_path),
                    "valid": True,
                    "message": "JSON is valid",
                    "size": len(data) if isinstance(data, (list, dict)) else 1
                }, indent=2)
            }]
        }
    except json.JSONDecodeError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(file_path),
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
    file_path = Path(args["file_path"])
    
    try:
        import yaml
        content = file_path.read_text()
        data = yaml.safe_load(content)
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(file_path),
                    "valid": True,
                    "message": "YAML is valid"
                }, indent=2)
            }]
        }
    except yaml.YAMLError as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "file": str(file_path),
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
