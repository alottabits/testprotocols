"""Tests for testoperations.netem_controller module."""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock

import pytest
from testoperations.netem_controller import (
    _PRESETS,  # pyright: ignore[reportPrivateUsage]
    NetemPreset,
    apply_preset,
    inject_blackout,
    inject_brownout,
    inject_latency_spike,
    inject_packet_storm,
)
from testprotocols.models.impairment import ImpairmentProfile

# A driver with only the released member names (no ``inject_event``): the operations make the
# released ``inject_transient`` calls. New-name drivers: test_renamed_host_members.py.
_OLD_NAMES = ["inject_transient", "set_impairment_profile", "set_interface_profile", "clear"]

# ---------------------------------------------------------------------------
# apply_preset
# ---------------------------------------------------------------------------


class TestApplyPreset:
    def test_applies_known_preset(self) -> None:
        netem = MagicMock()
        apply_preset(netem, NetemPreset.DSL)
        netem.set_impairment_profile.assert_called_once()
        profile = netem.set_impairment_profile.call_args[0][0]
        assert isinstance(profile, ImpairmentProfile)

    def test_a_plain_string_preset_warns_and_still_applies(self) -> None:
        netem = MagicMock()
        with pytest.warns(DeprecationWarning, match="NetemPreset.DSL"):
            apply_preset(netem, "dsl")
        assert netem.set_impairment_profile.call_args[0][0] == _PRESETS[NetemPreset.DSL]

    def test_the_enum_is_the_preset_table(self) -> None:
        assert {p.value for p in NetemPreset} == {
            "clean",
            "dsl",
            "cable",
            "lte",
            "3g",
            "satellite",
            "degraded",
            "lossy",
        }
        assert set(_PRESETS) == set(NetemPreset)

    def test_a_member_applies_silently(self) -> None:
        netem = MagicMock()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            for preset in NetemPreset:
                apply_preset(netem, preset)

    def test_raises_for_unknown_preset(self) -> None:
        netem = MagicMock()
        with pytest.raises(ValueError, match="preset_name"):
            apply_preset(netem, "nonexistent_preset")


# ---------------------------------------------------------------------------
# inject_blackout
# ---------------------------------------------------------------------------


class TestInjectBlackout:
    def test_delegates_to_netem_inject_transient(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        inject_blackout(netem, duration_ms=2000)
        netem.inject_transient.assert_called_once_with("blackout", 2000)

    def test_passes_duration(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        inject_blackout(netem, duration_ms=500)
        netem.inject_transient.assert_called_once_with("blackout", 500)


# ---------------------------------------------------------------------------
# inject_brownout
# ---------------------------------------------------------------------------


class TestInjectBrownout:
    def test_delegates_to_netem_inject_transient(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        inject_brownout(netem, duration_ms=3000, loss_percent=50.0)
        netem.inject_transient.assert_called_once_with("brownout", 3000, loss_percent=50.0)


# ---------------------------------------------------------------------------
# inject_latency_spike
# ---------------------------------------------------------------------------


class TestInjectLatencySpike:
    def test_delegates_to_netem_inject_transient(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        inject_latency_spike(netem, duration_ms=1000, latency_ms=500)
        netem.inject_transient.assert_called_once_with("latency_spike", 1000, latency_ms=500)


# ---------------------------------------------------------------------------
# inject_packet_storm
# ---------------------------------------------------------------------------


class TestInjectPacketStorm:
    def test_delegates_to_netem_inject_transient(self) -> None:
        netem = MagicMock(spec=_OLD_NAMES)
        inject_packet_storm(netem, duration_ms=500, duplicate_percent=100.0)
        netem.inject_transient.assert_called_once_with("packet_storm", 500, duplicate_percent=100.0)
