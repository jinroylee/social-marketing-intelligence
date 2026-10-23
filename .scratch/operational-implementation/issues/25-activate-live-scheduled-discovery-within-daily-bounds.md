# 25: Activate live scheduled discovery within daily bounds

**What to build:** An operator can enable a verified live route for scheduled keyword discovery while the shared daily new-post allowance and spending controls remain enforced.

**Blocked by:** 22: Enforce the shared daily unique-post allowance; 24: Enable one verified live on-demand discovery route.

**Status:** resolved

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Connect the proven live route to the existing scheduler and allowance; no new provider, query type, or scheduling engine.

- [x] Explicit route/schedule configuration enables live scheduled tasks under recorded schedule authority; an offline schedule never becomes live silently.
- [x] All keywords share the configured unique-new-post/day allowance and normal freshness/avoidance policy.
- [x] Every attempted provider operation uses shared spending admission, route limits, and recovery; exhausted daily or monetary allowance stops further relevant work visibly.
- [x] Scheduled outcomes distinguish fetched records, admitted new posts, usable publications, unchanged records, and partial/no-update results.
- [x] Restart/concurrent schedule tests with simulated live transport verify actual call counts and no bypass via origin or configuration changes.
- [x] Live execution still requires the established external configuration/authorization; no additional paid validation is silently authorized.

**Spec coverage:** user stories 39, 40, 41, 42, 44, 46; acceptance scenarios T18, T19, T20, T21 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementation handoff

- Software and simulated verification are complete in [the ticket 25 report](../reports/ticket-25.md). Runtime/frozen checked commit `df3b65255120c9bde828a6d809834b089b55b6aa`; required offline shared checks passed **630 tests in 629.49 seconds**, exit 0, log `/tmp/smi-ticket-25-shared-check.log`. The 101-test compatibility pass and final 11-test live schedule suite, exact 60-entry wheel verification and all runtime limitations are retained in the report.
- Recorded operator activation pins exact route authority without converting offline schedules through process switches. Shared day admission, unchanged/freshness history, simulated concurrent dispatch, pending-snapshot recovery, unknown commitments and all existing runtime/spending gates remain enforced. No actual provider/model/source/paid call, external message, push, PR or deployment occurred; no human-quality or live-readiness claim is made.
- At worker handoff, status was **claimed** pending merger-owned integrated checks and resolution. The initial frozen-to-handoff span changes only this checklist/handoff and the ticket's own report; the documentation follow-up and completed integration evidence follow.


## Completion

- Runtime implementation and frozen worker checked commit: `df3b65255120c9bde828a6d809834b089b55b6aa`. Initial metadata handoff and required root full-gate commit: `f89ad86378510b1e642f0485c4d45324475b7309`, fast-forward integrated from clean `2deb42aeeb5f69362b485cb6c809a6a81a2506b4`.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **630 tests in 679.94 seconds**, exit 0; log `/tmp/smi-ticket-25-integrated-shared.log`. The worker's completed 630-test gate is preserved without rerun; all six technical acceptance criteria are checked.
- Final documentation follow-up `1c167a908c567a08a840d8de14833f52cc580714` changes only `docs/source-integrations.md` and `docs/tasks.md` to describe recorded schedule activation. Root independently passed `UV_OFFLINE=1 uv run --locked python tools/check.py --static`, exit 0; log `/tmp/smi-ticket-25-integrated-docs-static.log`. Runtime, tests and packaged bytes are unchanged, so the full passing gate was retained rather than repeated.
- Independently verified existing wheel **301523 bytes**, SHA-256 `186491a9eea60820b3bf072178ea29ef8abd7094728e1e61da6274066136f14f`, and all **60 entries** against integrated source/archive bytes, sizes, hashes and relative guidance symlink targets, including after the documentation follow-up. Exact evidence is retained in [the implementation report](../reports/ticket-25.md) and continuation manifest.
- Explicit recorded live schedule activation software is complete and validated with real PostgreSQL and simulated HTTP. Actual credentials, source-use permission, live-operation authorization, server/worker enablement, current commercial route/rate/bound/ceiling configuration and a separately authorized live receipt remain unmet independent runtime gates. They disable actual dispatch and are not software-implementation blockers; no live-readiness or human-quality claim is made. No actual source/model/paid call, external message, push, PR or deployment occurred.
