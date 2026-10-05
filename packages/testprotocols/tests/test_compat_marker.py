"""``testprotocols`` has no runtime dependency: the ``deprecated`` marker needs none.

Type checkers resolve ``typing_extensions.deprecated`` from their bundled stubs; at run time
Python 3.13 and later supply ``warnings.deprecated`` and Python 3.12 an identity stand-in.
"""

from __future__ import annotations

import pkgutil
import subprocess
import sys
import tomllib
import warnings
from pathlib import Path

import testprotocols
from testprotocols import _compat

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_the_package_declares_no_dependency() -> None:
    project = tomllib.loads(_PYPROJECT.read_text())["project"]
    assert project["dependencies"] == []


def test_every_module_imports_without_typing_extensions() -> None:
    """``typing_extensions`` is made unimportable before any module is imported."""
    modules = sorted(
        info.name for info in pkgutil.walk_packages(testprotocols.__path__, prefix="testprotocols.")
    )
    code = (
        "import importlib, sys\n"
        "sys.modules['typing_extensions'] = None\n"
        "for m in sys.argv[1:]:\n"
        "    importlib.import_module(m)\n"
    )
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", code, "testprotocols", *modules],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_the_marker_is_the_standard_one_or_an_identity() -> None:
    if sys.version_info >= (3, 13):
        assert _compat.deprecated is warnings.deprecated
        return

    class Marked:
        pass

    def member() -> int:
        return 1

    marker = _compat.deprecated("Deprecated: use other.", category=None)
    assert marker(Marked) is Marked
    assert marker(member) is member
    assert not hasattr(Marked, "__deprecated__")
    assert member() == 1
