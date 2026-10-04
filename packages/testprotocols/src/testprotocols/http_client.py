"""HTTP / Client template.

Defines the abstract contract for HTTP client operations including curl
and GET requests.
"""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Protocol, runtime_checkable

from testprotocols.models.networking import HTTPResult, HttpScheme


@runtime_checkable
class HttpClient(Protocol):
    """Abstract contract for HTTP client operations."""

    def curl(
        self,
        url: str | IPv4Address,
        protocol: HttpScheme | str,
        port: str | int | None = None,
        options: str = "",
        *,
        no_proxy: bool = False,
        insecure: bool = False,
        follow_redirects: bool = False,
    ) -> bool:
        """Execute a curl request to *url* using *protocol*.

        *protocol* is the URL scheme, an :class:`~testprotocols.models.HttpScheme`
        (``"http"`` or ``"https"``): the released implementers fold it into the target
        URL as ``<protocol>://<url>``. A plain ``str`` naming a member is deprecated: the
        driver converts it and warns.

        *no_proxy* bypasses any proxy, *insecure* skips certificate verification and
        *follow_redirects* follows redirects; they replace the released *options* string,
        which is deprecated (a driver warns when it is non-empty and raises ``ValueError``
        when it is given together with a typed parameter).
        """
        ...

    def http_get(
        self,
        url: str,
        timeout: int = 20,
        options: str = "",
        *,
        no_proxy: bool = False,
        insecure: bool = False,
        follow_redirects: bool = False,
    ) -> HTTPResult:
        """Perform an HTTP GET request to *url* and return the result.

        *no_proxy*, *insecure* and *follow_redirects* are as for :meth:`curl`; they replace
        the released *options* string, which is deprecated in the same way.

        The result's *status*, *body* and *raw* are the typed attributes; its released
        *code* (text) and *beautified_text* are deprecated.
        """
        ...
