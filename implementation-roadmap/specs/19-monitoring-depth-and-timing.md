# S19. Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Projections of stored receipt fields plus a live-page rule whose semantics and acceptance are fully specified.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_monitoring.recent owns window projections; smi_monitoring.alerts and smi_monitoring.semantic own the new live-page method versions
Direct spec blockers: [Restore a complete, time-stable verification baseline](01-stable-verification-clock.md) (Changes the recent, alerts and semantic owners whose suites must be green; cadence stays a topic-revision setting, so there is no configuration edge.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Live-page method versions are enabled only under an accepted W02. Saturation semantics follow the U3 choice.

## User outcome

Live X windows state their saturation and receipt-time bounds truthfully and, under an accepted W02, produce honest live volume and controversy outcomes inside ADR 0023's one-page rule.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_monitoring/polling/route.py](../../src/smi_monitoring/polling/route.py)
- [src/smi_monitoring/recent/store.py](../../src/smi_monitoring/recent/store.py)
- [src/smi_monitoring/alerts/store.py](../../src/smi_monitoring/alerts/store.py)
- [src/smi_monitoring/semantic/method.py](../../src/smi_monitoring/semantic/method.py)
- [docs/adr/0019-source-free-quantitative-alert-history.md](../../docs/adr/0019-source-free-quantitative-alert-history.md)
- [docs/adr/0023-bounded-recent-x-poll-authority.md](../../docs/adr/0023-bounded-recent-x-poll-authority.md)
- [tests/test_live_recent.py](../../tests/test_live_recent.py)

## Scope and non-goals

(1) Project the stored acquisition.pagination_remaining as a typed collection_saturated limitation on window, volume and semantic reads. (2) Project the stored acquisition.retrieved_at (receipt time) as metrics_retrieved_at with its elapsed_seconds bound on live windows; offline and fixture windows report it as unrecorded; no column and no backfill write. (3) Add a separately versioned live-page eligibility rule to the volume and controversy owners: an unsaturated live page is a complete sample of the provider's recent-search results for the literal query, with market coverage unknown; receipt time bounds unknown capture and measurement times from above; a saturated window supports only a lower-bound crossing claim; a non-crossing result on a saturated window, and any saturated baseline, is not_assessable with collection_saturated. (4) Provide a shared live-shaped fixture builder that reproduces XRecentRoute.collect's receipt (declared_coverage partial, unknown capture time, pagination_remaining true or false). (5) Draft the W02 amendment text for ADR 0019, ADR 0023 and docs/monitoring.md. Non-goals: pagination or the counts endpoint (U3); global cadence configuration (cadence stays a topic-revision setting); rewriting stored coverage; recomputing existing assessments.

## Owners, interfaces and data shapes

Window reads gain collection_saturated: bool | null and metrics_retrieved_at plus retrieval_bound_seconds, where null means unrecorded. The method version is pinned on each assessment. The live-page versions are registered only when W02 is accepted; installed v1 behavior is unchanged.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No schema column and no backfill. Version the new method rules alongside the installed ones. Update docs/monitoring.md, the monitoring owner instructions and, once W02 is accepted, the ADR 0019/0023 amendments.

## UI reads, commands and agent integration

S20, S21, S23 and S24 consume the projections, the live-page eligibility rule and the shared live-shaped fixture builder.

## Invariants and authorization

One page per window stays the ADR 0023 rule; a remaining page is a limitation, never a pagination loop. Receipt time is never presented as a capture or source timestamp.

## Failure and recovery

Unknown poll responses keep their liability. A legacy window without a receipt stays unrecorded and is never assigned a time.

## Acceptance

### S19-A01

A live-shaped unsaturated window and a comparable live-shaped baseline yield significant_change or no_change under the live-page volume version, and still not_assessable (collection_incomplete) under installed v1.

### S19-A02

A saturated detection window over an unsaturated baseline yields an increase only when its lower bound meets the threshold, labelled as a lower bound; a saturated baseline or a saturated non-crossing result is not_assessable with collection_saturated. The same rule holds for the controversy method's thresholds.

### S19-A03

Live windows expose metrics_retrieved_at from the stored receipt and offline windows report it as unrecorded; it is never presented as capture time, and no schema column is added.

### S19-A04

Regression: cadence alignment, revision pinning and forced reactivation behave exactly as installed.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C01, FR-C02, FR-C03, FR-P09, OFR-C01, R2-STREAM. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
