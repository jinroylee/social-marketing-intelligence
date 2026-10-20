# 07: Coordinate competing workers without duplicate effects

**What to build:** Multiple workers can process the durable task frontier while an interrupted or stale worker cannot duplicate or overwrite completed work.

**Blocked by:** 06: Recover interrupted tasks and expose partial outcomes.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Claim, handoff, and stale-worker protection for the established task lifecycle; do not introduce a distributed broker or general workflow engine.

- [x] Competing public worker claims grant one active execution authority for the same task phase and expose queued/running/recoverable state accurately.
- [x] Worker handoff after interruption uses committed progress and cannot create duplicate observations, publications, or logical task outcomes.
- [x] A worker that lost authority cannot commit stale results over a successor's progress.
- [x] Independent tasks can progress without one task's claim serializing the entire workspace.
- [x] Real competing connections/processes exercise claim races, lost acknowledgment, and recovery; sequential helper calls are not accepted as concurrency proof.
- [x] The visible task history records bounded attempts and recovery without exposing payloads or secrets.

**Spec coverage:** user stories 20, 35, 36, 37; acceptance scenarios T03, T04, T07 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

Implemented locally with **111 focused tests** and **278 shared tests** passing. [Ticket 07 report](../reports/ticket-07.md) records public interfaces, actual competing connections/processes, stale-effect commit fencing, TDD evidence and operational limits. Status remains claimed for integration validation and resolution by the merger.
