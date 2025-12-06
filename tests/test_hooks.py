"""
Tests for hooks/validation.py - Pre-write validation hooks
"""

import pytest


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
