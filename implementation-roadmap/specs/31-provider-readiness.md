# S31. Record live discovery, model and recurring-work readiness

Status: planned, no implementation or validation claimed.
Lane: live-validation
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Operator readiness row with a fixed record format.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Named local operator plus source, model, monitoring, costs and notification maintainers
Direct spec blockers: [Probe bounded live model, discovery, X and email-provider feasibility early](05-live-feasibility-probes.md) (Reuses the probe authorizations and record format.), [Run bounded local work continuously with restart, health and lifecycle maintenance](09-local-runtime.md) (Recurring keyword discovery needs the runtime.), [Inspect and operate independent spending controls](26-spending-operations.md) (Reconciles this capability's actual charges through operator controls.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Blocked until actual account permissions, provider/model and recipient/sender configuration, defensible charge bounds or explicit forecast classification, credentials and live-run/send authorization exist. Human/operator completion evidence is mandatory.

## User outcome

The pilot can truthfully state whether live keyword discovery, the model and recurring keyword work are permitted, usable and metered, with actual bounded receipts.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [docs/source-integrations.md](../../docs/source-integrations.md)
- [docs/costs.md](../../docs/costs.md)
- [docs/evaluation.md](../../docs/evaluation.md)
- [tests/test_live_discovery.py](../../tests/test_live_discovery.py)
- [docs/roadmap.md](../../docs/roadmap.md)

## Scope and non-goals

The final signed-off readiness row for keyword discovery, the model and recurring keyword work. Keep the S05 record format, owner and invariants, link the matching probe row and state what changed since the probe. Other capabilities have their own rows: S32, S33 and S34. No prices or readiness are inferred from test fixtures.

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

### S31-A01

Actual authorized keyword discovery and model receipts reopen usable permitted publications and answers through public owners.

### S31-A02

Recurring keyword discovery runs with finite bounds and refuses on source policy or ceiling, with no fifty-post throughput claim.

### S31-A03

Actual provider-basis charges reconcile against exact operations, or remain recorded as unknown.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-S01, OFR-S01, OFR-S03, OFR-E03, PROP-28, UD-02. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
