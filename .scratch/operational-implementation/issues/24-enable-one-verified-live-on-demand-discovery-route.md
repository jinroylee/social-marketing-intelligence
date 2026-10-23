# 24: Enable one verified live on-demand discovery route

**What to build:** An authorized on-demand task can use one explicitly configured live TikTok query-discovery route and report the actual usable KB update and attributable cost.

**Blocked by:** 07: Coordinate competing workers without duplicate effects; 11: Reconcile delayed charges and failed meters; 23: Avoid redundant discovery while preserving refresh history.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One provider, platform, and query type; schedules remain offline until their separate activation ticket, and no automatic provider fallback is added.

- [x] Select and verify one permitted discovery-capable route against current primary documentation and bounded responses during implementation; existing supplied-profile/oEmbed success is insufficient.
- [x] Use the established query task, worker coordination, retrieval avoidance, normal ingestion/publication, coverage, and source-policy contracts.
- [x] Before every chargeable call, enforce configured admission and bounded commitments; account for actual known units/charges and expose forecast-only or delayed portions.
- [x] Pending/ambiguous provider work resumes or reconciles without a blind paid retry; source/schema/identity conflicts yield accurate partial/failure outcomes.
- [x] Missing credentials, source-use policy, required route/cost configuration, or explicit live-operation authorization is an unmet external prerequisite, never an invented readiness pass.
- [x] Default tests remain simulated. A separately authorized bounded live receipt records requests, returned/usable records, capture times, missingness, and derivable charges without secrets; preserve source-specific identities and semantics.

**Spec coverage:** user stories 35, 37, 42, 43, 44, 45, 46, 58, 59, 63; acceptance scenarios T04, T19, T20, T21, T22, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Implementation handoff

Software implementation and verification remain local/simulated. See [ticket-24 report](../reports/ticket-24.md) and [primary contract note](../research/ticket-24-brightdata-keyword-contract.md). Actual credentials, source-use permission, operation authorization, enabled process/server, commercial configuration and a separately authorized bounded live receipt remain unmet runtime prerequisites; none is invented by simulated tests. At worker handoff, the ticket was **claimed** pending merger-owned integrated checks and resolution; the completed integration evidence follows.

## Completion

- Final corrected runtime and frozen checked commit: `7308c5cb7645302859c9058d8e626cffdef54d4e`, following initial `c084df49f880d3c7b654b263317bfcb965c5b4db` and its localized bounded-header repair. Final worker head and root integrated checked commit: `9e9b604dd8f17b9a1449f3d260939ded6206439f`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only its report.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **619 tests in 624.35 seconds**; log `/tmp/smi-ticket-24-integrated-shared.log`. All technical acceptance criteria are checked. The interrupted initial-runtime gate is not a completed PASS or completion evidence.
- Independently verified final wheel size (**299575 bytes**), SHA-256 and all 41 source/archive entries against integrated bytes, sizes, hashes and declared symlink targets. [The implementation report](../reports/ticket-24.md) and [primary-contract research](../research/ticket-24-brightdata-keyword-contract.md) retain exact evidence.
- Current primary contract verified **2026-10-23**; concrete software validated with real PostgreSQL and simulated HTTP. Credentials, source-use authorization, live-operation authorization, server/worker enablement, current commercial route/rate/bound/ceiling configuration and a separately authorized live receipt remain unmet external runtime gates. They disable actual dispatch and are not software-implementation blockers; no live-readiness or human-quality claim is made. No actual source/model/paid call, external message, push, PR or deployment occurred.
