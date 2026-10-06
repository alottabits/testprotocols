"""HTTP / Server template.

Defines the abstract contract for HTTP server operations including
starting and stopping an HTTP service.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class HttpServer(Protocol):
    """Abstract contract for HTTP server operations."""

    def start_http_service(self, port: str, ip_version: str) -> str:
        """Start an HTTP service on *port* for *ip_version*.

        *port* is the port number as text (``"8080"``). *ip_version* is ``"4"`` or
        ``"6"``: the released implementers pass it to the server command as ``-<ip_version>``.
        Both stay ``str``, because the released implementers declare ``str``.

        Deprecated: *port* as ``str`` and *ip_version* as ``str`` narrow to ``int`` and to
        :class:`~testprotocols.models.IpFamily` (``V4`` / ``V6``, whose values are those
        numbers). Removal not before the first release 6 months after the release that
        deprecates it.
        """
        ...

    def stop_http_service(self, port: str) -> None:
        """Stop the HTTP service listening on *port*."""
        ...
