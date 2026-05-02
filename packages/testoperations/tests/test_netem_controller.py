"""Tests for testoperations.netem_controller module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.netem_controller import (
    apply_preset,
    inject_blackout,
    inject_brownout,
    inject_latency_spike,
    inject_packet_storm,
)
from testprotocols.models.impairment import ImpairmentProfile

# ---------------------------------------------------------------------------
# apply_preset
# ---------------------------------------------------------------------------


class TestApplyPreset:
    def test_applies_known_preset(self):
        netem = MagicMock()
        apply_preset(netem, "dsl")
        netem.set_impairment_profile.assert_called_once()
        profile = netem.set_impairment_profile.call_args[0][0]
        assert isinstance(profile, ImpairmentProfile)

    def test_raises_for_unknown_preset(self):
        netem = MagicMock()
        with pytest.raises(ValueError, match="unknown preset"):
            apply_preset(netem, "nonexistent_preset")


# ---------------------------------------------------------------------------
# inject_blackout
# ---------------------------------------------------------------------------


class TestInjectBlackout:
    def test_delegates_to_netem_inject_transient(self):
        netem = MagicMock()
        inject_blackout(netem, duration_ms=2000)
        netem.inject_transient.assert_called_once_with("blackout", 2000)

    def test_passes_duration(self):
        netem = MagicMock()
        inject_blackout(netem, duration_ms=500)
        netem.inject_transient.assert_called_once_with("blackout", 500)


# ---------------------------------------------------------------------------
# inject_brownout
# ---------------------------------------------------------------------------


class TestInjectBrownout:
    def test_delegates_to_netem_inject_transient(self):
        netem = MagicMock()
        inject_brownout(netem, duration_ms=3000, loss_percent=50.0)
        netem.inject_transient.assert_called_once_with("brownout", 3000, loss_percent=50.0)


# ---------------------------------------------------------------------------
# inject_latency_spike
# ---------------------------------------------------------------------------


class TestInjectLatencySpike:
    def test_delegates_to_netem_inject_transient(self):
        netem = MagicMock()
        inject_latency_spike(netem, duration_ms=1000, latency_ms=500)
        netem.inject_transient.assert_called_once_with("latency_spike", 1000, latency_ms=500)


# ---------------------------------------------------------------------------
# inject_packet_storm
# ---------------------------------------------------------------------------


class TestInjectPacketStorm:
    def test_delegates_to_netem_inject_transient(self):
        netem = MagicMock()
        inject_packet_storm(netem, duration_ms=500, duplicate_percent=100.0)
        netem.inject_transient.assert_called_once_with("packet_storm", 500, duplicate_percent=100.0)
