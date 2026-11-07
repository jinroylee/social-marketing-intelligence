# S34. Record email send readiness

Status: planned, no implementation or validation claimed.
Lane: live-validation
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Operator readiness row with a fixed record format.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Named local operator plus source, model, monitoring, costs and notification maintainers
Direct spec blockers: [Probe bounded live model, discovery, X and email-provider feasibility early](05-live-feasibility-probes.md) (Reuses the email-provider row.), [Deliver durable task and alert notifications through inbox and email](29-inbox-email.md) (The transport, delivery identity and inbox under test.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Requires the operator mailbox account (U7) and explicit send authorization.

## User outcome

The pilot can truthfully state whether notification email reaches the configured recipient through the configured transport.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/notifications/store.py](../../src/smi_tasks/notifications/store.py)
- [docs/user-guide.md](../../docs/user-guide.md)

## Scope and non-goals

The readiness row for the S29 transport. Keep the S05 record format, owner and invariants, link the matching probe row and state what changed since the probe.

## Owners, interfaces and data shapes

Create a signed-off readiness record per capability/version with operator, workspace, account/permission basis, configuration digest, permitted test scope, actual request/response/evidence IDs, final billing basis and unresolved portions. Link exact owner operations and exclude secrets. Verify supplementary metric capture-age support, broad/detail route field semantics and recurring activation in their real account context.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No feature migration. Store actual operational records in their owner-approved evidence locations with governed retention. Update source-integrations, costs, monitoring, evaluation and roadmap only for demonstrated facts, never for planned tests.

## UI reads, commands and agent integration

Capability screens report passed/blocked/unknown per route and retain simulated labels elsewhere. Validate email to an explicitly authorized recipient and actual local-link access. Activate a keyword/topic only with exact recorded authority after its prerequisites pass.

## Invariants and authorization

A successful HTTP response is not permission, final bill, useful publication, semantic quality or delivery receipt. Commercial hard ceilings require defensible per-call charge bounds/provider caps. Forecast-only routes cannot claim strict enforcement. This planning package authorizes no calls or email.

## Failure and recovery

Unknown response or charge records liability and pauses reissue. Provider rejection/schema drift records a blocked capability without inventing replacement data. Reconciliation does not recover response. Failed metric readiness blocks that live method, not the already built code or unrelated capabilities.

## Acceptance

### S34-A01

One explicitly authorized test email goes to the configured recipient.

### S34-A02

Provider acceptance and actual recipient receipt are recorded separately.

### S34-A03

The governed link is verified from the intended access context.

### S34-A04

Uncertain-delivery handling is exercised with a simulated failure only, with no extra live sends.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C05, UD-05. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
