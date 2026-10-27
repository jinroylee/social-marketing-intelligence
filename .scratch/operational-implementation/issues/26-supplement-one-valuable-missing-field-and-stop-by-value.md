# 26: Supplement one valuable missing field and stop by value

**What to build:** A discovery task can selectively retrieve one configured missing field from an existing supplementary route and explain why it continued or stopped.

**Blocked by:** 24: Enable one verified live on-demand discovery route.

**Status:** resolved

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

At worker handoff, software was implemented and worker-verified, with status **claimed** pending merger-owned independent integrated checking and resolution; the completed integration evidence follows. See [ticket-26 report](../reports/ticket-26.md), [exact wheel manifest](../reports/ticket-26-wheel-manifest.json) and [primary-contract note](../research/ticket-26-brightdata-profile-field-contract.md). Frozen runtime `c461a49ff89e9057973848ba049a9273095016bd` passed the required offline shared checks: **656 tests / 461.21 seconds**, exit 0. Exact wheel source/archive verification passed. All source/model/paid execution remained simulated. Actual credentials, source-use/execution/profile authorization, enabled process and commercial binding remain unmet runtime prerequisites; no live-readiness or human-quality claim.


## Completion

- Runtime implementation and frozen worker checked commit: `c461a49ff89e9057973848ba049a9273095016bd`. Final worker handoff and root integrated checked commit: `ca4bd0a4da32cb1944d5013dc882999a2a267423`, fast-forward integrated from clean `1ee8d8dae94780551cec8462c490147f4b36c169`. Frozen-to-final changes are limited to this checklist/handoff, the ticket's report and exact wheel manifest.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **656 tests in 454.35 seconds**, exit **0**, session `49478`. Durable root log: `.scratch/operational-implementation/verification/ticket-26-integrated/shared.log`; sibling `shared.started`, `shared.head`, `shared.command`, `shared.session` and `shared.exit` retain execution identity/status. The completed worker PASS is preserved without rerun; all six acceptance criteria are checked.
- Independently verified the existing persistent wheel: **312978 bytes**, SHA-256 `9591bfebc7f8678ff83d183bfcac1b47324f186ca6cad7d77e2f7b76893f82cf`, **147 archive entries** and all **68 source/archive pairs** matching integrated bytes, sizes, hashes and relative guidance symlink targets. This covers all nine SQL schemas, both review assets and all 22 packaged guidance pairs. [The report](../reports/ticket-26.md), [exact manifest](../reports/ticket-26-wheel-manifest.json), [verifier](../reports/verify-ticket-26-wheel.py) and root `verification/ticket-26-integrated/wheel-verification.json` retain the evidence.
- Current primary profile contract was verified **2026-10-27**; the one-field software slice is complete and validated with real PostgreSQL and simulated HTTP. Exact approved profile URL/native ID, nickname-only projection, original cumulative limits and separate `tiktok:public` support remain enforced without identity merging. Actual profile route/method attribution and unknown costs remain under an explicit shared local declared Bright Data ceiling; no verified commercial profile billing, live readiness or human-quality claim follows.
- Real credentials, source-use authorization, live-operation and independent profile-operation authorization, server/worker enablement, current commercial configuration and a separately authorized live receipt remain unmet independent runtime gates. Their absence disables actual dispatch and is not by itself a software blocker. No actual source/model/paid call, external message, push, PR or deployment occurred.
