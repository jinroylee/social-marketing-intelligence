# Operational implementation tickets

## Goal

Continue approved tickets 11–39 sequentially using fresh implementer worktrees, public-interface TDD, real PostgreSQL, simulated I/O, dependency/merge/shared-check gates, final standards/spec review against the original starting commit, and local tracker completion. Preserve completed tickets 01–10. Keep live verification and genuine human review prerequisites honest.

## Next Step

Implement ticket 25 in its fresh context/worktree, connect explicit live schedule activation to existing allowance/spending/freshness controls, then merge and validate before advancing. Tickets 11–24 are integrated and resolved; actual live runtime prerequisites remain separate and unmet.

## Current Phase

Phase 29 — ticket 25 in progress after successful ticket 24 integration. The completed first batch and its reviews are preserved; approved continuation remains tickets 11–39.

### Phase 1 — Read the source and inspect implementation seams

**Status:** complete

Read the full source spec, to-tickets instructions, repository rules, domain vocabulary, accepted ADRs, public ingestion/knowledge/campaign/review interfaces, prior tests, and previous verification findings. No source issue or comments exist because the source is a local document.

### Phase 2 — Draft and audit the breakdown

**Status:** complete

Draft individual tickets outside the published issues directory. Keep them explicitly draft until the required user review. Cover all 70 stories and T01–T30, record direct blockers only, and explain the largest scope boundaries.

Completed 39 per-ticket drafts (9 small, 30 medium), 233 observable acceptance criteria, a numbered breakdown with blocker rationale, and full story/scenario traceability. Validated topological order, no cycles or redundant transitive blocking edges, exact blocker titles, links, source coverage, draft status, and no implementation paths/code snippets in tickets. Documentation and whitespace checks pass. Shared checks stop at the unchanged baseline ingestion defect now scoped in ticket 01; pytest does not start.

### Phase 3 — Review and publish

**Status:** complete

Present the numbered title/blocker/deliverable list and ask about granularity, dependencies, and merges/splits as required by to-tickets. Publish approved tickets in dependency order, with ready-for-agent and the required local or native tracker edges. Do not close or modify a parent issue.

## Decisions Made

| Decision | Reason |
| --- | --- |
| Cover the whole spec rather than the first milestone alone | The user passed the whole implementation spec for conversion. |
| Prepare one draft file per proposed ticket before asking for review | Approval should concern concrete, reviewable work; no ready-for-agent ticket publication before skill-required review. |
| Keep offline delivery separate from live enablement | Source/model access and spending configuration must not be silently assumed. |
| Avoid horizontal migrations/API/UI work packages | Each product ticket delivers an observable behavior through its required layers. |
| Separate the existing completion defect from feature implementation | The current shared check and runner contract are already broken; restore a green baseline first. |

## Errors Encountered

| Error | Resolution |
| --- | --- |
| Tracker setup was not supplied and GitHub CLI has no authenticated account | Resolved by the user-approved local Markdown tracker configuration; no external tracker was needed. |
| An edit patch repeated the manifest file in separate operations and was rejected before mutation | Combined the manifest edits into one file operation; the corrected patch and artifact audit passed. |
| Shared checks stop at the pre-existing undefined completion value | Kept runtime code unchanged and made its repair the first ticket. Direct documentation checks pass; no fresh pytest pass is claimed. |

## Approved implementation batch

Starting commit: `6220fff49b5b8e982ef5a8d54b7c788e45b0f648`. Integration branch: `integration/operational-tickets-01-10`. User explicitly approved local publication, testing boundaries, routine decisions and autonomous resolution. Real test PostgreSQL is reachable. Tickets after 10 remain draft.

### Phase 4 — Implement ticket 01

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `11bc6cbe9c25fde9443b2785dbf5482b2ae18c0a`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **209 tests in 132.74 seconds**. All acceptance criteria are checked and local ticket 01 is resolved.

### Phase 5 — Implement ticket 02

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `09f3d18d9a4195c8f14fd670e51c1b157a7f2ced`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **223 tests in 128.48 seconds**. All acceptance criteria are checked and local ticket 02 is resolved.

### Phase 6 — Implement ticket 03

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `e3e55d3e89684bf3a5696d3caf0c1d257dde107c`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **235 tests in 126.73 seconds**. All acceptance criteria are checked and local ticket 03 is resolved.

### Phase 7 — Implement ticket 04

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `a27b433cdac2ba1d23fe409bb0f15aff65f82b4c`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **248 tests in 132.96 seconds**. All acceptance criteria are checked and local ticket 04 is resolved.

### Phase 8 — Implement ticket 05

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `7ba1c46fe1b355afb6f2e42e703e0079fc359f3d`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **256 tests in 148.43 seconds**. All acceptance criteria are checked and local ticket 05 is resolved.

