# Repository checks

This directory owns deterministic development verification. `check.py` runs the same lint, documentation and test checks locally and in CI; `--static` skips database-dependent tests. `check_docs.py` validates local product-document links, physical ERD table coverage and relative instruction symlinks.

Keep checks read-only apart from normal tool caches and isolated test schemas. Database preflight must fail once with an actionable, sanitized message; never print connection strings or credentials. CI and the local entry point must use the same check command. Product behavior belongs to `src/`, not these scripts.
