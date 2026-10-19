# 03: Search current knowledge and pin result support

**What to build:** A marketer can search published knowledge, inspect coverage and freshness, and reopen the exact support selection behind a result.

**Blocked by:** 02: Publish and inspect permitted ingested support.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Use bounded text/subject/platform/time filters and a stable support manifest; defer semantic/vector search and graph navigation.

- [ ] A public query and local knowledge-search surface search only committed, permitted publications and expose source references, relevant dates, methods, unknowns, and coverage.
- [ ] Search distinguishes age-based freshness from permission/derivation health and does not count ingestion/publication time as a new capture.
- [ ] A consequential query result can pin the actual observation/assertion/interpretation membership and versions used, rather than only storing the query.
- [ ] A later publication can appear in a new query while an earlier pinned result retains exact membership and unavailable/superseded support indicators.
- [ ] Queries and reopened results honor workspace and purpose boundaries, exclude synthetic inputs unless explicitly selected for development, and do not leak pending raw responses or denied text.
- [ ] Default integration tests use real public readers and PostgreSQL, including source-only accounts, empty scope, newer publications, and withdrawal.

**Spec coverage:** user stories 5, 9, 10, 14, 22, 24, 32, 33, 68; acceptance scenarios T01, T08, T09, T16, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
