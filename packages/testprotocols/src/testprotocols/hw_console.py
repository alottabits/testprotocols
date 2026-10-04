"""Hardware console template.

Defines the abstract contract for managing physical hardware consoles,
power cycling, and bootloader-level flashing of a device under test.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

ExpectPattern = str | type[Exception]
"""One thing ``expect`` waits for: a regular expression, or a sentinel class such as a
timeout or end-of-file exception class that a pexpect-style console accepts in a list."""


@runtime_checkable
class Console(Protocol):
    """An interactive text console: run a command, or send a line and wait for a pattern.

    Exactly the members that callers of the consoles ``HwConsole`` returns were seen to
    use (see ``docs/architecture/precise-types-design.md``, "HwConsole"). A pexpect-style
    console satisfies it without inheriting from it.
    """

    def execute_command(self, command: str, /, timeout: int = -1) -> str:
        """Run *command* in the console's shell and return its output.

        ``timeout`` is in seconds; ``-1`` means the console's own default.
        """
        ...

    def sendline(self, text: str = "", /) -> None:
        """Send *text* followed by a line end."""
        ...

    def expect(
        self,
        pattern: ExpectPattern | Sequence[ExpectPattern],
        /,
        timeout: int = -1,
    ) -> int:
        """Wait for a regular expression (or any of a list) and return the matched index."""
        ...

    def expect_exact(
        self,
        pattern: ExpectPattern | Sequence[ExpectPattern],
        /,
        timeout: int = -1,
    ) -> int:
        """Wait for literal text (or any of a list) and return the matched index."""
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

    def flash_via_bootloader(
        self,
        image: str,
        # framework objects passed opaquely; implementers declare framework types
        # (released signature kept)
        tftp_devices: dict[str, Any],
        # framework objects passed opaquely; implementers declare framework types
        # (released signature kept)
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
