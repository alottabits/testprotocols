"""L7 firewall template — application-aware allow/deny for a managed appliance.

Defines the abstract contract for an SD-WAN appliance's L7 (application-aware)
firewall: an ordered list of rules that match by application, application
category, host, port, or IP range and allow/deny accordingly. Like
``l3_firewall.L3Firewall`` the policy is read and replaced as a whole list.

In scope: read and replace the ordered L7 rule list.

Out of scope: L3 5-tuple filtering (see ``l3_firewall``), URL / content-category
blocking (see ``content_filtering``), and traffic shaping (see
``traffic_shaping``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import L7Rule


@runtime_checkable
class L7Firewall(Protocol):
    """Abstract contract for an appliance's ordered L7 firewall policy."""

    def set_rules(self, rules: list[L7Rule]) -> None:
        """Replace the ordered L7 policy with *rules* (complete, in order)."""
        ...

    def get_rules(self) -> list[L7Rule]:
        """Return the L7 rules in evaluation order."""
        ...
