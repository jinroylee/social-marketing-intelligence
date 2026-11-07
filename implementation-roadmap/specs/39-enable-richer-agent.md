# S39. Enable only the accepted grounded research and synthesis contract

Status: planned, no implementation or validation claimed.
Lane: decision-blocked
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Implements whatever W01 decides; scope is undefined until then. Decisions to chart before implementation: production contracts chosen by W01; error and abstention policy; runtime and provider readiness for new models.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_assistant owns accepted synthesis/plan behavior; tasks owns every approved external step; review owns K1/A1 UI
Direct spec blockers: [Obtain actual adjudication for the richer-agent successor](38-agent-human-evidence.md) (Acceptance needs actual adjudication evidence.)
Direct decision blockers: [Set the richer research and synthesis boundary](../decisions/001-richer-agent-boundary.md) (W01)
Configuration or actual-evidence prerequisites: Actual successor decision, validated method/error policy and runtime/provider readiness for any new model are required.

## User outcome

Marketers use the accepted richer assistant while retaining exact human external approval and governed evidence.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_assistant/](../../src/smi_assistant/)
- [src/smi_tasks/assistant/](../../src/smi_tasks/assistant/)
- [docs/adr/0017-exact-supported-answers.md](../../docs/adr/0017-exact-supported-answers.md)
- [docs/adr/0018-explicit-assistant-gap-scope.md](../../docs/adr/0018-explicit-assistant-gap-scope.md)

## Scope and non-goals

Implement only the successor behavior actually chosen in the decision issue. Current candidate recommendation is non-authoritative. This spec cannot execute until S38 evidence and the actual decision are accepted.

## Owners, interfaces and data shapes

Adopt the chosen ResearchDraft/SynthesisCandidate interfaces as versioned production contracts. Pin exact context, every claim and full model input; expose validator/method version, withheld claims and gaps. Task execution accepts only immutable saved scopes with attributable approval, and each step rechecks remaining bounds/current policy/cost. Any new executable scope requires a new exact approval.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Migrate candidate records only by explicit reviewed promotion retaining original provenance; never relabel historical extractive answers. Record actual successor ADRs/glossary definitions and update knowledge, tasks, architecture, ERD, evaluation and local-review together. Delete candidate-only APIs after callers migrate.

## UI reads, commands and agent integration

Conventional chat may present validated prose and explicit research drafts only if chosen. Claim inspector resolves current support. Async status/events remain task-owned; publication enables later explicit questions. Monitoring context stays KB-only.

## Invariants and authorization

A model cannot self-approve, impersonate configured campaign/schedule authority, override spending or treat a prior conversational yes as approval. Production streaming withholds factual tokens until validation or remains disabled.

## Failure and recovery

Withhold unsupported claims/full answers, preserve partial uncertainty and exact retry identity. Unknown paid response waits. Policy loss removes every dependent result including unselected-input influence. No fallback can be labelled validated synthesis without passing the accepted contract.

## Acceptance

### S39-A01

Run the accepted adversarial and held-out review set through public conversation/tool operations with its actual accepted thresholds and denominators.

### S39-A02

Approve one plan scope, modify one step and observe refusal/new approval requirement before any call.

### S39-A03

Exercise no evidence, contradictions, policy loss, model/validator/meter failure and interrupted execution with no unpublished answers or duplicate paid reissue.

### S39-A04

Obtain actual enabling acceptance for the exact successor build before removing experimental labels.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-B01, FR-B02, FR-B03, FR-B04, FR-B05, FR-B07, FR-C04, FR-P08, OFR-B02, PROP-05, PROP-17, UD-04, R2-CHAT. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
