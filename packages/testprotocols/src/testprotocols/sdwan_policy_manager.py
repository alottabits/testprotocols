"""SD-WAN policy manager template.

Defines the abstract contract for SD-WAN path/policy management: generic
policy application, SLA policies, and application-flow visibility.

Firewall-rule administration is **not** here — it moved to the dedicated
``l3_firewall`` / ``l7_firewall`` capabilities (coherent-domain split; see
SPLITS.md). Path/app steering with typed rules (uplink selection, performance
classes) is a planned addition tracked in GAPS.md.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.wan_edge import AppFlow, SLAPolicy


@runtime_checkable
class SdwanPolicyManager(Protocol):
    """Abstract contract for SD-WAN policy management operations."""

    def apply_policy(self, policy: dict[str, Any]) -> None:
        """Apply a generic SD-WAN policy specified as a dict."""
        ...

    def remove_policy(self, name: str) -> None:
        """Remove the SD-WAN policy with the given name."""
        ...

    def configure_sla_policy(self, policy: SLAPolicy) -> None:
        """Configure an SLA policy on the SD-WAN device."""
        ...

    def remove_sla_policy(self, name: str) -> None:
        """Remove the SLA policy with the given name."""
        ...

    def get_application_flows(
        self,
        since_s: int = 60,
        app_filter: str | None = None,
    ) -> list[AppFlow]:
        """Return application flows observed in the last *since_s* seconds."""
        ...
