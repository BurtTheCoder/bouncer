"""
Notification Formatter
Formats bouncer results based on detail level configuration
"""

from typing import List, Dict, Any
from datetime import datetime


class NotificationFormatter:
    """Format bouncer results for notifications with configurable detail levels"""
    
    DETAIL_LEVELS = ['summary', 'detailed', 'full_transcript']
    
    def __init__(self, detail_level: str = 'summary'):
        """
        Initialize formatter
        
        Args:
            detail_level: Level of detail (summary, detailed, full_transcript)
        """
        if detail_level not in self.DETAIL_LEVELS:
            raise ValueError(f"Invalid detail_level: {detail_level}. Must be one of {self.DETAIL_LEVELS}")
        
        self.detail_level = detail_level
    
    def format(self, event, results: List, transcript: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format results based on detail level
        
        Args:
            event: FileChangeEvent
            results: List of BouncerResult objects
            transcript: Optional full conversation transcript
        
        Returns:
            Formatted notification data
        """
        if self.detail_level == 'summary':
            return self._format_summary(event, results)
        elif self.detail_level == 'detailed':
            return self._format_detailed(event, results)
        elif self.detail_level == 'full_transcript':
            return self._format_full_transcript(event, results, transcript)
    
    def _format_summary(self, event, results: List) -> Dict[str, Any]:
        """
        Summary format - just the essentials
        
        Returns:
            - File path
            - Event type
            - Overall status
            - Issue count
            - Fix count
            - Top 3 issues
        """
        total_issues = sum(len(r.issues_found) for r in results)
        total_fixes = sum(len(r.fixes_applied) for r in results)
        
        # Get top 3 most severe issues
        all_issues = []
        for result in results:
            for issue in result.issues_found:
                all_issues.append({
                    'bouncer': result.bouncer_name,
                    'message': issue.get('message', ''),
                    'severity': issue.get('severity', 'info'),
                    'category': issue.get('category', 'general')
                })
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'warning': 2, 'info': 3}
        all_issues.sort(key=lambda x: severity_order.get(x['severity'], 99))
        top_issues = all_issues[:3]
        
        # Determine overall status
        statuses = [r.status for r in results]
        if 'denied' in statuses:
            overall_status = 'denied'
        elif 'warning' in statuses:
            overall_status = 'warning'
        elif 'fixed' in statuses:
            overall_status = 'fixed'
        else:
            overall_status = 'approved'
        
        return {
            'format': 'summary',
            'file_path': str(event.path),
            'file_name': event.path.name,
            'event_type': event.event_type,
            'timestamp': datetime.fromtimestamp(event.timestamp).isoformat(),
            'overall_status': overall_status,
            'summary': {
                'total_issues': total_issues,
                'total_fixes': total_fixes,
                'bouncers_run': len(results),
                'top_issues': top_issues
            },
            'bouncers': [
                {
                    'name': r.bouncer_name,
                    'status': r.status,
                    'issue_count': len(r.issues_found),
                    'fix_count': len(r.fixes_applied)
                }
                for r in results
            ]
        }
    
    def _format_detailed(self, event, results: List) -> Dict[str, Any]:
        """
        Detailed format - all issues, fixes, and suggestions
        
        Returns everything from summary plus:
            - All issues with full details
            - All fixes with full details
            - Suggestions from each bouncer
        """
        summary_data = self._format_summary(event, results)
        
        # Add full issue and fix details
        detailed_results = []
        for result in results:
            detailed_results.append({
                'bouncer': result.bouncer_name,
                'status': result.status,
                'issues': result.issues_found,
                'fixes': result.fixes_applied,
                'messages': result.messages
            })
        
        summary_data['format'] = 'detailed'
        summary_data['results'] = detailed_results
        
        return summary_data
    
    def _format_full_transcript(self, event, results: List, transcript: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Full transcript format - everything including agent thinking
        
        Returns everything from detailed plus:
            - Full conversation transcript
            - Tool calls made
            - Agent reasoning
            - Intermediate steps
        """
        detailed_data = self._format_detailed(event, results)
        
        detailed_data['format'] = 'full_transcript'
        detailed_data['transcript'] = transcript or {
            'note': 'Full transcript not available - enable transcript collection in bouncer configuration'
        }
        
        return detailed_data
    
    @staticmethod
    def get_severity_emoji(severity: str) -> str:
        """Get emoji for severity level"""
        return {
            'info': 'ℹ️',
            'warning': '⚠️',
            'high': '🔴',
            'critical': '🚨'
        }.get(severity, '❓')
    
    @staticmethod
    def get_status_emoji(status: str) -> str:
        """Get emoji for status"""
        return {
            'approved': '✅',
            'denied': '❌',
            'fixed': '🔧',
            'warning': '⚠️'
        }.get(status, '❓')
