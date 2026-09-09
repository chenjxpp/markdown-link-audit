"""Local-link and heading-anchor validation for Markdown files.

The core avoids network access and console I/O. Design constraints and known
parser limits are recorded in ``docs/architecture-overview.md``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
import string
from typing import Iterator
from urllib.parse import unquote, urlsplit


_INLINE_LINK = re.compile(
    r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^\s)]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\)"
)
_ATX_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_SETEXT_UNDERLINE = re.compile(r"^\s*(=+|-+)\s*$")
_INLINE_CODE = re.compile(r"(`+)(?:.*?)(?<!`)\1(?!`)")


@dataclass(frozen=True)
class LinkIssue:
    """Describe one invalid local Markdown link.

    ``source`` is relative to the selected root when possible. ``line_number``
    is one-based. ``code`` is stable for automation, while ``message`` gives a
    human-readable explanation.
    """

    source: str
    line_number: int
    code: str
    target: str
    message: str


@dataclass
class AuditResult:
    """Aggregate scanned-file count and link issues for one audit."""

    scanned_files: int = 0
    issues: list[LinkIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return ``True`` when every checked local link is valid."""

        return not self.issues

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the result."""

        return {
            "scanned_files": self.scanned_files,
            "issue_count": len(self.issues),
            "ok": self.ok,
            "issues": [asdict(issue) for issue in self.issues],
        }


def _content_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield line numbers and text while omitting fenced code blocks."""

    fence: str | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None:
            yield line_number, line


def _without_inline_code(line: str) -> str:
    """Remove common backtick code spans before looking for Markdown links."""

    return _INLINE_CODE.sub("", line)


def github_slug(heading: str) -> str:
    """Approximate GitHub's heading slug for common Latin and Unicode text."""

    normalized = heading.strip().lower()
    allowed_punctuation = {"-", "_", " "}
    without_markup = re.sub(r"[`*_~]", "", normalized)
    filtered = "".join(
        character
        for character in without_markup
        if character not in string.punctuation or character in allowed_punctuation
    )
    return re.sub(r"[\s-]+", "-", filtered).strip("-")


def heading_anchors(text: str) -> set[str]:
    """Collect de-duplicated GitHub-style anchors from ATX and Setext headings."""

    headings: list[str] = []
    lines = list(_content_lines(text))
    for index, (_, line) in enumerate(lines):
        match = _ATX_HEADING.match(line)
        if match:
            headings.append(match.group(2))
            continue
        if index > 0 and _SETEXT_UNDERLINE.match(line) and lines[index - 1][1].strip():
            headings.append(lines[index - 1][1].strip())

    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for heading in headings:
        base = github_slug(heading)
        if not base:
            continue
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def _display_source(path: Path, root: Path) -> str:
    """Return a stable root-relative source name when possible."""

    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def audit_markdown_file(path: Path, root: Path) -> list[LinkIssue]:
    """Audit inline local links in one Markdown file within ``root``.

    External schemes are skipped. Resolved local paths may not escape ``root``.
    Missing target files and missing heading anchors are returned as issues.
    """

    root = root.resolve()
    path = path.resolve()
    text = path.read_text(encoding="utf-8")
    issues: list[LinkIssue] = []
    anchor_cache: dict[Path, set[str]] = {path: heading_anchors(text)}
    source_name = _display_source(path, root)

    for line_number, line in _content_lines(text):
        for match in _INLINE_LINK.finditer(_without_inline_code(line)):
            raw_target = match.group("target").strip("<>")
            parsed = urlsplit(raw_target)
            if parsed.scheme or parsed.netloc:
                continue
            decoded_path = unquote(parsed.path)
            target_path = path if not decoded_path else (path.parent / decoded_path).resolve()

            try:
                target_path.relative_to(root)
            except ValueError:
                issues.append(
                    LinkIssue(source_name, line_number, "outside_root", raw_target, "target resolves outside the audit root")
                )
                continue

            if not target_path.exists():
                issues.append(
                    LinkIssue(source_name, line_number, "missing_target", raw_target, f"{decoded_path or path.name} does not exist")
                )
                continue

            fragment = unquote(parsed.fragment).lower()
            if fragment and target_path.is_file() and target_path.suffix.lower() in {".md", ".markdown"}:
                if target_path not in anchor_cache:
                    anchor_cache[target_path] = heading_anchors(target_path.read_text(encoding="utf-8"))
                if fragment not in anchor_cache[target_path]:
                    issues.append(
                        LinkIssue(
                            source_name,
                            line_number,
                            "missing_anchor",
                            raw_target,
                            f"{_display_source(target_path, root)} has no heading anchor #{fragment}",
                        )
                    )

    return issues


def audit_tree(root: Path) -> AuditResult:
    """Recursively audit every Markdown file under ``root`` in stable order."""

    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"audit root is not a directory: {root}")
    files = sorted(path for path in root.rglob("*.md") if ".git" not in path.parts)
    result = AuditResult(scanned_files=len(files))
    for path in files:
        result.issues.extend(audit_markdown_file(path, root))
    return result
