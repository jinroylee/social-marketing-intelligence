# Operational implementation tickets

## Goal

Continue approved tickets 11–39 sequentially using fresh implementer worktrees, public-interface TDD, real PostgreSQL, simulated I/O, dependency/merge/shared-check gates, final standards/spec review against the original starting commit, and local tracker completion. Preserve completed tickets 01–10. Keep live verification and genuine human review prerequisites honest.

## Next Step

Implement ticket 14 in its fresh context/worktree, then merge and validate before advancing. Tickets 11–13 are integrated and resolved.

## Current Phase

Phase 18 — ticket 14 in progress after successful ticket 13 integration. The completed first batch and its reviews are preserved; approved continuation remains tickets 11–39.

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

**Status:** in_progress

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 19 — Implement ticket 15

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 20 — Implement ticket 16

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 21 — Implement ticket 17

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 22 — Implement ticket 18

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 23 — Implement ticket 19

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 24 — Implement ticket 20

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 25 — Implement ticket 21

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 26 — Implement ticket 22

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 27 — Implement ticket 23

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 28 — Implement ticket 24

**Status:** pending

Fresh implementer context/worktree; public TDD; exact acceptance and external prerequisites; integration shared-check gate before resolution and the next dependent ticket.

### Phase 29 — Implement ticket 25

**Status:** pending

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
