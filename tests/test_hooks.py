"""
Tests for hooks - validation hooks and HooksManager
"""

import pytest
from pathlib import Path


class TestHooksManager:
    """Tests for HooksManager configuration-driven hooks"""

    def test_init_disabled(self):
        """Test HooksManager when disabled"""
        from hooks.manager import HooksManager

        config = {'enabled': False}
        manager = HooksManager(config)

        assert manager.is_enabled() is False
        assert manager.is_validation_enabled() is False
        assert manager.is_logging_enabled() is False

    def test_init_enabled(self):
        """Test HooksManager when enabled"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'validation': {'enabled': True},
            'logging': {'enabled': True}
        }
        manager = HooksManager(config)

        assert manager.is_enabled() is True
        assert manager.is_validation_enabled() is True
        assert manager.is_logging_enabled() is True

    def test_validation_disabled_logging_enabled(self):
        """Test mixed hook settings"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'validation': {'enabled': False},
            'logging': {'enabled': True}
        }
        manager = HooksManager(config)

        assert manager.is_enabled() is True
        assert manager.is_validation_enabled() is False
        assert manager.is_logging_enabled() is True

    def test_get_pre_tool_hooks_when_disabled(self):
        """Test pre-tool hooks list when disabled"""
        from hooks.manager import HooksManager

        config = {'enabled': False}
        manager = HooksManager(config)

        hooks = manager.get_pre_tool_hooks()
        assert hooks == []

    def test_get_pre_tool_hooks_when_enabled(self):
        """Test pre-tool hooks list when enabled"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'validation': {'enabled': True}
        }
        manager = HooksManager(config)

        hooks = manager.get_pre_tool_hooks()
        assert len(hooks) == 2  # validate_before_write and validate_before_bash

    def test_get_post_tool_hooks_when_disabled(self):
        """Test post-tool hooks list when disabled"""
        from hooks.manager import HooksManager

        config = {'enabled': False}
        manager = HooksManager(config)

        hooks = manager.get_post_tool_hooks()
        assert hooks == []

    def test_get_post_tool_hooks_when_enabled(self):
        """Test post-tool hooks list when enabled"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'logging': {
                'enabled': True,
                'log_writes': True,
                'log_bash': True,
                'log_all_tools': False
            }
        }
        manager = HooksManager(config)

        hooks = manager.get_post_tool_hooks()
        assert len(hooks) == 2  # log_after_write and log_after_bash

    def test_get_post_tool_hooks_all_tools(self):
        """Test post-tool hooks with all tools logging"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'logging': {
                'enabled': True,
                'log_writes': True,
                'log_bash': True,
                'log_all_tools': True
            }
        }
        manager = HooksManager(config)

        hooks = manager.get_post_tool_hooks()
        assert len(hooks) == 3  # includes log_tool_use

    @pytest.mark.asyncio
    async def test_validate_before_write_disabled(self):
        """Test write validation when hooks disabled"""
        from hooks.manager import HooksManager

        config = {'enabled': False}
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Write",
            "tool_input": {"path": ".env", "content": "SECRET=abc"}
        }

        result = await manager.validate_before_write(input_data, "test-id", {})
        assert result == {}  # Allowed because hooks disabled

    @pytest.mark.asyncio
    async def test_validate_before_write_blocks_protected(self):
        """Test write validation blocks protected files"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'validation': {
                'enabled': True,
                'block_protected_files': True,
                'protected_file_patterns': ['.env', 'secrets']
            }
        }
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Write",
            "tool_input": {"path": "/app/.env", "content": "data"}
        }

        result = await manager.validate_before_write(input_data, "test-id", {})
        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_validate_before_write_custom_patterns(self):
        """Test write validation with custom secret patterns"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'validation': {
                'enabled': True,
                'block_hardcoded_secrets': True,
                'secret_patterns': ['my_custom_secret']
            }
        }
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Write",
            "tool_input": {"path": "/app/main.py", "content": "my_custom_secret = 'value'"}
        }

        result = await manager.validate_before_write(input_data, "test-id", {})
        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_validate_before_bash_disabled(self):
        """Test bash validation when hooks disabled"""
        from hooks.manager import HooksManager

        config = {'enabled': False}
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"}
        }

        result = await manager.validate_before_bash(input_data, "test-id", {})
        assert result == {}  # Allowed because hooks disabled

    @pytest.mark.asyncio
    async def test_validate_before_bash_blocks_dangerous(self):
        """Test bash validation blocks dangerous commands"""
        from hooks.manager import HooksManager

        config = {
            'enabled': True,
            'validation': {
                'enabled': True,
                'block_dangerous_commands': True,
                'dangerous_commands': ['rm -rf']
            }
        }
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/data"}
        }

        result = await manager.validate_before_bash(input_data, "test-id", {})
        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_logging_when_disabled(self, temp_dir):
        """Test logging hooks when disabled"""
        from hooks.manager import HooksManager

        config = {'enabled': False}
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Write",
            "tool_input": {"path": "/app/test.py", "content": "test"}
        }

        result = await manager.log_after_write(input_data, "test-id", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_logging_writes_audit(self, temp_dir):
        """Test logging hooks write audit file"""
        from hooks.manager import HooksManager
        import json

        audit_dir = temp_dir / "audit"

        config = {
            'enabled': True,
            'logging': {
                'enabled': True,
                'audit_dir': str(audit_dir),
                'log_writes': True
            }
        }
        manager = HooksManager(config)

        input_data = {
            "tool_name": "Write",
            "tool_input": {"path": "/app/test.py", "content": "test content"}
        }

        await manager.log_after_write(input_data, "test-id", {})

        # Check audit file was created
        assert audit_dir.exists()
        audit_files = list(audit_dir.glob("*.json"))
        assert len(audit_files) == 1

        # Check content
        logs = json.loads(audit_files[0].read_text())
        assert len(logs) == 1
        assert logs[0]["action"] == "file_write"
        assert logs[0]["file"] == "/app/test.py"


class TestValidateBeforeWrite:
    """Tests for validate_before_write hook"""

    @pytest.mark.asyncio
    async def test_non_write_tool_passes(self):
        """Test that non-Write tools are not validated"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Read",
            "tool_input": {"path": "/etc/passwd"}
        }

        result = await validate_before_write(input_data, "test-id", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_protected_file_blocked(self):
        """Test that writes to protected files are blocked"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/.env",
                "content": "some content"
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "protected file" in result["hookSpecificOutput"]["permissionDecisionReason"].lower()

    @pytest.mark.asyncio
    async def test_secrets_file_blocked(self):
        """Test that writes to secrets files are blocked"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/config/secrets.json",
                "content": "{}"
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_credentials_file_blocked(self):
        """Test that writes to credentials files are blocked"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/credentials.yaml",
                "content": "{}"
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_hardcoded_api_key_blocked(self):
        """Test that hardcoded API keys are blocked"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/main.py",
                "content": 'api_key = "sk-1234567890"'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "secrets" in result["hookSpecificOutput"]["permissionDecisionReason"].lower()

    @pytest.mark.asyncio
    async def test_hardcoded_password_blocked(self):
        """Test that hardcoded passwords are blocked"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/config.py",
                "content": 'password = "hunter2"'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_large_file_blocked(self):
        """Test that large files are blocked"""
        from hooks.validation import validate_before_write

        # Create content larger than 1MB
        large_content = "x" * 1_000_001

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/large_file.txt",
                "content": large_content
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "size" in result["hookSpecificOutput"]["permissionDecisionReason"].lower()

    @pytest.mark.asyncio
    async def test_eval_blocked(self):
        """Test that eval() is blocked (high-risk)"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/dangerous.py",
                "content": 'result = eval(user_input)'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "eval(" in result["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.asyncio
    async def test_exec_blocked(self):
        """Test that exec() is blocked (high-risk)"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/dangerous.py",
                "content": 'exec(user_code)'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "exec(" in result["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.asyncio
    async def test_os_system_requires_review(self):
        """Test that os.system() requires review (medium-risk)"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/utils.py",
                "content": 'os.system("ls -la")'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "ask"
        assert "os.system(" in result["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.asyncio
    async def test_subprocess_popen_requires_review(self):
        """Test that subprocess.Popen() requires review (medium-risk)"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/utils.py",
                "content": 'subprocess.Popen(["ls", "-la"])'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "ask"

    @pytest.mark.asyncio
    async def test_pickle_loads_requires_review(self):
        """Test that pickle.loads() requires review (medium-risk)"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/serialization.py",
                "content": 'data = pickle.loads(raw_data)'
            }
        }

        result = await validate_before_write(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "ask"

    @pytest.mark.asyncio
    async def test_safe_code_passes(self):
        """Test that safe code passes validation"""
        from hooks.validation import validate_before_write

        input_data = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/app/main.py",
                "content": '''
def hello_world():
    """A safe function"""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
'''
            }
        }

        result = await validate_before_write(input_data, "test-id", {})
        assert result == {}


