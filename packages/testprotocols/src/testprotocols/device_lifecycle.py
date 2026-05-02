"""Device lifecycle template.

Defines the abstract contract for controlling a CPE device through its
boot lifecycle, including boot detection, factory reset, and finalization.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DeviceLifecycle(Protocol):
    """Abstract contract for device lifecycle and boot management operations."""

    def verify_cpe_is_booting(self) -> None:
        """Verify that the CPE device has entered the boot process."""
        ...

    def wait_for_boot(self) -> None:
        """Block until the device has completed booting."""
        ...

    def factory_reset(self, method: str | None = None) -> bool:
        """Perform a factory reset using the given method. Return True on success."""
        ...

    def reset(self, method: str | None = None) -> None:
        """Perform a reset (soft or hard) using the given method."""
        ...

    def finalize_boot(self) -> bool:
        """Finalize the boot sequence and return True if the device is ready."""
        ...
