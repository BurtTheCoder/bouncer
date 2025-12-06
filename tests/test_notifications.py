"""
Tests for notification systems
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


class TestFileLoggerNotifier:
    """Tests for FileLoggerNotifier"""

    def test_init_creates_directory(self, temp_dir):
        """Test that initialization creates log directory"""
        from notifications.file_logger import FileLoggerNotifier

        log_dir = temp_dir / "logs"
        notifier = FileLoggerNotifier({
            'enabled': True,
            'log_dir': str(log_dir)
        })

        assert log_dir.exists()

    def test_init_disabled(self, temp_dir):
        """Test that disabled notifier doesn't create directory"""
        from notifications.file_logger import FileLoggerNotifier

        log_dir = temp_dir / "logs_disabled"
        notifier = FileLoggerNotifier({
            'enabled': False,
            'log_dir': str(log_dir)
        })

        assert not log_dir.exists()

    def test_get_log_file_daily(self, temp_dir):
        """Test daily log file rotation"""
        from notifications.file_logger import FileLoggerNotifier

        notifier = FileLoggerNotifier({
            'enabled': True,
            'log_dir': str(temp_dir),
            'rotation': 'daily'
        })

        log_file = notifier._get_log_file()
        expected = f"{datetime.now():%Y-%m-%d}.json"
        assert log_file.name == expected

    def test_get_log_file_weekly(self, temp_dir):
        """Test weekly log file rotation"""
        from notifications.file_logger import FileLoggerNotifier

        notifier = FileLoggerNotifier({
            'enabled': True,
            'log_dir': str(temp_dir),
            'rotation': 'weekly'
        })

        log_file = notifier._get_log_file()
        expected = f"{datetime.now():%Y-W%W}.json"
        assert log_file.name == expected

    def test_get_log_file_monthly(self, temp_dir):
        """Test monthly log file rotation"""
        from notifications.file_logger import FileLoggerNotifier

        notifier = FileLoggerNotifier({
            'enabled': True,
            'log_dir': str(temp_dir),
            'rotation': 'monthly'
        })

        log_file = notifier._get_log_file()
        expected = f"{datetime.now():%Y-%m}.json"
        assert log_file.name == expected

    def test_get_log_file_none(self, temp_dir):
        """Test no rotation (single file)"""
        from notifications.file_logger import FileLoggerNotifier

        notifier = FileLoggerNotifier({
            'enabled': True,
            'log_dir': str(temp_dir),
            'rotation': 'none'
        })

        log_file = notifier._get_log_file()
        assert log_file.name == "bouncer.json"

    @pytest.mark.asyncio
    async def test_notify_disabled(self, temp_dir, file_change_event):
        """Test that disabled notifier doesn't write"""
        from notifications.file_logger import FileLoggerNotifier

        log_dir = temp_dir / "disabled_logs"
        notifier = FileLoggerNotifier({
            'enabled': False,
            'log_dir': str(log_dir)
        })

        await notifier.notify(file_change_event, [])

        # Directory shouldn't exist since notifier is disabled
        assert not log_dir.exists()

    @pytest.mark.asyncio
    async def test_notify_writes_log(self, temp_dir, file_change_event):
        """Test that notify writes log entries"""
        from notifications.file_logger import FileLoggerNotifier
        from bouncer.core import BouncerResult
        import time

        notifier = FileLoggerNotifier({
            'enabled': True,
            'log_dir': str(temp_dir),
            'rotation': 'none'
        })

        result = BouncerResult(
            bouncer_name='test',
            file_path=file_change_event.path,
            status='approved',
            issues_found=tuple(),
            fixes_applied=tuple(),
            messages=tuple(['Test message']),
            timestamp=time.time()
        )

        await notifier.notify(file_change_event, [result])

        log_file = temp_dir / "bouncer.json"
        assert log_file.exists()

        logs = json.loads(log_file.read_text())
        assert len(logs) == 1
        assert logs[0]['results'][0]['bouncer'] == 'test'
        assert logs[0]['results'][0]['status'] == 'approved'


