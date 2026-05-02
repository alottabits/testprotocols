"""Traffic / IperfGenerator template.

Defines the abstract contract for a higher-level iperf traffic generator
that manages flows and returns structured results.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.traffic import TrafficResult, TrafficSpec


@runtime_checkable
class IperfGenerator(Protocol):
    """Abstract contract for iperf-based traffic flow management."""

    @property
    def server_ip(self) -> str:
        """IP address of the iperf server."""
        ...

    @property
    def active_flows(self) -> list[str]:
        """List of currently active traffic flow IDs."""
        ...

    def start_traffic(self, spec: TrafficSpec) -> str:
        """Start a traffic flow defined by *spec* and return its flow ID."""
        ...

    def stop_traffic(self, flow_id: str) -> TrafficResult:
        """Stop the traffic flow identified by *flow_id* and return its result."""
        ...

    def stop_all_traffic(self) -> dict[str, TrafficResult]:
        """Stop all active traffic flows and return a mapping of flow_id to result."""
        ...

    def run_traffic(self, spec: TrafficSpec) -> TrafficResult:
        """Run a traffic flow defined by *spec* to completion and return the result."""
        ...
