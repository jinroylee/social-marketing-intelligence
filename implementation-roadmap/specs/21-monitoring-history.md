# S21. Plot current and selected monitoring windows without fabricated data

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. On-read projection and SVG chart with precise missing/zero/latest/lower-bound semantics and a given registration signature.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_monitoring history projection composes current governed window/method readers; smi_review owns chart and equivalent table
Direct spec blockers: [Operate independent topics, activation and alert history](20-monitoring-workspace.md) (The chart is a view of topic windows and alert history composed in M1.), [Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility](19-monitoring-depth-and-timing.md) (The chart renders saturated windows as lower bounds from the window projection.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer sees the stream over time, recognizes the latest interval and inspects an older selected interval's own support.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_monitoring/recent/store.py](../../src/smi_monitoring/recent/store.py)
- [src/smi_monitoring/alerts/store.py](../../src/smi_monitoring/alerts/store.py)
- [src/smi_monitoring/semantic/store.py](../../src/smi_monitoring/semantic/store.py)
- [.scratch/product-design-2026-11/task3/r2/design-spec.md](../../.scratch/product-design-2026-11/task3/r2/design-spec.md)

## Scope and non-goals

Implement R2-STREAM bounded history pages, metric selector, current/latest highlight, independent selected-window shading, evidence links and keyboard/table alternative. Render engagement/shift as unavailable until S23/S24 return real method results. No fixture numeric defaults.

## Owners, interfaces and data shapes

Proposed MonitoringHistory.read(topic, actor, metric_key, from_time, to_time, cursor, limit) returns UTC intervals, status collected/missing/not_scheduled/partial/unavailable, latest_window_id, metric definition/version/unit/capture-age, value or null, exact numerator/denominator/support IDs, method/baseline/comparability state and policy frontier. Response declares actual loaded interval and gaps. Cursor binds scope/frontier. Values reopen current policy and method validity on every read. This spec owns the chart-series reducer and defines a method-series registration contract register(method_key, version, read_points(topic, from, to, cursor)), where each point carries a value or null, unit, denominator, support IDs and comparability.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Prefer an on-read projection over recent and assessment owners. Add source-free expected-interval metadata only where activation/attempt history cannot distinguish missed from unscheduled. No copied quantitative claims. Update monitoring, local-review, architecture and ERD if metadata is added.

## UI reads, commands and agent integration

Chart and selected summary consume the same returned object. Posts, matched-age likes, coded-negative percentage and controversy-input count have separate support sets/denominators. UTC proportional spacing, axis units, latest marker, selected shading and a selectable table are mandatory. Saturated windows render as lower bounds (>=N) with a distinct marker in chart and table. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Unknown/missing is null, never zero. A real zero is labelled zero eligible observations in this bounded sample. Break lines at missing, unloaded and nonadjacent intervals. Invalid semantic method withholds derived points while permitted original evidence stays inspectable. Missing baseline withholds comparison, not a valid snapshot.

## Failure and recovery

Expired cursor/filter change restarts history. Stale requests cannot replace selected-window state. Withdrawal clears dependent values and aggregates; latest identity never becomes an older selected interval. Do not interpolate or pool native metrics.

## Acceptance

### S21-A01

Use irregular windows containing missing, not-scheduled, observed zero and partial states; chart and table agree and lines break correctly.

### S21-A02

Select an older point and observe its own evidence while latest remains highlighted; paginate without inventing unloaded values.

### S21-A03

Remove a baseline and invalidate a semantic method; retain valid original snapshot values while withholding affected comparisons/derived points.

### S21-A04

Withdraw an input and observe policy-safe history, summary and evidence. Deliver the S25 checklist for keyboard selection, latest/selected/gap behavior and EN/KO metric-state stability.

### S21-A05

A stub method registered through the contract appears in the selector and table with its own denominators, with no chart-code change. Live-shaped saturated windows render as lower bounds in both chart and table.

### S21-A06

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C02, FR-C03, FR-C05, FR-C06, OFR-C01, PROP-15, PROP-27, UD-03, UD-07, R2-STREAM. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
