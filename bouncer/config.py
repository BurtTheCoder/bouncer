"""
Configuration loader for Bouncer
Loads and validates YAML configuration
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates Bouncer configuration"""
    
    @staticmethod
    def load(config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable overrides"""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Expand environment variables in config values
        config = ConfigLoader._expand_env_vars(config)
        
        # Apply environment variable overrides
        config = ConfigLoader._apply_env_overrides(config)
        
        # Validate
        ConfigLoader._validate(config)
        
        logger.info(f"📋 Configuration loaded from: {config_path}")
        return config
    
    @staticmethod
    def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        # Watch directory override
        if os.getenv('BOUNCER_WATCH_DIR'):
            config['watch_dir'] = os.getenv('BOUNCER_WATCH_DIR')
            logger.info(f"🔧 Override: watch_dir = {config['watch_dir']}")
        
        # Recursive monitoring override
        if os.getenv('BOUNCER_RECURSIVE'):
            recursive = os.getenv('BOUNCER_RECURSIVE', 'true').lower() == 'true'
            config['recursive'] = recursive
            logger.info(f"🔧 Override: recursive = {recursive}")
        
        # Debounce delay override
        if os.getenv('BOUNCER_DEBOUNCE_DELAY'):
            config['debounce_delay'] = float(os.getenv('BOUNCER_DEBOUNCE_DELAY'))
            logger.info(f"🔧 Override: debounce_delay = {config['debounce_delay']}")
        
        # Report-only mode override
        if os.getenv('BOUNCER_REPORT_ONLY'):
            report_only = os.getenv('BOUNCER_REPORT_ONLY', 'false').lower() == 'true'
            config['report_only'] = report_only
            logger.info(f"🔧 Override: report_only = {report_only}")
        
        # Global auto-fix override
        if os.getenv('BOUNCER_AUTO_FIX'):
            auto_fix = os.getenv('BOUNCER_AUTO_FIX', 'true').lower() == 'true'
            config['auto_fix_override'] = auto_fix
            logger.info(f"🔧 Override: auto_fix (global) = {auto_fix}")
        
        # Log level override
        if os.getenv('BOUNCER_LOG_LEVEL'):
            config['log_level'] = os.getenv('BOUNCER_LOG_LEVEL').upper()
            logger.info(f"🔧 Override: log_level = {config['log_level']}")
        
        # Max file size override
        if os.getenv('BOUNCER_MAX_FILE_SIZE'):
            config['max_file_size'] = int(os.getenv('BOUNCER_MAX_FILE_SIZE'))
            logger.info(f"🔧 Override: max_file_size = {config['max_file_size']} bytes")
        
        # Enabled bouncers override (comma-separated list)
        if os.getenv('BOUNCER_ENABLED_BOUNCERS'):
            enabled_list = [b.strip() for b in os.getenv('BOUNCER_ENABLED_BOUNCERS').split(',')]
            if 'bouncers' in config:
                for bouncer_name in config['bouncers']:
                    config['bouncers'][bouncer_name]['enabled'] = bouncer_name in enabled_list
            logger.info(f"🔧 Override: enabled_bouncers = {enabled_list}")
        
        return config
    
    @staticmethod
    def _expand_env_vars(config: Any) -> Any:
        """Recursively expand environment variables in config"""
        if isinstance(config, dict):
            return {k: ConfigLoader._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [ConfigLoader._expand_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config
    
    @staticmethod
    def _validate(config: Dict[str, Any]):
        """Validate configuration"""
        required_fields = ['watch_dir']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        
        # Validate watch_dir exists
        watch_dir = Path(config['watch_dir'])
        if not watch_dir.exists():
            raise ValueError(f"Watch directory does not exist: {watch_dir}")
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'watch_dir': '.',
            'debounce_delay': 2,
            'ignore_patterns': [
                '.git',
                'node_modules',
                '__pycache__',
                '*.pyc',
                'venv',
                '.env',
                '.bouncer'
            ],
            'bouncers': {
                'code_quality': {
                    'enabled': True,
                    'file_types': ['.py', '.js', '.ts', '.jsx', '.tsx'],
                    'auto_fix': True,
                    'checks': ['syntax', 'linting', 'formatting']
                },
                'security': {
                    'enabled': True,
                    'file_types': ['.py', '.js', '.ts', '.java', '.go'],
                    'auto_fix': False,
                    'severity_threshold': 'medium'
                },
                'documentation': {
                    'enabled': True,
                    'file_types': ['.md', '.rst', '.txt'],
                    'auto_fix': True,
                    'checks': ['links', 'spelling', 'formatting']
                },
                'data_validation': {
                    'enabled': True,
                    'file_types': ['.json', '.yaml', '.yml', '.csv'],
                    'auto_fix': True,
                    'checks': ['schema', 'formatting']
                }
            },
            'notifications': {
                'slack': {
                    'enabled': False,
                    'webhook_url': '${SLACK_WEBHOOK_URL}',
                    'channel': '#bouncer',
                    'min_severity': 'warning'
                },
                'file_log': {
                    'enabled': True,
                    'log_dir': '.bouncer/logs',
                    'rotation': 'daily'
                }
            }
        }
