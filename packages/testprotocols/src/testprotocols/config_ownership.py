"""Config ownership template.

Defines the abstract contract for session write-ownership of a device's
network configuration — e.g. a warm-spare member whose primary owns the
writes. The natural home for future redundancy-role facts.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigOwnership(Protocol):
    """Abstract contract for network-config write ownership."""

    @property
    def manages_network(self) -> bool:
        """Whether this session owns the device's network configuration.
        False for a warm-spare member whose primary owns the writes."""
        ...
