"""L2 bridge — the gateway's bridges and their membership.

Realises the membership half of the ``GAPS.md`` 2026-05-02 entry: create,
delete, list and read a bridge; add, remove and read its members, which are
ports or wireless networks. Membership of a wireless network decides which
bridge the network joins and is this capability's alone; the VLAN tag the
network's traffic carries on a VLAN-aware bridge is ``wifi_bss``'s alone
(``set_vlan``, ``create_bss(vlan_id=...)``). The STP vocabulary is the shared
one of ``models/l2_common.py``; the STP timers and the forwarding-table read of
the GAPS entry stay open there.

In scope: bridge create / delete / list / get, member add / remove / read.

Out of scope: the bridge's address and DHCP pool (see ``interface_dhcp`` on the
bridge interface), the tag a wireless network carries (see ``wifi_bss``), the
forwarding table (see ``mac_table``), STP timers and port parameters (see
``spanning_tree``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import BridgeConfig, BridgeMember, BridgeMemberState


@runtime_checkable
class L2Bridge(Protocol):
    """Abstract contract for the gateway's bridges."""

    def create_bridge(self, config: BridgeConfig) -> None:
        """Create the bridge *config* names, with no members; paired read ``get_bridge``.

        Creates the bridge only: ``add_member`` and ``remove_member`` are the only writes of
        membership. A family that publishes no bridge object raises ``NotSupportedError``.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found bridge list where the family commits atomically,
        otherwise the steps applied before the rejection.
        """
        ...

    def delete_bridge(self, name: str) -> None:
        """Delete the bridge *name*; paired read ``list_bridges``.

        Raises ``KeyError`` if no bridge named *name* exists.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found bridge list where the family commits atomically, otherwise
        the steps applied before the rejection.
        """
        ...

    def list_bridges(self) -> list[BridgeConfig]:
        """Return every bridge."""
        ...

    def get_bridge(self, name: str) -> BridgeConfig:
        """Return the bridge *name*; ``stp_mode`` is ``None`` when spanning tree is off.

        Raises ``KeyError`` if no bridge named *name* exists.
        """
        ...

    def add_member(self, bridge: str, member: BridgeMember) -> None:
        """Add *member* to *bridge*; paired read ``get_members``.

        For a ``WIRELESS_NETWORK`` member this decides which bridge the network joins; the
        tag its traffic carries stays ``wifi_bss``'s. Raises ``KeyError`` if no bridge named
        *bridge* exists.
        """
        ...

    def remove_member(self, bridge: str, member_name: str) -> None:
        """Remove the member *member_name* from *bridge*; paired read ``get_members``.

        Raises ``KeyError`` if no bridge named *bridge* exists or it has no such member.
        """
        ...

    def get_members(self, bridge: str) -> list[BridgeMemberState]:
        """Return the members of *bridge* in the device's own order (compare as a set);
        each state field is ``None`` where the family publishes no such state.

        Raises ``KeyError`` if no bridge named *bridge* exists.
        """
        ...
