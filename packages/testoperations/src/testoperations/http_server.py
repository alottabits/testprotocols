"""HTTP server operations — context manager wrapping start/stop lifecycle.

Receives a resolved ``http_server`` template instance from the caller.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from testprotocols.http_server import HttpServer


@contextmanager
def start_http_server(
    http_server: HttpServer,
    port: str,
    ip_version: str = "ipv4",
) -> Generator[str, None, None]:
    """Context manager that starts an HTTP service and stops it on exit.

    Yields the handle returned by *start_http_service* (typically a PID string).
    """
    handle = http_server.start_http_service(port, ip_version)
    try:
        yield handle
    finally:
        http_server.stop_http_service(port)
