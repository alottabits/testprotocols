"""Tests for testoperations.device_management module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.device_management import wait_for_reboot_completion

# ---------------------------------------------------------------------------
# wait_for_reboot_completion
# ---------------------------------------------------------------------------


class TestWaitForRebootCompletion:
    def test_polls_until_online_returns_true_after_false(self):
        mgmt = MagicMock()
        # First goes offline, then comes back online
        mgmt.is_online.side_effect = [True, False, False, True]

        wait_for_reboot_completion(mgmt, timeout=5)
        assert mgmt.is_online.call_count >= 3

    def test_returns_when_starting_offline_then_online(self):
        mgmt = MagicMock()
        mgmt.is_online.side_effect = [False, True]

        wait_for_reboot_completion(mgmt, timeout=5)
        assert mgmt.is_online.call_count >= 2
