"""Firewall / NAT template.

Defines the abstract contract for low-level NAT primitives — SNAT,
DNAT, and 1:1 / static NAT. Rules are identified by a stable logical
*name* and expressed as transport-agnostic ``NatRule`` records.

In scope: rule lifecycle (add / remove / list / get / flush), enable
toggles, and per-rule packet/byte counters.

Out of scope: high-level / named port-forwarding entries (see the
port-mapping surface on ``firewall.Firewall``), packet-filter rules
(see ``packet_filter`` or the rule-administration surface inherited
by ``firewall.Firewall``), and zone-level masquerade (a per-zone flag
on ``firewall_zones``).

NAT and packet-filter rules are kept in separate templates because a
device may legitimately compose one without the other (e.g. a transit
router does NAT only; a host firewall does packet-filter only).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import NatRule


@runtime_checkable
class Nat(Protocol):
    """Abstract contract for low-level NAT primitives."""

    # --- Rule lifecycle ---

    def add_nat_rule(self, rule: NatRule) -> None:
        """Install a NAT rule.

        Validates that *rule.mode* is one of ``"snat"``, ``"dnat"``,
        ``"1to1"`` and that the per-mode field invariants hold (see
        ``NatRule`` docstring). Raises ValueError on a duplicate
        ``rule.name``, on an unknown mode, or on mode/field
        inconsistency (e.g. *translated_src* set with ``mode="dnat"``).
        """
        ...

    def remove_nat_rule(self, name: str) -> None:
        """Remove the NAT rule identified by *name*.

        Raises KeyError if no rule with that name exists.
        """
        ...

    def list_nat_rules(self, mode: str | None = None) -> list[NatRule]:
        """Return installed NAT rules, optionally filtered by *mode*.

        *mode* is one of ``None`` (all), ``"snat"``, ``"dnat"``,
        ``"1to1"``. Raises ValueError if *mode* is set but not one of
        the recognized values.
        """
        ...

    def get_nat_rule(self, name: str) -> NatRule:
        """Return the NAT rule identified by *name*.

        Raises KeyError if no rule with that name exists.
        """
        ...

    def set_nat_rule_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable an existing NAT rule without removing it.

        Raises KeyError if no rule with that name exists.
        """
        ...

    def flush_nat_rules(self) -> None:
        """Remove every NAT rule on this device."""
        ...

    # --- Counters ---

    def get_nat_rule_counters(self, name: str) -> tuple[int, int]:
        """Return ``(packets, bytes)`` matched by the rule since it was added.

        Raises KeyError if no rule with that name exists.
        Drivers without per-rule counter support raise NotImplementedError.
        """
        ...
