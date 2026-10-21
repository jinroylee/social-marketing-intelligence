# 15: Automatically save an attributed ordered shortlist

**What to build:** A campaign's supported deterministic recommendation is saved automatically as an ordered shortlist revision that can be reopened without a human-review step.

**Blocked by:** 14: Compare eligible accounts from current knowledge.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Implement automated save authority and ordered persistence using the existing deterministic assessment; semantic LLM ranking and optional human curation are separate.

- [ ] A recommendation operation automatically persists the actual automation producer, exact brief/profile/method, candidate order, rationale, gaps, and pinned support.
- [ ] An empty eligible result is saved explicitly; no un-ingested account or fabricated evidence is inserted to avoid an empty shortlist.
- [ ] Saving requires no human approval/review/confirmation and never fabricates human authorship or endorsement.
- [ ] Identical requests reopen the original saved revision without reassessment; changed payload under a request identity and stale revision updates conflict.
- [ ] Existing human shortlist records and their statuses/attribution survive schema upgrade and restart unchanged.
- [ ] Saved explanations enforce current policy and retention withdrawal while permitted historical membership and producer attribution remain pinned.

**Spec coverage:** user stories 8, 11, 12, 14, 20, 69; acceptance scenarios T03, T09, T13, T14, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
