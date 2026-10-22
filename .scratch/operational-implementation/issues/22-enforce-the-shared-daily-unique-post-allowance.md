# 22: Enforce the shared daily unique-post allowance

**What to build:** Scheduled discovery admits at most the configured daily total of unique eligible new posts across all keywords and competing workers.

**Blocked by:** 21: Schedule offline discovery for registered keywords.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Atomic new-post admission at the established scheduled ingestion boundary; do not treat request counts, refreshes, or costs as the same allowance.

- [ ] The initial configurable total is fifty unique eligible new posts per workspace/day across all registered keywords, not fifty per keyword.
- [ ] Overlapping query results and competing tasks cannot admit the same eligible new post twice or collectively exceed the day's allowance; invalid/denied records do not count as successful new-post admission, and failed admission/ingestion releases or reconciles reservations safely.
- [ ] Known-record refreshes remain distinct from new-post admission and cannot be disguised as additional new eligible posts.
- [ ] Restarts, keyword edits, and configuration revisions preserve consumption under the recorded accounting-day/timezone boundary.
- [ ] Task and schedule views show used/remaining allowance, deduplication, limits, and legitimate fewer-record outcomes without promising a fill target.
- [ ] Real competing public operations test overlapping identities, exhausted allowance, day rollover, and configuration changes without paid I/O.

**Spec coverage:** user stories 40, 41, 44; acceptance scenarios T07, T18, T20 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
