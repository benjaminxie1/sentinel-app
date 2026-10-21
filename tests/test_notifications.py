"""
Unit tests for Sentinel Notification System and Alert Message queuing.
"""

import time
import pytest
from backend.alerts.app_notification_system import AlertMessage


class TestNotificationSystem:
    """Tests for AlertMessage creation, serialization, and priority tiering."""

    def test_alert_message_creation(self):
        now = time.time()
        msg = AlertMessage(
            camera_id="cam_east_01",
            confidence=0.97,
            timestamp=now,
            alert_level="P1",
            message="Critical: Flame detected in loading bay",
        )
        assert msg.camera_id == "cam_east_01"
        assert msg.confidence == 0.97
        assert msg.alert_level == "P1"

    def test_alert_message_p2_review(self):
        now = time.time()
        msg = AlertMessage(
            camera_id="cam_hall_02",
            confidence=0.88,
            timestamp=now,
            alert_level="P2",
            message="Warning: Possible smoke signature in corridor",
        )
        assert msg.alert_level == "P2"
        assert msg.confidence < 0.95

    def test_alert_cooldown_deduplication(self):
        """Simulate cooldown window preventing duplicate message flood."""
        cooldown_seconds = 180
        last_sent = { "cam_01": time.time() - 50 } # Sent 50s ago
        now = time.time()
        
        # Within cooldown window -> should throttle
        is_throttled = (now - last_sent["cam_01"]) < cooldown_seconds
        assert is_throttled is True

        # Beyond cooldown window -> should permit
        last_sent["cam_01"] = time.time() - 200
        is_throttled = (now - last_sent["cam_01"]) < cooldown_seconds
        assert is_throttled is False
