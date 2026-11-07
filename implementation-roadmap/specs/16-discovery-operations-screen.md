# S16. Configure scheduled discovery and see route and runtime health

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. One screen over public reads from the registry, schedules and runtime health.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_review owns the D1 screen; ScheduledDiscovery, SourceCapabilities and LocalRuntime keep their logic behind public ports
Direct spec blockers: [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (D1 renders in the shell with the shared inspector.), [Describe usable source routes and bounded selection policy](11-source-capabilities.md) (Route capability, readiness and selection basis come from the registry.), [Run bounded local work continuously with restart, health and lifecycle maintenance](09-local-runtime.md) (Last tick, per-component health and next due come from the runtime health read.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

In one D1 screen, an operator configures up to ten scheduled keywords and the shared daily allowance, activates schedules as recorded commands, and sees route capability, readiness, selection basis and runtime health.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/schedules/__init__.py](../../src/smi_tasks/schedules/__init__.py)
- [src/smi_review/app.py](../../src/smi_review/app.py)
- [.scratch/product-design-2026-11/task3/r2/design-spec.md](../../.scratch/product-design-2026-11/task3/r2/design-spec.md)

## Scope and non-goals

The r2 D1 screen (ten-keyword limit, recorded activation, day allowance, route health, selection basis) plus runtime health (last tick, per-component health, next due, actual activation). Retire the legacy /schedules form after parity. Non-goals: new scheduling or selection logic; topic activation (S20); spending forms (S26).

## Owners, interfaces and data shapes

/api/v1 reads for schedule settings, occurrences and allowance, per-route capability and readiness, and runtime health; commands to configure or activate a schedule with an expected version and request ID. Installed, access-unknown, permission-denied, configuration-blocked and activated states stay separate.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No business tables. Update docs/local-review.md and the review owner instructions; remove the legacy schedule views and migrate their tests after parity.

## UI reads, commands and agent integration

Reads S11 readiness and S09 health through public ports; schedule activation stays a recorded command under ADR 0015. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Saving settings grants no live authority; activation is an explicit recorded operator command. Configuration edits never alter an existing occurrence's scope or accounting day.

## Failure and recovery

Stale edits conflict and preserve input. A stopped runtime shows stale health rather than last-known-good as current.

## Acceptance

### S16-A01

An eleventh scheduled keyword is refused, the daily cap and occurrence authority are shown truthfully, and configuration edits never alter an existing occurrence's scope.

### S16-A02

Route states display separately from the readiness read, including access-unknown and configuration-blocked.

### S16-A03

When the runtime stops, health turns stale within the configured bound; after restart, the new last tick and next due appear.

### S16-A04

The legacy /schedules routes are removed after their parity tests pass.

### S16-A05

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-L01, FR-P01, FR-P02, OFR-E03, PROP-34, UD-03. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
