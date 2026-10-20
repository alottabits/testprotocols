"""Device management operations — reboot polling loop.

Receives a resolved health instance (any ``DeviceHealth``) from the caller.
The thin wrapper ``get_seconds_uptime`` is deleted — step definitions call
the template method directly.
"""

from __future__ import annotations

import time

from testprotocols.device_health import DeviceHealth


def wait_for_reboot_completion(
    device_mgmt: DeviceHealth,
    timeout: int = 60,
) -> None:
    """Block until the device has completed a reboot cycle.

    Accepts any ``DeviceHealth``: a host's ``DeviceManagement`` and a closed
    product's ``health`` alike. Polls ``device_mgmt.is_online()`` until it
    transitions from True -> False -> True (or starts from False). Raises
    ``TimeoutError`` if *timeout* seconds elapse before the device comes back
    online.
    """
    deadline = time.monotonic() + timeout

    # Wait for device to go offline first
    while time.monotonic() < deadline:
        if not device_mgmt.is_online():
            break
        time.sleep(0.5)

    # Wait for device to come back online
    while time.monotonic() < deadline:
        if device_mgmt.is_online():
            return
        time.sleep(0.5)

    raise TimeoutError(f"Device did not complete reboot within {timeout} seconds")
