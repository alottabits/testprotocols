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

    def wait_for_boot(self, timeout_s: int | None = None) -> None:
        """Block until the device has completed booting.

        Implementations verify completion via a signal that
        unambiguously postdates the most recent ``reset()`` — for
        example, comparing an ACS-side ``last_boot_time`` against a
        timestamp captured before the reset was issued. Raises
        ``TimeoutError`` if completion is not observed within
        *timeout_s*; when *timeout_s* is ``None`` the implementation
        applies its own default deadline.
        """
        ...

    def factory_reset(self, method: str | None = None) -> bool:
        """Perform a factory reset using the given method. Return True on success."""
        ...

    def reset(self, method: str | None = None) -> None:
        """Perform a reset (soft or hard) using the given method.

        The implementation is expected to capture an internal baseline
        (e.g. a wall-clock timestamp) so the matching ``wait_for_boot()``
        call can confirm the device's post-reset boot is fresh, not a
        stale signal from before the reset was issued.
        """
        ...

    def finalize_boot(self) -> bool:
        """Finalize the boot sequence and return True if the device is ready."""
        ...
