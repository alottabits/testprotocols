"""IP / Interface template.

Defines the abstract contract for querying and configuring IP interface state.
"""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Protocol, runtime_checkable

from testprotocols.models.networking import LinkAdminState


@runtime_checkable
class IpInterface(Protocol):
    """Abstract contract for IP interface operations."""

    def get_interface_ipv4addr(self, interface: str) -> str:
        """Return the IPv4 address assigned to *interface*."""
        ...

    def get_interface_ipv6addr(self, interface: str) -> str:
        """Return the global IPv6 address assigned to *interface*."""
        ...

    def get_interface_link_local_ipv6addr(self, interface: str) -> str:
        """Return the link-local IPv6 address of *interface*."""
        ...

    def get_interface_macaddr(self, interface: str) -> str:
        """Return the MAC address of *interface*."""
        ...

    def get_interface_mask(self, interface: str) -> str:
        """Return the subnet mask of *interface*."""
        ...

    def get_interface_mtu_size(self, interface: str) -> int:
        """Return the MTU size of *interface*."""
        ...

    def set_interface_mtu_size(self, interface: str, mtu: int) -> None:
        """Set the MTU of *interface* to *mtu* bytes.

        The write counterpart to :meth:`get_interface_mtu_size`. Lowering the
        MTU also lowers the MSS the host advertises on that interface, so it
        governs TCP segment size in *both* directions of a flow — unlike a
        per-socket ``TCP_MAXSEG``, which caps only the local send. Stateless
        in contract: a caller that needs to revert captures the prior via
        :meth:`get_interface_mtu_size` and restores it itself.
        """
        ...

    def is_link_up(self, interface: str, pattern: str = "BROADCAST,MULTICAST,UP") -> bool:
        """Return True if *interface* flags match *pattern*.

        Deprecated: the *pattern* parameter, a free-text grammar (the ``ip link`` flag list). A
        driver keeps matching it. A caller that wants the administrative state uses
        :meth:`is_link_admin_up`; at removal *pattern* goes and the default call is unchanged.
        Removal not before the first release 6 months after the release that deprecates it.
        """
        ...

    def is_link_admin_up(self, interface: str) -> bool:
        """Return True if *interface* is administratively up (the state :meth:`set_link_state`
        sets), whether or not a carrier is present."""
        ...

    def set_link_state(self, interface: str, state: LinkAdminState | str) -> None:
        """Bring *interface* up or down according to *state*.

        *state* is a :class:`~testprotocols.models.LinkAdminState` (``"up"`` or
        ``"down"``).

        Deprecated: the plain ``str`` form of *state*; the parameter narrows to
        :class:`~testprotocols.models.LinkAdminState`. Removal not before the first release 6
        months after the release that deprecates it.
        """
        ...

    def enable_ipv6(self) -> None:
        """Enable IPv6 on the device."""
        ...

    def disable_ipv6(self) -> None:
        """Disable IPv6 on the device."""
        ...

    def set_static_ip(self, interface: str, ip_address: IPv4Address, netmask: IPv4Address) -> None:
        """Assign a static IP address and netmask to *interface*."""
        ...

    def remove_static_ip(self, interface: str) -> None:
        """Remove any static IP address configuration from *interface*."""
        ...
