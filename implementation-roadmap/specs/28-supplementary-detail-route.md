# S28. Task-integrate one named supplementary detail route

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. One named route integrated as plan steps; fields come from the probe and U4.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_ingestion adapters own the route and evidence; smi_tasks plan steps own execution
Direct spec blockers: [Plan finite field-capability acquisition steps and stop honestly](27-progressive-acquisition.md) (The route executes as plan steps under the plan model's scope and stop rules.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Live use requires the Bright Data probe row and the final readiness record; U4 for any web route.

## User outcome

A plan step can collect one named kind of supplementary detail evidence for an approved subject within finite cost and request bounds.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_ingestion/adapters/bright_data.py](../../src/smi_ingestion/adapters/bright_data.py)
- [src/smi_ingestion/adapters/registry.py](../../src/smi_ingestion/adapters/registry.py)
- [src/smi_tasks/supplementation/policy.py](../../src/smi_tasks/supplementation/policy.py)

## Scope and non-goals

Task-integrate one named route. The default is Bright Data profile/post detail fields (follower count, post metrics, post history window), with exact fields fixed by the Bright Data row of S05. tiktok-web only if the user grants source use (U4); oEmbed is limited to identity and title. Non-goal: a multi-provider route catalog.

## Owners, interfaces and data shapes

Proposed capability entry with exact field/subject/billing and allowed parent scope, registered in the S11 registry, executed as an AcquisitionPlan step with request/record/byte/charge bounds.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add route-specific evidence fields only with explicit legacy-unrecorded migration. Update source integrations, costs and adapter instructions.

## UI reads, commands and agent integration

The pipeline renders the detail step, its field support and stop reason. New support follows ingestion/publication before any answer or ranking.

## Invariants and authorization

Each step stays inside the approved parent scope and independent spending/novelty admission. Namespaces from this route stay separate from keyword captures.

## Failure and recovery

Pending, ambiguous or failed responses are never blindly retried. An unsupported field is explicitly unavailable.

## Acceptance

### S28-A01

A broad-plus-detail task records one supplementary observation per step within cost and request bounds.

### S28-A02

Pending, ambiguous or failed responses are never blindly retried.

### S28-A03

Namespaces stay separate from keyword captures and no capture age is refreshed by matching.

### S28-A04

An unsupported field is explicitly unavailable.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-P04, FR-P06, PROP-23. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
