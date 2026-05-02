"""UPnP / Client template.

Defines the abstract contract for UPnP client operations including
port mapping rule creation and deletion.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class UpnpClient(Protocol):
    """Abstract contract for UPnP client operations."""

    def create_upnp_rule(
        self,
        interface: str,
        ipaddr: str,
        int_port: str,
        ext_port: str,
        protocol: str,
        extra_args: str,
        url: str,
    ) -> str:
        """Create a UPnP port-mapping rule and return the result string."""
        ...

    def delete_upnp_rule(
        self,
        interface: str,
        ext_port: str,
        protocol: str,
        url: str,
    ) -> str:
        """Delete a UPnP port-mapping rule and return the result string."""
        ...
