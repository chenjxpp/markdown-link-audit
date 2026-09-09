"""Command-line adapter for markdown-link-audit.

See ``docs/architecture-overview.md`` for the separation between traversal,
validation, rendering, and process status.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .core import AuditResult, audit_tree


def build_parser() -> argparse.ArgumentParser:
    """Build the public command-line argument parser."""

    parser = argparse.ArgumentParser(description="Audit local links and anchors in a Markdown tree.")
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd(), help="directory to scan (default: current)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit a machine-readable JSON report")
    return parser


def render_text(result: AuditResult) -> str:
    """Render the audit summary and every issue as readable text."""

    lines = [f"Scanned {result.scanned_files} Markdown file(s); found {len(result.issues)} issue(s)"]
    lines.extend(
        f"{issue.source}:{issue.line_number} [{issue.code}] {issue.message}"
        for issue in result.issues
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return ``0`` clean, ``1`` issues, or ``2`` input/I/O errors."""

    args = build_parser().parse_args(argv)
    try:
        result = audit_tree(args.root)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
