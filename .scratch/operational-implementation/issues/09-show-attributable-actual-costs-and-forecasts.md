# 09: Show attributable actual costs and forecasts

**What to build:** An operator can inspect a task's measured usage and derived charges separately from forecasts and outstanding commitments.

**Blocked by:** 04: Run one authorized offline acquisition task.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One configured synthetic metered service and one forecast-only scope, through a public usage operation and local cost detail; no real paid calls or ceiling enforcement yet.

- [ ] Persist explicit metered/forecast-only classification, currency, period, service/provider, attributable task/attempt or operation, units, rate version, and measurement provenance/time.
- [ ] Measured usage or charges produce derivable actual spending with auditable rate inputs; estimates and forecasts do not masquerade as actuals, and simulated measurements are labeled synthetic rather than commercial charges.
- [ ] Repeated measurement identity reconciles once and conflicting reuse is visible rather than silently overwriting accounting history.
- [ ] The cost surface distinguishes actuals, commitments, forecasts, unknown coverage, and meter failure; unknown cost is not zero.
- [ ] Model operations without an acquisition task can receive an equivalent attributable operation identity.
- [ ] Public-interface integration tests use simulated units/rates and prove forecast-only scopes never claim enforced monetary control.

**Spec coverage:** user stories 41, 58, 61, 62, 63, 67; acceptance scenarios T21, T22, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
