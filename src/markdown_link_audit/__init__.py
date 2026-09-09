"""Public API for markdown-link-audit.

See ``docs/architecture-overview.md`` for supported Markdown forms and module
responsibilities.
"""

from .core import AuditResult, LinkIssue, audit_markdown_file, audit_tree

__all__ = ["AuditResult", "LinkIssue", "audit_markdown_file", "audit_tree"]
