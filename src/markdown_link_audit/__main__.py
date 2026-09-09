"""Module entry point for ``python -m markdown_link_audit``.

See ``docs/architecture-overview.md`` for the package call flow.
"""

from .cli import main

raise SystemExit(main())
