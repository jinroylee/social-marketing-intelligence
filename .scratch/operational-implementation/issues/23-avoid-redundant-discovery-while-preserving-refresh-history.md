# 23: Avoid redundant discovery while preserving refresh history

**What to build:** An operator can see unnecessary repeated retrieval skipped while legitimate stale-record refreshes and new observations retain their provenance.

**Blocked by:** 18: Execute bounded offline keyword discovery.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One discovery route's query/retrieval history and explicit freshness/processing policy; no global cross-provider identity merge or automatic fallback.

- [ ] Persist prior query/retrieval scope, source identity, capture time, failures, usable publication, and method/version context needed for an explicit avoidance decision.
- [ ] Repeated unchanged work within the configured freshness policy can be skipped with an inspectable reason rather than re-fetched or re-published as a new update.
- [ ] Stale captures, changed source observations, required mapper revisions, and recoverable failed work remain eligible for appropriate new processing.
- [ ] Unknown or unavailable freshness stays explicit; import/publication time cannot make old captures current.
- [ ] Source namespaces, metric definitions, conflict history, and old result pins remain separate across refresh and deduplication.
- [ ] Public task/KB tests count simulated retrievals and verify skip/refresh/failure behavior and historical support after restart.

**Spec coverage:** user stories 43, 44, 45, 46; acceptance scenarios T06, T19, T20 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
