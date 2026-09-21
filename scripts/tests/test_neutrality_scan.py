"""Tests for scripts/neutrality_scan.py."""

from __future__ import annotations

from neutrality_scan import AddedLine, added_lines

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
