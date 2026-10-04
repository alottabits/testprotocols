"""HwConsole returns a Console protocol and takes no ``Any`` (Phase 5b Task 10)."""

from __future__ import annotations

import ast
import typing
from collections.abc import Mapping, Sequence
from pathlib import Path

import testprotocols
import testprotocols.hw_console as hw_console_module
from _helpers import protocol_attrs
from testprotocols.hw_console import Console, ExpectPattern, HwConsole


class FakeConsole:
    """A console that satisfies ``Console`` structurally (no inheritance)."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def execute_command(self, command: str, timeout: int = -1) -> str:
        self.sent.append(command)
        return f"ran {command} ({timeout})"

    def sendline(self, text: str = "") -> None:
        self.sent.append(text)

    def expect(self, pattern: ExpectPattern | Sequence[ExpectPattern], timeout: int = -1) -> int:
        return 0

    def expect_exact(
        self, pattern: ExpectPattern | Sequence[ExpectPattern], timeout: int = -1
    ) -> int:
        return 0

    def start_interactive_session(self) -> None:
        return None


class FakeHw:
    """A conforming ``HwConsole`` whose consoles are ``FakeConsole``."""

    def __init__(self) -> None:
        self._console = FakeConsole()

    def connect_to_consoles(self, device_name: str) -> None: ...

    def disconnect_from_consoles(self) -> None: ...

    def get_console(self, console_name: str) -> Console:
        if console_name != "console":
            raise ValueError(console_name)
        return self._console

    def get_interactive_consoles(self) -> Mapping[str, Console]:
        return {"console": self._console}

    def power_cycle(self) -> None: ...

    def wait_for_hw_boot(self) -> None: ...

    def flash_via_bootloader(
        self,
        image: str,
        tftp_devices: Mapping[str, object],
        termination_sys: object = None,
        method: str | None = None,
    ) -> None: ...


def test_console_members_are_exactly_those_callers_use() -> None:
    assert protocol_attrs(Console) == {
        "execute_command",
        "sendline",
        "expect",
        "expect_exact",
        "start_interactive_session",
    }


def test_console_is_runtime_checkable() -> None:
    assert isinstance(FakeConsole(), Console)
    assert not isinstance(object(), Console)


def test_console_missing_a_member_does_not_conform() -> None:
    class NoExpect:
        def execute_command(self, command: str, timeout: int = -1) -> str:
            return ""

        def sendline(self, text: str = "") -> None: ...

    assert not isinstance(NoExpect(), Console)


def test_fake_hw_conforms_and_consoles_conform() -> None:
    hw = FakeHw()
    assert isinstance(hw, HwConsole)
    assert isinstance(hw.get_console("console"), Console)
    assert all(isinstance(c, Console) for c in hw.get_interactive_consoles().values())
    assert hw.get_console("console").execute_command("ls", timeout=5) == "ran ls (5)"


def test_hw_console_annotations_are_precise() -> None:
    hints = typing.get_type_hints(HwConsole.get_console)
    assert hints["return"] is Console
    assert (
        typing.get_type_hints(HwConsole.get_interactive_consoles)["return"] == Mapping[str, Console]
    )
    flash = typing.get_type_hints(HwConsole.flash_via_bootloader)
    assert flash["tftp_devices"] == dict[str, typing.Any]
    assert flash["termination_sys"] is typing.Any


def test_console_exported_at_top_level() -> None:
    assert testprotocols.Console is Console
    assert "Console" in testprotocols.__all__


def test_released_flash_call_still_binds() -> None:
    hw = FakeHw()
    hw.flash_via_bootloader("img.bin", {"tftp": object()})
    hw.flash_via_bootloader("img.bin", {}, None, "tftp")


def test_hw_console_any_is_only_the_two_flash_parameters() -> None:
    source = Path(hw_console_module.__file__).read_text()
    tree = ast.parse(source)
    lines = {n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "Any"}
    assert len(lines) == 2
    assert all("passed opaquely" in source.splitlines()[i - 3] for i in lines)
