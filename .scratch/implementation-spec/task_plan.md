# Operational implementation specification

## Goal

Synthesize the accepted A/B/C workflows and shared operational requirements into one reviewable specification using the to-spec template. Do not implement runtime behavior. Publish to the configured issue tracker only after the required test-seam check and tracker access are available.

## Next Step

Resolve the required test-boundary check and configured tracker access, then publish with ready-for-agent. The local specification and documentation checks are complete.

## Current Phase

Phase 3 — awaiting the required user check and tracker setup; the verified local draft is ready.

### Phase 1 — Establish requirements and current implementation

**Status:** complete

Read the referenced handoff, maintained requirements, glossary, ADRs, public module interfaces, and prior integration tests. Confirmed a clean main branch at the start and a GitHub origin.

### Phase 2 — Write and verify the local specification

**Status:** complete

Use the exact to-spec sections, extensive user stories, concrete observable acceptance cases, and no implementation file paths or code snippets in implementation decisions. Add the product documentation index entry and run shared checks.

Completed: 70 stories, 30 acceptance scenarios, six delivery milestones, all seven template sections, no file paths/code snippets in implementation decisions, documentation/link/ERD/symlink checks, and whitespace checks. Full shared check was attempted and stopped at an unrelated pre-existing Ruff failure in HEAD; runtime code was not changed.

### Phase 3 — Check test seams and publish

**Status:** pending

Obtain the test-seam check required by to-spec. Confirm issue-tracker setup and triage vocabulary, restore tracker access, publish the spec with ready-for-agent, and read it back. If unavailable, deliver the verified local spec and state the exact unmet prerequisites.

## Decisions Made

| Decision | Reason |
| --- | --- |
| Cover the full accepted operational product | The user requested synthesis of the existing documents, not implementation of only the first recommended slice. |
| Preserve task-to-knowledge delivery as the first milestone | This supplies a reusable boundary for campaign acquisition and approved assistant enrichment. |
| Prefer public application/domain integration boundaries and real PostgreSQL | Existing suites already prove restart, retry, concurrency and policy behavior at these seams. |
| Keep drafting notes in .scratch and the durable spec in docs | Repository instructions separate product contracts from session tracking. |

## Errors Encountered

| Error | Resolution |
| --- | --- |
| GitHub CLI exits 4 because it is not authenticated | Local drafting continues. Publication requires configured tracker access; do not search for credentials. |
| Shared checks fail at F821: undefined complete in source evidence save, line 170 | Confirmed the same code is present in HEAD and no runtime files changed. Ran documentation checks independently; they passed. Tests did not start because lint stopped the shared command. Report the baseline issue without expanding this specification-only task into a runtime fix. |
