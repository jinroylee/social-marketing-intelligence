# 20: Offer explicit regeneration after campaign updates

**What to build:** A campaign discovery completion notification offers regeneration, and only a marketer's explicit action creates a newly assessed saved shortlist revision.

**Blocked by:** 08: Deliver durable task completion notifications; 19: Queue discovery when campaign coverage is insufficient.

**Status:** claimed

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Reuse the configured recommendation method and completion inbox; no silent rerank, automatic replacement, or new ranking method.

- [x] Usable or partial published updates link the campaign notification to exact task/publication outcomes and an explicit regeneration action.
- [x] No-update/failure messages do not imply new evidence is available for a better recommendation.
- [x] Before the action, the saved shortlist's membership, order, methods, and support remain unchanged.
- [x] The explicit action uses the current campaign context, performs the configured assessment, and automatically saves an attributed successor under concurrency checks.
- [x] Duplicate action submission returns the same successor; a changed brief or stale version produces a visible conflict/recovery path.
- [x] A restart-capable HTTP journey verifies notification, no background mutation, regeneration, and both historical revisions.

**Spec coverage:** user stories 18, 19, 20, 33; acceptance scenarios T09, T15 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Comments

- All technical acceptance criteria are demonstrated in [the ticket 20 report](../reports/ticket-20.md). Runtime/tests/docs commit `c81b5e02cd052bf66f317dd53abdbe9a2ff51ba6`; frozen checked merge `44409a4e42a2281aed19837e903ba628adb97e85` includes latest integration metadata. Final focused compatibility passed **133 tests in 122.03s** after correcting the pre-inbox fixture's new foreign-key dependency. Frozen shared offline check passed **511 tests in 358.85s** with real isolated PostgreSQL. Offline wheel byte verification passed all **23** required packaged entries; the report preserves exact hashes/files/logs. Status remains claimed for root integrated verification and resolution. No actual source/model/paid execution or human-usefulness validation is claimed.
