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
from notifications import SlackNotifier, FileLoggerNotifier


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('.bouncer/bouncer.log')
        ]
    )
    
    # Create log directory
    Path('.bouncer').mkdir(exist_ok=True)


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
        choices=['start', 'scan', 'init', 'version'],
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
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Handle commands
    if args.command == 'version':
        from bouncer import __version__
        print(f"Bouncer v{__version__}")
        return
    
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
