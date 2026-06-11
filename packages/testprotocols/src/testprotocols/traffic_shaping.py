"""Traffic-shaping template — managed SD-WAN appliance.

Defines the abstract contract for an appliance's bandwidth and QoS shaping:
per-uplink bandwidth caps, a global per-client cap, and an ordered set of
shaping rules that match a traffic class and limit / DSCP-mark / prioritize it.

In scope: uplink bandwidth, global per-client bandwidth, and the shaping-rule
list (which also carries DSCP marking).

Out of scope: SD-WAN path selection / SLA steering (see ``sdwan_policy_manager``),
firewall rules (see ``l3_firewall`` / ``l7_firewall``), and link impairment
(``netem`` lives on the traffic-controller device, not the appliance).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import ShapingRule


@runtime_checkable
class TrafficShaping(Protocol):
    """Abstract contract for an appliance's bandwidth / QoS shaping."""

    def set_uplink_bandwidth(self, uplink: str, down_kbps: int, up_kbps: int) -> None:
        """Set the down/up bandwidth limit (kbps) for the named WAN *uplink*."""
        ...

    def get_uplink_bandwidth(self) -> dict[str, tuple[int, int]]:
        """Return ``{uplink: (down_kbps, up_kbps)}`` for every uplink."""
        ...

    def set_global_client_bandwidth(self, down_kbps: int, up_kbps: int) -> None:
        """Set the global per-client down/up bandwidth limit (kbps)."""
        ...

    def get_global_client_bandwidth(self) -> tuple[int, int]:
        """Return the global per-client ``(down_kbps, up_kbps)`` limit."""
        ...

    def set_shaping_rules(self, rules: list[ShapingRule]) -> None:
        """Replace the ordered shaping-rule list with *rules*."""
        ...

    def get_shaping_rules(self) -> list[ShapingRule]:
        """Return the shaping rules in evaluation order."""
        ...
