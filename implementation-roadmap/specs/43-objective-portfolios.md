# S43. Compare objective-specific creator factors and feasible portfolios

Status: planned, no implementation or validation claimed.
Lane: later-proposal
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Creator factor and portfolio modelling. Decisions to chart before implementation: factor evidence contracts; portfolio feasibility model; overlap and uncertainty handling.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_campaigns owns factor/profile/portfolio decisions; source owners own audience/performance/commercial evidence
Direct spec blockers: [Improve multilingual retrieval with pinned, rebuildable support](36-evaluated-retrieval.md) (Factor retrieval depth.), [Add evidenced multimodal and richer ontology concepts](42-multimodal-ontology.md) (Richer creator concepts.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer compares creators and portfolio scenarios using supported costs, overlap, constraints and uncertainty.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_campaigns/ranking/](../../src/smi_campaigns/ranking/)
- [src/smi_campaigns/planning/](../../src/smi_campaigns/planning/)
- [docs/campaigns.md](../../docs/campaigns.md)
- [POPOSAL.md](../../POPOSAL.md)

## Scope and non-goals

Add factor evidence contracts for audience, collaboration, performance, cost, availability and authenticity risk only when data exists. Extend visible ranking profiles and deterministic portfolio feasibility. No inferred fees, availability, sales performance or consent.

## Owners, interfaces and data shapes

Factor includes metric definition/population/time/source/method, interval/unknown policy and exact support. Profile version preserves human hard constraints. PortfolioScenario pins candidate/shortlist/profile/factor versions, budget/currency/period, overlap assumptions, objective and feasibility/unknown reasons. Deterministic services own sums/constraints; model judgments remain bounded and validated.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add versioned factor and portfolio tables with exact dependencies and source-free retained decision metadata. Keep incomplete-account eligibility for exploratory recommendation. Update campaigns, planning, evaluation, ERD, architecture and domain glossary only for accepted terms.

## UI reads, commands and agent integration

C1 compares individual fit separately from portfolio fit and exposes unknown feasibility. UI may save a proposed scenario internally; no creator contact/contract/campaign activation occurs. Agent tools may compare and save under normal internal authority, never invent availability.

## Invariants and authorization

Do not pool incompatible audience metrics or double count overlap. A feasible budget scenario is not a guaranteed price or performance claim. Source-dependent copied rationale follows full-input policy.

## Failure and recovery

Missing commercial support returns unknown/not-feasible-under-stated-policy, not zero cost. Factor corrections create new assessments; historical scenario remains pinned. Conflicting rates/currencies require explicit selection or refusal.

## Acceptance

### S43-A01

Reproduce a small portfolio's constraints and objective with exact supported factors and inspect all assumptions.

### S43-A02

Remove fee/audience/overlap support and observe explicit unknown feasibility instead of invented values.

### S43-A03

Revise profile or source facts and observe historical scenario unchanged until explicit regeneration.

### S43-A04

Obtain actual objective-specific usefulness review before effectiveness claims or default optimization.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A02, OFR-A01, PROP-10, PROP-11, PROP-17, PROP-24. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
