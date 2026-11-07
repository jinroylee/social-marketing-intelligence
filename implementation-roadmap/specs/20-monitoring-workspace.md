# S20. Operate independent topics, activation and alert history

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. M1 UI composing installed recent, polling and alert owners.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_monitoring recent/polling/alerts/semantic retain their separate contracts; smi_review renders M1
Direct spec blockers: [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (M1 renders windows and alerts through the shell and inspector.), [Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility](19-monitoring-depth-and-timing.md) (M1 shows saturation, receipt-time bounds and live-page method outcomes unconditionally.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer configures and explicitly activates an independent topic and inspects its windows, alert history and original alert evidence.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_monitoring/recent/store.py](../../src/smi_monitoring/recent/store.py)
- [src/smi_monitoring/polling/store.py](../../src/smi_monitoring/polling/store.py)
- [src/smi_monitoring/context/](../../src/smi_monitoring/context/)
- [src/smi_monitoring/promotion/](../../src/smi_monitoring/promotion/)
- [tests/test_recent_monitoring.py](../../tests/test_recent_monitoring.py)
- [tests/test_monitoring_promotion.py](../../tests/test_monitoring_promotion.py)

## Scope and non-goals

Deliver topic revision/activation/pause, method/cadence/bounds/retention controls, actual last collection and health, alert history and snapshots. Start with installed volume and provisional controversy; register S23/S24 methods when available. Investigation and promotion are S22.

## Owners, interfaces and data shapes

M1 composes RecentMonitoring.configure/read_topic/read_window/timeline, RecentPolling.activate/deactivate/read, quantitative/semantic readers and snapshot MonitoringStore. New adapters require exact topic version, window/alert selections, request IDs and trusted operator context. Preserve source publication, capture, metric measurement and import times independently.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Reuse monitoring owner tables. Add public bounded list/history adapters rather than querying another owner's SQL. Update monitoring, local-review, source integrations and owner instructions; ERD only for necessary new indexes/columns.

## UI reads, commands and agent integration

Monitoring is accessible with no campaign or populated KB. Saturation, receipt-time bounds and live-page method outcomes from S19 are shown unconditionally; S23 and S24 method registration follows the integration rule. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Saving topic settings grants no recurring live authority. Configuration edits require fresh activation.

## Failure and recovery

Unknown poll response stays waiting with liability. Pause leaves in-flight history intact. A withheld alert keeps source-free historical identity.

## Acceptance

### S20-A01

Operate a topic without a campaign or KB, detect a bounded volume/controversy sample and inspect method/window/coverage.

### S20-A02

Change topic revision and observe old activation blocked until explicit reactivation; pause and resume without duplicate logical intervals.

### S20-A03

A live-shaped window from the S19 builder shows its saturation and receipt-time limitation and the live-page method outcome in M1.

### S20-A04

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C01, FR-C02, FR-C03, FR-C05, FR-C06, FR-P09, OFR-C01, OFR-E03, PROP-01, PROP-06, PROP-09, PROP-25. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
