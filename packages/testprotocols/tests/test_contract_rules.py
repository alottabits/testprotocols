"""The contract rules of ``docs/architecture/precise-types-design.md``, checked by AST.

- C1 and C5: ``testprotocols`` carries no runtime transition code and its records hold no
  code: no ``__post_init__``, no ``__setattr__``, no ``warnings.warn`` and no
  ``DeprecationWarning`` anywhere in ``packages/testprotocols/src``. The one exception is
  ``testprotocols._compat``, whose Python 3.12 stand-in for ``warnings.deprecated`` keeps
  the standard signature (``category=DeprecationWarning``) and never warns.
- C2: every ``@deprecated(...)`` in ``packages/*/src`` passes ``category=None``, so the
  marker is seen by the type checkers and nothing warns at run time.
- C4: a protocol member added since the last release (``git describe --tags`` from
  ``HEAD``; releases are tagged ``vX.Y.Z``) has no released form, so a parameter typed
  with an enum takes the bare enum, never ``E | str`` (or ``E | int``). The comparison is
  ``scripts/contract_surface.py``'s; the recorded exceptions are its ``OPEN_VOCABULARY``.
  The test needs git and the release tag (CI checks out the full history); without them
  it is skipped, and the ``lint`` workflow's contract step applies the same rule to the
  PR's own diff.
"""

from __future__ import annotations

import ast
import io
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest
from contract_surface import enum_param_problems, read_surface

_ROOT = Path(__file__).resolve().parents[3]
_PROTOCOLS = _ROOT / "packages" / "testprotocols" / "src" / "testprotocols"
_COMPAT = _PROTOCOLS / "_compat.py"
# The release before the precise-types change, for a checkout with no release tag.
_FALLBACK_BASE = "7664964"
_FORBIDDEN_METHODS = frozenset({"__post_init__", "__setattr__"})


def _sources(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def _transition_code(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(_ROOT).as_posix()
    found: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name in _FORBIDDEN_METHODS
        ):
            found.append(f"{rel}:{node.lineno}: def {node.name}")
        elif isinstance(node, ast.Name) and node.id == "DeprecationWarning":
            found.append(f"{rel}:{node.lineno}: DeprecationWarning")
        elif isinstance(node, ast.Attribute) and node.attr == "DeprecationWarning":
            found.append(f"{rel}:{node.lineno}: DeprecationWarning")
        elif isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == "warn") or (
                isinstance(func, ast.Name) and func.id == "warn"
            ):
                found.append(f"{rel}:{node.lineno}: warn(...)")
        elif isinstance(node, ast.ImportFrom) and node.module == "warnings":
            found += [
                f"{rel}:{node.lineno}: from warnings import {a.name}"
                for a in node.names
                if a.name == "warn"
            ]
    return found


def test_testprotocols_carries_no_transition_code() -> None:
    found = [
        hit for path in _sources(_PROTOCOLS) if path != _COMPAT for hit in _transition_code(path)
    ]
    assert found == [], "runtime transition code in testprotocols (C1, C5):\n" + "\n".join(found)


def test_the_compat_exception_is_the_marker_stand_in_only() -> None:
    """``_compat`` names ``DeprecationWarning`` only as the stand-in's default, and never warns."""
    hits = _transition_code(_COMPAT)
    assert hits and all(h.endswith(": DeprecationWarning") for h in hits), hits


def _deprecated_calls(path: Path) -> list[ast.Call]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            for dec in node.decorator_list:
                target = dec.func if isinstance(dec, ast.Call) else dec
                name = (
                    target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
                )
                if name == "deprecated":
                    calls.append(dec if isinstance(dec, ast.Call) else ast.Call(target, [], []))
    return calls


def test_every_deprecated_marker_passes_category_none() -> None:
    bad: list[str] = []
    count = 0
    for path in _sources(_ROOT / "packages"):
        if "/src/" not in path.as_posix():
            continue
        for call in _deprecated_calls(path):
            count += 1
            category = next((k.value for k in call.keywords if k.arg == "category"), None)
            if not (isinstance(category, ast.Constant) and category.value is None):
                bad.append(f"{path.relative_to(_ROOT).as_posix()}:{call.lineno}")
    assert count > 0, "no @deprecated marker found: the scan is broken"
    assert bad == [], "@deprecated without category=None (C2): " + ", ".join(bad)


def _release_base(tmp_path: Path) -> Path:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not available")

    def run(*args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([git, *args], cwd=_ROOT, capture_output=True, check=False)

    described = run("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", "HEAD")
    ref = described.stdout.decode().strip() if described.returncode == 0 else _FALLBACK_BASE
    archive = run("archive", "--format=tar", ref, "packages")
    if archive.returncode != 0:
        pytest.skip(f"no release to compare with: {ref} is not in this checkout")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(tmp_path, filter="data")
    return tmp_path


def test_new_protocol_members_take_the_bare_enum(tmp_path: Path) -> None:
    base = read_surface(_release_base(tmp_path))
    head = read_surface(_ROOT)
    problems = enum_param_problems(base, head)
    assert problems == [], "\n".join(problems)