class TestNotificationFormatter:
    """Tests for NotificationFormatter"""

    def test_init_summary_level(self):
        """Test formatter with summary detail level"""
        from notifications.formatter import NotificationFormatter

        formatter = NotificationFormatter('summary')
        assert formatter.detail_level == 'summary'

    def test_init_detailed_level(self):
        """Test formatter with detailed detail level"""
        from notifications.formatter import NotificationFormatter

        formatter = NotificationFormatter('detailed')
        assert formatter.detail_level == 'detailed'

    def test_init_full_transcript_level(self):
        """Test formatter with full_transcript detail level"""
        from notifications.formatter import NotificationFormatter

        formatter = NotificationFormatter('full_transcript')
        assert formatter.detail_level == 'full_transcript'

    def test_invalid_detail_level(self):
        """Test formatter rejects invalid detail level"""
        from notifications.formatter import NotificationFormatter

        with pytest.raises(ValueError):
            NotificationFormatter('invalid')


class TestWebhookNotifier:
    """Tests for WebhookNotifier"""

    def test_init(self):
        """Test WebhookNotifier initialization"""
        from notifications.webhook import WebhookNotifier

        notifier = WebhookNotifier({
            'enabled': True,
            'webhook_url': 'https://example.com/webhook'
        })

        assert notifier.enabled is True
        assert notifier.webhook_url == 'https://example.com/webhook'

    def test_init_disabled(self):
        """Test disabled WebhookNotifier"""
        from notifications.webhook import WebhookNotifier

        notifier = WebhookNotifier({
            'enabled': False
        })

        assert notifier.enabled is False

    @pytest.mark.asyncio
    async def test_send_disabled(self):
        """Test that disabled webhook doesn't send"""
        from notifications.webhook import WebhookNotifier

        notifier = WebhookNotifier({
            'enabled': False,
            'webhook_url': 'https://example.com/webhook'
        })

        # Should not raise - just returns early
        await notifier.send({'file_path': 'test.py'})


class TestEmailNotifier:
    """Tests for EmailNotifier"""

    def test_init(self):
        """Test EmailNotifier initialization"""
        from notifications.email import EmailNotifier

        notifier = EmailNotifier({
            'enabled': True,
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'from_address': 'bouncer@example.com',
            'to_addresses': ['dev@example.com']
        })

        assert notifier.smtp_host == 'smtp.example.com'
        assert notifier.smtp_port == 587

    def test_init_disabled(self):
        """Test disabled EmailNotifier"""
        from notifications.email import EmailNotifier

        notifier = EmailNotifier({'enabled': False})
        assert notifier.enabled is False

    def test_send_disabled(self):
        """Test that disabled email doesn't send"""
        from notifications.email import EmailNotifier

        notifier = EmailNotifier({'enabled': False})

        # Should not raise - just returns early (sync method)
        notifier.send({'file_path': 'test.py'})


class TestDiscordNotifier:
    """Tests for DiscordNotifier"""

    def test_init(self):
        """Test DiscordNotifier initialization"""
        from notifications.discord import DiscordNotifier

        notifier = DiscordNotifier({
            'enabled': True,
            'webhook_url': 'https://discord.com/api/webhooks/123/abc'
        })

        assert notifier.enabled is True
        assert notifier.webhook_url == 'https://discord.com/api/webhooks/123/abc'

    def test_init_disabled(self):
        """Test disabled DiscordNotifier"""
        from notifications.discord import DiscordNotifier

        notifier = DiscordNotifier({'enabled': False})
        assert notifier.enabled is False

    @pytest.mark.asyncio
    async def test_send_disabled(self):
        """Test that disabled Discord doesn't send"""
        from notifications.discord import DiscordNotifier

        notifier = DiscordNotifier({'enabled': False})

        # Should not raise - just returns early
        await notifier.send({'file_path': 'test.py'})


class TestTeamsNotifier:
    """Tests for TeamsNotifier"""

    def test_init(self):
        """Test TeamsNotifier initialization"""
        from notifications.teams import TeamsNotifier

        notifier = TeamsNotifier({
            'enabled': True,
            'webhook_url': 'https://outlook.office.com/webhook/123'
        })

        assert notifier.enabled is True

    def test_init_disabled(self):
        """Test disabled TeamsNotifier"""
        from notifications.teams import TeamsNotifier

        notifier = TeamsNotifier({'enabled': False})
        assert notifier.enabled is False

    @pytest.mark.asyncio
    async def test_send_disabled(self):
        """Test that disabled Teams doesn't send"""
        from notifications.teams import TeamsNotifier

        notifier = TeamsNotifier({'enabled': False})

        # Should not raise - just returns early
        await notifier.send({'file_path': 'test.py'})
