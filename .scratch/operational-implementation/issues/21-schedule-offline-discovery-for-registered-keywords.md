# 21: Schedule offline discovery for registered keywords

**What to build:** An operator can register scheduled keywords and inspect due offline discovery tasks created under the schedule's recorded authority.

**Blocked by:** 18: Execute bounded offline keyword discovery.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Keyword configuration and durable due-task creation/execution through the offline discovery route; keep live schedule activation disabled.

- [x] A local configuration surface and public operation allow up to ten registered scheduled keywords per workspace, independently from monitoring topics.
- [x] Schedule records include configuration version and explicit day/timezone/cadence context; scheduled tasks retain their actual schedule/keyword authority.
- [x] A due tick creates bounded offline tasks once per logical scheduled occurrence and exposes status through the existing task surface.
- [x] Assistant/client input cannot choose schedule origin to bypass approval, and on-demand approved scope is not restricted to the registered list.
- [x] Restarts and concurrent due ticks do not create duplicate occurrences or reset recorded schedule history.
- [x] The UI labels the route offline and the daily target as a configurable admission allowance rather than measured throughput or per-keyword yield.

**Spec coverage:** user stories 34, 39, 40, 41; acceptance scenarios T02, T18 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Comments

- All six technical criteria are proven in [the ticket 21 report](../reports/ticket-21.md): 24 schedule-focused public/HTTP checks within a 188-test regression union, frozen shared checks with 535 tests in 459.49 seconds, and 24-entry offline wheel byte verification. Runtime implementation `de7d01220109d4db200b6b66e17209f871803681`; frozen checked head `b027f0f6e9ed615a5452ebcd406344d0ee1ae801`. Status remains claimed for merger-owned integration/resolution.
- Scheduled daily new-post allowance is explicitly configurable metadata until ticket 22 installs atomic unique-new-post admission. This slice preserves stable accounting-day/timezone context and does not activate live routes, a daemon or an external scheduler. No actual source/model/paid calls or human-quality claims occurred.

## Completion

- Runtime implementation: `de7d01220109d4db200b6b66e17209f871803681`. Frozen worker checked merge: `b027f0f6e9ed615a5452ebcd406344d0ee1ae801`. Final worker head and root integrated checked commit: `dbadd45a9327b02fd9ca707aea65bc5001b0614c`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **535 tests in 453.56 seconds**; log `/tmp/smi-ticket-21-integrated-shared.log`. All acceptance criteria are checked.
- Independently verified wheel SHA-256 and all 24 packaged entries against integrated bytes, sizes, hashes and declared symlink targets. [The implementation report](../reports/ticket-21.md) preserves existing worker gates and exact root evidence.
- Verification used real PostgreSQL and simulated external I/O. Scheduled execution remains offline; no live activation, atomic new-post quota claim, actual provider/model/paid call, readiness or human-quality claim, external message, push, PR or deployment occurred.
