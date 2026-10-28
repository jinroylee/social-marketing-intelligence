# 33: Promote selected monitoring evidence into knowledge

**What to build:** An operator can deliberately promote selected permitted recent X observations through normal ingestion and publication, with traceable origins.

**Blocked by:** 02: Publish and inspect permitted ingested support; 29: Collect bounded recent X evidence offline.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One local selected-observation promotion path; do not fetch new data or publish the whole feed automatically.

- [x] A trusted explicit selection creates normal source observations/canonical mappings where supported and usable knowledge publications with links back to the monitoring inputs.
- [x] Promotion preserves source policy, capture times, native identities/namespaces, metric semantics, mapper versions, and unknown identity fields.
- [x] Retrying the same promotion does not duplicate canonical effects or logical publications.
- [x] No additional provider request or campaign is created; unselected observations remain solely in the bounded monitoring evidence path.
- [x] Monitoring and KB/alert copies honor their applicable retention, expiry, and withdrawal dependencies without using promotion to bypass denied support.
- [x] A local selection/result surface and public integration tests verify lineage, repeat promotion, partial invalid records, and policy changes.

**Spec coverage:** user stories 45, 53, 55, 56, 68; acceptance scenarios T08, T20, T27 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

- Runtime implementation: `67c58b6dab6bfa0db7a0a02693d7be9c6d96ad02`; latest integration metadata merged before clean frozen checked head `48cc8052cb604c6c5872ccdc1a7215a8e8c1556e`.
- Required offline locked shared gate **passed exit 0**, **794 tests in 731.13s**, completed session **78065**. Durable worker `verification/ticket-33/shared.{json,log}` records exact command/head/start/finish/session/exit. No completed unchanged gate was repeated.
- Offline wheel independently verified: **397759 bytes**, **192 unique entries**, SHA-256 `890aeafc00bd710601770833479d2b32742a42dfbf911c01023fb741da02441a`; **88 source/archive pairs**, including sixteen SQL schemas, both review assets and all 29 packaged guidance pairs. [Report](../reports/ticket-33.md), [exact manifest](../reports/ticket-33-wheel-manifest.json) and [verifier](../reports/verify-ticket-33-wheel.py) retain reviewable evidence.
- All acceptance criteria have local public-operation/HTTP evidence. At worker handoff, the issue was **claimed** pending independent merger gating, artifact verification and resolution; completed evidence follows. No runtime/test/product-doc/guidance change followed frozen PASS; only this handoff, own report and exact manifest/verifier metadata changed. Artifacts remain in the persistent worker worktree for verified root archival/relocation before eventual cleanup. No live source/model/paid call, external message, push, PR, deployment or cleanup occurred; no human-language, marketer-usefulness or live-readiness claim is made.


## Completion

- Runtime implementation: `67c58b6dab6bfa0db7a0a02693d7be9c6d96ad02`; frozen worker checked merge: `48cc8052cb604c6c5872ccdc1a7215a8e8c1556e`. Final worker handoff and root integrated checked commit: `3f9d1050c23d25c8757855141ab1284cffdca746`, fast-forward integrated from clean `8a519fff96836c5bb3c40b8b0765ecc3d00f6400`. Frozen-to-final changes are exactly four own scratch handoff files. All 285 protected file bytes/sizes/hashes/relative targets independently match integrated root.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **794 tests in 700.00 seconds**, exit **0**, session `20417`. Durable root `.scratch/operational-implementation/verification/ticket-33-integrated/shared.{started,finished,head,runtime,worker-frozen,command,session,log,exit}` retains exact identity/status. Worker 794/731.13s and earlier completed gates were preserved without rerun; all six criteria are checked.
- Independently verified existing wheel **397759 bytes**, SHA-256 `890aeafc00bd710601770833479d2b32742a42dfbf911c01023fb741da02441a`, **192 unique entries**, all **88 source/archive pairs**, sixteen SQL schemas, both review assets and all 29 guidance pairs. Root guidance also matches exact bytes/hash/relative target. [Report](../reports/ticket-33.md), [manifest](../reports/ticket-33-wheel-manifest.json), [verifier](../reports/verify-ticket-33-wheel.py) and durable root `verification/ticket-33-integrated/wheel-verification.json` retain exact evidence.
- Root-reviewed source-as-of, public-port and workspace reconciliation corrections are complete: absent original source-as-of/identity remain unknown; ingestion-owned `SourceDependencies` composes monitoring lifecycle mutations without private sibling access; reconciliation stays workspace scoped. Public 19-case journey coverage, focused 87/56.03s and root 794-test PASS cover normal mapping/publication, direct KB policy/withdrawal/expiry, partial invalid selection, repeated/concurrent promotion, atomic rollback and lock isolation. No blocking root finding remains.
- Promotion is one trusted explicit selected-capture path with original acquisition/times, native metric meanings and policy/retention lineage. It records zero new provider requests, creates no task/campaign, leaves unselected evidence in monitoring and prevents purged support from being reconstructed by retries, aliases or new requests. No live-readiness, original-language or marketer-usefulness claim is made; actual live configuration/authorization/commercial receipts and human quality remain unestablished.
- Coordinator-created persistent root archive for worker 33 is preserved and independently identity-verified: **369596 bytes**, **38 entries**, SHA-256 `9b13f15039e674a87cf29bbc9b6e6898a018c3c49a6d75b969b2c714dd97d0d1`; excluded `verification/worker-archives/relocation-index.json` retains original paths/member hashes. Existing committed relocation report for 26–32 is untouched; all worker 33 files remain. No runtime/test edit, actual source/model/paid call, external message, push, PR, deployment, archive/index mutation or cleanup occurred in merger resolution.
