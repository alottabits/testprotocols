"""Device info template.

Defines the abstract contract for a device's inventory identity — today the
hardware model. Vendor-neutral metadata the driver resolves from its
management API, inventory config, or class knowledge; the coverage axis for
model-parameterised tests. Extensible with further identity facts (serial,
firmware version) when a consumer needs them.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DeviceInfo(Protocol):
    """Abstract contract for device inventory identity."""

    @property
    def model(self) -> str:
        """Hardware model identifier (e.g. ``"MX250"``)."""
        ...
