"""Hardware console template.

Defines the abstract contract for managing physical hardware consoles,
power cycling, and bootloader-level flashing of a device under test.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Console(Protocol):
    """An interactive text console: run a command, or send a line and read what came before.

    Only the members that callers of the consoles ``HwConsole`` returns were seen to use
    and that a ``pexpect.spawn`` subclass can satisfy without this package depending on
    pexpect (see ``docs/architecture/precise-types-design.md``, "HwConsole"). A pexpect-based
    console satisfies it without inheriting from it. Pattern matching (``expect``,
    ``expect_exact``) is not here: a console's own pattern types cannot be matched by one
    contract type, so a caller that matches patterns keeps the concrete console type.
    """

    def execute_command(self, command: str, /, timeout: int = -1) -> str:
        """Run *command* in the console's shell and return its output.

        ``timeout`` is in seconds; ``-1`` means the console's own default.
        """
        ...

    def sendline(self, text: str = "", /) -> object:
        """Send *text* followed by a line end; the return value is not part of the contract."""
        ...

    @property
    def before(self) -> str | bytes | None:
        """The output received before the last match (``None`` before any match)."""
        ...

    def start_interactive_session(self) -> None:
        """Hand the terminal to the console until the user leaves it."""
        ...


@runtime_checkable
class HwConsole(Protocol):
    """Abstract contract for hardware console and power management operations."""

    def connect_to_consoles(self, device_name: str) -> None:
        """Connect to all hardware consoles for the named device."""
        ...

    def disconnect_from_consoles(self) -> None:
        """Disconnect from all hardware consoles."""
        ...

    def get_console(self, console_name: str) -> Console:
        """Return the console object identified by *console_name*."""
        ...

    def get_interactive_consoles(self) -> Mapping[str, Console]:
        """Return a mapping of console names to interactive console objects."""
        ...

    def power_cycle(self) -> None:
        """Power cycle the device (power off, then power on)."""
        ...

    def wait_for_hw_boot(self) -> None:
        """Block until the hardware has completed its boot sequence."""
        ...

    def flash_via_bootloader(  # type: ignore[explicit-any]  # released parameter kept: implementers declare their own types
        self,
        image: str,
        tftp_devices: dict[str, Any],
        termination_sys: Any = None,
        method: str | None = None,
    ) -> None:
        """Flash the given image to the device via the bootloader.

        ``tftp_devices`` (LAN-side TFTP servers by name) and ``termination_sys`` (the
        line-termination system, for example a CMTS) are framework device objects the
        driver is handed; no implementer was seen to call a member on either, and implementers
        declare the framework's own types (for example ``dict[str, <TFTP type>]``, which an
        invariant ``dict`` parameter cannot accept any other way), so the released ``Any``
        annotations are kept.
        """
        ...
