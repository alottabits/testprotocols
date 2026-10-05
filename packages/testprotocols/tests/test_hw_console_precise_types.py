"""HwConsole's consoles satisfy the Console protocol; the released ``Any`` returns are kept
(compatibility class), their narrowing to Console announced."""

from __future__ import annotations

import ast
import typing
from collections.abc import Mapping
from pathlib import Path

import testprotocols
import testprotocols.hw_console as hw_console_module
from _helpers import protocol_attrs
from testprotocols.hw_console import Console, HwConsole


class FakeConsole:
    """A console that satisfies ``Console`` structurally (no inheritance)."""

    def __init__(self) -> None:
        self.sent: list[str] = []
        self._before: str | None = None

    def execute_command(self, command: str, timeout: int = -1) -> str:
        self.sent.append(command)
        return f"ran {command} ({timeout})"

    def sendline(self, text: str = "") -> int:
        self.sent.append(text)
        return len(text)

    @property
    def before(self) -> str | None:
        return self._before

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

    def get_interactive_consoles(self) -> dict[str, Console]:
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
        "before",
        "start_interactive_session",
    }


def test_console_is_runtime_checkable() -> None:
    assert isinstance(FakeConsole(), Console)
    assert not isinstance(object(), Console)


def test_console_missing_a_member_does_not_conform() -> None:
    class NoBefore:
        def execute_command(self, command: str, timeout: int = -1) -> str:
            return ""

        def sendline(self, text: str = "") -> None: ...

        def start_interactive_session(self) -> None: ...

    assert not isinstance(NoBefore(), Console)


def test_fake_hw_conforms_and_consoles_conform() -> None:
    hw: HwConsole = FakeHw()  # a driver returning Console-typed consoles conforms statically
    assert isinstance(hw, HwConsole)
    assert isinstance(hw.get_console("console"), Console)
    assert all(isinstance(c, Console) for c in hw.get_interactive_consoles().values())
    assert hw.get_console("console").execute_command("ls", timeout=5) == "ran ls (5)"


def test_hw_console_keeps_its_released_annotations() -> None:
    assert typing.get_type_hints(HwConsole.get_console)["return"] is typing.Any
    assert (
        typing.get_type_hints(HwConsole.get_interactive_consoles)["return"] == dict[str, typing.Any]
    )
    flash = typing.get_type_hints(HwConsole.flash_via_bootloader)
    assert flash["tftp_devices"] == dict[str, typing.Any]
    assert flash["termination_sys"] is typing.Any


def test_console_sendline_returns_the_bytes_written() -> None:
    assert typing.get_type_hints(Console.sendline)["return"] is int


def test_console_exported_at_top_level() -> None:
    assert testprotocols.Console is Console
    assert "Console" in testprotocols.__all__


def test_released_flash_call_still_binds() -> None:
    hw = FakeHw()
    hw.flash_via_bootloader("img.bin", {"tftp": object()})
    hw.flash_via_bootloader("img.bin", {}, None, "tftp")


def test_hw_console_any_is_only_the_released_signatures() -> None:
    source = Path(hw_console_module.__file__).read_text()
    lines = source.splitlines()
    tree = ast.parse(source)
    any_lines = sorted(
        {n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "Any"}
    )
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    flash = defs["flash_via_bootloader"]
    returns = [defs["get_console"].lineno, defs["get_interactive_consoles"].lineno]
    flash_lines = [line for line in any_lines if line not in returns]
    assert set(returns) <= set(any_lines)
    assert len(flash_lines) == 2
    assert all(flash.lineno < line < flash.body[0].lineno for line in flash_lines)
    assert lines[flash.lineno - 1].endswith(
        "# type: ignore[explicit-any]  "
        "# released parameter kept: implementers declare their own types"
    )
    for line in returns:
        assert lines[line - 1].endswith(
            "# type: ignore[explicit-any]  "
            "# released return kept: implementers return their own types"
        )
