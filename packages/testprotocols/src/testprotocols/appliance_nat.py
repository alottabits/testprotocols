"""NAT template — managed SD-WAN appliance edition.

Defines the abstract contract for an appliance's NAT surfaces: 1:1 NAT, 1:Many
(PAT), and port-forwarding (DNAT). Each is an ordered list read and replaced as
a whole — the appliance-native shape, distinct from the host-tier ``nat.Nat``
(iptables SNAT/DNAT primitives, add/remove by name) used by the Linux digital
twin.

In scope: read/replace the 1:1, 1:Many, and port-forwarding rule lists.

Out of scope: low-level iptables NAT primitives (see ``nat``), firewall rules
(see ``l3_firewall`` / ``l7_firewall``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import (
    OneToManyNatRule,
    OneToOneNatRule,
    PortForwardRule,
)


@runtime_checkable
class ApplianceNat(Protocol):
    """Abstract contract for an appliance's NAT rule sets."""

    def set_one_to_one_rules(self, rules: list[OneToOneNatRule]) -> None:
        """Replace the 1:1 NAT mapping list with *rules*."""
        ...

    def get_one_to_one_rules(self) -> list[OneToOneNatRule]:
        """Return the 1:1 NAT mappings."""
        ...

    def set_one_to_many_rules(self, rules: list[OneToManyNatRule]) -> None:
        """Replace the 1:Many (PAT) mapping list with *rules*."""
        ...

    def get_one_to_many_rules(self) -> list[OneToManyNatRule]:
        """Return the 1:Many (PAT) mappings."""
        ...

    def set_port_forwarding_rules(self, rules: list[PortForwardRule]) -> None:
        """Replace the port-forwarding rule list with *rules*."""
        ...

    def get_port_forwarding_rules(self) -> list[PortForwardRule]:
        """Return the port-forwarding rules."""
        ...
