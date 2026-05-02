"""Tests for testoperations.tr069_server module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.tr069_server import is_cpe_online

# ---------------------------------------------------------------------------
# is_cpe_online
# ---------------------------------------------------------------------------


class TestIsCpeOnline:
    def test_returns_true_when_gpv_succeeds(self):
        acs = MagicMock()
        result = is_cpe_online(acs, "cpe-001")
        assert result is True
        acs.GPV.assert_called_once_with(
            "InternetGatewayDevice.DeviceInfo.UpTime",
            cpe_id="cpe-001",
        )

    def test_returns_false_when_gpv_raises(self):
        acs = MagicMock()
        acs.GPV.side_effect = Exception("unreachable")
        result = is_cpe_online(acs, "cpe-001")
        assert result is False
