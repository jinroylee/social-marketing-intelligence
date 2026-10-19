# 04: Run one authorized offline acquisition task

**What to build:** A marketer can submit one bounded offline acquisition for an existing campaign, receive a task identity immediately, and inspect its ingestion and publication outcome.

**Blocked by:** 02: Publish and inspect permitted ingested support.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One server-authorized campaign origin, one offline route, and one bounded worker entry point; reject unsupported origins and keep live execution disabled.

- [x] Trusted campaign context establishes task origin and immutable scope/limits; arbitrary actor/origin fields cannot create schedule or assistant authority.
- [x] Submission persists actor, campaign basis, scope version, request identity, limits, and initial status before returning acknowledgment; it does not synchronously fetch.
- [x] A bounded worker uses the existing ingestion runner and publication operation, records its attempt/run links, and exposes a local task-detail surface after restart.
- [x] Queue acceptance, collection, ingestion, publication, failure, and no-usable-update meanings are distinguishable; raw fetch success alone never means a successful KB update.
- [x] Identical submission retries return the same task; changed scope under the same identity conflicts; foreign workspaces and forged origins dispatch no work.
- [x] No real source/model calls are possible in this slice; empty or unchanged inputs do not create fictitious update claims.

**Spec coverage:** user stories 16, 30, 34, 35, 38; acceptance scenarios T01, T02, T03, T05, T06 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Implementation evidence

Implemented locally on `smi/operational-ticket-04`; the ticket remains claimed until integration verification. See [the implementation report](../reports/ticket-04.md) for public interfaces, red/green evidence, the **248-test** shared check and follow-on contracts.
