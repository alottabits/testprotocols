"""WAN connection — the gateway's upstream connection as one object with a mode.

A CPE gateway's uplink is one connection whose address comes from a lease, a
static assignment or a PPPoE session; IPoE on a tagged uplink is ``DHCP`` or
``STATIC`` with the VLAN part set. The configuration is one record with a mode
and mode-specific parts, the state a separate read record, and the only lever is
the PPPoE session reset.

In scope: the connection's configuration (mode, credentials, static addressing,
tag, IPv6 part), its observed state, the PPPoE session reset.

Out of scope: the administrative state of the uplink (see ``wan_link_admin``,
whose label is the connection's name), the lease levers (see ``dhcp_client``),
the link beneath the connection (see ``port_status``), the forwarder's own
upstreams (see ``dns_forwarder``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import WanConnectionConfig, WanConnectionState


@runtime_checkable
class WanConnection(Protocol):
    """Abstract contract for the gateway's WAN connection."""

    def set_wan_connection(self, config: WanConnectionConfig) -> None:
        """Write the connection *config* under its ``name``; paired read ``get_wan_connection``.

        A part that does not apply to ``config.mode`` is ``None``, and a configuration whose
        parts contradict its mode is rejected before any write. ``PppoeCredentials.password``
        is required on a write and ``None`` on every read: the written value is confirmed by
        ``get_wan_state`` showing ``WanStatus.CONNECTED`` after ``AUTHENTICATING``. A family
        that publishes no selector for a part of the record (the mode, the service name, the
        tag, the tag's priority) raises ``NotSupportedError`` for a configuration that sets it,
        before any write.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found connection where the family commits atomically, otherwise
        the steps applied before the rejection.
        """
        ...

    def get_wan_connection(self, name: str) -> WanConnectionConfig:
        """Return the configuration of the connection *name*, every secret ``None``.

        Raises ``KeyError`` if no connection named *name* exists.
        """
        ...

    def list_wan_connections(self) -> list[WanConnectionConfig]:
        """Return every configured connection, every secret ``None``."""
        ...

    def get_wan_state(self, name: str) -> WanConnectionState:
        """Return the observed state of the connection *name*.

        ``dns_servers`` are the resolvers the connection supplies, not the forwarder's
        configured upstreams (``dns_forwarder.get_upstreams``). Raises ``KeyError`` if no
        connection named *name* exists.
        """
        ...

    def reset_session(self, name: str) -> None:
        """Terminate and redial the PPPoE session of the connection *name*.

        A lever on a ``PPPOE`` connection, confirmed by ``get_wan_state`` showing the status
        leave ``CONNECTED`` and return. On a ``DHCP`` or ``STATIC`` connection raises
        ``NotSupportedError``: use ``dhcp_client`` (release and renew) for the lease and
        ``wan_admin`` (down and up, with the connection's name as the label) for the
        administrative state; their paired read on a gateway is ``get_wan_state``.
        Raises ``KeyError`` if no connection named *name* exists.
        """
        ...
