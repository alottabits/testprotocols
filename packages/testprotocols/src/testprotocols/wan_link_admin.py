"""WAN link administration template — host-substrate WAN edge.

Defines the abstract contract for administratively bringing a WAN link down
or up by label. This is a **host-substrate lever**: a Linux-based WAN edge
(the digital twin) can admin-down its own uplink, but an API-managed
appliance generally cannot — its management plane exposes no such operation,
and link impairment for appliance tests is the traffic-controller's job (the
same boundary as the netem precedent; see SPLITS.md). The methods moved here
from ``router.Router`` so the read surface stays universal across both
WAN-edge archetypes while link administration rides only on the twin.

In scope: administrative up/down of a WAN link identified by label.

Out of scope: link impairment — latency/loss/blackout shaping (see
``netem_controller``), uplink status reads (see ``router`` /
``appliance_uplinks``), and per-netdev interface config (see ``ip_interface``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WanLinkAdmin(Protocol):
    """Abstract contract for administrative WAN link up/down."""

    def bring_wan_down(self, label: str) -> None:
        """Bring down the WAN interface identified by *label*."""
        ...

    def bring_wan_up(self, label: str) -> None:
        """Bring up the WAN interface identified by *label*."""
        ...
