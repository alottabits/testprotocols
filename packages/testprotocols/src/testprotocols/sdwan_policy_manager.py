"""SD-WAN policy manager template.

Defines the abstract contract for SD-WAN path/policy management: generic
policy application, SLA policies, and application-flow visibility.

Firewall-rule administration is **not** here — it moved to the dedicated
``l3_firewall`` / ``l7_firewall`` capabilities (coherent-domain split; see
SPLITS.md). Typed path steering (``set_uplink_selection`` /
``get_uplink_selection`` over ordered ``UplinkSelectionRule``s; performance
classes reuse ``SLAPolicy`` by name) landed 2026-06-12; the default
(primary) uplink pair (``get_default_uplink`` / ``set_default_uplink``)
landed 2026-07-03 — the network-wide "which uplink carries default-routed
traffic" knob, distinct from per-flow steering. ``apply_policy`` remains
the generic escape hatch for vendor-shaped policies beyond that surface.
Application-match steering grows on evidence.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import UplinkSelectionRule
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

    def get_default_uplink(self) -> str:
        """Return the name of the network's default (primary) uplink.

        The default uplink carries all default-routed traffic that no
        uplink-selection rule steers elsewhere — e.g. ``"wan1"``. Vendor
        drivers map this to their primary-uplink notion.
        """
        ...

    def set_default_uplink(self, uplink: str) -> None:
        """Set the network's default (primary) uplink to *uplink*.

        Changes only which uplink carries default-routed traffic; the
        ordered uplink-selection rules (``set_uplink_selection``) are left
        untouched. Drivers reject names the product cannot express (e.g.
        an uplink the appliance does not have) rather than approximating.
        """
        ...

    def set_uplink_selection(self, rules: list[UplinkSelectionRule]) -> None:
        """Replace the ordered uplink-selection rule list with *rules*.

        The list is the complete steering policy in evaluation order. A rule
        referencing a ``performance_class`` requires the named ``SLAPolicy``
        to be configured (``configure_sla_policy``); products that cannot
        express arbitrary performance thresholds raise unsupported-capability
        for such rules rather than approximating.
        """
        ...

    def get_uplink_selection(self) -> list[UplinkSelectionRule]:
        """Return the uplink-selection rules in evaluation order."""
        ...
