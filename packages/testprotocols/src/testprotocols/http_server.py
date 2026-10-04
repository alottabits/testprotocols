"""HTTP / Server template.

Defines the abstract contract for HTTP server operations including
starting and stopping an HTTP service.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.networking import IpVersion


@runtime_checkable
class HttpServer(Protocol):
    """Abstract contract for HTTP server operations."""

    def start_http_service(self, port: int | str, ip_version: IpVersion | str) -> str:
        """Start an HTTP service on *port* for *ip_version*.

        *port* is a number; the released ``str`` form (``"8080"``) is deprecated and
        the driver converts it with ``coerce_int`` and warns. *ip_version* is an
        :class:`~testprotocols.models.IpVersion` (``"ipv4"`` or ``"ipv6"``, the words
        ``testoperations`` passes); a plain ``str`` naming a member is deprecated and
        the driver converts it with ``coerce_enum`` and warns.
        """
        ...

    def stop_http_service(self, port: int | str) -> None:
        """Stop the HTTP service listening on *port*."""
        ...
