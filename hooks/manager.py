"""
Hooks Manager - Config-driven hook management for Bouncer

Manages validation and logging hooks based on configuration settings.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)


class HooksManager:
    """
    Manages hooks for bouncer operations based on configuration.

    Provides pre-tool-use validation and post-tool-use logging
    that can be enabled/disabled and configured via bouncer.yaml.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize HooksManager with configuration.

        Args:
            config: The 'hooks' section from bouncer.yaml
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.validation_config = config.get('validation', {})
        self.logging_config = config.get('logging', {})

        if self.enabled:
            logger.info("🪝 Hooks enabled")
            if self.validation_config.get('enabled', True):
                logger.info("  ├── Validation hooks: enabled")
            if self.logging_config.get('enabled', True):
                logger.info("  └── Logging hooks: enabled")
        else:
            logger.debug("🪝 Hooks disabled")

    def is_enabled(self) -> bool:
        """Check if hooks are globally enabled"""
        return self.enabled

    def is_validation_enabled(self) -> bool:
        """Check if validation hooks are enabled"""
        return self.enabled and self.validation_config.get('enabled', True)

    def is_logging_enabled(self) -> bool:
        """Check if logging hooks are enabled"""
        return self.enabled and self.logging_config.get('enabled', True)

    # =========================================================================
    # Validation Hooks
    # =========================================================================

    async def validate_before_write(self, input_data: Dict, tool_use_id: str, context: Dict) -> Dict:
        """
        Validate changes before writing to files.

        Returns empty dict to allow, or hookSpecificOutput to deny/ask.
        """
        if not self.is_validation_enabled():
            return {}

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name != "Write":
            return {}

        file_path = tool_input.get("path", "")
        content = tool_input.get("content", "")

        logger.debug(f"🔍 Validating write to: {file_path}")

        # Check 1: Protected files
        if self.validation_config.get('block_protected_files', True):
            protected_patterns = self.validation_config.get('protected_file_patterns', [])
            if any(pattern in file_path.lower() for pattern in protected_patterns):
                logger.warning(f"❌ Blocked write to protected file: {file_path}")
                return self._deny(f"Cannot modify protected file: {file_path}")

        # Check 2: Hardcoded secrets
        if self.validation_config.get('block_hardcoded_secrets', True):
            secret_patterns = self.validation_config.get('secret_patterns', [])
            content_lower = content.lower()
            found_secrets = [p for p in secret_patterns if p in content_lower]

            if found_secrets:
                logger.warning(f"⚠️  Potential secrets detected in {file_path}: {found_secrets}")
                return self._deny(
                    f"Potential hardcoded secrets detected: {', '.join(found_secrets)}. "
                    "Use environment variables instead."
                )

        # Check 3: File size limit
        file_size_limit = self.validation_config.get('file_size_limit', 1_000_000)
        if len(content) > file_size_limit:
            logger.warning(f"❌ File too large: {len(content)} bytes")
            return self._deny(
                f"File size ({len(content)} bytes) exceeds limit ({file_size_limit} bytes)"
            )

        # Check 4: Blocked code patterns (always deny)
        if self.validation_config.get('block_dangerous_code', True):
            blocked_patterns = self.validation_config.get('blocked_code_patterns', [])
            found_blocked = [p for p in blocked_patterns if p in content]

            if found_blocked:
                logger.warning(f"❌ Blocked code patterns in {file_path}: {found_blocked}")
                return self._deny(
                    f"Dangerous code patterns blocked: {', '.join(found_blocked)}. "
                    "Use safer alternatives."
                )

            # Check 5: Warning code patterns (ask for confirmation)
            warning_patterns = self.validation_config.get('warning_code_patterns', [])
            found_warning = [p for p in warning_patterns if p in content]

            if found_warning:
                logger.warning(f"⚠️  Warning code patterns in {file_path}: {found_warning}")
                return self._ask(
                    f"Potentially risky patterns detected: {', '.join(found_warning)}. "
                    "Please confirm this is intentional."
                )

        logger.debug(f"✅ Validation passed for: {file_path}")
        return {}

    async def validate_before_bash(self, input_data: Dict, tool_use_id: str, context: Dict) -> Dict:
        """
        Validate bash commands before execution.

        Returns empty dict to allow, or hookSpecificOutput to deny/ask.
        """
        if not self.is_validation_enabled():
            return {}

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name != "Bash":
            return {}

        command = tool_input.get("command", "")

        logger.debug(f"🔍 Validating bash command: {command}")

        # Check dangerous commands
        if self.validation_config.get('block_dangerous_commands', True):
            dangerous_commands = self.validation_config.get('dangerous_commands', [])

            for dangerous in dangerous_commands:
                if dangerous in command:
                    logger.warning(f"❌ Blocked dangerous command: {command}")
                    return self._deny(f"Dangerous command blocked: {dangerous}")

            # Check warning commands (require approval)
            warning_commands = self.validation_config.get('warning_commands', [])

            for warn_cmd in warning_commands:
                if warn_cmd in command:
                    logger.info(f"⚠️  System command requires approval: {command}")
                    return self._ask(
                        f"System modification command requires approval: {warn_cmd}"
                    )

        logger.debug(f"✅ Bash command validated: {command}")
        return {}

    # =========================================================================
    # Logging Hooks
    # =========================================================================

    async def log_after_write(self, input_data: Dict, tool_use_id: str, context: Dict) -> Dict:
        """Log file write operations for audit trail"""
        if not self.is_logging_enabled():
            return {}

        if not self.logging_config.get('log_writes', True):
            return {}

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name != "Write":
            return {}

        file_path = tool_input.get("path", "")
        content = tool_input.get("content", "")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "file_write",
            "file": file_path,
            "size": len(content),
            "tool_use_id": tool_use_id
        }

        logger.info(f"📝 File written: {file_path} ({len(content)} bytes)")
        await self._write_audit_log(log_entry)

        return {}

    async def log_after_bash(self, input_data: Dict, tool_use_id: str, context: Dict) -> Dict:
        """Log bash command executions for audit trail"""
        if not self.is_logging_enabled():
            return {}

        if not self.logging_config.get('log_bash', True):
            return {}

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
        await self._write_audit_log(log_entry)

        return {}

    async def log_tool_use(self, input_data: Dict, tool_use_id: str, context: Dict) -> Dict:
        """Log all tool usage for analytics"""
        if not self.is_logging_enabled():
            return {}

        if not self.logging_config.get('log_all_tools', False):
            return {}

        tool_name = input_data.get("tool_name", "")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "tool_use",
            "tool": tool_name,
            "tool_use_id": tool_use_id
        }

        logger.debug(f"🔧 Tool used: {tool_name}")
        await self._write_audit_log(log_entry)

        return {}

    # =========================================================================
    # Hook Collections for Claude Agent SDK
    # =========================================================================

    def get_pre_tool_hooks(self) -> List[Callable]:
        """Get list of pre-tool-use hooks for Claude Agent SDK"""
        if not self.is_validation_enabled():
            return []

        return [
            self.validate_before_write,
            self.validate_before_bash
        ]

    def get_post_tool_hooks(self) -> List[Callable]:
        """Get list of post-tool-use hooks for Claude Agent SDK"""
        if not self.is_logging_enabled():
            return []

        hooks = []
        if self.logging_config.get('log_writes', True):
            hooks.append(self.log_after_write)
        if self.logging_config.get('log_bash', True):
            hooks.append(self.log_after_bash)
        if self.logging_config.get('log_all_tools', False):
            hooks.append(self.log_tool_use)

        return hooks

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _deny(self, reason: str) -> Dict:
        """Create a deny response"""
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }

    def _ask(self, reason: str) -> Dict:
        """Create an ask response (requires user confirmation)"""
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason
            }
        }

    async def _write_audit_log(self, log_entry: Dict) -> None:
        """Write an entry to the audit log"""
        try:
            audit_dir = Path(self.logging_config.get('audit_dir', '.bouncer/audit'))
            audit_dir.mkdir(parents=True, exist_ok=True)

            audit_file = audit_dir / f"{datetime.now():%Y-%m-%d}.json"

            # Read existing logs
            logs = []
            if audit_file.exists():
                try:
                    logs = json.loads(audit_file.read_text())
                except json.JSONDecodeError:
                    logs = []

            # Append new log
            logs.append(log_entry)

            # Write back
            audit_file.write_text(json.dumps(logs, indent=2))

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
