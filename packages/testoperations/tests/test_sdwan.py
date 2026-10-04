"""Tests for testoperations.sdwan module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.sdwan import measure_failover_convergence

# A driver with only the released member names (no ``inject_event``).
_OLD_NAMES = ["inject_transient"]

# ---------------------------------------------------------------------------
# measure_failover_convergence
# ---------------------------------------------------------------------------


class TestMeasureFailoverConvergence:
    def test_calls_inject_transient_on_netem(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        router = MagicMock()
        # First call returns original wan, subsequent calls return new wan
        router.get_active_wan_interface.side_effect = ["wan0", "wan0", "wan1"]

        result = measure_failover_convergence(netem, router, "wan0", timeout_ms=3000)

        netem.inject_transient.assert_called_once_with("blackout", 3000)
        assert isinstance(result, (int, float))

    def test_returns_elapsed_ms(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        router = MagicMock()
        router.get_active_wan_interface.side_effect = ["wan0", "wan1"]

        result = measure_failover_convergence(netem, router, "wan0", timeout_ms=1000)
        assert result >= 0
