"""Firewall / Zones template.

Defines the abstract contract for zone-based firewall administration —
the OpenWrt / firewalld / pfSense interface-group model in which traffic
policy is expressed at the zone level rather than as flat chain rules.

A zone groups one or more interfaces and / or CIDR networks under a
shared default-input / default-forward / default-output action. Per-zone-
pair forwarding policy controls fall-through traffic between zones; more
specific rules go in the ``packet_filter`` template (or the inherited
rule-administration surface on ``firewall.Firewall`` for gateway
devices) — on a zone-aware device they target a zone instead of a
chain, which drivers map internally.

In scope: zone CRUD, interface / network membership, zone defaults,
masquerade and MSS-clamping toggles, and zone-pair forwarding policy.

Out of scope: per-flow filtering (see ``packet_filter`` / ``firewall``),
NAT rules (see ``nat``), and per-zone counters (deferred — not all
drivers expose them).

Devices on a flat-chain firewall (no zones) should not compose this
template; ``packet_filter`` (or ``firewall`` for gateways) alone is
sufficient for them.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import Zone, ZonePolicy


@runtime_checkable
class FirewallZones(Protocol):
    """Abstract contract for zone-based firewall administration."""

    # --- Zone lifecycle ---

    def create_zone(self, zone: Zone) -> None:
        """Create a new zone.

        Raises ValueError on a duplicate ``zone.name`` or on default
        action values outside ``{"accept", "drop", "reject"}``.
        """
        ...

    def delete_zone(self, name: str) -> None:
        """Delete the zone identified by *name*.

        Raises KeyError if no zone with that name exists.
        """
        ...

    def list_zones(self) -> list[Zone]:
        """Return all zones currently configured on the device."""
        ...

    def get_zone(self, name: str) -> Zone:
        """Return the zone identified by *name*.

        Raises KeyError if no zone with that name exists.
        """
        ...

    # --- Membership ---

    def add_zone_interface(self, zone_name: str, interface: str) -> None:
        """Add *interface* to *zone_name*. No-op if already a member.

        Raises KeyError if no zone with that name exists.
        """
        ...

    def remove_zone_interface(self, zone_name: str, interface: str) -> None:
        """Remove *interface* from *zone_name*. No-op if not a member.

        Raises KeyError if no zone with that name exists.
        """
        ...

    def add_zone_network(self, zone_name: str, cidr: str) -> None:
        """Add the *cidr* network to *zone_name*. No-op if already a member.

        Raises KeyError if no zone with that name exists.
        Raises ValueError if *cidr* is malformed.
        """
        ...

    def remove_zone_network(self, zone_name: str, cidr: str) -> None:
        """Remove the *cidr* network from *zone_name*. No-op if not a member.

        Raises KeyError if no zone with that name exists.
        """
        ...

    # --- Per-zone defaults ---

    def set_zone_defaults(
        self,
        zone_name: str,
        *,
        input_action: str | None = None,
        forward_action: str | None = None,
        output_action: str | None = None,
        masquerade: bool | None = None,
        mss_clamping: bool | None = None,
    ) -> None:
        """Update one or more default-policy fields of *zone_name*.

        Only fields passed (non-None) are changed. Action values must be
        one of ``"accept"``, ``"drop"``, ``"reject"``.

        Raises KeyError if no zone with that name exists.
        Raises ValueError on a bad action value.
        """
        ...

    # --- Zone-pair forwarding ---

    def set_forwarding(self, src_zone: str, dst_zone: str, action: str) -> None:
        """Set the default forwarding action between *src_zone* and *dst_zone*.

        *action* is one of ``"accept"``, ``"drop"``, ``"reject"``.

        Raises KeyError if either zone is unknown.
        Raises ValueError on a bad action value.
        """
        ...

    def list_forwarding(self) -> list[ZonePolicy]:
        """Return every configured zone-pair forwarding policy."""
        ...
