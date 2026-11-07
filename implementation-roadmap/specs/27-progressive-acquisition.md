# S27. Plan finite field-capability acquisition steps and stop honestly

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. L-sized plan/step engine replacing the legacy nickname planner. Decisions to chart before implementation: plan and step schema; information-value estimate and stop rules; cross-route avoidance identity comparison; migration of legacy plan methods.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_tasks.discovery/supplementation own plan decisions and step execution; adapters and source support retain evidence ownership
Direct spec blockers: [Describe usable source routes and bounded selection policy](11-source-capabilities.md) (Steps are planned only over declared route/field capability and selection policy.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A task plans finite broad-plus-detail steps over declared route capability, reuses eligible evidence and stops with a visible reason.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/discovery/history.py](../../src/smi_tasks/discovery/history.py)
- [src/smi_tasks/discovery/policy.py](../../src/smi_tasks/discovery/policy.py)
- [src/smi_tasks/supplementation/](../../src/smi_tasks/supplementation/)
- [src/smi_tasks/worker.py](../../src/smi_tasks/worker.py)
- [tests/test_supplementation.py](../../tests/test_supplementation.py)
- [tests/test_discovery_history.py](../../tests/test_discovery_history.py)

## Scope and non-goals

Generalize the installed one-nickname fill into an AcquisitionPlan/step model with value-based stopping and cross-route avoidance over the existing keyword and nickname routes. The successor-approval path uses installed proposal operations; A1 UI linkage is a conditional check. A new supplementary route is S28.

## Owners, interfaces and data shapes

Proposed AcquisitionPlan contains immutable parent scope digest, capability/selection/value-policy versions, evidence dependencies and finite steps. Step includes exact native target/field/route/purpose, expected information value basis, remaining request/record/byte/charge bound and stop disposition. Plan public operations prepare/read/execute_next use the same TaskExecution connection and checkpoint identity. Broad candidates may be selected only within explicitly approved finite query/subject expansion rules; absent parent authority requires a successor human-approved proposal, not an inferred URL. Generalized reuse compares route/context/query/field/native namespace/capture age/processing/policy support, never semantic identity guesses.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add task-owned plan revisions, steps and source-free value/avoidance decisions referencing source-owned support and cost operation IDs. Preserve existing exact nickname/legacy plan methods, migrate callers to the new public path and retain immutable history without a permanent compatibility layer. Update tasks, source integrations, costs, architecture, ERD and plan owner instructions.

## UI reads, commands and agent integration

Under the integration rule, the S13 pipeline view renders broad/detail choices, field support, estimated value assumptions, remaining bounds, reused support and terminal stop reasons, using the AcquisitionPlan.read model this spec provides. Agent may propose a plan; server validates it and only exact authorized steps execute. New support follows ingestion/publication before any answer or ranking.

## Invariants and authorization

Stop reasons distinguish sufficient/fresh, low marginal value, unavailable capability, denied policy, exhausted hard bounds, monetary refusal and unknown response. Value score is an estimate, not source truth or a guaranteed ROI. Independent spending, novelty admission and source scope remain enforced at each step.

## Failure and recovery

Crash recovery resumes the original step/checkpoint/receipt without paid redispatch. Partial useful primary evidence can publish despite detail failure. Unknown captures, incomplete prior work, changed mapper or withdrawn support prevent unjustified reuse. Prior no-update support is not a new publication.

## Acceptance

### S27-A01

Run a broad-plus-detail task over the keyword and nickname routes through public worker operations and inspect exact step scope, decision support, one supplementary observation and final publication.

### S27-A02

Reject a generated step with new subjects/routes/limits or unapproved identity; verify no source call and an explicit successor-approval path.

### S27-A03

Exercise each stop reason and two routes observing the same native subject without merging namespaces or refreshing capture age.

### S27-A04

Crash before/after step checkpoint and publication; observe original identities, bounded spending and no unknown-response retry. Race tasks against one daily post cap and one cost scope.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A03, FR-B03, FR-B04, FR-B05, FR-P02, FR-P03, FR-P05, FR-P06, FR-P07, FR-S03, PROP-07. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
