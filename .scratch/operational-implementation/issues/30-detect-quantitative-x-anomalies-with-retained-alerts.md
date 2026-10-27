# 30: Detect quantitative X anomalies with retained alerts

**What to build:** A marketer receives an inspectable alert when a configured quantitative method finds a justified X volume or engagement anomaly.

**Blocked by:** 08: Deliver durable task completion notifications; 29: Collect bounded recent X evidence offline.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One configured quantitative method and comparable baseline/window pair, with retained alert history and local inbox delivery; no semantic detection or external investigation.

- [x] Record explicit detection/baseline windows, sampling and metric comparability, method/version, significance configuration, coverage, and necessary evidence.
- [x] A supported significant change creates a retained alert and concise durable notification with evidence and uncertainty.
- [x] Absent/incomparable baselines or insufficient coverage cannot produce an unsupported numerical spike claim and are visible as assessment limitations.
- [x] Alert detail/history survive restart and reflect current policy, expiry, and unavailable support without retaining denied copied wording.
- [x] Detection requires no full KB publication for all recent observations and cannot create campaigns, expand topic scope, or launch external searches.
- [x] Public polling/detection/inbox tests use controlled windows for real anomaly, no anomaly, missing baseline, changed sampling, retries, and withdrawal.

**Spec coverage:** user stories 49, 51, 54, 56, 57; acceptance scenarios T24, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementation handoff

At worker handoff, implementation was complete at runtime/frozen `2132df92c4df6c77948169701ef1ad4710f63172` and the ticket was **claimed** pending independent merger validation and resolution; completed evidence follows. [Ticket 30 report](../reports/ticket-30.md) records the configured distinct-native-post volume method, governed retained alerts/local inbox notifications and public PostgreSQL/HTTP coverage. Required `UV_OFFLINE=1 uv run --locked python tools/check.py` passed exit 0: **722 tests in 493.31s**, completed session **45901**, durable `verification/ticket-30/shared.{json,log}`. Final owner 16-case and expanded compatibility/CLI checks passed. The passing full gate was preserved without rerun.

The offline wheel passed exact source/archive verification for all changed packaged files, thirteen SQL schemas, both review assets and all 26 packaged guidance pairs; [manifest](../reports/ticket-30-wheel-manifest.json) and [standalone verifier](../reports/verify-ticket-30-wheel.py) retain exact bytes/size/hash/relative-target evidence. No runtime/test/product-doc/guidance change followed freeze; only this checklist/handoff, report and artifact manifest/verifier were written after PASS. No live source/model/paid execution, external message, push, PR, deployment or cleanup occurred. Semantic detection, KB explanation, promotion and live X remain out of scope. Merger-owned integration gating/resolution and eventual archive-before-cleanup remain required.


## Completion

- Runtime implementation and frozen worker checked commit: `2132df92c4df6c77948169701ef1ad4710f63172`. Final worker handoff and root integrated checked commit: `c9d456fe85d9597c1dea7eea409e2a0318f9f63d`, fast-forward integrated from clean `60018486acfe9984d2ec870ab49428fa3b016e62`. Frozen-to-final changes are exactly four own scratch handoff files: issue checklist/comment, report, exact manifest and verifier.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **722 tests in 489.96 seconds**, exit **0**, session `62247`. Durable root `.scratch/operational-implementation/verification/ticket-30-integrated/shared.{started,finished,head,runtime,worker-frozen,command,session,log,exit}` retains exact execution identity/status. Worker and earlier completed gates were preserved; all six criteria are checked.
- Independently verified the persistent wheel: **361960 bytes**, SHA-256 `808e3ee7c1a3f0fe5f98ff0a142e687c46be36edf252619003b0c62e8428f3d9`, **172 unique archive entries** and all **76 source/archive pairs**, including all thirteen SQL schemas, both review assets, all 26 guidance pairs and every changed packaged file. Source/archive bytes, sizes, hashes and relative sibling targets match integrated root. [Report](../reports/ticket-30.md), [manifest](../reports/ticket-30-wheel-manifest.json), [verifier](../reports/verify-ticket-30-wheel.py) and durable root `verification/ticket-30-integrated/wheel-verification.json` retain exact evidence.
- Root review reported no blocking issue. Public suites cover comparable/nonoverlapping windows, sampling/zero/missing/partial baselines, native capture deduplication/time conflicts, policy/expiry/withdrawal, atomic alert/notification rollback, retries/concurrency/authority, real policy-lock contention and HTTP/inbox/restart. Alerts/notifications retain source-free identities and reopen current counts/evidence through the recent owner; no fabricated task events, campaigns or external investigation are introduced.
- Offline configured distinct-native-post sample volume threshold software is complete. This does not establish independent statistical significance, market completeness, live readiness or human usefulness. The worker's completed 722/493.31s PASS preceded its usage interruption; packaging-only resume preserved all 289 frozen files and did not repeat the broad gate. No runtime/test edit, actual source/model/paid call, external message, push, PR, deployment or cleanup occurred. Worker artifacts remain intact for verified root archival with relocation index/hash checks before eventual worktree removal.
