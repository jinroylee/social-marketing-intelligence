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

## Current test-fixture limitation

The assistant-enrichment test `test_only_supported_kb_gaps_offer_proposals_not_model_failures_or_generic_unknowns` publishes a fixed `2026-10-01` capture and expects it to have no freshness gap. Once the real clock moves beyond its default 30-day threshold, the implementation correctly reports `stale_published_information`, and that assertion fails. The same failure reproduces on the unchanged implementation baseline.

```bash
uv run --locked pytest -q tests/test_assistant_enrichment.py::test_only_supported_kb_gaps_offer_proposals_not_model_failures_or_generic_unknowns
```

This is pending fixture maintenance. Use an intentional controlled clock or current relative capture for the fresh-input scenario in a future code/test change, preserving the separate stale-input assertions and actual product freshness policy. Static documentation checks remain independently runnable; a historical passing test count does not establish that today's full suite passes.
