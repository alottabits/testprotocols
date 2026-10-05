"""Telemetry (shape 5): Router.read_telemetry supersedes get_telemetry."""

from __future__ import annotations

import dataclasses
import typing
from collections.abc import Mapping

import pytest
from testprotocols.deprecation import warn_renamed
from testprotocols.models import (
    LinkHealthReport,
    LinkStatus,
    PathMetrics,
    RouteEntry,
    Telemetry,
)
from testprotocols.router import Router
from testprotocols.sdwan_policy_manager import SdwanPolicyManager


def test_telemetry_fields_and_defaults() -> None:
    t = Telemetry(uptime_seconds=12.5)
    assert (t.uptime_seconds, t.cpu_load_percent, t.mem_used_percent) == (12.5, None, None)
    full = Telemetry(1.0, 2.0, 3.0)
    assert dataclasses.astuple(full) == (1.0, 2.0, 3.0)
    assert [f.name for f in dataclasses.fields(Telemetry)] == [
        "uptime_seconds",
        "cpu_load_percent",
        "mem_used_percent",
    ]


def test_telemetry_is_frozen() -> None:
    t = Telemetry(1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.uptime_seconds = 2.0  # type: ignore[misc]


def test_telemetry_accepts_ints() -> None:
    assert Telemetry(uptime_seconds=5, cpu_load_percent=0).uptime_seconds == 5


def _released(telemetry: Telemetry) -> dict[str, float]:
    """The released ``get_telemetry`` mapping: the reported values, by field name."""
    return {k: v for k, v in dataclasses.asdict(telemetry).items() if v is not None}


class _Router:
    """A driver in the migration shape: the new member, and the old one delegating."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._telemetry = telemetry

    def read_telemetry(self) -> Telemetry:
        return self._telemetry

    def get_telemetry(self) -> Mapping[str, float]:
        warn_renamed("get_telemetry", "read_telemetry")
        return _released(self.read_telemetry())

    def get_active_wan_interface(self, flow_dst: str | None = None) -> str | None:
        return None

    def get_wan_interface_status(self) -> dict[str, LinkStatus]:
        return {}

    def get_wan_path_metrics(self) -> dict[str, PathMetrics]:
        return {}

    def get_link_health(self, wan_label: str) -> LinkHealthReport:
        raise NotImplementedError

    def get_routing_table(self) -> list[RouteEntry]:
        return []


@pytest.mark.parametrize(
    "telemetry", [Telemetry(10.0), Telemetry(10.0, 5.5, 40.0), Telemetry(0.0, 0.0, 0.0)]
)
def test_old_member_equals_the_new_record_as_a_dict(telemetry: Telemetry) -> None:
    router = _Router(telemetry)
    assert isinstance(router, Router)
    with pytest.warns(DeprecationWarning, match=r"get_telemetry is deprecated; use read_telemetry"):
        old = router.get_telemetry()
    new = router.read_telemetry()
    assert old == _released(new)


def test_a_driver_without_the_new_member_is_not_a_router() -> None:
    class Old:
        def get_telemetry(self) -> dict[str, float]:
            return {}

    assert not isinstance(Old(), Router)


def test_apply_policy_keeps_its_name_and_takes_dict_of_objects_not_any() -> None:
    hints = typing.get_type_hints(SdwanPolicyManager.apply_policy)
    assert hints["policy"] == dict[str, object]
    assert hints["return"] is type(None)
    assert "deprecated" in (SdwanPolicyManager.apply_policy.__doc__ or "").lower()
