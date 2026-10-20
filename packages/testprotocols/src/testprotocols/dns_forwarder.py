"""DNS forwarder — the gateway's own resolver for its LAN.

The forwarder answers the LAN's queries from its configured upstreams, its
host overrides and its rebind protection. Its configured upstreams are distinct
from the resolvers the WAN connection supplies (a lease's, or the static
addressing's), which ``wan_connection.get_wan_state`` reports.

In scope: the configured upstreams (a list replace), host overrides, rebind
protection.

Out of scope: a host's own resolver (see ``dns_client``), the connection's
resolvers (see ``wan_connection``), the LAN's addressing (see
``interface_dhcp``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import DnsHostOverride, DnsUpstream


@runtime_checkable
class DnsForwarder(Protocol):
    """Abstract contract for the gateway's DNS forwarder."""

    def set_upstreams(self, upstreams: tuple[DnsUpstream, ...]) -> None:
        """Replace the forwarder's configured upstreams; paired read ``get_upstreams``.

        The configured upstreams are distinct from the resolvers the connection supplies
        (``wan_connection.get_wan_state().dns_servers``), which the write never touches; an
        empty tuple means the connection's resolvers serve. The device may keep the upstreams
        in its own order, so the contract promises the set, not the order: compare the read
        as a set. A family that publishes no upstream write raises ``NotSupportedError``.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found upstream list where the family commits atomically,
        otherwise the steps applied before the rejection.
        """
        ...

    def get_upstreams(self) -> tuple[DnsUpstream, ...]:
        """Return the configured upstreams in the device's own order (compare as a set)."""
        ...

    def add_host_override(self, override: DnsHostOverride) -> None:
        """Add the host *override*; paired read ``list_host_overrides``.

        A name the family would rewrite (a character outside its allowed set) is rejected
        before the write with the reason, so a read-back equals the write. A family that
        publishes overrides only as a LAN host's name raises ``NotSupportedError`` for a name
        that is not one.
        """
        ...

    def remove_host_override(self, name: str) -> None:
        """Remove the override for *name*; paired read ``list_host_overrides``."""
        ...

    def list_host_overrides(self) -> list[DnsHostOverride]:
        """Return every configured host override."""
        ...

    def set_rebind_protection(self, enabled: bool) -> None:
        """Enable or disable rebind protection; paired read ``get_rebind_protection``.

        Raises ``NotSupportedError`` where the family publishes no such setting, or publishes
        it always on and *enabled* is ``False``.
        """
        ...

    def get_rebind_protection(self) -> bool:
        """Return whether rebind protection is on; raises ``NotSupportedError`` where the
        family publishes no such setting."""
        ...
