"""WAN link administration template — host-substrate WAN edge.

Defines the abstract contract for administratively bringing a WAN link down
or up by label. The lever is published by a Linux-based WAN edge (the
digital twin), which can admin-down its own uplink, and by a closed gateway
whose management plane carries an administrative WAN enable (the CPE gateway
archetype composes it as ``wan_admin``, with the connection's name as the
label and ``wan_connection.get_wan_state`` as the paired read). An
API-managed appliance generally cannot — its management plane exposes no
such operation, and link impairment for appliance tests is the
traffic-controller's job (the same boundary as the netem precedent; see
SPLITS.md). The methods moved here from ``router.Router`` so the read
surface stays universal across the WAN-edge archetypes while link
administration rides only on the substrates that publish it.

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
