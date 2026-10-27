# 26: Supplement one valuable missing field and stop by value

**What to build:** A discovery task can selectively retrieve one configured missing field from an existing supplementary route and explain why it continued or stopped.

**Blocked by:** 24: Enable one verified live on-demand discovery route.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One supported missing-field case and one supplementary route; no general autonomous research loop or arbitrary route switching.

- [x] An explicit selection policy considers missingness, freshness, permission, capability, expected information value, and cost before requesting supplementation.
- [x] Only the valuable in-scope record/field is fetched using parent task authority, remaining request/byte/record limits, and shared spending admission.
- [x] Supplementary observations retain their own source namespace, metric meaning, capture times, and provenance; conflicting support is not silently merged.
- [x] Unchanged evidence, unavailable capability, insufficient value, exhausted limits, source failure, or denied cost admission each produces an inspectable stopping reason.
- [x] Reference-only oEmbed responses cannot be turned into retained creator/account facts or comparison-grade evidence.
- [x] The task detail and resulting KB view show the actual new support/unknowns; counted fake transports verify no extra call after a stop condition.

**Spec coverage:** user stories 42, 43, 45, 46; acceptance scenarios T19, T20, T21, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Implementation handoff

Software is implemented and worker-verified; status remains **claimed** for merger-owned independent integrated checking and resolution. See [ticket-26 report](../reports/ticket-26.md), [exact wheel manifest](../reports/ticket-26-wheel-manifest.json) and [primary-contract note](../research/ticket-26-brightdata-profile-field-contract.md). Frozen runtime `c461a49ff89e9057973848ba049a9273095016bd` passed the required offline shared checks: **656 tests / 461.21 seconds**, exit 0. Exact wheel source/archive verification passed. All source/model/paid execution remained simulated. Actual credentials, source-use/execution/profile authorization, enabled process and commercial binding remain unmet runtime prerequisites; no live-readiness or human-quality claim.
