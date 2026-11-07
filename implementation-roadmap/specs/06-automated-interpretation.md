# S06. Publish catalog-scoped caption interpretations from automated tasks

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Port signature, ordering before publication and failure state are pinned; one worker/knowledge change.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_knowledge owns the support-based interpretation port; the smi_tasks worker composes it before publication
Direct spec blockers: [Restore a complete, time-stable verification baseline](01-stable-verification-clock.md) (Changes task publication behavior covered by the existing worker suites.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

Task-discovered posts carry published brand/product interpretations, so campaign criteria and graph mention edges work on real data.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/worker.py](../../src/smi_tasks/worker.py)
- [src/smi_knowledge/publications/store.py](../../src/smi_knowledge/publications/store.py)
- [src/smi_knowledge/store.py](../../src/smi_knowledge/store.py)
- [src/smi_knowledge/queries/store.py](../../src/smi_knowledge/queries/store.py)
- [src/smi_campaigns/comparison.py](../../src/smi_campaigns/comparison.py)

## Scope and non-goals

Add a support-based interpretation port (the existing KnowledgeStore.prepare reads frozen datasets only). The worker interprets prepared support against the workspace's active catalogs inside its TaskExecution, before the publication transaction, and publishes members and claims together with interpretation_ids. On interpretation failure the members still publish with an explicit interpretation_failed coverage state. Non-goals: model-based interpretation; new catalog semantics.

## Owners, interfaces and data shapes

Proposed KnowledgeStore.prepare_support(support: tuple[SupportReference, ...], catalog_ids, actor, *, request_id, connection) -> interpretation IDs and coverage. Idempotent request identity is task + catalog + method version. An explicit re-interpretation creates a successor publication, and queries de-duplicate the same observation/derivation by preferring the newest current publication.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Schema change only if interpretation status needs a column on task coverage. Update docs/knowledge.md, docs/tasks.md, the ERD and the knowledge/tasks owner instructions in the same change.

## UI reads, commands and agent integration

Campaign comparison, graph mention edges and chat support read the published claims through existing public query operations. No UI change beyond coverage display.

## Invariants and authorization

Interpretation is deterministic rule work with no external I/O inside the fenced worker. It never asserts Creator identity, endorsement or causation, and a withdrawn source purges its interpretation copies.

## Failure and recovery

A crash between interpretation and publication resumes on the same request identity without duplicate claims. A forced failure never blocks member publication.

## Acceptance

### S06-A01

A keyword task over a corpus that mentions a registered brand yields supported claims in the query result, and the member is no longer flagged caption_interpretations_not_published.

### S06-A02

A forced interpretation failure still publishes the members and reports interpretation_failed.

### S06-A03

A re-interpretation never produces duplicate members in search.

### S06-A04

A crash between interpretation and publication recovers without duplicate claims.

### S06-A05

A withdrawn source purges its interpretation copies from new reads.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A02, FR-A03, FR-G02, PROP-17. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
