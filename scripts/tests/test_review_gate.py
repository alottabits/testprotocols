"""Tests for scripts/review_gate.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from review_gate import full_requested, main, maintainers, refusal

MAINTAINERS_MD = """# Maintainers

One line per maintainer, in this exact form:

```markdown
- @handle — <scope>
```

## Maintainers

- @octocat — everything (`*`)
- @second-maintainer — `packages/testoperations/`

Adding a maintainer is a line here.
"""

GREEN = {"dco": "success", "lint": "success", "hygiene": "success"}


def ok(**overrides: object) -> str | None:
    args: dict[str, object] = {
        "body": "/review",
        "commenter": "octocat",
        "permission": "admin",
        "maintainers_text": MAINTAINERS_MD,
        "is_draft": False,
        "checks": GREEN,
    }
    args.update(overrides)
    return refusal(**args)  # type: ignore[arg-type]


def test_maintainers_reads_only_the_list_section() -> None:
    assert maintainers(MAINTAINERS_MD) == frozenset({"octocat", "second-maintainer"})
    assert "handle" not in maintainers(MAINTAINERS_MD)
    assert maintainers("# nothing\n") == frozenset()


def test_gate_passes_for_a_listed_maintainer_with_write_access() -> None:
    assert ok() is None
    assert ok(permission="write") is None
    assert ok(permission="maintain") is None
    assert ok(body="/review\n") is None
    assert ok(body="/review full") is None
    assert ok(body="/review full\n") is None


def test_full_requested() -> None:
    assert full_requested("/review full") is True
    assert full_requested("/review full\n") is True
    assert full_requested("/review") is False
    assert full_requested("/review please") is False


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"body": "/review please"}, "the comment must be exactly `/review` or `/review full`"),
        ({"body": "/review  full"}, "the comment must be exactly `/review` or `/review full`"),
        ({"body": "/review Full"}, "the comment must be exactly `/review` or `/review full`"),
        ({"body": "/review full now"}, "the comment must be exactly `/review` or `/review full`"),
        (
            {"commenter": "stranger", "permission": "write"},
            "@stranger is not listed in MAINTAINERS.md",
        ),
        ({"permission": "read"}, "@octocat does not have write access"),
        ({"permission": "none"}, "@octocat does not have write access"),
        ({"is_draft": True}, "the PR is a draft"),
        ({"checks": {**GREEN, "hygiene": "failure"}}, "hygiene is failure on the head commit"),
        (
            {"checks": {"dco": "success", "lint": "success"}},
            "hygiene is missing on the head commit",
        ),
        ({"checks": {**GREEN, "lint": "pending"}}, "lint is pending on the head commit"),
    ],
)
def test_gate_refusals(overrides: dict[str, object], reason: str) -> None:
    assert ok(**overrides) == reason


def test_case_insensitive_handles() -> None:
    assert ok(commenter="OctoCat") is None


def test_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = tmp_path / "body.txt"
    body.write_text("/review\n")
    md = tmp_path / "MAINTAINERS.md"
    md.write_text(MAINTAINERS_MD)
    pr = tmp_path / "pr.json"
    pr.write_text(json.dumps({"draft": False}))
    checks = tmp_path / "checks.json"
    checks.write_text(json.dumps(GREEN))
    argv = [
        "--body",
        str(body),
        "--commenter",
        "octocat",
        "--permission",
        "admin",
        "--maintainers",
        str(md),
        "--pr",
        str(pr),
        "--checks",
        str(checks),
    ]
    assert main(argv) == 0
    assert capsys.readouterr().out == "ok\n"
    pr.write_text(json.dumps({"draft": True}))
    assert main(argv) == 1
    assert capsys.readouterr().out == "the PR is a draft\n"


def test_cli_full_out(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    md = tmp_path / "MAINTAINERS.md"
    md.write_text(MAINTAINERS_MD)
    pr = tmp_path / "pr.json"
    pr.write_text(json.dumps({"draft": False}))
    checks = tmp_path / "checks.json"
    checks.write_text(json.dumps(GREEN))
    body = tmp_path / "body.txt"
    full = tmp_path / "full.txt"
    argv = [
        "--body",
        str(body),
        "--commenter",
        "octocat",
        "--permission",
        "admin",
        "--maintainers",
        str(md),
        "--pr",
        str(pr),
        "--checks",
        str(checks),
        "--full-out",
        str(full),
    ]
    body.write_text("/review full\n")
    assert main(argv) == 0
    assert full.read_text() == "true\n"
    body.write_text("/review\n")
    assert main(argv) == 0
    assert full.read_text() == "false\n"
    full.unlink()
    body.write_text("/review everything\n")
    assert main(argv) == 1
    assert not full.exists()
    assert capsys.readouterr().out.splitlines() == [
        "ok",
        "ok",
        "the comment must be exactly `/review` or `/review full`",
    ]
