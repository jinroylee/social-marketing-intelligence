# S45. Estimate incremental effect only under an accepted causal design

Status: planned, no implementation or validation claimed.
Lane: later-proposal
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Causal study design. Decisions to chart before implementation: study design per decision; estimand and identification strategy; diagnostics and withholding rules.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Measurement/causal-method owner plus actual experiment/data/domain owners
Direct spec blockers: [Measure actual outcomes and rule-based attribution](44-outcomes-attribution.md) (Needs observed outcomes and attribution.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Actual feasible study design, sufficient authorized outcome/assignment data and method-owner/human approval are required. This is not a pilot release blocker.

## User outcome

A marketer can distinguish descriptive attribution from justified incremental effect and inspect assumptions and uncertainty.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [docs/planning.md](../../docs/planning.md)
- [POPOSAL.md](../../POPOSAL.md)
- [docs/evaluation.md](../../docs/evaluation.md)

## Scope and non-goals

Design randomized user/geographic experiments where feasible, or separately justified quasi-experimental/calibrated marketing-mix methods. Choose a method for actual data/decision needs. No universal causal engine or automatic lift from engagement.

## Owners, interfaces and data shapes

CausalStudy pins decision, eligible population/market, assignment or identification strategy, treatment/exposure/outcome windows, access/consent, estimand, confounding/spillover assumptions, method/code version, diagnostics and uncertainty. Public fit/read operations withhold claims when prerequisites/diagnostics fail. Experiment activation outside the internal system needs separate authorization.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add study/run/diagnostic/support tables only after the actual design is reviewed. Reuse governed outcomes and keep attribution runs distinct. Update accepted measurement ADR/glossary, evaluation, architecture/ERD and module instructions for the chosen method.

## UI reads, commands and agent integration

Measurement UI presents design/assumptions/diagnostics and clearly labelled incremental estimates. Assistant tools may read accepted study results with support, not infer causality from correlation or activate external experiments.

## Invariants and authorization

Randomization, observational identification and marketing-mix calibration are distinct evidence bases. Data sufficiency, access and method review precede claims. A descriptive performance chart cannot substitute for identification.

## Failure and recovery

Missing assignment/outcome support or failed diagnostics withholds causal claims. Reanalysis pins new data/method revisions. Source loss and study corrections propagate through dependent estimates and answers.

## Acceptance

### S45-A01

For the chosen method, reproduce assignment/eligibility or identification diagnostics and exact estimand from governed actual input.

### S45-A02

Use negative controls/placebos or randomized checks appropriate to that method and retain failed diagnostics.

### S45-A03

Record uncertainty, sensitivity and actual expert/domain review with no invented lift metric.

### S45-A04

Verify public UI/tools never label rule-based attribution or engagement change as causal effect.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-X01, PROP-13, PROP-14, PROP-15, PROP-33. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
