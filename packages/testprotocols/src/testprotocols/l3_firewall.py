"""L3 firewall template — managed SD-WAN appliance edition.

Defines the abstract contract for a managed SD-WAN appliance's L3 firewall:
**ordered allow/deny policy lists** for outbound (LAN→WAN) and inbound (WAN→LAN)
traffic. A managed appliance exposes each direction as a single ordered list
that is read and replaced as a whole — distinct from
``packet_filter.PacketFilter`` (netfilter INPUT/OUTPUT/FORWARD chains, add/remove
a rule by name), which models a Linux host's stateless filter.

In scope: read and replace the outbound and inbound ordered rule lists.

Out of scope: L7 / application-aware rules (see ``l7_firewall``), URL / category
filtering (see ``content_filtering``), NAT and port-forwarding (see
``appliance_nat``), and netfilter-chain filtering (see ``packet_filter``).

Rules are transport-agnostic ``L3Rule`` records; the driver translates them
into its product's API. Value vocabularies (``action``, ``protocol``) are the
normalized sets in ``models.sdwan_appliance``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import L3Rule


@runtime_checkable
class L3Firewall(Protocol):
    """Abstract contract for an appliance's ordered L3 firewall policy."""

    def set_outbound_rules(self, rules: list[L3Rule]) -> None:
        """Replace the ordered outbound (LAN→WAN) policy with *rules*.

        The list is the complete policy in evaluation order; the driver
        replaces the appliance's outbound ruleset wholesale.
        """
        ...

    def get_outbound_rules(self) -> list[L3Rule]:
        """Return the outbound (LAN→WAN) rules in evaluation order."""
        ...

    def set_inbound_rules(self, rules: list[L3Rule]) -> None:
        """Replace the ordered inbound (WAN→LAN) policy with *rules*.

        The list is the complete policy in evaluation order; the driver
        replaces the appliance's inbound ruleset wholesale.
        """
        ...

    def get_inbound_rules(self) -> list[L3Rule]:
        """Return the inbound (WAN→LAN) rules in evaluation order."""
        ...
