"""A ``pexpect.spawn`` subclass satisfies ``Console`` (checked by mypy and pyright).

``types-pexpect`` is a dev dependency only: ``testprotocols`` itself never imports pexpect.
The check is static (the gate's mypy and pyright runs); pexpect is not installed at run time,
so nothing here executes it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pexpect
    from testprotocols.hw_console import Console

    class _PexpectConsole(pexpect.spawn):  # type: ignore[type-arg]
        """What a boardfarm- or vitro-style console is: spawn plus two methods."""

        def execute_command(self, command: str, timeout: int = -1) -> str: ...

        def start_interactive_session(self) -> None: ...


def test_conformance_is_checked_statically() -> None:
    """The assignment below is the assertion; it only runs under the type checkers."""
    if TYPE_CHECKING:
        console: Console = _PexpectConsole("true")
        assert console is not None
