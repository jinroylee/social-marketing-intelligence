# 29: Collect bounded recent X evidence offline

**What to build:** An operator can configure an X monitoring topic, run a bounded offline collection window, and inspect retained recent observations independently of the full KB.

**Blocked by:** 01: Restore ingestion completion and safe resume.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One deterministic recent-X route, one topic/window collection journey, and retention/policy-aware timeline; no alerts, live provider, or full KB ingestion.

- [ ] Persist monitoring topic configuration separately from scheduled keywords with explicit cadence/window, bounded collection, source policy, and retention settings.
- [ ] A public bounded poll entry point retains recent observations with stable source references/identities, capture/publication times, window coverage, and acquisition context.
- [ ] The topic/window/timeline surface reopens observations after restart without creating campaigns or requiring knowledge publications for every post.
- [ ] Retries do not duplicate a logical window's observations; missing fields and incomplete coverage remain visible.
- [ ] Process/display/retention permissions, expiry, and withdrawal govern retained monitoring copies and their detail views.
- [ ] Offline integration tests prohibit external I/O and prove existing frozen-snapshot investigations keep their original independent behavior.

**Spec coverage:** user stories 47, 48, 53, 54, 56, 57, 68, 69; acceptance scenarios T08, T24, T26, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
