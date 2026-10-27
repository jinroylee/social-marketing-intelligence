# 29: Collect bounded recent X evidence offline

**What to build:** An operator can configure an X monitoring topic, run a bounded offline collection window, and inspect retained recent observations independently of the full KB.

**Blocked by:** 01: Restore ingestion completion and safe resume.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One deterministic recent-X route, one topic/window collection journey, and retention/policy-aware timeline; no alerts, live provider, or full KB ingestion.

- [x] Persist monitoring topic configuration separately from scheduled keywords with explicit cadence/window, bounded collection, source policy, and retention settings.
- [x] A public bounded poll entry point retains recent observations with stable source references/identities, capture/publication times, window coverage, and acquisition context.
- [x] The topic/window/timeline surface reopens observations after restart without creating campaigns or requiring knowledge publications for every post.
- [x] Retries do not duplicate a logical window's observations; missing fields and incomplete coverage remain visible.
- [x] Process/display/retention permissions, expiry, and withdrawal govern retained monitoring copies and their detail views.
- [x] Offline integration tests prohibit external I/O and prove existing frozen-snapshot investigations keep their original independent behavior.

**Spec coverage:** user stories 47, 48, 53, 54, 56, 57, 68, 69; acceptance scenarios T08, T24, T26, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

- Runtime `4aa3535eb5ba3987b9e7aa93b888665e808d7197`; latest integration merged and frozen at `51ce0aec6ca3c83d43991f9492c3c970ef3a8830`.
- Required offline locked shared check passed exit 0: **706 tests in 480.99s**, completed session `19612`; persistent worktree `verification/ticket-29/shared.{json,log}` records exact execution evidence.
- Offline wheel and 72 exact source/archive pairs verified, covering all changed packaged files, 12 SQL schemas, both review assets and 25 packaged guidance pairs. See [the implementer report](../reports/ticket-29.md), manifest and standalone verifier.
- At worker handoff, status was **claimed** pending independent integration verification and merger-owned resolution; completed evidence follows. No runtime/test/product-doc/guidance edit followed freeze; no live call, paid operation, external message, push, PR, deployment or cleanup occurred.


## Completion

- Runtime implementation: `4aa3535eb5ba3987b9e7aa93b888665e808d7197`; actual frozen worker checked merge: `51ce0aec6ca3c83d43991f9492c3c970ef3a8830`. Final worker handoff and root integrated checked commit: `80c3329e8428efcebe3fa1f0fba682f66c7beda7`, fast-forward integrated from clean `2e037cfd25e35fa10424d46641014a43e81f67de`. Frozen-to-final changes are only this checklist/handoff, the ticket's report and exact verification manifest/verifier.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **706 tests in 483.80 seconds**, exit **0**, session `65481`. Durable root `.scratch/operational-implementation/verification/ticket-29-integrated/shared.{started,finished,head,runtime,worker-frozen,command,session,log,exit}` retains execution identity/status. Worker and earlier completed gates were preserved; all six criteria are checked.
- Independently verified the existing persistent wheel: **351118 bytes**, SHA-256 `f09819f8e80a4c1a1e93c86b18a6a6316ebb684976b92da9fa5d3640e3dba690`, **166 unique archive entries** and all **72 source/archive pairs**, including all twelve SQL schemas, both assets, all 25 guidance pairs and every changed packaged file. Bytes, sizes, hashes and relative sibling targets match integrated root. [Report](../reports/ticket-29.md), [exact manifest](../reports/ticket-29-wheel-manifest.json), [verifier](../reports/verify-ticket-29-wheel.py) and durable root `verification/ticket-29-integrated/wheel-verification.json` retain exact evidence.
- Root alias-purge finding is closed by native/original-source-time identity, label-independent content fingerprinting and deduplication. Public overlapping-window regression proves renamed labels cannot reconstruct purged bodies or reset first import/retention; true later captures stay distinct and changed values within one capture conflict. Future source-time validation remains public-tested. Final 26-case owner, 51-case compatibility and root 706-test PASS cover the repaired bytes; no blocking root finding remains.
- Bounded offline recent-X topic/window/timeline software is complete with current policy, retention, withdrawal, stable retries and original acquisition/source-time distinctions. Existing frozen investigations retain their independent behavior. No alerts, live route or full-KB promotion was added; no market completeness, trend, live-readiness or human-quality claim is made. No actual source/model/paid call, external message, push, PR, deployment or cleanup occurred. Worker artifacts remain intact; eventual cleanup first requires verified archival into root persistent verification with a relocation index and hash checks.
