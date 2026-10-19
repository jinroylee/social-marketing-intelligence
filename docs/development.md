# Development verification

Run the same check command used by CI:

```bash
uv sync --locked
uv run --locked python tools/check.py
```

The command runs Ruff correctness/syntax lint, validates local product-document links, physical ERD table coverage and relative instruction symlinks, checks PostgreSQL connectivity once, then runs pytest with bounded failure output. Tests use temporary schemas and remove them after execution.

Start the local database with `docker compose up -d --wait postgres`, or configure `SMI_TEST_DATABASE_URL` for another development/test PostgreSQL instance. Failed preflight produces one sanitized actionable message and stops before database-dependent tests.

Use `uv run --locked python tools/check.py --static` for lint and documentation checks without PostgreSQL. Test prerequisites are deliberate; a missing database is a failed check rather than a silently skipped test suite.

The [CI workflow](../.github/workflows/checks.yml) runs on pushes and pull requests, provides PostgreSQL 16 and invokes this same command with locked dependencies. The configured workflow becomes active when the change is pushed to the repository. Branch-protection requirements remain repository hosting configuration.
