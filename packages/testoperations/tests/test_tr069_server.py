"""Tests for testoperations.tr069_server module."""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock

import pytest
from testoperations.tr069_server import is_cpe_online
from testprotocols.models import CwmpType, ParameterValue

_UPTIME = "InternetGatewayDevice.DeviceInfo.UpTime"

# A driver with only the released RPC names (no ``get_parameter_values``): the operation makes
# the released ``GPV`` call. A migrated driver has both names; the operation uses the new one.
_OLD_NAMES = ["GPV"]
_NEW_NAMES = ["get_parameter_values", "GPV"]

# ---------------------------------------------------------------------------
# is_cpe_online
# ---------------------------------------------------------------------------


class TestIsCpeOnline:
    def test_returns_true_when_the_typed_rpc_succeeds(self) -> None:
        acs = MagicMock(spec=_NEW_NAMES)
        acs.get_parameter_values.return_value = [ParameterValue(_UPTIME, 42, CwmpType.UNSIGNED_INT)]
        assert is_cpe_online(acs, "cpe-001") is True
        acs.get_parameter_values.assert_called_once_with([_UPTIME], cpe_id="cpe-001")
        acs.GPV.assert_not_called()

    def test_returns_false_when_the_typed_rpc_raises(self) -> None:
        acs = MagicMock(spec=_NEW_NAMES)
        acs.get_parameter_values.side_effect = Exception("unreachable")
        assert is_cpe_online(acs, "cpe-001") is False
        acs.GPV.assert_not_called()

    def test_old_rpc_still_works_through_the_accessor(self) -> None:
        acs = MagicMock(spec=_OLD_NAMES)
        acs.GPV.return_value = [{"key": _UPTIME, "value": "42", "type": "xsd:unsignedInt"}]
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert is_cpe_online(acs, "cpe-001") is True
        acs.GPV.assert_called_once_with(_UPTIME, cpe_id="cpe-001")

    def test_returns_false_when_the_old_rpc_raises(self) -> None:
        acs = MagicMock(spec=_OLD_NAMES)
        acs.GPV.side_effect = Exception("unreachable")
        assert is_cpe_online(acs, "cpe-001") is False


def test_the_accessor_refuses_a_name_that_is_not_one_str() -> None:
    from testoperations._renamed import get_parameter_value

    acs = MagicMock(spec=_NEW_NAMES)
    with pytest.raises(TypeError, match="one parameter name"):
        get_parameter_value(acs, [_UPTIME])  # type: ignore[arg-type]
    acs.get_parameter_values.assert_not_called()
