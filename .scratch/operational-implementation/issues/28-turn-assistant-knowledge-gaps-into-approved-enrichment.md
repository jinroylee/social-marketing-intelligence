# 28: Turn assistant knowledge gaps into approved enrichment

**What to build:** A marketer can turn an unanswered or stale assistant question into a scoped proposal, approve it, follow the task, and use published updates in a later query.

**Blocked by:** 05: Approve an exact assistant enrichment proposal; 08: Deliver durable task completion notifications; 27: Answer free-form questions from permitted knowledge.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Compose the existing question, proposal/approval, task, and notification operations into one assistant journey; do not add new acquisition or model providers.

- [ ] An assistant knowledge gap can produce a visible proposal for refresh, attribute fill, or bounded subject expansion with an identifiable exact scope.
- [ ] The assistant cannot submit before actual human approval and cannot convert a model-generated statement, forged origin, or changed scope into authority.
- [ ] Approved scope may exceed scheduled keywords; material expansion requires corresponding new approval and still respects cost/source/task bounds.
- [ ] After approval the interaction returns a task acknowledgment/status and later the durable actual completion/partial/failure notification.
- [ ] Newly fetched information is never returned as a KB answer before ingestion/publication; a later explicit query can use usable publications.
- [ ] HTTP/public-operation tests cover successful update, publication failure, broadened proposal, foreign actor, repeated approval, and source withdrawal.

**Spec coverage:** user stories 25, 26, 27, 28, 29, 30, 31, 32, 33, 34; acceptance scenarios T02, T03, T05, T12, T17 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
