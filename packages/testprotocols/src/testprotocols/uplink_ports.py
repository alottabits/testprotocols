"""Uplink switch-port wiring — boundary view of a WAN edge's declared uplink ports.

A testbed that instruments a WAN uplink (splicing an impairment path into it,
re-VLANing the port that carries it) needs to know **which managed-switch
ports carry which uplink**. That is a declared-topology fact the device's
driver resolves from its own configuration — a boundary view in the
``DeviceInfo`` / ``PlacementPipe`` family, not behaviour.

The placement split carries over: the WAN-edge device declares which ports
carry its uplinks (**topology**, this view — the ``PlacementPipe`` analogue),
while the switch's ``PlacementPorts`` remains the **write authorization** for
re-VLANing anything. The two declarations stay independent, owned by the two
resources they describe.

One uplink maps to a *tuple* of port references — one per chassis / redundant
pair member — because a warm-spare pair shares its WAN segments: moving one
member's port and not its twin's splits the segment, so a consumer must see
the full member set to act on an uplink coherently.

The **as-found VLAN is deliberately absent**: port VLANs drift, so a recorded
value would rot; a consumer captures the as-found state live from the switch
at the moment it writes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class UplinkPortRef:
    """One switch port carrying (one member's leg of) a WAN uplink."""

    member: str
    """Device (chassis / redundant-pair member) whose WAN port this is."""

    switch: str
    """Name of the managed switch carrying the port."""

    port: str
    """The switch port carrying this member's uplink."""


@runtime_checkable
class UplinkPorts(Protocol):
    """Abstract contract for a WAN edge's declared uplink→switch-port wiring."""

    @property
    def wan_ports(self) -> Mapping[str, tuple[UplinkPortRef, ...]]:
        """Uplink name → the switch ports carrying that uplink, one entry per
        chassis / pair member; empty mapping when the wiring is undeclared."""
        ...
