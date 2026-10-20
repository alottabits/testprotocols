"""Device info template.

Defines the abstract contract for a device's inventory identity: the hardware
model, the manufacturer, the serial number, the software version and, where the
family publishes them, the organisationally unique identifier and the hardware
version. Vendor-neutral metadata the driver resolves from its management API,
inventory config, or class knowledge; the coverage axis for model-parameterised
tests. Worded for any closed network product.
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

    @property
    def manufacturer(self) -> str:
        """The manufacturer's name as the device publishes it; raises ``NotSupportedError``
        where the family publishes no manufacturer field."""
        ...

    @property
    def serial_number(self) -> str:
        """The device's serial number; raises ``NotSupportedError`` where the family
        publishes no serial-number field."""
        ...

    @property
    def software_version(self) -> str:
        """The running software (firmware) version as the device publishes it; the
        confirming observation of ``DeviceLifecycle.upgrade_firmware``."""
        ...

    @property
    def oui(self) -> str | None:
        """The manufacturer's organisationally unique identifier, ``None`` where the family
        publishes no such field."""
        ...

    @property
    def hardware_version(self) -> str | None:
        """The hardware revision, ``None`` where the family publishes no such field."""
        ...
