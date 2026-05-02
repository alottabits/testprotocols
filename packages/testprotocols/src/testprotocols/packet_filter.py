"""Firewall / PacketFilter template.

Defines the abstract contract for stateless and stateful packet-filtering
rules on a device's INPUT, OUTPUT, and FORWARD paths. Rules are addressed
by a stable logical *name* and expressed as transport-agnostic
``FirewallRule`` records — drivers translate into iptables, nftables,
pf, or vendor CLI as appropriate.

In scope: per-chain rule administration (add / remove / list / get /
flush), chain default-policy control, and per-rule packet/byte counters.

Out of scope: NAT (see ``nat``), high-level port forwarding (see
``port_forwarding``), conntrack inspection (see ``conntrack``),
zone-based policy (see ``firewall_zones``), and L7 application-aware
classification (see ``sdwan_policy_manager.apply_firewall_rule``).

The IPv4 / IPv6 split is not a contract dimension — each rule's address
family is inferred from its CIDR fields. Drivers that maintain separate
v4/v6 tables internally do so transparently.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import FirewallRule


@runtime_checkable
class PacketFilter(Protocol):
    """Abstract contract for stateless / stateful packet filtering."""

    # --- Rule lifecycle ---

    def add_rule(
        self,
        chain: str,
        rule: FirewallRule,
        position: int | None = None,
    ) -> None:
        """Insert *rule* into *chain* at *position*.

        *chain* is one of ``"INPUT"``, ``"OUTPUT"``, ``"FORWARD"``.
        *position* is 1-based: ``1`` inserts at the top, ``None`` appends
        at the end.

        Raises ValueError if *chain* is unknown, if a rule named
        ``rule.name`` already exists in *chain*, or if *position* is
        less than 1.
        """
        ...

    def remove_rule(self, chain: str, name: str) -> None:
        """Remove the rule identified by *name* from *chain*.

        Raises ValueError if *chain* is unknown.
        Raises KeyError if no rule with that name exists in *chain*.
        """
        ...

    def list_rules(self, chain: str) -> list[FirewallRule]:
        """Return all rules currently installed in *chain*, in evaluation order.

        Raises ValueError if *chain* is unknown.
        """
        ...

    def get_rule(self, chain: str, name: str) -> FirewallRule:
        """Return the rule identified by *name* in *chain*.

        Raises ValueError if *chain* is unknown.
        Raises KeyError if no rule with that name exists in *chain*.
        """
        ...

    def flush_chain(self, chain: str) -> None:
        """Remove every rule from *chain*. Default policy is unchanged.

        Raises ValueError if *chain* is unknown.
        """
        ...

    # --- Default policy ---

    def set_default_policy(self, chain: str, policy: str) -> None:
        """Set the default action for traffic on *chain* that matches no rule.

        *policy* is one of ``"accept"``, ``"drop"``, ``"reject"``.
        Raises ValueError if *chain* is unknown or *policy* is not
        a valid value.
        """
        ...

    def get_default_policy(self, chain: str) -> str:
        """Return the current default policy of *chain*.

        Raises ValueError if *chain* is unknown.
        """
        ...

    # --- Counters ---

    def get_rule_counters(self, chain: str, name: str) -> tuple[int, int]:
        """Return ``(packets, bytes)`` matched by the rule since it was added.

        Raises ValueError if *chain* is unknown.
        Raises KeyError if no rule with that name exists in *chain*.
        Drivers without per-rule counter support raise NotImplementedError.
        """
        ...


@runtime_checkable
class PacketFilterWhiteBox(PacketFilter, Protocol):
    """White-box extension of PacketFilter for raw kernel-level introspection.

    Linux drivers that can shell into the box satisfy this extension by
    capturing the underlying iptables / nftables ruleset. Vendor-RTOS or
    locked-down devices typically satisfy only the base ``PacketFilter``
    Protocol; tests requiring kernel-level rule verification should pin
    against ``PacketFilterWhiteBox`` and accept the collection-skip on
    drivers that don't satisfy it (per the ``@white_box`` scenario tag rule).
    """

    def get_kernel_iptables_dump(self) -> str:
        """Return the raw ``iptables-save`` output (legacy iptables backend).

        For drivers running on a Linux kernel with the legacy iptables
        backend. Format is the standard iptables-save serialisation. Tests
        parse this to verify rules landed at the kernel level rather than
        only in the driver's intermediate state.
        """
        ...

    def get_nftables_ruleset(self) -> str:
        """Return the raw ``nft list ruleset`` output (nftables backend).

        For drivers running on a Linux kernel with the nftables backend.
        Format is the standard nftables ruleset serialisation. Returns
        the entire ruleset across all tables and families; tests grep
        for the rules they care about.
        """
        ...
