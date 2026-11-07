# S41. Reconcile retained copies and rebuildable projections with operational recovery

Status: planned, no implementation or validation claimed.
Lane: later-proposal
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Operational governance for retained copies and projections. Decisions to chart before implementation: outbox/revision model; projection lag and rebuild; managed storage, backup and restore.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Ingestion/source lifecycle owns dependency truth; projection/storage owners own retained copies and checkpoints; operations owns backup/telemetry
Direct spec blockers: [Improve multilingual retrieval with pinned, rebuildable support](36-evaluated-retrieval.md) (Governs the retrieval index and projections it introduces.), [Move the proven pilot to authenticated workspace tenancy](40-hosted-actors-tenancy.md) (Managed storage, secrets and restore are hosted concerns.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Require actual storage/hosting/backup configuration and defined retention/deletion responsibilities before live cutover.

## User outcome

Hosted projections and retained evidence follow policy changes, bounded lag and tested restore without resurrecting forbidden values.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_ingestion/support/](../../src/smi_ingestion/support/)
- [src/smi_knowledge/publications/](../../src/smi_knowledge/publications/)
- [docs/adr/0002-pinned-support-current-policy.md](../../docs/adr/0002-pinned-support-current-policy.md)
- [docs/adr/0022-promoted-source-lifecycle-inheritance.md](../../docs/adr/0022-promoted-source-lifecycle-inheritance.md)
- [docs/data-model.md](../../docs/data-model.md)

## Scope and non-goals

Add source-owned revision/outbox and idempotent projection consumers only for real asynchronous consumers. Define managed evidence storage/encryption/retention, deletion ownership, backup/restore and source/projection health. Choose CDC/specialized governance tools only for demonstrated need.

## Owners, interfaces and data shapes

Each update has workspace/source/dependency revision, effect identity, tombstone/expiry and method version. Projection apply/checkpoint/reconcile/rebuild reads public source ports and records lag/frontier and missed updates. A source correction can flag a consequential result without rewriting its historical inputs. Health distinguishes source unavailable, stale projection, control failure and incomplete deletion.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add owner outbox/checkpoint/dependency records and storage object metadata with governed paths and retention. Migrate local evidence via content/identity verification and explicit cutover receipt, preserving deadlines. Backups and exports need deletion/restore policy, not an unsupported universal purge claim. Update architecture, physical ERD, source integrations, owner rules and recovery runbook.

## UI reads, commands and agent integration

G1/K1/C1/S1/M1 carry current usability/frontier and bounded lag. New index/object copies remain reconstructible from canonical permitted evidence. Agent tools cannot bypass policy by reading raw storage or stale exports.

## Invariants and authorization

Policy denial applies at serving time even if a purge/consumer is delayed. Rebuild applies tombstones before data; all caches/indexes/analytical extracts and monitoring-promoted copies retain dependency identities and tenant/source rights.

## Failure and recovery

Duplicate/out-of-order messages converge by revision. Missing update triggers reconciliation. Restore replays later tombstones before exposure. A failed deletion is a visible operational failure with owner and retry, not a completed compliance assertion.

## Acceptance

### S41-A01

Drop/reorder/duplicate updates, reconcile and verify exact current projection with bounded reported lag.

### S41-A02

Withdraw/expire source evidence across index, object copies, monitoring, graph and analytical extracts; observe no served values while purge is pending.

### S41-A03

Restore an older backup and rebuild; previously forbidden content cannot reappear.

### S41-A04

Perform actual authorized backup/restore and storage retention checks separately from simulated consumer tests.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C07, FR-P06, PROP-23, PROP-26, PROP-27, PROP-30, PROP-31, PROP-32, PROP-34, PROP-35. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
