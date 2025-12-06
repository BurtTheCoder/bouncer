"""
Tests for bouncer/config.py - Configuration loading and validation
"""

import pytest
import os
from pathlib import Path


class TestConfigLoader:
    """Tests for ConfigLoader"""

    def test_load_valid_config(self, temp_dir):
        """Test loading a valid configuration file"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
debounce_delay: 2
ignore_patterns:
  - .git
  - __pycache__
bouncers:
  code_quality:
    enabled: true
    file_types:
      - .py
notifications:
  file_log:
    enabled: true
    log_dir: .bouncer/logs
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        # Change to temp_dir so watch_dir '.' validates
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)

            assert config['watch_dir'] == '.'
            assert config['debounce_delay'] == 2
            assert '.git' in config['ignore_patterns']
            assert config['bouncers']['code_quality']['enabled'] is True
        finally:
            os.chdir(original_dir)

    def test_load_missing_config(self, temp_dir):
        """Test loading a non-existent config file"""
        from bouncer.config import ConfigLoader

        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(temp_dir / "nonexistent.yaml")

    def test_environment_variable_expansion(self, temp_dir, monkeypatch):
        """Test that environment variables are expanded in config"""
        from bouncer.config import ConfigLoader

        # Set environment variable
        monkeypatch.setenv('TEST_WEBHOOK_URL', 'https://example.com/webhook')

        config_content = """
watch_dir: .
notifications:
  webhook:
    enabled: true
    webhook_url: ${TEST_WEBHOOK_URL}
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['webhook']['webhook_url'] == 'https://example.com/webhook'
        finally:
            os.chdir(original_dir)

    def test_missing_environment_variable(self, temp_dir):
        """Test handling of missing environment variables"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  webhook:
    enabled: true
    webhook_url: ${NONEXISTENT_VAR}
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            # Should keep the placeholder since env var doesn't exist
            webhook_url = config['notifications']['webhook']['webhook_url']
            assert webhook_url == '${NONEXISTENT_VAR}'
        finally:
            os.chdir(original_dir)

    def test_invalid_yaml_syntax(self, temp_dir):
        """Test handling of invalid YAML syntax"""
        from bouncer.config import ConfigLoader
        import yaml

        config_content = """
watch_dir: .
invalid: yaml: content: [
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        with pytest.raises(yaml.YAMLError):
            ConfigLoader.load(config_path)

    def test_validate_required_fields(self, temp_dir):
        """Test validation of required configuration fields"""
        from bouncer.config import ConfigLoader

        # Config without watch_dir
        config_content = """
debounce_delay: 2
bouncers: {}
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        # Should raise an error about missing watch_dir
        with pytest.raises(ValueError, match="watch_dir"):
            ConfigLoader.load(config_path)

    def test_bouncer_config_defaults(self, temp_dir):
        """Test that bouncer configs get proper defaults"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
bouncers:
  code_quality:
    enabled: true
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)

            bouncer_config = config['bouncers']['code_quality']
            assert bouncer_config['enabled'] is True
        finally:
            os.chdir(original_dir)

    def test_get_default_config(self):
        """Test getting default configuration"""
        from bouncer.config import ConfigLoader

        default_config = ConfigLoader.get_default_config()

        assert 'watch_dir' in default_config
        assert 'debounce_delay' in default_config
        assert 'ignore_patterns' in default_config
        assert 'bouncers' in default_config
        assert 'notifications' in default_config
        assert 'hooks' in default_config

    def test_hooks_enabled_env_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_HOOKS_ENABLED environment variable override"""
        from bouncer.config import ConfigLoader

        # Config with hooks disabled
        config_content = """
watch_dir: .
hooks:
  enabled: false
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        # Set env var to enable hooks
        monkeypatch.setenv('BOUNCER_HOOKS_ENABLED', 'true')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['hooks']['enabled'] is True
        finally:
            os.chdir(original_dir)

    def test_hooks_validation_enabled_env_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_HOOKS_VALIDATION_ENABLED environment variable override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
hooks:
  enabled: true
  validation:
    enabled: true
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        # Set env var to disable validation
        monkeypatch.setenv('BOUNCER_HOOKS_VALIDATION_ENABLED', 'false')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['hooks']['validation']['enabled'] is False
        finally:
            os.chdir(original_dir)

    def test_hooks_logging_enabled_env_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_HOOKS_LOGGING_ENABLED environment variable override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
