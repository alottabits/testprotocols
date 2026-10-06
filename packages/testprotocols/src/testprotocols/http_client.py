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
        URL as ``<protocol>://<url>``.

        *no_proxy* bypasses any proxy, *insecure* skips certificate verification and
        *follow_redirects* follows redirects; they replace the released *options* string.
        Giving *options* together with a typed parameter raises ``ValueError``.

        Deprecated: the plain ``str`` form of *protocol*; the parameter narrows to
        :class:`~testprotocols.models.HttpScheme`. Removal not before the first release 6
        months after the release that deprecates it.

        Deprecated: the *options* string; use *no_proxy*, *insecure* and *follow_redirects*.
        Removal not before the first release 6 months after the release that deprecates it.
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
        the released *options* string.

        The result's *status*, *body* and *raw* are the typed attributes.

        Deprecated: the *options* string, as for :meth:`curl`; and the result's released *code*
        (text) and *beautified_text*, as for :class:`~testprotocols.models.HTTPResult`. Removal
        not before the first release 6 months after the release that deprecates it.
        """
        ...
