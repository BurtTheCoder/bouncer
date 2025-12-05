"""
Logging Hooks
Post-action logging for audit trail
"""

import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


async def log_after_write(input_data, tool_use_id, context):
    """
    Log all file write operations
    Creates an audit trail of changes
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Write":
        return {}
    
    file_path = tool_input.get("path", "")
    content = tool_input.get("content", "")
    
    # Log to audit file
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "file_write",
        "file": file_path,
        "size": len(content),
        "tool_use_id": tool_use_id
    }
    
    logger.info(f"📝 File written: {file_path} ({len(content)} bytes)")
    
    # Append to audit log
    try:
        audit_dir = Path(".bouncer/audit")
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        audit_file = audit_dir / f"{datetime.now():%Y-%m-%d}.json"
        
        # Read existing logs
        logs = []
        if audit_file.exists():
            logs = json.loads(audit_file.read_text())
        
        # Append new log
        logs.append(log_entry)
        
        # Write back
        audit_file.write_text(json.dumps(logs, indent=2))
    
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
    
    return {}


async def log_after_bash(input_data, tool_use_id, context):
    """
    Log all bash command executions
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Bash":
        return {}
    
    command = tool_input.get("command", "")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "bash_command",
        "command": command,
        "tool_use_id": tool_use_id
    }
    
    logger.info(f"⚡ Bash command executed: {command}")
    
    # Append to audit log
    try:
        audit_dir = Path(".bouncer/audit")
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        audit_file = audit_dir / f"{datetime.now():%Y-%m-%d}.json"
        
        logs = []
        if audit_file.exists():
            logs = json.loads(audit_file.read_text())
        
        logs.append(log_entry)
        audit_file.write_text(json.dumps(logs, indent=2))
    
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
    
    return {}


async def log_tool_use(input_data, tool_use_id, context):
    """
    Log all tool uses for analytics
    """
    tool_name = input_data.get("tool_name", "")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "tool_use_id": tool_use_id
    }
    
    logger.debug(f"🔧 Tool used: {tool_name}")
    
    # Could send to analytics service here
    
    return {}
