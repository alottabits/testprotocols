"""Device lifecycle template.

Defines the abstract contract for controlling a managed device through its
boot lifecycle — boot detection, factory reset, reboot and finalization — and
through its software lifecycle: the firmware upgrade and the export and import
of its configuration archive. Each lever promises the device's acknowledgement;
its effect is confirmed by ``wait_for_boot`` and the reads named per member.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.device_management import ImageSource


@runtime_checkable
class DeviceLifecycle(Protocol):
    """Abstract contract for device lifecycle and boot management operations."""

    def verify_booting(self) -> None:
        """Verify that the device has entered the boot process."""
        ...

    @deprecated(
        "Deprecated: use verify_booting. Removal not before the first release 6 months "
        "after the release that deprecates it.",
        category=None,
    )
    def verify_cpe_is_booting(self) -> None:
        """Verify that the device has entered the boot process.

        Deprecated: use verify_booting. Removal not before the first release 6 months after
        the release that deprecates it.
        """
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

    def upgrade_firmware(self, image: ImageSource) -> None:
        """Upgrade the device's firmware from *image*.

        A lever: the acknowledgement is the family accepting the transfer and the apply;
        confirmed by ``wait_for_boot`` and then ``DeviceInfo.software_version``. On a family
        that uploads the image and then reboots, the two steps are named and a rejection
        raises naming the step; the driver puts nothing back.
        """
        ...

    def export_configuration(self) -> bytes:
        """Return the device's configuration archive in the family's own format, opaque to
        the contract; the paired write is ``import_configuration``."""
        ...

    def import_configuration(self, archive: bytes) -> None:
        """Restore the configuration *archive* ``export_configuration`` returned.

        A lever: confirmed by ``wait_for_boot`` where the family reboots on import, and by
        the test re-reading a setting it changed after the export (``wifi_bss.
        get_bss_config`` is the natural one).
        """
        ...
