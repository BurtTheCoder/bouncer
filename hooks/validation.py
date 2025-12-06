"""
Validation Hooks
Pre-write validation to prevent dangerous changes
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def validate_before_write(input_data, tool_use_id, context):
    """
    Validate changes before writing to files
    
    Checks:
    - No hardcoded secrets
    - File size limits
    - Protected files
    - Dangerous operations
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only validate Write operations
    if tool_name != "Write":
        return {}
    
    file_path = tool_input.get("path", "")
    content = tool_input.get("content", "")
    
    logger.debug(f"🔍 Validating write to: {file_path}")
    
    # Check 1: Protected files
    protected_patterns = [
        ".env",
        "secrets",
        "credentials",
        "private_key",
        "id_rsa"
    ]
    
    if any(pattern in file_path.lower() for pattern in protected_patterns):
        logger.warning(f"❌ Blocked write to protected file: {file_path}")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Cannot modify protected file: {file_path}"
            }
        }
    
    # Check 2: Hardcoded secrets
    secret_patterns = [
        "api_key",
        "api-key",
        "apikey",
        "password",
        "secret_key",
        "secret-key",
        "secretkey",
        "private_key",
        "access_token",
        "auth_token"
    ]
    
    content_lower = content.lower()
    found_secrets = [p for p in secret_patterns if p in content_lower]
    
    if found_secrets:
        logger.warning(f"⚠️  Potential secrets detected in {file_path}: {found_secrets}")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Potential hardcoded secrets detected: {', '.join(found_secrets)}. Use environment variables instead."
            }
        }
    
    # Check 3: File size limit (1MB)
    max_size = 1_000_000
    if len(content) > max_size:
        logger.warning(f"❌ File too large: {len(content)} bytes")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"File size ({len(content)} bytes) exceeds limit ({max_size} bytes)"
            }
        }
    
    # Check 4: High-risk code patterns (always deny)
    high_risk_patterns = [
        "eval(",
        "exec(",
    ]

    found_high_risk = [p for p in high_risk_patterns if p in content]

    if found_high_risk:
        logger.warning(f"❌ High-risk code patterns in {file_path}: {found_high_risk}")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"High-risk code patterns blocked: {', '.join(found_high_risk)}. Use safer alternatives (e.g., ast.literal_eval, importlib)."
            }
        }

    # Check 5: Medium-risk code patterns (require review/ask)
    medium_risk_patterns = [
        "os.system(",
        "subprocess.call(",
        "subprocess.Popen(",
        "__import__",
        "rm -rf",
        "pickle.loads(",
        "yaml.load(",  # unsafe yaml.load without Loader
        "marshal.loads(",
    ]

    found_medium_risk = [p for p in medium_risk_patterns if p in content]

    if found_medium_risk:
        logger.warning(f"⚠️  Medium-risk patterns in {file_path}: {found_medium_risk}")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"Medium-risk patterns detected: {', '.join(found_medium_risk)}. Please confirm this is intentional and safe."
            }
        }
    
    # All checks passed
    logger.debug(f"✅ Validation passed for: {file_path}")
    return {}


async def validate_before_bash(input_data, tool_use_id, context):
    """
    Validate bash commands before execution
    
    Prevents:
    - Destructive commands
    - System modifications
    - Network operations (in strict mode)
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Bash":
        return {}
    
    command = tool_input.get("command", "")
    
    logger.debug(f"🔍 Validating bash command: {command}")
    
    # Dangerous commands
    dangerous_commands = [
        "rm -rf",
        "dd if=",
        "mkfs",
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/sda",
        "chmod -R 777",
        "chown -R"
    ]
    
    for dangerous in dangerous_commands:
        if dangerous in command:
            logger.warning(f"❌ Blocked dangerous command: {command}")
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous command blocked: {dangerous}"
                }
            }
    
    # System modification commands (require approval)
    system_commands = [
        "sudo",
        "apt-get",
        "yum",
        "systemctl",
        "service"
    ]
    
    for sys_cmd in system_commands:
        if sys_cmd in command:
            logger.info(f"⚠️  System command requires approval: {command}")
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"System modification command requires approval: {sys_cmd}"
                }
            }
    
    logger.debug(f"✅ Bash command validated: {command}")
    return {}
