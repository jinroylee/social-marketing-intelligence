# S25. Check graph, chart, campaign and chat interaction in a real browser

Status: planned, no implementation or validation claimed.
Lane: human-validation
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Human-run browser checklist with a fixed record format.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: A named human tester, supported by the graph client and monitoring chart maintainers
Direct spec blockers: [Explore the production graph with camera, pins and incremental branches](18-interactive-graph.md) (Graph drag/pin/branch/stale-page behavior under test.), [Plot current and selected monitoring windows without fabricated data](21-monitoring-history.md) (Chart latest/selected/gap behavior under test.), [Complete brief to saved recommendation and explicit regeneration](12-campaign-decisions.md) (The campaign browser checklist under test.), [Save conventional chat threads with question-scoped extractive turns](15-conversations.md) (The chat browser checklist (EN/KO, IME, drafts) under test.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Requires a named human tester with permitted browser use. Agent browser access remains declined unless the user changes U5.

## User outcome

The two client behaviors agents cannot verify while browser access stays declined are checked by a human on the implemented build.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [.scratch/product-design-2026-11/task3/r2/review-guide.md](../../.scratch/product-design-2026-11/task3/r2/review-guide.md)
- [.scratch/product-design-2026-11/ui-review-status.md](../../.scratch/product-design-2026-11/ui-review-status.md)
- [docs/evaluation.md](../../docs/evaluation.md)

## Scope and non-goals

A human executes the S18 and S21 checklists: drag/pin, overlapping branches, stale-page discard, keyboard/list equivalence, reduced motion, chart latest/selected/gap behavior and narrow CJK layouts. Also execute the S12 and S15 browser checklists in EN and KO; the marketer is preferred for those two journeys, otherwise a named human reviewer.

## Owners, interfaces and data shapes

Record build identity, browser and platform, and each checklist item as pass/fail with evidence under the quality owner's attributable review contract.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No production schema change beyond quality-owner records. Update docs/evaluation.md with the actual outcome.

## UI reads, commands and agent integration

Failures are filed against their owning spec. Results feed S35 at the same build identity.

## Invariants and authorization

Agent source checks and Node tests are not this checkpoint. A model cannot be the human tester.

## Failure and recovery

A failed item keeps its evidence and owner; fixes re-run the affected items at the new build identity.

## Acceptance

### S25-A01

The build identity and each checklist item are recorded as pass/fail with evidence.

### S25-A02

Each failure is filed against its owning spec.

### S25-A03

Accessibility observations are recorded separately from functional results.

### S25-A04

Campaign and chat checklists are recorded with per-item pass/fail in EN and KO, with failing examples filed against their owning specs.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A01, FR-B01, FR-G01, UD-01, UD-03, UD-06, UD-07, R2-CHAT, R2-STREAM, R2-GRAPH. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