class TestValidateBeforeBash:
    """Tests for validate_before_bash hook"""

    @pytest.mark.asyncio
    async def test_non_bash_tool_passes(self):
        """Test that non-Bash tools are not validated"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Write",
            "tool_input": {"command": "rm -rf /"}
        }

        result = await validate_before_bash(input_data, "test-id", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_rm_rf_blocked(self):
        """Test that rm -rf is blocked"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/data"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "rm -rf" in result["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.asyncio
    async def test_fork_bomb_blocked(self):
        """Test that fork bomb is blocked"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": ":(){ :|:& };:"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_dd_blocked(self):
        """Test that dd to device is blocked"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "dd if=/dev/zero of=/dev/sda"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_chmod_777_blocked(self):
        """Test that chmod -R 777 is blocked"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "chmod -R 777 /app"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.asyncio
    async def test_sudo_requires_approval(self):
        """Test that sudo requires approval"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "sudo apt-get update"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "ask"
        assert "sudo" in result["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.asyncio
    async def test_apt_get_requires_approval(self):
        """Test that apt-get requires approval"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "apt-get install python3"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "ask"

    @pytest.mark.asyncio
    async def test_systemctl_requires_approval(self):
        """Test that systemctl requires approval"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "systemctl restart nginx"}
        }

        result = await validate_before_bash(input_data, "test-id", {})

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["permissionDecision"] == "ask"

    @pytest.mark.asyncio
    async def test_safe_command_passes(self):
        """Test that safe commands pass"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"}
        }

        result = await validate_before_bash(input_data, "test-id", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_git_command_passes(self):
        """Test that git commands pass"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"}
        }

        result = await validate_before_bash(input_data, "test-id", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_python_command_passes(self):
        """Test that python commands pass"""
        from hooks.validation import validate_before_bash

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "python -m pytest"}
        }

        result = await validate_before_bash(input_data, "test-id", {})
        assert result == {}
