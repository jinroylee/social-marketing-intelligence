# S08. Check shortlist and answer usefulness with a marketer on real discovered data

Status: planned, no implementation or validation claimed.
Lane: human-validation
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Human-run procedure with pre-declared outcomes and a fixed record format.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Actual pilot marketer and a KR/JP reader, supported by the campaign, knowledge and assistant maintainers
Direct spec blockers: [Probe bounded live model, discovery, X and email-provider feasibility early](05-live-feasibility-probes.md) (Requires passed model and Bright Data keyword rows and the bounded discovery corpus under U1.), [Publish catalog-scoped caption interpretations from automated tasks](06-automated-interpretation.md) (Discovered posts must carry published mention interpretations.), [Select question-, brief- and graph-scoped governed support at pilot scale](07-pilot-scale-retrieval.md) (Shortlists and answers must use pilot-scale, question-scoped retrieval.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Requires an actual marketer, a KR/JP reader, the model and Bright Data keyword rows of the live probes passed, and the bounded discovery corpus authorized under U1.

## User outcome

Early, on real discovered data, a marketer and a KR/JP reader judge whether shortlists, mention judgments and extractive answers are useful, so S06 and S07 can change before the campaign and chat UIs are built.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [docs/evaluation.md](../../docs/evaluation.md)
- [src/smi_review/quality/](../../src/smi_review/quality/)
- [.scratch/product-design-2026-11/ui-review-status.md](../../.scratch/product-design-2026-11/ui-review-status.md)

## Scope and non-goals

Under U1 caps, the operator runs the bounded live keyword-discovery corpus through the installed live task path with automated interpretation. The reviewers grade about 10 briefs' shortlists and about 10 questions' supporting findings, including EN and KO questions over KR/JP captions, through whatever UI exists at that build (legacy forms and CLI expected; the new campaign and chat screens if they have landed). Record denominators, precision@k for supporting findings (no threshold claimed) and mention-judgment errors. Pre-declared outcomes: retrieval fails -> revise the S07 ranking rule or pull a named subset of S36 forward before S15 lands; mention judgments fail -> revise the S06 catalog rules. Non-goals: UI review (S25, S35); release gating.

## Owners, interfaces and data shapes

Record reviewer, language, build and configuration digest and live provenance under the quality owner's attributable review contract, plus per-item grades and denominators.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No production schema change beyond quality-owner records. Update docs/evaluation.md with the actual checkpoint outcome and unresolved gaps.

## UI reads, commands and agent integration

Each triggered pre-declared outcome is filed against its owning spec's execution issue. Results are inputs to S35.

## Invariants and authorization

A model, fixture or coordinator cannot stand in for the marketer. Design approval and agent checks are not this checkpoint.

## Failure and recovery

A failed journey keeps its failing examples and owner; fixes re-run the affected journey rather than rewriting the record.

## Acceptance

### S08-A01

Named reviewers, build and configuration identity, and live data provenance are recorded.

### S08-A02

Each brief and question is graded with its denominator, and failing examples are kept.

### S08-A03

Precision@k for supporting findings and mention-judgment error counts are recorded per language.

### S08-A04

Each triggered pre-declared outcome is filed against its owning spec's execution issue with the declared action.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A01, FR-B01, OFR-E01, PROP-03, PROP-16. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
