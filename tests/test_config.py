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
