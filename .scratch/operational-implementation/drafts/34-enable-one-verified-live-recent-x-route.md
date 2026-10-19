# 34: Enable one verified live recent-X route

**What to build:** An operator can enable one configured live recent-X collection route for monitoring topics and inspect bounded recent windows without full KB ingestion.

**Blocked by:** 07: Coordinate competing workers without duplicate effects; 11: Reconcile delayed charges and failed meters; 29: Collect bounded recent X evidence offline.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One provider and recent-post query type wired to existing topic/window collection; no new anomaly method or external follow-up research.

- [ ] Verify the selected route's current primary contract, permitted use, identities, pagination, limits, and bounded response shape during implementation.
- [ ] Configured periodic polling uses coordinated worker execution and creates exact recent windows under topic authority, independently of KB publication.
- [ ] Source limits, request/byte/record bounds, shared spending admission, usage/reconciliation, and retention apply before and after each call.
- [ ] Pending/ambiguous outcomes and concurrent due polls do not blindly repeat chargeable work or duplicate logical windows.
- [ ] Missing credentials/policy/cost configuration or explicit live authorization remains an external prerequisite; never invent a successful readiness receipt.
- [ ] Default tests simulate transport. Any separately authorized bounded live receipt records actual attempts, timestamps, missingness, coverage and derivable costs without secrets.

**Spec coverage:** user stories 47, 48, 53, 54, 56, 58, 59, 63; acceptance scenarios T07, T19, T21, T22, T23, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
