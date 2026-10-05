"""DHCP / Server template.

Defines the abstract contract for DHCP server operations such as CPE
provisioning.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DhcpServer(Protocol):
    """Abstract contract for DHCP server operations."""

    def provision_cpe(  # object: open value: the contract does not enumerate it
        self,
        cpe_mac: str,
        dhcpv4_options: dict[str, dict[str, object]],
        dhcpv6_options: dict[str, dict[str, object]],
    ) -> None:
        """Provision a CPE device by MAC address with the given DHCP options.

        Each options argument maps a service-pool name (``"data"``, ``"voice"``, ...) to the
        option values the server hands out in that pool, keyed by option name
        (``"dns-server"``, ``"ntp-server"``, ``"valid-lifetime"``, vendor-specific
        information, ...); ``{}`` asks for the server's defaults, and a partial map is
        completed with them.
        """
        ...
