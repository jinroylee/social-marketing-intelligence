# 10: Enforce shared monetary admission before work

**What to build:** An operator can configure a metered ceiling and see competing chargeable operations admitted or refused before their simulated external calls.

**Blocked by:** 09: Show attributable actual costs and forecasts.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Coordinated bounded commitments and ceiling admission for the existing synthetic cost scope; delayed billing and uncertain outcomes follow separately.

- [ ] Configured ceilings have explicit currency, accounting period, and cost scope; admissions consider actual spend plus outstanding bounded commitments.
- [ ] Competing workers and public operation adapters share one authoritative admission decision and cannot exceed available bounded commitments through races.
- [ ] Refused or paused work makes no additional chargeable call and exposes its allowance/blocked reason in task or operation status.
- [ ] Task approval, scheduled authorization, and automatic shortlist saving cannot bypass monetary admission.
- [ ] Forecast-only scopes remain forecast-only and retain request/record/byte bounds independently.
- [ ] Tests use genuinely competing admissions and a counted fake transport, including exact allowance, exhausted allowance, and missing required control.

**Spec coverage:** user stories 43, 59, 60, 63; acceptance scenarios T07, T21, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
