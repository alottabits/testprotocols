"""Tests for the boundary-facing capability protocol templates.

These protocols carry vendor-neutral metadata a driver resolves from its own
config or discovers at runtime (homing, placement, identity, ownership) —
formerly bare scalars on the device archetypes. Each is a small namespace of
read-only properties so archetypes stay capability-only.
"""

from __future__ import annotations

from _helpers import protocol_attrs
from testprotocols.config_ownership import ConfigOwnership
from testprotocols.device_info import DeviceInfo
from testprotocols.network_attachment import NetworkAttachment
from testprotocols.placement import PlacementPipe, PlacementPorts
from testprotocols.uplink_ports import UplinkPortRef, UplinkPorts


def test_network_attachment_members() -> None:
    assert protocol_attrs(NetworkAttachment) == {
        "test_ip",
        "mgmt_ip",
        "segment",
        "subnet",
        "test_interface",
    }


def test_placement_pipe_members() -> None:
    assert protocol_attrs(PlacementPipe) == {"switch", "port"}


def test_placement_ports_members() -> None:
    assert protocol_attrs(PlacementPorts) == {"ports"}


def test_device_info_members() -> None:
    assert protocol_attrs(DeviceInfo) == {"model"}


def test_config_ownership_members() -> None:
    assert protocol_attrs(ConfigOwnership) == {"manages_network"}


def test_uplink_ports_members() -> None:
    assert protocol_attrs(UplinkPorts) == {"wan_ports"}


def test_uplink_ports_view_satisfies_runtime_check() -> None:
    """A driver view exposing the wiring mapping satisfies the runtime check."""

    class _View:
        @property
        def wan_ports(self) -> dict[str, tuple[UplinkPortRef, ...]]:
            return {
                "wan1": (
                    UplinkPortRef(member="edge-a", switch="dist-1", port="7"),
                    UplinkPortRef(member="edge-b", switch="dist-1", port="8"),
                ),
            }

    assert isinstance(_View(), UplinkPorts)
    assert _View().wan_ports["wan1"][0].switch == "dist-1"


def test_runtime_checkable_with_plain_attributes() -> None:
    """A driver view exposing plain attributes satisfies the runtime check."""

    class _View:
        test_ip = "10.1.30.50/24"
        mgmt_ip = "192.0.2.10"
        segment = "provider-vpn"
        subnet = "10.1.30.0/24"
        test_interface = "eth1"

    assert isinstance(_View(), NetworkAttachment)
