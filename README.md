# markdown-link-audit

A dependency-free Python CLI that finds broken local links before documentation
is merged or published.

The audit checks:

- relative document and image targets;
- same-file and cross-file heading anchors;
- links that escape the selected documentation root;
- Markdown links outside fenced code blocks.

External URLs are intentionally skipped. Network link checking is often slow,
non-deterministic, and better handled by a dedicated CI step.

## Quick start

```bash
python -m markdown_link_audit docs
python -m markdown_link_audit . --json
```

Example output:

```text
Scanned 7 Markdown file(s); found 2 issue(s)
docs/setup.md:18 [missing_target] ../images/flow.png does not exist
README.md:27 [missing_anchor] docs/guide.md has no heading anchor #install
```

The command exits with `0` when all local links are valid, `1` when issues are
found, and `2` for invalid input or I/O errors.

## Supported links

Inline links and images such as `[guide](docs/guide.md#install)` and
`![diagram](images/flow.png)` are checked. Links inside backtick or tilde fenced
code blocks are ignored. ATX and Setext headings are recognized using a
GitHub-compatible anchor approximation.

## Development

```bash
python -m unittest discover -s tests -v
```

See [`docs/architecture-overview.md`](docs/architecture-overview.md) for the
module responsibilities and known limits.

## License

MIT
