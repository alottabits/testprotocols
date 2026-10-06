"""Tests for scripts/review_gate.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from review_gate import conclusions, full_requested, main, maintainers, refusal

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
GREEN_RUNS = [
    {"id": 1, "name": "dco", "status": "completed", "conclusion": "success"},
    {"id": 2, "name": "lint", "status": "completed", "conclusion": "success"},
    {"id": 3, "name": "hygiene", "status": "completed", "conclusion": "success"},
]


def run(run_id: int, name: str, status: str, conclusion: str | None = None) -> dict[str, object]:
    return {"id": run_id, "name": name, "status": status, "conclusion": conclusion}


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


@pytest.mark.parametrize(
    ("hygiene_runs", "state"),
    [
        # A body edit's run cancelled the push's run; the later one passed.
        (
            [
                run(10, "hygiene", "completed", "cancelled"),
                run(11, "hygiene", "completed", "success"),
            ],
            "success",
        ),
        # Listed out of order: the id decides, not the list position.
        (
            [
                run(11, "hygiene", "completed", "success"),
                run(10, "hygiene", "completed", "cancelled"),
            ],
            "success",
        ),
        # A newer run was cancelled after an older one passed.
        (
            [
                run(10, "hygiene", "completed", "success"),
                run(11, "hygiene", "completed", "cancelled"),
            ],
            "cancelled",
        ),
        # A run still going beside a finished success: wait for it.
        (
            [run(10, "hygiene", "completed", "success"), run(11, "hygiene", "in_progress")],
            "in_progress",
        ),
        ([run(10, "hygiene", "queued"), run(11, "hygiene", "completed", "success")], "queued"),
        # A re-run of a failed run.
        (
            [
                run(10, "hygiene", "completed", "failure"),
                run(12, "hygiene", "completed", "success"),
            ],
            "success",
        ),
        # A re-run of a cancelled run, itself cancelled.
        (
            [
                run(10, "hygiene", "completed", "cancelled"),
                run(12, "hygiene", "completed", "cancelled"),
            ],
            "cancelled",
        ),
        ([run(10, "hygiene", "completed", "cancelled")], "cancelled"),
    ],
)
def test_conclusions_pick_the_newest_completed_run(
    hygiene_runs: list[dict[str, object]], state: str
) -> None:
    states = conclusions([*GREEN_RUNS[:2], *hygiene_runs])
    assert states == {"dco": "success", "lint": "success", "hygiene": state}


@pytest.mark.parametrize(
    ("hygiene_runs", "reason"),
    [
        (
            [
                run(10, "hygiene", "completed", "cancelled"),
                run(11, "hygiene", "completed", "success"),
            ],
            None,
        ),
        (
            [
                run(10, "hygiene", "completed", "success"),
                run(11, "hygiene", "completed", "cancelled"),
            ],
            "hygiene is cancelled on the head commit",
        ),
        (
            [run(10, "hygiene", "completed", "success"), run(11, "hygiene", "in_progress")],
            "hygiene is in_progress on the head commit",
        ),
        (
            [
                run(10, "hygiene", "completed", "failure"),
                run(11, "hygiene", "completed", "success"),
            ],
            None,
        ),
        ([run(10, "hygiene", "completed", "cancelled")], "hygiene is cancelled on the head commit"),
        ([], "hygiene is missing on the head commit"),
    ],
)
def test_gate_over_check_runs(hygiene_runs: list[dict[str, object]], reason: str | None) -> None:
    assert ok(checks=conclusions([*GREEN_RUNS[:2], *hygiene_runs])) == reason


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
    checks.write_text(json.dumps(GREEN_RUNS))
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
    checks.write_text(json.dumps(GREEN_RUNS))
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
