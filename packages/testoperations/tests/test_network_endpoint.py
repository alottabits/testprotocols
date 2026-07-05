"""Tests for testoperations.network_endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.network_endpoint import wait_for_endpoint_ready


class TestWaitForEndpointReady:
    def test_returns_first_non_empty_ip(self):
        endpoint = MagicMock()
        endpoint.get_ipv4_addr.side_effect = ["", "", "192.168.10.234"]

        result = wait_for_endpoint_ready(endpoint, timeout_s=5, poll_s=0)

        assert result == "192.168.10.234"
        assert endpoint.get_ipv4_addr.call_count == 3

    def test_returns_immediately_when_already_ready(self):
        endpoint = MagicMock()
        endpoint.get_ipv4_addr.return_value = "192.168.10.234"

        result = wait_for_endpoint_ready(endpoint, timeout_s=5, poll_s=0)

        assert result == "192.168.10.234"
        assert endpoint.get_ipv4_addr.call_count == 1

    def test_raises_timeout_when_only_empty_strings(self):
        endpoint = MagicMock()
        endpoint.get_ipv4_addr.return_value = ""

        with pytest.raises(TimeoutError, match="kept returning empty"):
            wait_for_endpoint_ready(endpoint, timeout_s=0.05, poll_s=0.01)

    def test_swallows_transient_errors_and_keeps_polling(self):
        """The interface query may glitch mid-recovery (console not back
        yet, DHCP-client process restarting, etc.); we shouldn't abort
        the whole wait on a single bad poll."""
        endpoint = MagicMock()
        endpoint.get_ipv4_addr.side_effect = [
            RuntimeError("console not ready"),
            "",
            "192.168.10.234",
        ]

        result = wait_for_endpoint_ready(endpoint, timeout_s=5, poll_s=0)

        assert result == "192.168.10.234"
        assert endpoint.get_ipv4_addr.call_count == 3

    def test_timeout_message_carries_last_error_when_present(self):
        endpoint = MagicMock()
        endpoint.get_ipv4_addr.side_effect = RuntimeError("console lost")

        with pytest.raises(TimeoutError, match="console lost"):
            wait_for_endpoint_ready(endpoint, timeout_s=0.05, poll_s=0.01)
