"""TFTP / Server template.

Defines the abstract contract for TFTP server operations including
image download and lighttpd service management.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TftpServer(Protocol):
    """Abstract contract for TFTP server operations."""

    def download_image_from_uri(self, image_uri: str) -> str:
        """Download an image from *image_uri* and return the local path."""
        ...

    def restart_lighttpd(self) -> None:
        """Restart the lighttpd service on the TFTP server."""
        ...
