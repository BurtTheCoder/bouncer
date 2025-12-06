#!/usr/bin/env python3
"""
Bouncer - Quality control at the door
Main entry point
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from bouncer import BouncerOrchestrator, ConfigLoader
from bouncers import (
    CodeQualityBouncer,
    SecurityBouncer,
    DocumentationBouncer,
    DataValidationBouncer,
    PerformanceBouncer,
    AccessibilityBouncer,
    LicenseBouncer,
    InfrastructureBouncer,
    APIContractBouncer,
    DependencyBouncer,
    ObsidianBouncer,
    LogInvestigator
)
from notifications import (
    SlackNotifier,
    FileLoggerNotifier,
    DiscordNotifier,
    EmailNotifier,
    TeamsNotifier,
    WebhookNotifier
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    # Create log directory first (before FileHandler tries to open the file)
    Path('.bouncer').mkdir(exist_ok=True)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('.bouncer/bouncer.log')
        ]
    )


def create_orchestrator(config: dict) -> BouncerOrchestrator:
    """Create and configure the bouncer orchestrator"""
    orchestrator = BouncerOrchestrator(config)
    
    # Register bouncers based on config
    bouncer_config = config.get('bouncers', {})
    
    if bouncer_config.get('code_quality', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'code_quality',
            CodeQualityBouncer(bouncer_config.get('code_quality', {}))
        )
    
    if bouncer_config.get('security', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'security',
            SecurityBouncer(bouncer_config.get('security', {}))
        )
    
    if bouncer_config.get('documentation', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'documentation',
            DocumentationBouncer(bouncer_config.get('documentation', {}))
        )
    
    if bouncer_config.get('data_validation', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'data_validation',
            DataValidationBouncer(bouncer_config.get('data_validation', {}))
        )
    
    if bouncer_config.get('performance', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'performance',
            PerformanceBouncer(bouncer_config.get('performance', {}))
        )
    
    if bouncer_config.get('accessibility', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'accessibility',
            AccessibilityBouncer(bouncer_config.get('accessibility', {}))
        )
    
    if bouncer_config.get('license', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'license',
            LicenseBouncer(bouncer_config.get('license', {}))
        )
    
    if bouncer_config.get('infrastructure', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'infrastructure',
            InfrastructureBouncer(bouncer_config.get('infrastructure', {}))
        )
    
    if bouncer_config.get('api_contract', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'api_contract',
            APIContractBouncer(bouncer_config.get('api_contract', {}))
        )
    
    if bouncer_config.get('dependency', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'dependency',
            DependencyBouncer(bouncer_config.get('dependency', {}))
        )
    
    if bouncer_config.get('obsidian', {}).get('enabled', True):
        orchestrator.register_bouncer(
            'obsidian',
            ObsidianBouncer(bouncer_config.get('obsidian', {}))
        )
    
    if bouncer_config.get('log_investigator', {}).get('enabled', False):
        orchestrator.register_bouncer(
            'log_investigator',
            LogInvestigator(bouncer_config.get('log_investigator', {}))
        )
    
    # Register notifiers
    notifications_config = config.get('notifications', {})
    
    if notifications_config.get('slack', {}).get('enabled', False):
        orchestrator.register_notifier(
            SlackNotifier(notifications_config.get('slack', {}))
        )
    
    if notifications_config.get('discord', {}).get('enabled', False):
        orchestrator.register_notifier(
            DiscordNotifier(notifications_config.get('discord', {}))
        )
    
    if notifications_config.get('email', {}).get('enabled', False):
        orchestrator.register_notifier(
            EmailNotifier(notifications_config.get('email', {}))
        )
    
    if notifications_config.get('teams', {}).get('enabled', False):
        orchestrator.register_notifier(
            TeamsNotifier(notifications_config.get('teams', {}))
        )
    
    if notifications_config.get('webhook', {}).get('enabled', False):
        orchestrator.register_notifier(
            WebhookNotifier(notifications_config.get('webhook', {}))
        )
    
    if notifications_config.get('file_log', {}).get('enabled', True):
        orchestrator.register_notifier(
            FileLoggerNotifier(notifications_config.get('file_log', {}))
        )
    
    return orchestrator


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Bouncer - Quality control at the door',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bouncer start                    # Start with default config
  bouncer start --config custom.yaml
  bouncer init                     # Create default config
  bouncer --verbose start          # Start with debug logging
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'scan', 'init', 'version', 'validate-config', 'wizard', 'auth-status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('bouncer.yaml'),
        help='Path to configuration file (default: bouncer.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        'target_dir',
        type=Path,
        nargs='?',
        help='Target directory to scan (required for scan command)'
    )
    
    parser.add_argument(
        '--git-diff',
        action='store_true',
        help='Only scan files in git diff (incremental mode)'
    )
    
    parser.add_argument(
        '--since',
        type=str,
        help='Time window for git diff (e.g., "1 hour ago", "24 hours ago")'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Report issues without making any changes (disables auto-fix)'
    )
    
    parser.add_argument(
        '--diff-only',
        action='store_true',
        help='Only check files that have changed (alias for --git-diff)'
    )
    
    args = parser.parse_args()
    
    # Handle flag aliases
    if args.diff_only:
        args.git_diff = True
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Handle commands
    if args.command == 'version':
        from bouncer import __version__
        print(f"Bouncer v{__version__}")
        return
    
    elif args.command == 'validate-config':
        # Validate configuration file
        if not args.config.exists():
            logger.error(f"❌ Config file not found: {args.config}")
            sys.exit(1)
        
        try:
            config = ConfigLoader.load(args.config)
            logger.info(f"✅ Config file is valid: {args.config}")
            
            # Validate structure
            errors = []
            warnings = []
            
            # Check required fields
            if 'watch_dir' not in config:
                errors.append("Missing required field: watch_dir")
            elif not Path(config['watch_dir']).exists():
                warnings.append(f"Watch directory does not exist: {config['watch_dir']}")
            
            # Check bouncers
            if 'bouncers' not in config:
                warnings.append("No bouncers configured")
            else:
                available_bouncers = [
                    'code_quality', 'security', 'documentation', 'data_validation',
                    'performance', 'accessibility', 'license', 'infrastructure',
                    'api_contract', 'dependency', 'obsidian', 'log_investigator'
                ]
                for bouncer_name in config.get('bouncers', {}):
                    if bouncer_name not in available_bouncers:
                        warnings.append(f"Unknown bouncer: {bouncer_name}")
            
            # Check integrations
            if 'integrations' in config:
                available_integrations = ['github', 'gitlab', 'linear', 'jira']
                for integration_name in config.get('integrations', {}):
                    if integration_name not in available_integrations:
                        warnings.append(f"Unknown integration: {integration_name}")
            
            # Print results
            if errors:
                logger.error("❌ Validation failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                sys.exit(1)
            
            if warnings:
                logger.warning("⚠️  Validation warnings:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
            
            logger.info("✅ Configuration is valid!")
            return
            
        except Exception as e:
            logger.error(f"❌ Failed to validate config: {e}")
            sys.exit(1)
    
    elif args.command == 'wizard':
        # Launch interactive setup wizard
        try:
            from bouncer.wizard import BouncerWizard
            wizard = BouncerWizard(config_path=args.config)
            # Textual handles its own event loop
            sys.exit(wizard.run())
        except ImportError:
            logger.error("❌ Textual library not installed")
            logger.info("Install with: pip install textual")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Wizard failed: {e}", exc_info=True)
            sys.exit(1)
    
    elif args.command == 'init':
        # Create default config
        if args.config.exists():
            logger.error(f"Config file already exists: {args.config}")
            sys.exit(1)
        
        import yaml
        default_config = ConfigLoader.get_default_config()
        
        with open(args.config, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"✅ Created default config: {args.config}")
        logger.info("Edit the config file and run: bouncer start")
        return
    
    elif args.command == 'scan':
        # Validate target directory
        if not args.target_dir:
            logger.error("Target directory is required for scan command")
            logger.info("Usage: bouncer scan /path/to/directory")
            sys.exit(1)
        
        if not args.target_dir.exists():
            logger.error(f"Target directory does not exist: {args.target_dir}")
            sys.exit(1)
        
        # Load config
        try:
            config = ConfigLoader.load(args.config)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {args.config}")
            logger.info("Using default configuration")
            config = ConfigLoader.get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
        
        # Override watch_dir with target_dir
        config['watch_dir'] = str(args.target_dir)
        
        # Apply --report-only flag
        if args.report_only:
            logger.info("📋 Report-only mode: auto-fix disabled for all bouncers")
            for bouncer_name in config.get('bouncers', {}):
                if isinstance(config['bouncers'][bouncer_name], dict):
                    config['bouncers'][bouncer_name]['auto_fix'] = False
        
        # Create orchestrator
        orchestrator = create_orchestrator(config)
        
        # Run scan
        logger.info("🔍 Starting Bouncer scan...")
        
        try:
            summary = await orchestrator.scan(
                target_dir=args.target_dir,
                git_diff=args.git_diff,
                since=args.since
            )
            
            # Print summary
            logger.info("\n" + "="*50)
            logger.info("📊 SCAN SUMMARY")
            logger.info("="*50)
            logger.info(f"Files scanned: {summary['files_scanned']}")
            logger.info(f"Issues found: {summary['issues_found']}")
            logger.info(f"Fixes applied: {summary['fixes_applied']}")
            logger.info("="*50)
            
            # Exit with appropriate code
            if summary['issues_found'] > 0:
                sys.exit(1)  # Exit with error if issues found
            else:
                sys.exit(0)  # Success
                
        except Exception as e:
            logger.error(f"❌ Scan failed: {e}", exc_info=True)
            sys.exit(1)
    
    elif args.command == 'auth-status':
        # Check authentication status
        import os
        
        logger.info("🔐 Checking authentication status...\n")
        
        has_api_key = bool(os.getenv('ANTHROPIC_API_KEY'))
        claude_json = Path.home() / '.claude.json'
        has_oauth = claude_json.exists()
        
        # Check macOS Keychain (if on macOS)
        has_keychain = False
        if sys.platform == 'darwin':
            try:
                import subprocess
                result = subprocess.run(
                    ['security', 'find-generic-password', '-s', 'Claude Code', '-w'],
                    capture_output=True,
                    text=True
                )
                has_keychain = result.returncode == 0
            except:
                pass
        
        authenticated = has_api_key or has_oauth or has_keychain
        
        if authenticated:
            logger.info("✅ AUTHENTICATED\n")
            
            if has_api_key:
                api_key = os.getenv('ANTHROPIC_API_KEY')
                masked_key = api_key[:7] + '...' + api_key[-4:] if len(api_key) > 11 else '***'
                logger.info(f"  🔑 API Key: {masked_key}")
                logger.info(f"     Source: ANTHROPIC_API_KEY environment variable")
                logger.info(f"     Usage: Unlimited (pay-per-use)\n")
            
            if has_keychain:
                logger.info(f"  🔐 OAuth: Active (macOS Keychain)")
                logger.info(f"     Source: Claude Code authentication")
                logger.info(f"     Usage: Unlimited (Claude Code subscription)\n")
            
            if has_oauth and not has_keychain:
                logger.info(f"  🔐 OAuth: Active")
                logger.info(f"     Source: {claude_json}")
                logger.info(f"     Usage: Unlimited (Claude Code subscription)\n")
            
            if args.verbose:
                logger.info("📋 Authentication Priority:")
                logger.info("   1. ANTHROPIC_API_KEY (if set)")
                logger.info("   2. Claude Code OAuth (if authenticated)\n")
            
            logger.info("✅ Bouncer is ready to use!")
            return
        
        else:
            logger.error("❌ NOT AUTHENTICATED\n")
            logger.info("You need to authenticate before using Bouncer.\n")
            logger.info("🎯 RECOMMENDED: Claude Code OAuth (Unlimited Usage)")
            logger.info("   If you have a Claude Code subscription:")
            logger.info("   1. Install Claude Code: https://code.claude.com")
            logger.info("   2. Run the /login command")
            logger.info("   3. Bouncer will automatically use your credentials\n")
            logger.info("💡 ALTERNATIVE: API Key (Pay-per-use)")
            logger.info("   If you don't have Claude Code:")
            logger.info("   1. Get an API key: https://console.anthropic.com/settings/keys")
            logger.info("   2. Set environment variable:")
            logger.info("      export ANTHROPIC_API_KEY=sk-ant-...")
            logger.info("   3. Or create a .env file with your key\n")
            logger.info("📖 For more details, see: docs/AUTHENTICATION.md")
            sys.exit(1)
    
    elif args.command == 'start':
        # Load config
        try:
            config = ConfigLoader.load(args.config)
        except FileNotFoundError:
            logger.error(f"Config file not found: {args.config}")
            logger.info("Run 'bouncer init' to create a default config")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
        
        # Apply --report-only flag
        if args.report_only:
            logger.info("📋 Report-only mode: auto-fix disabled for all bouncers")
            for bouncer_name in config.get('bouncers', {}):
                if isinstance(config['bouncers'][bouncer_name], dict):
                    config['bouncers'][bouncer_name]['auto_fix'] = False
        
        # Create orchestrator
        orchestrator = create_orchestrator(config)
        
        # Start bouncer
        logger.info("🚪 Starting Bouncer...")
        
        try:
            await orchestrator.start()
        except KeyboardInterrupt:
            logger.info("\n🛑 Received interrupt signal")
            await orchestrator.stop()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
