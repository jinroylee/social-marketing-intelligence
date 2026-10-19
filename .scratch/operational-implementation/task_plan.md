# Operational implementation tickets

## Goal

Implement approved tickets 01–10 sequentially in fresh implementer worktrees, merge each into the integration branch, require shared checks before advancing, review the final diff against starting commit 6220fff49b5b8e982ef5a8d54b7c788e45b0f648, resolve review findings, and finish offline/local with all ten local tickets resolved.

## Next Step

Await dispatch of pending ticket 04 in a fresh implementer worktree based on the verified integration tip. Ticket 03 is integrated and resolved; ticket 04 has not started.

## Current Phase

Phase 7 — ticket 04 pending after successful ticket 03 integration; execute tickets 01–10 sequentially within the approved boundaries and local tracker setup.

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
| Tracker setup was not supplied and GitHub CLI has no authenticated account | Drafting continues locally; tell the user to run /setup-matt-pocock-skills before external publication. |
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

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 8 — Implement ticket 05

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 9 — Implement ticket 06

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 10 — Implement ticket 07

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 11 — Implement ticket 08

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 12 — Implement ticket 09

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 13 — Implement ticket 10

**Status:** pending

Fresh implementer worktree, TDD, documented interfaces/schema, local commit, merger integration, shared check, then local ticket resolution.

### Phase 14 — Final standards/spec review and fixes

**Status:** pending

Review the integration branch against the starting commit with independent standards/spec reviewers, resolve all actionable findings through one implementer worktree, run shared checks, and clean up implementer worktrees.
