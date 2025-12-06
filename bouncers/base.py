"""
Base bouncer class
All specialized bouncers inherit from this
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
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