### Phase 9 — Implement ticket 06

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `19b65407b2b52082314916f2a744f54bd6bc1cf2`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **263 tests in 145.93 seconds**. All acceptance criteria are checked and local ticket 06 is resolved.

### Phase 10 — Implement ticket 07

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `b8c232945859cf40b1c1ec1340dbcad66aee32f2`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **278 tests in 144.00 seconds**. All acceptance criteria are checked and local ticket 07 is resolved.

### Phase 11 — Implement ticket 08

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `96754561b3c39caa8f31c102a9eeda671ddc735e`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **291 tests in 164.22 seconds**. All acceptance criteria are checked and local ticket 08 is resolved.

### Phase 12 — Implement ticket 09

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `02f931faba0fb5a2136b01141a92031646c40224`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **301 tests in 165.55 seconds**. All acceptance criteria are checked and local ticket 09 is resolved.

### Phase 13 — Implement ticket 10

**Status:** complete

Implemented in a fresh worktree and fast-forward integrated as `ce86f8caaf36d0be3c5fc01dc8b5553f6d525c7f`. The integration worktree passed `UV_OFFLINE=1 uv run --locked python tools/check.py`, including **315 tests in 193.21 seconds**. All acceptance criteria are checked and local ticket 10 is resolved.

### Phase 14 — Final standards/spec review and fixes

**Status:** complete

Review the integration branch against the starting commit with independent standards/spec reviewers, resolve all actionable findings through one implementer worktree, run shared checks, and clean up implementer worktrees.

Final review repairs `0831737` passed the integration shared check with **325 tests in 269.09 seconds**. Standards: 3 addressed/0 remaining. Spec: 1 addressed/0 remaining. Cleanup and the final report are complete; no ticket after 10 was started.

## Approved continuation

The user requested all remaining tickets in the exact same manner. Tickets 11–39 are published in the local tracker; the continuation integration branch starts at `532e6072b37bad64049345bae630ef6fb193a78a`. The original review baseline remains `6220fff49b5b8e982ef5a8d54b7c788e45b0f648`. All first-batch evidence remains in execution-manifest.json and reports/final.md. Current scope and gates are recorded in continuation-manifest.json. No live operation or fabricated human validation is authorized.

### Phase 15 — Implement ticket 11

**Status:** complete

Fast-forward integrated `e31e823e527ba9903daa5aab6e10c6cb02a145b9`. The root integration gate `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **338 tests in 207.81 seconds**; the worker wheel matches all six changed runtime/schema files. All acceptance criteria are checked and local ticket 11 is resolved.

### Phase 16 — Implement ticket 12

**Status:** complete

Fast-forward integrated `7d42792ab0f65ab58bd72c9f20bb433c04d3b337`. The root integration gate `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **342 tests in 216.08 seconds**; the worker wheel matches all seven changed runtime/schema/asset files. All acceptance criteria are checked and local ticket 12 is resolved.

### Phase 17 — Implement ticket 13

**Status:** complete

Fast-forward integrated `2420af1de46a1756d370914a555ae826e574a306`. Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **381 tests in 253.68 seconds**; the worker wheel matches all 20 listed changed packaged files. All acceptance criteria are checked and local ticket 13 is resolved. Primary-contract verification and concrete disabled-by-default provider software are complete; live credentials/rates/configuration/readiness and human quality remain unestablished.

### Phase 18 — Implement ticket 14

**Status:** complete

Fast-forward integrated `b9f371db5dccf13e13d8491cc31e94745d5b761f`. Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **391 tests in 251.61 seconds**; the worker wheel matches all 22 changed packaged files. All acceptance criteria are checked and local ticket 14 is resolved. Current-KB comparison adds no new model/source dispatch or automatic shortlist save.

### Phase 19 — Implement ticket 15

**Status:** complete

