# 37: Trace tasks through publications and attributable costs

**What to build:** An operator can trace an acquisition task through attempts, runs, observations, transformations, publications, failures, and attributable usage in one lineage view.

**Blocked by:** 06: Recover interrupted tasks and expose partial outcomes; 09: Show attributable actual costs and forecasts.

**Status:** resolved

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
- Runtime/frozen commit: `815fd97f42a23537d5802f971f6d977bb6549872`; focused **120/108.91s** and required frozen full check **861/761.28s**, exit **0**, session **53956**. Status was **claimed** pending independent integration checks; those checks passed as recorded below and the ticket is now resolved. The source-free projection has bounded/independent committed owner reads; historical completion never grants current source permission or proves complete billing/market coverage or human usefulness.


## Completion

- Runtime/frozen implementation: `815fd97f42a23537d5802f971f6d977bb6549872`; final worker handoff and independently checked integration: `7b4948bdb4b6b8209f650e344ce5391725d7a720`. Clean ancestry and frozen-to-final four own scratch metadata paths were verified before fast-forward integration.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static/documentation/preflight stages and **861 tests in 747.33 seconds**, exit 0 / session 37124. Durable command/head/runtime/frozen/start/session/log/exit/finish evidence: `.scratch/operational-implementation/verification/ticket-37-integrated/shared.*` (started `2026-10-29T04:33:43.886852+00:00`, finished `2026-10-29T04:46:12.246930+00:00`). Worker full **861/761.28s**, focused **120/108.91s**, final lineage **15/22.75s**, and all prior completed gates are preserved without rerun.
- Independently verified existing wheel **437088 bytes**, **208 unique entries**, SHA-256 `2316da6b893d20c78daa2549c4091dd25124208221d934df3938e7eab7f20de2`; all **91** source/archive pairs, all **13** changed packaged paths, **18** SQL schemas, **2** assets, **32** packaged guidance pairs plus root relative guidance, and all **305** frozen protected file bytes/sizes/hashes/relative targets match the integrated root; exact manifest/verifier and `.scratch/operational-implementation/verification/ticket-37-integrated/wheel-verification.json` / `freeze-verification.json` retain evidence. No rebuild occurred.
- Coordinator-created archive 37 is independently identity/member-verified and preserved: **418363 bytes**, **39 members**, SHA-256 `3a2939b26539d6ba25bf2d3f46fbaab9ed4c6ce9fb7738944447ff64325e0b52`. The relocation index retains original paths/member hashes; original worker files and the committed 26–36 relocation report remain untouched.
- All six criteria are checked. The source-free read-only projection composes independent committed owner frontiers and bounded histories, not an atomic complete event/billing snapshot. Historical completion does not grant current source permission. Recorded actuals/commitments/forecasts retain provenance, lag and unknown coverage without cross-currency/period/scope aggregation, guaranteed ceilings or zero-overshoot claims. Waiting-code allowlisting is defensive hardening: the existing public writer already restricts codes, with no observed public-writer exploit. No actual source/model/paid I/O occurred. Live readiness, source truth, complete market coverage and human usefulness remain unestablished.
