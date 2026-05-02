"""HTTP / Client template.

Defines the abstract contract for HTTP client operations including curl
and GET requests.
"""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Protocol, runtime_checkable

from testprotocols.models.networking import HTTPResult


@runtime_checkable
class HttpClient(Protocol):
    """Abstract contract for HTTP client operations."""

    def curl(
        self,
        url: str | IPv4Address,
        protocol: str,
        port: str | int | None = None,
        options: str = "",
    ) -> bool:
        """Execute a curl request to *url* using *protocol*."""
        ...

    def http_get(
        self,
        url: str,
        timeout: int = 20,
        options: str = "",
    ) -> HTTPResult:
        """Perform an HTTP GET request to *url* and return the result."""
        ...
