"""UPnP / Client template.

Defines the abstract contract for UPnP client operations including
port mapping rule creation and deletion.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import PortMappingProtocol


@runtime_checkable
class UpnpClient(Protocol):
    """Abstract contract for UPnP client operations."""

    def create_upnp_rule(
        self,
        interface: str,
        ipaddr: str,
        int_port: str,
        ext_port: str,
        protocol: PortMappingProtocol | str,
        extra_args: str,
        url: str,
    ) -> str:
        """Create a UPnP port-mapping rule and return the result string.

        *int_port* and *ext_port* are port numbers as text; they stay ``str`` because the
        released implementers declare ``str``.
        *protocol* is a :class:`~testprotocols.models.PortMappingProtocol`, ``TCP`` or ``UDP``
        here (``TCP_UDP`` is not a UPnP protocol and a driver raises ``ValueError`` for it).

        Deprecated: *int_port* and *ext_port* as ``str``; they narrow to ``int``. Removal not before
        the first release 6 months after the release that deprecates it.

        Deprecated: the plain ``str`` form of *protocol*; the parameter narrows to
        :class:`~testprotocols.models.PortMappingProtocol`. Removal not before the first release 6
        months after the release that deprecates it.
        """
        ...

    def delete_upnp_rule(
        self,
        interface: str,
        ext_port: str,
        protocol: PortMappingProtocol | str,
        url: str,
    ) -> str:
        """Delete a UPnP port-mapping rule and return the result string.

        *ext_port* and *protocol* follow :meth:`create_upnp_rule`.

        Deprecated: *ext_port* as ``str`` and the plain ``str`` form of *protocol*, as for
        :meth:`create_upnp_rule`. Removal not before the first release 6 months after the release
        that deprecates it.
        """
        ...
