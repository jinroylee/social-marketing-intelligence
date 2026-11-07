# S13. Read asynchronous progress and exact pipeline lineage

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Small read model, preferably derived from existing attempt phases; T1 states are fixed.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_tasks owns source-free progress events and task reads; smi_tasks.lineage composes public owners; smi_review renders T1
Direct spec blockers: [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (The T1 timeline opens lineage evidence in the shared inspector.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer can follow an admitted task through retrieval, publication and completion and understand a safe wait or partial failure.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/worker.py](../../src/smi_tasks/worker.py)
- [src/smi_tasks/execution.py](../../src/smi_tasks/execution.py)
- [src/smi_tasks/lineage/](../../src/smi_tasks/lineage/)
- [tests/test_task_concurrency.py](../../tests/test_task_concurrency.py)

## Scope and non-goals

Add bounded task-list filters and resumable progress reads. Display pipeline stages and independent owner read frontiers. No operational action on GET and no global atomic pipeline claim.

## Owners, interfaces and data shapes

Proposed AcquisitionTasks.events(task_id, actor, after_sequence, limit) -> events/cursor/head; TaskLineage.read remains the evidence source. Each progress event has task/attempt/execution identity, sequence, phase, timestamp where recorded, sanitized code and publication receipt ID where committed. The owner may implement events() over the existing acquisition_attempts.phases and adds a table only where cursor or timestamp requirements are unmet. Polling is sufficient; an event stream must resume by cursor and use the same checks.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Prefer derivation from existing attempt phases. If a task-owned task_progress_events table is needed, give it unique task/sequence and effect identity, write it on TaskExecution's ownership connection with each phase commit, and backfill only source-free snapshot markers for legacy tasks, never invented historical phases. Update tasks, architecture, ERD and lineage/review contracts for any actual change.

## UI reads, commands and agent integration

T1 separates accepted, queued, running, retrieved-not-usable, waiting, published, terminal partial/no-update/failure. Cross-links go to governed evidence, cost operations and completion. task.status and task.events tools are read-only. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Keep session fencing, exact attempt/run/prepared support, publication ownership receipts and one completion event. A connected paused worker remains owner. Events contain no source prose, provider handles, paths or credentials.

## Failure and recovery

A cursor behind retained history returns an explicit reset marker. A read failure never resubmits. Unknown external response retains commitment and waiting. A publication committed before completion remains separately visible.

## Acceptance

### S13-A01

Observe events through public reads while a real PostgreSQL worker runs with simulated I/O; reconnect using the cursor without duplicate effects.

### S13-A02

Kill the process before publication acknowledgment and after publication commit; successor reads and resumes the same receipt, attempt and run.

### S13-A03

Exercise partial processing, no-update, denied support and meter waiting. Historical counts remain separate from current usable publication.

### S13-A04

Inspect HTTP payloads for sanitized metadata and actual truncation; reads cause no source dispatch.

### S13-A05

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A07, FR-B08, FR-L01, FR-L02, OFR-P01, OFR-L01, PROP-07, PROP-15. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
