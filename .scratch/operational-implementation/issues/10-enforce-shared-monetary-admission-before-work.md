# 10: Enforce shared monetary admission before work

**What to build:** An operator can configure a metered ceiling and see competing chargeable operations admitted or refused before their simulated external calls.

**Blocked by:** 09: Show attributable actual costs and forecasts.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Coordinated bounded commitments and ceiling admission for the existing synthetic cost scope; delayed billing and uncertain outcomes follow separately.

- [x] Configured ceilings have explicit currency, accounting period, and cost scope; admissions consider actual spend plus outstanding bounded commitments.
- [x] Competing workers and public operation adapters share one authoritative admission decision and cannot exceed available bounded commitments through races.
- [x] Refused or paused work makes no additional chargeable call and exposes its allowance/blocked reason in task or operation status.
- [x] Task approval, scheduled authorization, and automatic shortlist saving cannot bypass monetary admission.
- [x] Forecast-only scopes remain forecast-only and retain request/record/byte bounds independently.
- [x] Tests use genuinely competing admissions and a counted fake transport, including exact allowance, exhausted allowance, and missing required control.

**Spec coverage:** user stories 43, 59, 60, 63; acceptance scenarios T07, T21, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

Implemented on `smi/operational-ticket-10`; see [the ticket report](../reports/ticket-10.md). Status remains claimed pending integration/shared-check verification by the merger.
