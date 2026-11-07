# S38. Obtain actual adjudication for the richer-agent successor

Status: planned, no implementation or validation claimed.
Lane: human-validation-later
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Human adjudication procedure; the decisions it informs belong to W01, not to this spec.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Actual domain owner and named KR/JP reviewers; quality owner records evidence
Direct spec blockers: [Prepare a bounded research and synthesis candidate for decision review](37-agent-candidate.md) (Adjudicates the candidate's outputs.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Requires actual reviewers and product/domain-owner time. This task is not blocked on the decision it informs; it must gather evidence first.

## User outcome

The domain owner can decide the proposed research-scope and claim-validation boundary using actual examples and named review evidence.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [docs/evaluation.md](../../docs/evaluation.md)
- [.scratch/product-design-2026-11/task1-recovery/decisions.md](../../.scratch/product-design-2026-11/task1-recovery/decisions.md)

## Scope and non-goals

Review candidate plan drafts, exact approval experience, independent claim checking, abstentions and failures. Obtain real original-language reviews and acceptable error policy. Do not auto-close the wayfinder grilling issue based on packet generation or coordinator opinion.

## Owners, interfaces and data shapes

Record exact candidate/method/model/input versions, reviewer denominators, disagreement, false-support examples and proposed thresholds under the quality contract. Present the full independent product frontier in one human round. The currently open successor-contract issue owns the answers and eventual resolution.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No feature migration. Link actual evidence and the human's wording in the decision issue; map indexes a closed resolution only after a real future exchange. Accepted upstream choices remain external evidence, not newly resolved tickets.

## UI reads, commands and agent integration

Review the target claim inspector and scope-draft editing with actual people. Preserve pilot extractive behavior until the successor is accepted and enabled by S39.

## Invariants and authorization

Source span validity alone cannot pass semantic review. Human approval of a design cannot count as review of a validator or grant all future external task authority.

## Failure and recovery

Missing reviewer or inadequate evidence leaves this validation incomplete and S39 blocked. A human may choose a narrower contract, requiring a candidate/spec revision before enablement.

## Acceptance

### S38-A01

Record named KR/JP review of exact positive, negative and ambiguous candidate claims with all reviewed denominators.

### S38-A02

Record the actual domain owner's decision on model-drafted scope and validated prose, including unresolved method/error-policy choices.

### S38-A03

Keep failed/uncertain judgments and dissent accessible under policy; only the actual resolution closes the decision ticket.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-E01, PROP-16, UD-04. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
