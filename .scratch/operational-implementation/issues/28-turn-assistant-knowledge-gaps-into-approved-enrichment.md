# 28: Turn assistant knowledge gaps into approved enrichment

**What to build:** A marketer can turn an unanswered or stale assistant question into a scoped proposal, approve it, follow the task, and use published updates in a later query.

**Blocked by:** 05: Approve an exact assistant enrichment proposal; 08: Deliver durable task completion notifications; 27: Answer free-form questions from permitted knowledge.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Compose the existing question, proposal/approval, task, and notification operations into one assistant journey; do not add new acquisition or model providers.

- [x] An assistant knowledge gap can produce a visible proposal for refresh, attribute fill, or bounded subject expansion with an identifiable exact scope.
- [x] The assistant cannot submit before actual human approval and cannot convert a model-generated statement, forged origin, or changed scope into authority.
- [x] Approved scope may exceed scheduled keywords; material expansion requires corresponding new approval and still respects cost/source/task bounds.
- [x] After approval the interaction returns a task acknowledgment/status and later the durable actual completion/partial/failure notification.
- [x] Newly fetched information is never returned as a KB answer before ingestion/publication; a later explicit query can use usable publications.
- [x] HTTP/public-operation tests cover successful update, publication failure, broadened proposal, foreign actor, repeated approval, and source withdrawal.

**Spec coverage:** user stories 25, 26, 27, 28, 29, 30, 31, 32, 33, 34; acceptance scenarios T02, T03, T05, T12, T17 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

Implemented locally with the existing public answer/proposal/approval/task/completion owners. Frozen shared check passed **680 tests in 472.39 seconds**, exit 0, at `1d0c137cc1936a4fe6ddd7f6a796a8a1f20f9d93`; runtime implementation is `d9d3276a8c257092dbda6b4c1f489a5128771c5a`. [The implementation report](../reports/ticket-28.md) records exact recovery/public/HTTP coverage, persistent gate and 68-pair source/archive verification. Offline wheel: 336398 bytes, SHA-256 `485099d9851128f34c17a11101e1b85d037c9ac5516992091d7e05973d8f3391`, 159 unique entries. Technical acceptance is checked; status stays **claimed** for independent merger validation and resolution. No live source/model/paid execution or human usefulness claim.
