# 03: Search current knowledge and pin result support

**What to build:** A marketer can search published knowledge, inspect coverage and freshness, and reopen the exact support selection behind a result.

**Blocked by:** 02: Publish and inspect permitted ingested support.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Use bounded text/subject/platform/time filters and a stable support manifest; defer semantic/vector search and graph navigation.

- [x] A public query and local knowledge-search surface search only committed, permitted publications and expose source references, relevant dates, methods, unknowns, and coverage.
- [x] Search distinguishes age-based freshness from permission/derivation health and does not count ingestion/publication time as a new capture.
- [x] A consequential query result can pin the actual observation/assertion/interpretation membership and versions used, rather than only storing the query.
- [x] A later publication can appear in a new query while an earlier pinned result retains exact membership and unavailable/superseded support indicators.
- [x] Queries and reopened results honor workspace and purpose boundaries, exclude synthetic inputs unless explicitly selected for development, and do not leak pending raw responses or denied text.
- [x] Default integration tests use real public readers and PostgreSQL, including source-only accounts, empty scope, newer publications, and withdrawal.

**Spec coverage:** user stories 5, 9, 10, 14, 22, 24, 32, 33, 68; acceptance scenarios T01, T08, T09, T16, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Completion

- Implementation commit: `e3e55d3e89684bf3a5696d3caf0c1d257dde107c`, fast-forward integrated into `integration/operational-tickets-01-10`.
- Integrated verification: `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **235 tests in 126.73 seconds**.
- All acceptance criteria are checked. See [the implementation report](../reports/ticket-03.md) for public interfaces and focused verification. Delivery remained offline and local, with real PostgreSQL and simulated external I/O; no push or PR occurred.
