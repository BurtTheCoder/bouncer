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

        # Hooks enabled override
        if os.getenv('BOUNCER_HOOKS_ENABLED'):
            hooks_enabled = os.getenv('BOUNCER_HOOKS_ENABLED', 'false').lower() == 'true'
            if 'hooks' not in config:
                config['hooks'] = ConfigLoader.get_default_hooks_config()
            config['hooks']['enabled'] = hooks_enabled
            logger.info(f"🔧 Override: hooks.enabled = {hooks_enabled}")

        # Hooks validation enabled override
        if os.getenv('BOUNCER_HOOKS_VALIDATION_ENABLED'):
            validation_enabled = os.getenv('BOUNCER_HOOKS_VALIDATION_ENABLED', 'true').lower() == 'true'
            if 'hooks' not in config:
                config['hooks'] = ConfigLoader.get_default_hooks_config()
            if 'validation' not in config['hooks']:
                config['hooks']['validation'] = {}
            config['hooks']['validation']['enabled'] = validation_enabled
            logger.info(f"🔧 Override: hooks.validation.enabled = {validation_enabled}")

        # Hooks logging enabled override
        if os.getenv('BOUNCER_HOOKS_LOGGING_ENABLED'):
            logging_enabled = os.getenv('BOUNCER_HOOKS_LOGGING_ENABLED', 'true').lower() == 'true'
            if 'hooks' not in config:
                config['hooks'] = ConfigLoader.get_default_hooks_config()
            if 'logging' not in config['hooks']:
                config['hooks']['logging'] = {}
            config['hooks']['logging']['enabled'] = logging_enabled
            logger.info(f"🔧 Override: hooks.logging.enabled = {logging_enabled}")

        # Notification overrides
        config = ConfigLoader._apply_notification_overrides(config)

        return config

    @staticmethod
    def _apply_notification_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply notification-specific environment variable overrides"""
        if 'notifications' not in config:
            config['notifications'] = {}

        # Notifier configurations: (env_prefix, config_key, extra_fields)
        notifiers = [
            ('SLACK', 'slack', ['webhook_url', 'channel']),
            ('DISCORD', 'discord', ['webhook_url', 'username']),
            ('EMAIL', 'email', ['smtp_host', 'smtp_port', 'smtp_user', 'from_email']),
            ('TEAMS', 'teams', ['webhook_url']),
            ('WEBHOOK', 'webhook', ['webhook_url', 'method']),
            ('FILE_LOG', 'file_log', ['log_dir', 'rotation']),
        ]

        for env_prefix, config_key, extra_fields in notifiers:
            # Initialize notifier config if needed
            if config_key not in config['notifications']:
                config['notifications'][config_key] = {}

            notifier_config = config['notifications'][config_key]

            # Enabled override
            env_enabled = os.getenv(f'BOUNCER_{env_prefix}_ENABLED')
            if env_enabled:
                enabled = env_enabled.lower() == 'true'
                notifier_config['enabled'] = enabled
                logger.info(f"🔧 Override: notifications.{config_key}.enabled = {enabled}")

            # Detail level override
            env_detail = os.getenv(f'BOUNCER_{env_prefix}_DETAIL_LEVEL')
            if env_detail:
                if env_detail.lower() in ['summary', 'detailed', 'full_transcript']:
                    notifier_config['detail_level'] = env_detail.lower()
                    logger.info(f"🔧 Override: notifications.{config_key}.detail_level = {env_detail.lower()}")

            # Min severity override
            env_severity = os.getenv(f'BOUNCER_{env_prefix}_MIN_SEVERITY')
            if env_severity:
                if env_severity.lower() in ['info', 'warning', 'denied', 'error']:
                    notifier_config['min_severity'] = env_severity.lower()
                    logger.info(f"🔧 Override: notifications.{config_key}.min_severity = {env_severity.lower()}")

            # Extra field overrides specific to each notifier
            for field in extra_fields:
                env_var = f'BOUNCER_{env_prefix}_{field.upper()}'
                env_value = os.getenv(env_var)
                if env_value:
                    # Handle numeric fields
                    if field in ['smtp_port']:
                        notifier_config[field] = int(env_value)
                    else:
                        notifier_config[field] = env_value
                    logger.info(f"🔧 Override: notifications.{config_key}.{field} = {env_value}")

        # Special handling for email to_emails (comma-separated list)
        env_to_emails = os.getenv('BOUNCER_EMAIL_TO_EMAILS')
        if env_to_emails:
            config['notifications']['email']['to_emails'] = [
                e.strip() for e in env_to_emails.split(',')
            ]
            logger.info(f"🔧 Override: notifications.email.to_emails = {env_to_emails}")

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
            },
            'hooks': ConfigLoader.get_default_hooks_config()
        }

    @staticmethod
    def get_default_hooks_config() -> Dict[str, Any]:
        """Get default hooks configuration"""
        return {
            'enabled': False,  # Disabled by default
            'validation': {
                'enabled': True,
                'block_protected_files': True,
                'protected_file_patterns': [
                    '.env', 'secrets', 'credentials', 'private_key', 'id_rsa'
                ],
                'block_hardcoded_secrets': True,
                'secret_patterns': [
                    'api_key', 'api-key', 'apikey', 'password',
                    'secret_key', 'access_token', 'auth_token'
                ],
                'block_dangerous_code': True,
                'blocked_code_patterns': ['eval(', 'exec('],
                'warning_code_patterns': [
                    'os.system(', 'subprocess.call(', 'subprocess.Popen(',
                    '__import__', 'rm -rf', 'pickle.loads(',
                    'yaml.load(', 'marshal.loads('
                ],
                'file_size_limit': 1_000_000,
                'block_dangerous_commands': True,
                'dangerous_commands': [
                    'rm -rf', 'dd if=', 'mkfs', ':(){ :|:& };:',
                    '> /dev/sda', 'chmod -R 777', 'chown -R'
                ],
                'warning_commands': [
                    'sudo', 'apt-get', 'yum', 'systemctl', 'service'
                ]
            },
            'logging': {
                'enabled': True,
                'audit_dir': '.bouncer/audit',
                'log_writes': True,
                'log_bash': True,
                'log_all_tools': False
            }
        }
