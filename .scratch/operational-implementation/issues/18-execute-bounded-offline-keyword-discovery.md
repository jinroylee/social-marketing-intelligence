# 18: Execute bounded offline keyword discovery

**What to build:** An authorized task can search a scoped offline discovery route, ingest newly found records, and expose the resulting published KB updates.

**Blocked by:** 03: Search current knowledge and pin result support; 06: Recover interrupted tasks and expose partial outcomes.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One deterministic query-discovery route and capability contract; no real provider, automatic fallback, scheduler, or supplemental retrieval.

- [x] Discovery accepts explicit query/subject/time scope and bounded limits rather than pretending a supplied-profile collector performs keyword search.
- [x] Configured capability and task authority are checked before dispatch; unsupported query routes expose an accurate unavailable reason.
- [x] A bounded offline discovery response flows through normal ingestion/publication and appears in current knowledge with query/route/selection lineage.
- [x] Results record actual capture times, coverage, missing fields, source identities, and prioritization/method context without inventing complete market coverage.
- [x] Empty, unchanged, partially valid, and failed results preserve the existing truthful task outcome meanings.
- [x] The public task/UI journey uses deterministic source-shaped fixtures and verifies no live calls, no duplicate publication benefit, and permitted support.

**Spec coverage:** user stories 16, 35, 38, 42, 43, 46; acceptance scenarios T01, T05, T06, T19 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

- Implementation and frozen offline verification are recorded in [the ticket 18 report](../reports/ticket-18.md). All technical acceptance criteria are demonstrated, including public/HTTP discovery, partial/empty/unchanged/policy outcomes, bounded source-shaped pages and recovery. The worker gate passed 469 tests in 302.95 seconds with real isolated PostgreSQL. Status remains claimed for the merger's integrated shared check and resolution.
