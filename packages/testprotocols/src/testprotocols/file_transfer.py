"""File Transfer template.

Defines the abstract contract for file transfer operations including
deletion and secure copy.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FileTransfer(Protocol):
    """Abstract contract for file transfer operations."""

    def delete_file(self, filename: str) -> None:
        """Delete *filename* from the device."""
        ...

    def scp_device_file_to_local(self, local_path: str, source_path: str) -> None:
        """Copy *source_path* from the device to *local_path* via SCP."""
        ...
