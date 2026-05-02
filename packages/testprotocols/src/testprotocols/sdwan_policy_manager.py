"""SD-WAN policy manager template.

Defines the abstract contract for managing SD-WAN policies including SLA
policies, firewall rules, and application flow visibility.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.firewall import FirewallRule
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

    def apply_firewall_rule(self, rule: FirewallRule) -> None:
        """Apply a firewall rule to the SD-WAN device."""
        ...

    def remove_firewall_rule(self, name: str) -> None:
        """Remove the firewall rule with the given name."""
        ...

    def get_application_flows(
        self,
        since_s: int = 60,
        app_filter: str | None = None,
    ) -> list[AppFlow]:
        """Return application flows observed in the last *since_s* seconds."""
        ...

    def get_firewall_rules(self) -> list[FirewallRule]:
        """Return the list of currently configured firewall rules."""
        ...
