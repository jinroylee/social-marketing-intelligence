# S22. Investigate alerts with existing KB context and promote selected evidence

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. M2 UI over installed context and promotion owners.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_monitoring context and promotion retain their contracts; smi_review renders M2
Direct spec blockers: [Operate independent topics, activation and alert history](20-monitoring-workspace.md) (Investigation and promotion start from an alert and window selected in M1.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer investigates an alert using only existing KB context and selectively promotes useful observations through normal ingestion.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_monitoring/context/](../../src/smi_monitoring/context/)
- [src/smi_monitoring/promotion/](../../src/smi_monitoring/promotion/)
- [tests/test_monitoring_promotion.py](../../tests/test_monitoring_promotion.py)

## Scope and non-goals

Deliver KB-only investigation and exact promotion review over installed context and promotion owners. Rich contextual prose stays later work.

## Owners, interfaces and data shapes

M2 composes context.investigate/read and promotion.promote/read with exact alert, window and observation selections, request IDs and trusted operator context.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Reuse monitoring owner tables. Add public bounded list/history adapters rather than querying another owner's SQL. Update monitoring and local-review contracts.

## UI reads, commands and agent integration

Context explanation pins the original recent alert plus the existing published KB selection; an empty KB is an explicit context gap. Promotion selects exact members, then normal ingestion/publication with inherited source identity and deadline. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Investigate makes zero external calls and creates no campaign. Promotion creates no unsupported Creator/product identity association or renewed age.

## Failure and recovery

Expired or withdrawn promotion cannot reconstruct copied evidence after permission restoration. Withheld context keeps source-free historical identity.

## Acceptance

### S22-A01

Investigate an alert with empty and then populated existing KB and assert zero collector calls and no new campaign.

### S22-A02

Promote selected observations, then withdraw/expire originals and observe inherited denial in independent KB, graph and campaign readers.

### S22-A03

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C04, FR-C07, PROP-04, PROP-07, UD-08. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
