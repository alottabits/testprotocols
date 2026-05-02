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
        """Start an HTTP service on *port* for *ip_version*."""
        ...

    def stop_http_service(self, port: str) -> None:
        """Stop the HTTP service listening on *port*."""
        ...
