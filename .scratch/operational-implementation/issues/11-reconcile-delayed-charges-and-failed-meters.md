# 11: Reconcile delayed charges and failed meters

**What to build:** An operator can reconcile delayed or uncertain charges after retries and restarts without double-counting or accidentally reopening an exhausted allowance.

**Blocked by:** 10: Enforce shared monetary admission before work.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** The established meter/commitment workflow, including late actuals and explicit control failure; do not add more providers.

- [ ] Late provider measurements replace or settle the correct outstanding commitment idempotently while preserving the measurement/rate audit trail.
- [ ] Ambiguous remote-call outcomes retain an explicit unresolved commitment until reconciled or handled by a recorded bounded policy.
- [ ] Retry and restart cannot double-charge accounting or release an unresolved operation as free work.
- [ ] An unavailable expected meter pauses/refuses further work in that scope and presents a visible control failure rather than silently switching to forecasts.
- [ ] Known charge bounds, billing lag, and strict-enforcement limitations are displayed; unbounded/delayed charges never imply guaranteed zero overshoot.
- [ ] Integration tests cover late success/failure, replayed billing, conflicting measurements, restart, and meter recovery through public operations.

**Spec coverage:** user stories 37, 58, 60, 61, 62, 63; acceptance scenarios T04, T22, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
