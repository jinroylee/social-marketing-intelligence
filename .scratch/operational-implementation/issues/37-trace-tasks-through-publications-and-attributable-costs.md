# 37: Trace tasks through publications and attributable costs

**What to build:** An operator can trace an acquisition task through attempts, runs, observations, transformations, publications, failures, and attributable usage in one lineage view.

**Blocked by:** 06: Recover interrupted tasks and expose partial outcomes; 09: Show attributable actual costs and forecasts.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Read-only task-to-publication lineage using public owners and existing status/cost records; no generic observability platform or graph-explorer dependency.

- [ ] A public lineage read and local view connect the actual task/authority to bounded attempts, ingestion runs, observations, derivation/method versions, and resulting publications.
- [ ] The view makes queue acceptance, source success, partial ingestion, publication failure, no update, and usable completion visibly distinct.
- [ ] Cost context links actuals, commitments, forecasts, meter provenance/lag, and unknown coverage where available without claiming unenforced ceilings.
- [ ] Support/source excerpts pass current permissions, retention, and workspace checks; no credential or unrestricted provider payload appears in detail or errors.
- [ ] Restart and recovery histories preserve links rather than inventing a successful continuous pipeline.
- [ ] Public/HTTP tests exercise a successful trace, partial failure, resumed attempt, denied support, and cost attribution through real stores.

**Spec coverage:** user stories 35, 38, 66, 67, 68; acceptance scenarios T04, T05, T08, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