Fast-forward integrated final head `567236079b3573daacbef9bd67379d793e7261f2` (runtime implementation `a80da4dca903b95d2c9aa9fe6bf8f845a6415a4c`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **404 tests in 262.27 seconds**; the worker wheel matches all nine changed packaged files. All acceptance criteria are checked and local ticket 15 is resolved. Automatic deterministic persistence records actual automation without human endorsement.

### Phase 20 — Implement ticket 16

**Status:** complete

Fast-forward integrated final head `650950bf2f80ad53488e3bc11b1fee12063f975b` (runtime implementation `285d7b2f9f80100f18de48c0356d13d5d597fbe2`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **443 tests in 511.85 seconds**; the completed gate and independently verified 19-file wheel were preserved across the usage interruption without reruns. All acceptance criteria are checked and local ticket 16 is resolved.

### Phase 21 — Implement ticket 17

**Status:** complete

Fast-forward integrated final head `4a879845fc9b6aba0ad8dc0b600d4daea67fe8d5` (runtime `f6c0380741b1e0126c0d0864166e1fdb5ff1c14e`, worker checked merge `9fc164fca493a43bc15e26da42a7033bd73fd1c6`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **452 tests in 290.70 seconds**; the wheel hash and all eight packaged files match the integrated tree. All acceptance criteria are checked and local ticket 17 is resolved.

### Phase 22 — Implement ticket 18

**Status:** complete

Fast-forward integrated final head `6f8668e0910500f04d7912cd4c9fb5cb3396996d` (runtime `4255116ba1924337d6f539073d7806d22950574c`, worker checked merge `46ac45930723bd6246f32154ebd2695e34cbb194`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **469 tests in 297.61 seconds**; the wheel hash and all 27 packaged entries match integrated source bytes, sizes, hashes and declared symlink targets. All acceptance criteria are checked and local ticket 18 is resolved.

### Phase 23 — Implement ticket 19

**Status:** complete

Fast-forward integrated final head `4c2d844418115c239bcadca4c93a378b9b4f7bae` (runtime `f715f4151460e64adcc8e69a6548db8018e4a885`, worker checked merge `c1fdf76f0c88a0388f6f3f3e0de6b3e0676d21bc`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **490 tests in 321.22 seconds**; the completed gate and independent 24-entry wheel verification were preserved across the usage interruption without reruns. All acceptance criteria are checked and local ticket 19 is resolved.

### Phase 24 — Implement ticket 20

**Status:** complete

Fast-forward integrated final head `b22bdf316710f161f092b2959f113ea1285e06ef` (runtime `c81b5e02cd052bf66f317dd53abdbe9a2ff51ba6`, worker checked merge `44409a4e42a2281aed19837e903ba628adb97e85`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **511 tests in 369.33 seconds**; the wheel hash and all 23 packaged entries match integrated source bytes, sizes, hashes and declared symlink targets. All acceptance criteria are checked and local ticket 20 is resolved.

### Phase 25 — Implement ticket 21

**Status:** complete

Fast-forward integrated final head `dbadd45a9327b02fd9ca707aea65bc5001b0614c` (runtime `de7d01220109d4db200b6b66e17209f871803681`, worker checked merge `b027f0f6e9ed615a5452ebcd406344d0ee1ae801`). Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **535 tests in 453.56 seconds**; wheel hash and all 24 packaged entries match integrated bytes, sizes, hashes and declared symlink targets. All acceptance criteria are checked and local ticket 21 is resolved.

### Phase 26 — Implement ticket 22

**Status:** complete

Fast-forward integrated final head `5cc5aa245d77e66f9bb739d3b9eda8d425b210ec` with final corrected runtime/frozen commit `cfceca281bcf0310cd16350707fdc36d7a1df4f7`. Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **549 tests in 510.97 seconds**; final wheel size/hash and all 27 entries match integrated bytes, sizes, hashes and declared symlink targets. All acceptance criteria are checked and local ticket 22 is resolved. The superseded initial gate is not completion evidence.

### Phase 27 — Implement ticket 23

**Status:** complete

Fast-forward integrated final head `74ac5997380b67c6a417b72475a9be9b4f483b10` with runtime/frozen checked commit `195eb279a1ce5a4bab52347fcd890c0c8699eee2`. Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **577 tests in 615.05 seconds**; wheel size/hash and all 31 entries match integrated bytes, sizes, hashes and declared symlink targets. All acceptance criteria are checked and local ticket 23 is resolved. Avoidance retains exact query/input/context and capture-freshness limits, without a concurrent cross-task exactly-once retrieval claim.

### Phase 28 — Implement ticket 24

**Status:** complete

Fast-forward integrated final head `9e9b604dd8f17b9a1449f3d260939ded6206439f` with corrected runtime/frozen `7308c5cb7645302859c9058d8e626cffdef54d4e`. Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static checks, PostgreSQL preflight and **619 tests in 624.35 seconds**; final wheel size/hash and all 41 entries match integrated source/archive bytes, sizes, hashes and declared symlink targets. All technical criteria are checked and local ticket 24 is resolved. Primary-contract/software verification is complete; actual runtime gates and live receipt remain unmet, without readiness or human-quality claims.

### Phase 29 — Implement ticket 25

**Status:** in_progress

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 30 — Implement ticket 26

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 31 — Implement ticket 27

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 32 — Implement ticket 28

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 33 — Implement ticket 29

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 34 — Implement ticket 30

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 35 — Implement ticket 31

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 36 — Implement ticket 32

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 37 — Implement ticket 33

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 38 — Implement ticket 34

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 39 — Implement ticket 35

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 40 — Implement ticket 36

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 41 — Implement ticket 37

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 42 — Implement ticket 38

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 43 — Implement ticket 39

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 44 — Continuation final standards/spec review and cleanup

**Status:** pending

Review against the original starting baseline, address findings in one fresh implementer context, verify integration, remove clean merged implementer worktrees, and report completed work plus genuine external blockers.
