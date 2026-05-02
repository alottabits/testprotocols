"""TR-069 ACS GUI template.

Defines the abstract contract for interacting with the TR-069 ACS web
graphical user interface, covering device search, status, and management
operations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Tr069Gui(Protocol):
    """Abstract contract for TR-069 ACS GUI interactions."""

    def login(self, username: str | None = None, password: str | None = None) -> bool:
        """Log in to the ACS GUI. Return True on success."""
        ...

    def logout(self) -> bool:
        """Log out of the ACS GUI. Return True on success."""
        ...

    def is_logged_in(self) -> bool:
        """Return True if currently logged in to the ACS GUI."""
        ...

    def search_device(self, cpe_id: str) -> bool:
        """Search for a device by CPE ID. Return True if found."""
        ...

    def get_device_count(self) -> int:
        """Return the total number of devices visible in the ACS GUI."""
        ...

    def filter_devices(self, filter_criteria: dict[str, str]) -> int:
        """Apply filter criteria and return the number of matching devices."""
        ...

    def get_device_status(self, cpe_id: str) -> dict[str, str]:
        """Return the status information dict for the given CPE ID."""
        ...

    def verify_device_online(self, cpe_id: str, timeout: int = 60) -> bool:
        """Wait up to *timeout* seconds and return True when the device is online."""
        ...

    def get_last_inform_time(self, cpe_id: str) -> str:
        """Return the timestamp of the last TR-069 Inform from the device."""
        ...

    def reboot_device_via_gui(self, cpe_id: str) -> bool:
        """Trigger a reboot of the device via the ACS GUI. Return True on success."""
        ...

    def factory_reset_via_gui(self, cpe_id: str) -> bool:
        """Trigger a factory reset of the device via the ACS GUI. Return True on success."""
        ...

    def delete_device_via_gui(self, cpe_id: str, confirm: bool = True) -> bool:
        """Delete the device record from the ACS GUI. Return True on success."""
        ...

    def get_device_parameter_via_gui(self, cpe_id: str, parameter: str) -> str | None:
        """Return the value of the named parameter for the device, or None if not found."""
        ...

    def set_device_parameter_via_gui(self, cpe_id: str, parameter: str, value: str) -> bool:
        """Set the named parameter to *value* via the ACS GUI. Return True on success."""
        ...

    def trigger_firmware_upgrade_via_gui(self, cpe_id: str, firmware_url: str) -> bool:
        """Initiate a firmware upgrade for the device via the ACS GUI. Return True on success."""
        ...

    def verify_firmware_version_via_gui(self, cpe_id: str, expected_version: str) -> bool:
        """Return True if the device reports the expected firmware version in the ACS GUI."""
        ...
