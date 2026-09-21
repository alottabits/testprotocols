"""Tests for scripts/neutrality_scan.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from neutrality_scan import AddedLine, Hit, added_lines, check_line, main, scan_diff

DIFF_TWO_FILES = """\
diff --git a/packages/testprotocols/src/testprotocols/x.py \
b/packages/testprotocols/src/testprotocols/x.py
--- a/packages/testprotocols/src/testprotocols/x.py
+++ b/packages/testprotocols/src/testprotocols/x.py
@@ -10,4 +10,6 @@ class X:
 kept = 1
-removed = 2
+added_one = 3
+added_two = 4
 kept_too = 5
@@ -30,2 +32,3 @@ def f():
     pass
+    return 1
diff --git a/docs/old.md b/docs/old.md
deleted file mode 100644
--- a/docs/old.md
+++ /dev/null
@@ -1,2 +0,0 @@
-gone
-gone too
diff --git a/docs/new.md b/docs/new.md
new file mode 100644
--- /dev/null
+++ b/docs/new.md
@@ -0,0 +1,2 @@
+# New
+++ not a file header
"""


def test_added_lines_carry_path_and_new_line_numbers() -> None:
    lines = list(added_lines(DIFF_TWO_FILES))
    assert lines == [
        AddedLine("packages/testprotocols/src/testprotocols/x.py", 11, "added_one = 3"),
        AddedLine("packages/testprotocols/src/testprotocols/x.py", 12, "added_two = 4"),
        AddedLine("packages/testprotocols/src/testprotocols/x.py", 33, "    return 1"),
        AddedLine("docs/new.md", 1, "# New"),
        AddedLine("docs/new.md", 2, "++ not a file header"),
    ]


def test_deleted_file_yields_nothing() -> None:
    assert [line for line in added_lines(DIFF_TWO_FILES) if line.path == "docs/old.md"] == []


def test_empty_diff_yields_nothing() -> None:
    assert list(added_lines("")) == []


SRC = "packages/testprotocols/src/testprotocols/x.py"
TEST = "packages/testprotocols/tests/test_x.py"
DOC = "docs/proposals/2026-01-01-thing.md"


@pytest.mark.parametrize(
    "text",
    [
        'addr = "203.0.113.7/24"',
        'peer = "192.0.2.1"',
        'decoy = "198.51.100.0/24"',
        'v6 = "2001:db8::9"',
        'any = "0.0.0.0/0"',
        'lo = "127.0.0.1"',
        'mask = "255.255.255.0"',
        'ospf = "224.0.0.5"',
        'll = "fe80::1"',
        'unspec = "::"',
        'mac = "00:11:22:33:44:55"',
        "at 12:30:45 the run",
        "version 1.2.3",
    ],
)
def test_allowed_addresses_anywhere(text: str) -> None:
    assert check_line(SRC, text) == []


@pytest.mark.parametrize(
    "text",
    ['a = "10.1.30.50/24"', 'b = "192.168.10.20"', 'c = "172.16.5.0/24"', 'd = "198.18.0.0/15"'],
)
def test_private_and_benchmark_ranges_allowed_under_tests_only(text: str) -> None:
    assert check_line(TEST, text) == []
    assert [kind for kind, _ in check_line(SRC, text)] == ["ip-literal"]


@pytest.mark.parametrize("text", ['dns = "1.1.1.1"', 'x = "8.8.8.8"', 'v6 = "2a02:1234::1"'])
def test_public_addresses_hit_even_under_tests(text: str) -> None:
    assert [kind for kind, _ in check_line(TEST, text)] == ["ip-literal"]


def test_ip_token_is_reported() -> None:
    assert check_line(SRC, 'x = "8.8.4.4"') == [("ip-literal", "8.8.4.4")]


@pytest.mark.parametrize(
    ("path", "text"),
    [
        (SRC, 'host = "gateway.site.lan"'),
        (SRC, 'h = "printer.local"'),
        (SRC, "# reach gateway.lan for the console"),
        (SRC, '"""Connect to core1.internal."""'),
        (DOC, "the box at core1.internal answers"),
        (DOC, "the box at gateway.lan."),
        (DOC, "(see gateway.lan)"),
        (DOC, "the `gateway.lan` box"),
    ],
)
def test_private_use_hostnames_hit(path: str, text: str) -> None:
    assert [kind for kind, _ in check_line(path, text)] == ["hostname"]


@pytest.mark.parametrize(
    ("path", "text"),
    [
        (SRC, "_delete_if_present(ap.lan, vlan_id)"),
        (SRC, "a.target.lan.set_vlan(a.vlan)"),
        (SRC, "return self.lan"),
        (SRC, "iface = ap.lan"),
        (SRC, 'host = "gateway.example.com"'),
        (SRC, "self.local = 1"),
        (DOC, "a.target.lan.set_vlan(a.vlan)"),
        (DOC, "self.local = 1"),
    ],
)
def test_attribute_access_and_public_names_are_not_hostnames(path: str, text: str) -> None:
    assert check_line(path, text) == []


def test_email_outside_example_domains_hits() -> None:
    assert check_line(SRC, "contact: someone@corp-mail.net") == [("email", "someone@corp-mail.net")]


@pytest.mark.parametrize(
    "text",
    [
        "Signed-off-by: Jane Doe <jane@corp-mail.net>",
        "jane.doe@example.com",
        "ops@example.org",
        'maintainers = [{ email = "rjvisser@alottabits.com" }]',
    ],
)
def test_allowed_emails(text: str) -> None:
    assert check_line(SRC, text) == []


def test_ticket_id_hits() -> None:
    assert check_line(SRC, "see NETOPS-4711 for the outage") == [("ticket-id", "NETOPS-4711")]


@pytest.mark.parametrize(
    "text",
    [
        "UC-019 P2",
        "ENG-007",
        "TR-069 and TR-181",
        "RFC-4271",
        "ISO-8601",
        "TLS-1",
        "TEST-NET-2",
        "UC-ACS-GUI-01-2a",
    ],
)
def test_allowed_identifiers(text: str) -> None:
    assert check_line(SRC, text) == []


def test_allow_marker_exempts_the_line_it_is_on() -> None:
    assert check_line(SRC, 'dns = "8.8.8.8"  # neutrality: allow') == []
    assert check_line(SRC, 'host = "gateway.lan"  # neutrality: allow') == []
    assert check_line(DOC, "the box at 8.8.8.8 <!-- neutrality: allow -->") == []
    assert check_line(DOC, "tracked as NETOPS-4711 <!-- neutrality: allow -->") == []
    # The marker exempts its own line only.
    assert [kind for kind, _ in check_line(DOC, "the box at 8.8.8.8")] == ["ip-literal"]


def test_the_scanner_and_its_own_tests_are_self_exempt() -> None:
    diff = (
        "--- a/scripts/neutrality_scan.py\n"
        "+++ b/scripts/neutrality_scan.py\n"
        "@@ -1,1 +1,2 @@\n"
        '+EXAMPLE = "8.8.8.8"\n'
        "--- a/scripts/tests/test_neutrality_scan.py\n"
        "+++ b/scripts/tests/test_neutrality_scan.py\n"
        "@@ -1,1 +1,2 @@\n"
        "+    assert check_line(SRC, 'x = \"8.8.8.8\"') == []\n"
    )
    assert scan_diff(diff) == []


@pytest.mark.parametrize(
    "text",
    [
        "LICENSE-2.0",
        "https://www.apache.org/licenses/LICENSE-2.0",
        "the text of /LICENSE-2.0 in the tree",
        "negotiated TLS-1.2",
    ],
)
def test_licence_and_standards_identifiers_are_not_tickets(text: str) -> None:
    assert check_line(DOC, text) == []
    assert check_line(SRC, text) == []


def test_ticket_shaped_id_still_hits_next_to_those() -> None:
    assert check_line(DOC, "NETOPS-4711 under LICENSE-2.0") == [("ticket-id", "NETOPS-4711")]


def test_scan_diff_reports_hits_with_location() -> None:
    diff = (
        "--- /dev/null\n"
        "+++ b/docs/proposals/2026-01-01-thing.md\n"
        "@@ -0,0 +1,3 @@\n"
        "+# Thing\n"
        "+reachable at 8.8.8.8\n"
        "+tracked as NETOPS-1\n"
    )
    assert scan_diff(diff) == [
        Hit("docs/proposals/2026-01-01-thing.md", 2, "ip-literal", "8.8.8.8"),
        Hit("docs/proposals/2026-01-01-thing.md", 3, "ticket-id", "NETOPS-1"),
    ]


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean = tmp_path / "clean.diff"
    clean.write_text("--- /dev/null\n+++ b/a.md\n@@ -0,0 +1 @@\n+hello 192.0.2.1\n")
    assert main([str(clean)]) == 0
    dirty = tmp_path / "dirty.diff"
    dirty.write_text("--- /dev/null\n+++ b/a.md\n@@ -0,0 +1 @@\n+hello 8.8.8.8\n")
    assert main([str(dirty)]) == 1
    assert "a.md:1: ip-literal: 8.8.8.8" in capsys.readouterr().out
