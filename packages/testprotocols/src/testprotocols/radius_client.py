"""RADIUS / RadiusClient template.

Defines the abstract contract for a device that authenticates upstream
to one or more RADIUS servers (e.g. a WiFi AP doing 802.1X, a wired
switch doing port-based authentication, a VPN concentrator).

The device maintains a registry of known servers indexed by a logical
*name*. Consumers (e.g. WifiBss) reference servers by name only — the
underlying address/port/secret resolution is the driver's responsibility.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.radius import RadiusServerConfig


@runtime_checkable
class RadiusClient(Protocol):
    """Abstract contract for a RADIUS-authenticating device."""

    def add_server(
        self,
        name: str,
        address: str,
        secret: str,
        port: int = 1812,
        acct_port: int | None = None,
    ) -> None:
        """Register a RADIUS server under *name*.

        *port* is the auth port (default 1812). *acct_port* (typically 1813)
        may be None to disable accounting on this server. Raises ValueError
        if *name* is already registered.
        """
        ...

    def update_server(
        self,
        name: str,
        *,
        address: str | None = None,
        secret: str | None = None,
        port: int | None = None,
        acct_port: int | None = None,
    ) -> None:
        """Update one or more fields of an already-registered server.

        Only fields passed (non-None) are changed. Raises KeyError if *name*
        is not registered.
        """
        ...

    def remove_server(self, name: str) -> None:
        """Unregister the RADIUS server identified by *name*. Raises KeyError if absent."""
        ...

    def list_servers(self) -> list[RadiusServerConfig]:
        """Return all registered RADIUS servers (without secrets)."""
        ...

    def get_server(self, name: str) -> RadiusServerConfig:
        """Return the registered RADIUS server identified by *name* (without secret).

        Raises KeyError if *name* is not registered.
        """
        ...

    def test_server_reachable(self, name: str, timeout: float = 5.0) -> bool:
        """Probe the registered server: return True if it responds to an Access-Request
        within *timeout* seconds.

        Drivers typically send an Access-Request with a sentinel user; the
        server's response (Access-Accept, Access-Reject, or any RADIUS reply)
        counts as reachable. No reply within timeout returns False.
        """
        ...
