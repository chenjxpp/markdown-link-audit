"""Regression tests for Markdown target and anchor validation.

The covered contract is documented in ``docs/architecture-overview.md``.
"""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from markdown_link_audit import audit_tree


class AuditTreeTests(unittest.TestCase):
    """Verify valid links and each stable local-link issue type."""

    def test_valid_relative_and_anchor_links(self) -> None:
        """Existing files and known anchors produce a clean result."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("# Install now\n", encoding="utf-8")
            (root / "README.md").write_text(
                "[guide](guide.md#install-now)\n[self](#home)\n# Home\n", encoding="utf-8"
            )
            result = audit_tree(root)
            self.assertTrue(result.ok)
            self.assertEqual(result.scanned_files, 2)

    def test_missing_target_and_anchor_are_reported(self) -> None:
        """Broken file paths and heading fragments receive stable issue codes."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "guide.md").write_text("# Existing\n", encoding="utf-8")
            (root / "README.md").write_text(
                "[missing](none.md)\n[anchor](guide.md#absent)\n", encoding="utf-8"
            )
            result = audit_tree(root)
            self.assertEqual([issue.code for issue in result.issues], ["missing_target", "missing_anchor"])

    def test_fenced_links_are_ignored_and_escape_is_rejected(self) -> None:
        """Code samples do not create false positives, while root escapes fail."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "```md\n[example](not-real.md)\n```\n[outside](../secret.md)\n", encoding="utf-8"
            )
            result = audit_tree(root)
            self.assertEqual(len(result.issues), 1)
            self.assertEqual(result.issues[0].code, "outside_root")

    def test_inline_code_link_examples_are_ignored(self) -> None:
        """Link syntax shown as inline code does not create a false positive."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "Use `[guide](not-real.md)` as an example.\n", encoding="utf-8"
            )
            result = audit_tree(root)
            self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
