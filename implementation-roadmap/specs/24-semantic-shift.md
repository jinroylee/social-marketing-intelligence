# S24. Detect provisional semantic shifts with a comparable baseline

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. L-sized LLM method with an independent validator and baseline rules. Decisions to chart before implementation: coding vocabulary, prompt and output schema; independent validator design; baseline comparability (language mix, sample); evaluation case design.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_monitoring semantic methods own coding and baseline comparison; shared responses/cost ports own model I/O
Direct spec blockers: [Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility](19-monitoring-depth-and-timing.md) (Baseline-aware comparison reuses the live-page eligibility rule and saturation limitation rather than a second definition.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer inspects a provisional semantic/sentiment shift and a possible controversy without confusing either with verified public opinion.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_monitoring/semantic/store.py](../../src/smi_monitoring/semantic/store.py)
- [src/smi_monitoring/semantic/AGENTS.md](../../src/smi_monitoring/semantic/AGENTS.md)
- [docs/adr/0020-bounded-semantic-positions-full-input-policy.md](../../docs/adr/0020-bounded-semantic-positions-full-input-policy.md)

## Scope and non-goals

Keep installed no-baseline controversy method intact. Add a separately versioned baseline-aware semantic coding and change method with evidence spans, language/sample comparability and explicit validation states. This closes core FR-C03, not an optional proposal lane.

## Owners, interfaces and data shapes

Proposed SemanticShift.assess(detection_window, baseline_window, actor, request_id, configured_method). Pin every actual text input, coding vocabulary, exact source spans, model/schema/prompt/threshold versions and usage. Independent validator checks membership, complete coding coverage, span accuracy, output bounds and baseline comparability. Deterministic comparison computes numerator/denominator and percentage-point difference. Semantic correctness and language quality require named evaluation.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add semantic_shift_assessments, input references and source-free alert identities without source prose caches. Retained coded judgments inherit full-input purge/withholding. Extend context/history/notifications via public typed method results, preserving old method IDs. Update monitoring, ERD, evaluation and a successor/additive ADR if the reviewed trade-off meets ADR criteria.

## UI reads, commands and agent integration

Runtime registers exact-window/method assessment. M1 shows provisional codes, ambiguous/unresolved cases, language mix, both samples and missing baseline. Chart, M1 and inbox integration follow the integration rule.

## Invariants and authorization

Citation/span validity is not semantic entailment or human usefulness. Same scope, route, coding method and language mixture are prerequisites for change claims. Full model input, including unresolved/unselected members, governs every saved judgment. No acquisition from investigate.

## Failure and recovery

Invalid/ambiguous/incomplete output withholds derived signal and preserves bounded failure/usage. No model reissue after uncertain response. Input withdrawal permanently clears dependent retained positions according to current lifecycle contracts. No baseline yields snapshot only.

## Acceptance

### S24-A01

Use explicit comparable windows with known coding counts and reproduce the change and denominators through public reads.

### S24-A02

Reject alien input IDs, inaccurate spans, missing members, mismatched language/sample methods and missing baselines; retain precise limitations.

### S24-A03

Exercise model/meter failure, interruption and loss of an unresolved input; observe no duplicate charge and no surviving derived point.

### S24-A04

A live-shaped window pair is assessed under the live-page eligibility rule, and a saturated baseline is not assessable.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C03, PROP-09, PROP-17, PROP-33, R2-STREAM. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
