# Decide live X window comparability and receipt-time semantics

Issue: W02
Labels: wayfinder:grilling
Parent: [Route from the installed system to the approved intelligence workspace](000-product-map.md)
Assignee: unassigned. No resolution is claimed by planning.
Status: open, actual human direction pending. Ask at plan start.
Blockers: none among decision issues.
Blocks: none (no build or validation spec). Informs [Make live X windows comparable](../specs/19-monitoring-depth-and-timing.md), [engagement anomalies](../specs/23-engagement-anomalies.md) and [semantic shift](../specs/24-semantic-shift.md); its state is recorded by [monitoring readiness](../specs/32-monitoring-readiness.md).
External evidence: the X row of [the live probes](../specs/05-live-feasibility-probes.md) and the amendment text drafted by the monitoring-depth spec.

## Question

The installed live X route stores every window as `partial` with unknown capture and metric-measurement times, and the installed volume and controversy methods accept only `complete` windows (ADR 0019, ADR 0020, `docs/monitoring.md`). As a result no live alert can fire. For live X windows:

1. May the recorded response receipt time bound capture time and metric measurement time from above?
2. May an unsaturated single page (no `next_token`) count as a complete sample of the provider's recent-search results for the literal query, with market coverage still unknown?
3. May a saturated window support only lower-bound crossing claims, with a saturated baseline or a saturated non-crossing result reported as not assessable?

Accepting these amends ADR 0019, ADR 0023 and `docs/monitoring.md` through new, separately versioned method rules; installed v1 behavior and history stay unchanged.

Recommended default: accept all three as a narrowly scoped amendment. If rejected, live windows stay not assessable, there are no live alerts and no live engagement, and monitoring readiness records `blocked_by_decision`. The build proceeds either way; the recommendation is not consent.

## Evidence and assets

- [Monitoring contract](../../docs/monitoring.md), [ADR 0019](../../docs/adr/0019-source-free-quantitative-alert-history.md) and [ADR 0023](../../docs/adr/0023-bounded-recent-x-poll-authority.md).
- [Round-2 review](../../.scratch/product-design-2026-11/history/spec-review/round-2/review.md) R2-F01 and [validation](../../.scratch/product-design-2026-11/history/spec-review/round-2/validation.md) decision table 4e.

## Comments

Charted in round 1 as a metric-time question blocking engagement; widened and made non-blocking in round 2. No human answer has been recorded.
