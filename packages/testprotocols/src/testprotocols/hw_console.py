"""Hardware console template.

Defines the abstract contract for managing physical hardware consoles,
power cycling, and bootloader-level flashing of a device under test.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HwConsole(Protocol):
    """Abstract contract for hardware console and power management operations."""

    def connect_to_consoles(self, device_name: str) -> None:
        """Connect to all hardware consoles for the named device."""
        ...

    def disconnect_from_consoles(self) -> None:
        """Disconnect from all hardware consoles."""
        ...

    def get_console(self, console_name: str) -> Any:
        """Return the console object identified by *console_name*."""
        ...

    def get_interactive_consoles(self) -> dict[str, Any]:
        """Return a mapping of console names to interactive console objects."""
        ...

    def power_cycle(self) -> None:
        """Power cycle the device (power off, then power on)."""
        ...

    def wait_for_hw_boot(self) -> None:
        """Block until the hardware has completed its boot sequence."""
        ...

    def flash_via_bootloader(
        self,
        image: str,
        tftp_devices: dict[str, Any],
        termination_sys: Any = None,
        method: str | None = None,
    ) -> None:
        """Flash the given image to the device via the bootloader."""
        ...
