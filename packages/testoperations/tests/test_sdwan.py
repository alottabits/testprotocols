"""Tests for testoperations.sdwan module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.sdwan import measure_failover_convergence

# ---------------------------------------------------------------------------
# measure_failover_convergence
# ---------------------------------------------------------------------------


class TestMeasureFailoverConvergence:
    def test_calls_inject_transient_on_netem(self):
        netem = MagicMock()
        router = MagicMock()
        # First call returns original wan, subsequent calls return new wan
        router.get_active_wan_interface.side_effect = ["wan0", "wan0", "wan1"]

        result = measure_failover_convergence(netem, router, "wan0", timeout_ms=3000)

        netem.inject_transient.assert_called_once_with("blackout", 3000)
        assert isinstance(result, (int, float))

    def test_returns_elapsed_ms(self):
        netem = MagicMock()
        router = MagicMock()
        router.get_active_wan_interface.side_effect = ["wan0", "wan1"]

        result = measure_failover_convergence(netem, router, "wan0", timeout_ms=1000)
        assert result >= 0
