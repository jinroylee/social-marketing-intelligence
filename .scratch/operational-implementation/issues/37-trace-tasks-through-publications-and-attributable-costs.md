# 37: Trace tasks through publications and attributable costs

**What to build:** An operator can trace an acquisition task through attempts, runs, observations, transformations, publications, failures, and attributable usage in one lineage view.

**Blocked by:** 06: Recover interrupted tasks and expose partial outcomes; 09: Show attributable actual costs and forecasts.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Read-only task-to-publication lineage using public owners and existing status/cost records; no generic observability platform or graph-explorer dependency.

- [x] A public lineage read and local view connect the actual task/authority to bounded attempts, ingestion runs, observations, derivation/method versions, and resulting publications.
- [x] The view makes queue acceptance, source success, partial ingestion, publication failure, no update, and usable completion visibly distinct.
- [x] Cost context links actuals, commitments, forecasts, meter provenance/lag, and unknown coverage where available without claiming unenforced ceilings.
- [x] Support/source excerpts pass current permissions, retention, and workspace checks; no credential or unrestricted provider payload appears in detail or errors.
- [x] Restart and recovery histories preserve links rather than inventing a successful continuous pipeline.
- [x] Public/HTTP tests exercise a successful trace, partial failure, resumed attempt, denied support, and cost attribution through real stores.

**Spec coverage:** user stories 35, 38, 66, 67, 68; acceptance scenarios T04, T05, T08, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

- All acceptance criteria are implemented and locally verified through public owner/HTTP seams with real isolated PostgreSQL and fake external I/O. See [the ticket 37 report](../reports/ticket-37.md), [exact wheel manifest](../reports/ticket-37-wheel-manifest.json) and [standalone verifier](../reports/verify-ticket-37-wheel.py).
- Runtime/frozen commit: `815fd97f42a23537d5802f971f6d977bb6549872`; focused **120/108.91s** and required frozen full check **861/761.28s**, exit **0**, session **53956**. Status remains **claimed** for independent integration checks and merger resolution. The source-free projection has bounded/independent committed owner reads; historical completion never grants current source permission or proves complete billing/market coverage or human usefulness.
