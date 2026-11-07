# S23. Detect supported engagement changes with comparable measurement ages

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. New quantitative method whose statistical design is open and depends on W02 and probe data. Decisions to chart before implementation: statistic and comparability rule; age tolerance and minimum sample; metric evidence fields through the source owner; young-age labelling under W02.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_monitoring quantitative methods own calculations; ingestion/recent own metric evidence and acquisition capability
Direct spec blockers: [Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility](19-monitoring-depth-and-timing.md) (Consumes the metrics_retrieved_at and saturation projections and the live-page eligibility rule.), [Describe usable source routes and bounded selection policy](11-source-capabilities.md) (Metric capability per route comes from the registry.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Require configured metric/capture-age capability and method thresholds. r2's six-hour/36/12 examples are illustrative, not defaults or evidence that a provider supports them.

## User outcome

A marketer can inspect an engagement spike based on comparable native metric observations rather than a volume proxy.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_monitoring/alerts/store.py](../../src/smi_monitoring/alerts/store.py)
- [src/smi_monitoring/recent/store.py](../../src/smi_monitoring/recent/store.py)
- [tests/test_recent_monitoring.py](../../tests/test_recent_monitoring.py)
- [docs/monitoring.md](../../docs/monitoring.md)

## Scope and non-goals

Add matched-age native engagement assessment and source-free alert/history integration. Keep metric, age tolerance, minimum sample and significance policy configured/versioned. Do not assume the installed one-page recent-X response supplies six-hour follow-up measurements. For live X, measurement age is metrics_retrieved_at minus published_at (an upper bound), comparable within a configured tolerance bounded by cadence and indexing delay; the result is labelled young-age engagement. This method version is registered only under an accepted W02; otherwise live engagement reports measurement_time_unknown. Six-hour re-measurement is a later path that needs a separately authorized operation and is not in the pilot. Chart and M1 integration follow the integration rule.

## Owners, interfaces and data shapes

Proposed EngagementAlerts.assess(detection_id, baseline_id, MetricDefinition, actor, request_id). MetricDefinition includes platform/native name/unit, statistic, reference age and tolerance, missing-value policy and comparability rule. Recent metric support retains observed_at, post publication time, metric measurement time/age and source ID. Additional measurement acquisition needs a separately activated bounded route/operation, never an implicit read-side refresh. Return exact support sets, denominator, missing count, comparable status and configured result.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add owner-owned metric-assessment and source-free alert references plus metric evidence fields only through their natural source owner. Pin method/config/input digest and preserve old volume history. Update monitoring, evidence, source integrations, ERD, evaluation and owner rules.

## UI reads, commands and agent integration

Register idempotent runtime assessment after a complete supported window. M1/history chart consumes native metric value/unit/age/sample, alert details expose original and baseline evidence. Missing capability displays unassessable with a precise readiness reason.

## Invariants and authorization

Never pool likes with views or snapshots of incompatible ages/routes. Duplicate native posts do not inflate sample. Human task approval and operator monitoring activation stay independent. A sample comparison does not establish population growth.

## Failure and recovery

Missing timestamp/metric/baseline or partial sampling withholds a spike claim. Method invalidity and current-policy loss remove derived comparison values. Unknown extra acquisition response retains its liability without repeating the call.

## Acceptance

### S23-A01

Assess a known comparable fixture through public operations and reproduce its median/statistic from exact observed inputs and denominator.

### S23-A02

Mix native metric names, capture ages, overlapping posts, partial windows and unknown measurement times; observe unassessable reasons, never silent pooling.

### S23-A03

Race duplicate runtime assessment/restart and observe one assessment/alert identity.

### S23-A04

Withdraw one required metric input and observe chart/alert withholding. Actual X metric access and capture-age feasibility remain S31 readiness evidence.

### S23-A05

A live-shaped window pair yields a matched-age comparison under the live version and measurement_time_unknown under the rejected-decision configuration.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C02, PROP-09, PROP-17, PROP-33, R2-STREAM. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