hooks:
  enabled: true
  logging:
    enabled: true
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        # Set env var to disable logging
        monkeypatch.setenv('BOUNCER_HOOKS_LOGGING_ENABLED', 'false')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['hooks']['logging']['enabled'] is False
        finally:
            os.chdir(original_dir)

    def test_get_default_hooks_config(self):
        """Test getting default hooks configuration"""
        from bouncer.config import ConfigLoader

        hooks_config = ConfigLoader.get_default_hooks_config()

        assert hooks_config['enabled'] is False  # Disabled by default
        assert 'validation' in hooks_config
        assert hooks_config['validation']['enabled'] is True
        assert hooks_config['validation']['block_protected_files'] is True
        assert hooks_config['validation']['block_hardcoded_secrets'] is True
        assert hooks_config['validation']['block_dangerous_code'] is True
        assert hooks_config['validation']['block_dangerous_commands'] is True
        assert 'logging' in hooks_config
        assert hooks_config['logging']['enabled'] is True
        assert hooks_config['logging']['log_writes'] is True
        assert hooks_config['logging']['log_bash'] is True
        assert hooks_config['logging']['log_all_tools'] is False


class TestNotificationOverrides:
    """Tests for notification environment variable overrides"""

    def test_slack_enabled_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_SLACK_ENABLED override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  slack:
    enabled: false
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_SLACK_ENABLED', 'true')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['slack']['enabled'] is True
        finally:
            os.chdir(original_dir)

    def test_slack_detail_level_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_SLACK_DETAIL_LEVEL override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  slack:
    enabled: true
    detail_level: summary
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_SLACK_DETAIL_LEVEL', 'detailed')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['slack']['detail_level'] == 'detailed'
        finally:
            os.chdir(original_dir)

    def test_slack_min_severity_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_SLACK_MIN_SEVERITY override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  slack:
    enabled: true
    min_severity: info
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_SLACK_MIN_SEVERITY', 'error')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['slack']['min_severity'] == 'error'
        finally:
            os.chdir(original_dir)

    def test_email_enabled_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_EMAIL_ENABLED override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  email:
    enabled: false
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_EMAIL_ENABLED', 'true')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['email']['enabled'] is True
        finally:
            os.chdir(original_dir)

    def test_email_to_emails_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_EMAIL_TO_EMAILS override (comma-separated)"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  email:
    enabled: true
    to_emails:
      - "old@example.com"
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_EMAIL_TO_EMAILS', 'new@example.com, alerts@example.com')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['email']['to_emails'] == ['new@example.com', 'alerts@example.com']
        finally:
            os.chdir(original_dir)

    def test_file_log_rotation_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_FILE_LOG_ROTATION override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  file_log:
    enabled: true
    rotation: daily
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_FILE_LOG_ROTATION', 'weekly')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['file_log']['rotation'] == 'weekly'
        finally:
            os.chdir(original_dir)

    def test_webhook_method_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_WEBHOOK_METHOD override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  webhook:
    enabled: true
    method: POST
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_WEBHOOK_METHOD', 'PUT')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['webhook']['method'] == 'PUT'
        finally:
            os.chdir(original_dir)

    def test_discord_username_override(self, temp_dir, monkeypatch):
        """Test BOUNCER_DISCORD_USERNAME override"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  discord:
    enabled: true
    username: "Old Bot"
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_DISCORD_USERNAME', 'Quality Bot')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['discord']['username'] == 'Quality Bot'
        finally:
            os.chdir(original_dir)

    def test_invalid_detail_level_ignored(self, temp_dir, monkeypatch):
        """Test that invalid detail levels are ignored"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  slack:
    enabled: true
    detail_level: summary
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_SLACK_DETAIL_LEVEL', 'invalid_level')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            # Should keep original value since invalid
            assert config['notifications']['slack']['detail_level'] == 'summary'
        finally:
            os.chdir(original_dir)

    def test_invalid_severity_ignored(self, temp_dir, monkeypatch):
        """Test that invalid severity levels are ignored"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  slack:
    enabled: true
    min_severity: warning
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_SLACK_MIN_SEVERITY', 'invalid_severity')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            # Should keep original value since invalid
            assert config['notifications']['slack']['min_severity'] == 'warning'
        finally:
            os.chdir(original_dir)

    def test_multiple_notifier_overrides(self, temp_dir, monkeypatch):
        """Test multiple notification overrides at once"""
        from bouncer.config import ConfigLoader

        config_content = """
watch_dir: .
notifications:
  slack:
    enabled: false
  discord:
    enabled: false
  file_log:
    enabled: true
"""
        config_path = temp_dir / "bouncer.yaml"
        config_path.write_text(config_content)

        monkeypatch.setenv('BOUNCER_SLACK_ENABLED', 'true')
        monkeypatch.setenv('BOUNCER_SLACK_DETAIL_LEVEL', 'detailed')
        monkeypatch.setenv('BOUNCER_DISCORD_ENABLED', 'true')
        monkeypatch.setenv('BOUNCER_FILE_LOG_ENABLED', 'false')

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        try:
            config = ConfigLoader.load(config_path)
            assert config['notifications']['slack']['enabled'] is True
            assert config['notifications']['slack']['detail_level'] == 'detailed'
            assert config['notifications']['discord']['enabled'] is True
            assert config['notifications']['file_log']['enabled'] is False
        finally:
            os.chdir(original_dir)
