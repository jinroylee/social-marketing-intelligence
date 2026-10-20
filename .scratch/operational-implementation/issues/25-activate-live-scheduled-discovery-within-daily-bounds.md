# 25: Activate live scheduled discovery within daily bounds

**What to build:** An operator can enable a verified live route for scheduled keyword discovery while the shared daily new-post allowance and spending controls remain enforced.

**Blocked by:** 22: Enforce the shared daily unique-post allowance; 24: Enable one verified live on-demand discovery route.

**Status:** ready-for-agent

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Connect the proven live route to the existing scheduler and allowance; no new provider, query type, or scheduling engine.

- [ ] Explicit route/schedule configuration enables live scheduled tasks under recorded schedule authority; an offline schedule never becomes live silently.
- [ ] All keywords share the configured unique-new-post/day allowance and normal freshness/avoidance policy.
- [ ] Every attempted provider operation uses shared spending admission, route limits, and recovery; exhausted daily or monetary allowance stops further relevant work visibly.
- [ ] Scheduled outcomes distinguish fetched records, admitted new posts, usable publications, unchanged records, and partial/no-update results.
- [ ] Restart/concurrent schedule tests with simulated live transport verify actual call counts and no bypass via origin or configuration changes.
- [ ] Live execution still requires the established external configuration/authorization; no additional paid validation is silently authorized.

**Spec coverage:** user stories 39, 40, 41, 42, 44, 46; acceptance scenarios T18, T19, T20, T21 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
