# S05. Probe bounded live model, discovery, X and email-provider feasibility early

Status: planned, no implementation or validation claimed.
Lane: live-validation
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Operator-run procedure with a fixed record format; needs U1 authorization, not design decisions.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Named local operator plus the model, ingestion, monitoring and notification maintainers
Direct spec blockers: [Give the operator recorded commands for cost controls and bounded X polling](03-operator-commands.md) (Every live route refuses until a cost scope and route binding exist, and X also needs a recorded activation; these commands are the only shipped path.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Blocked until the user grants bounded live authorization, credentials, per-capability call counts, the bounded discovery corpus and one spending ceiling (U1). If not granted, the build continues on fixtures and premise-dependent specs stay provisional.

## User outcome

The premises of S19, S23, S28 and S29 are settled by bounded real evidence, and a bounded real discovery corpus exists for S08, before those specs finish.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_ingestion/cli.py](../../src/smi_ingestion/cli.py)
- [src/smi_monitoring/polling/route.py](../../src/smi_monitoring/polling/route.py)
- [src/smi_assistant/answers.py](../../src/smi_assistant/answers.py)
- [docs/source-integrations.md](../../docs/source-integrations.md)
- [docs/costs.md](../../docs/costs.md)

## Scope and non-goals

One independently completable capability row each: model (schema adherence, latency, cost basis); Bright Data keyword (fields, capture times, cost basis, KR/JP yield, and the bounded discovery corpus for S08: up to 10 keywords and a few hundred posts); X recent (one topic activated through S03 for at most the authorized number of windows, recording the saturation rate as the share of windows with next_token, receipt-minus-publication ages, public_metrics fields and counts-endpoint availability for the account tier, ending with a U3 depth recommendation and W02 evidence); email (the chosen transport, by default SMTP submission through the operator mailbox: acceptance-reply semantics and Message-ID handling, with no product send). Non-goals: production readiness claims; fixture substitution.

## Owners, interfaces and data shapes

Each row records operator, authorization, caps, configuration digest, request/response/evidence IDs, billing basis and unresolved portions in the same record format S31 later reuses. Probes run through installed owners composed by S02.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No feature migration. Store probe records in owner-approved evidence locations with governed retention. Update docs/source-integrations.md and docs/monitoring.md only with demonstrated facts.

## UI reads, commands and agent integration

Findings feed the cadence and saturation configuration of S19, the W02 decision, the detail fields of S28 and the retry design of S29. Specs whose premises depend on a row keep those premises marked provisional until that row passes.

## Invariants and authorization

Only explicitly authorized, bounded calls with recorded caps. Probes create no unbounded or unrecorded activation: the X row activates one topic through S03 for at most the U1-authorized number of windows and records its deactivation. A successful HTTP response is not permission, final billing, usefulness or delivery.

## Failure and recovery

Unknown response or charge records liability and pauses reissue. A refused or blocked row is a valid recorded outcome and blocks only claims for that capability.

## Acceptance

### S05-A01

Each capability row has an actual authorized receipt or an explicit refused/blocked state with its reason.

### S05-A02

The X row runs one bounded activation for the authorized number of windows, records its deactivation, saturation rate and measurement ages, and ends with a recorded U3 depth recommendation and W02 evidence.

### S05-A03

The Bright Data row names candidate S28 detail fields and their observed coverage.

### S05-A04

Each billing basis reconciles against recorded commitments or is recorded as unknown.

### S05-A05

The email row names its transport and records acceptance-reply semantics, or a blocked reason.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C01, FR-P04, FR-P09, FR-S01, OFR-S03, PROP-23, PROP-28, UD-05. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
