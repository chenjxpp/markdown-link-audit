# Architecture overview

`src/markdown_link_audit/core.py` scans Markdown text, resolves local paths
against the source file, and validates fragments against headings in the target
document. It has no console concerns.

`src/markdown_link_audit/cli.py` selects the root, renders text or JSON, and
maps audit results to process exit codes.

```mermaid
flowchart LR
    A[Markdown tree] --> B[audit_tree]
    B --> C[Extract local links]
    C --> D[Resolve target path]
    D --> E[Validate file and anchor]
    E --> F[Text or JSON report]
```

## Public contract

- `LinkIssue`: source file, line number, stable issue code, target, and message.
- `AuditResult`: scanned-file count plus collected issues.
- `audit_markdown_file(path, root)`: check one file within a root.
- `audit_tree(root)`: recursively check all `*.md` files.

The parser intentionally targets common inline Markdown links rather than the
entire CommonMark grammar. Reference-style links and generated anchors with
unusual punctuation may require a future parser adapter. Existing behavior is
covered by `tests/test_core.py`.
