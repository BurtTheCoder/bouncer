"""
Base bouncer class
All specialized bouncers inherit from this
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class BaseBouncer(ABC):
    """
    Base class for all bouncers

    Each bouncer is a specialized agent that checks specific file types
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.file_types = config.get('file_types', [])
        self.auto_fix = config.get('auto_fix', False)
        self.name = self.__class__.__name__.replace('Bouncer', '')
        self.hooks_manager = None  # Set by orchestrator after registration

    def set_hooks_manager(self, hooks_manager) -> None:
        """Set the hooks manager for this bouncer"""
        self.hooks_manager = hooks_manager
        logger.debug(f"🪝 Hooks manager set for {self.name}")

    def get_hooks_config(self) -> Optional[Dict]:
        """
        Get hooks configuration for ClaudeAgentOptions.

        Returns dict with pre_tool_use and post_tool_use hooks if available.
        """
        if not self.hooks_manager or not self.hooks_manager.is_enabled():
            return None

        pre_hooks = self.hooks_manager.get_pre_tool_hooks()
        post_hooks = self.hooks_manager.get_post_tool_hooks()

        if not pre_hooks and not post_hooks:
            return None

        hooks_config = {}
        if pre_hooks:
            hooks_config['pre_tool_use'] = pre_hooks
        if post_hooks:
            hooks_config['post_tool_use'] = post_hooks

        return hooks_config
    
    async def should_check(self, event) -> bool:
        """
        Determine if this bouncer should check this file
        
        Args:
            event: FileChangeEvent
            
        Returns:
            bool: True if this bouncer should check the file
        """
        if not self.enabled:
            return False
        
        # Check file extension
        if self.file_types:
            return event.path.suffix in self.file_types
        
        return True
    
    @abstractmethod
    async def check(self, event) -> 'BouncerResult':
        """
        Check the file and return results
        
        Args:
            event: FileChangeEvent
            
        Returns:
            BouncerResult: Results of the check
        """
        pass
    
    def _create_result(
        self,
        event,
        status: str,
        issues_found: List[Dict[str, Any]] = None,
        fixes_applied: List[Dict[str, Any]] = None,
        messages: List[str] = None
    ):
        """Helper to create BouncerResult (immutable with tuples)"""
        from bouncer.core import BouncerResult

        return BouncerResult(
            bouncer_name=self.name,
            file_path=event.path,
            status=status,
            issues_found=tuple(issues_found or []),
            fixes_applied=tuple(fixes_applied or []),
            messages=tuple(messages or []),
            timestamp=time.time()
        )
