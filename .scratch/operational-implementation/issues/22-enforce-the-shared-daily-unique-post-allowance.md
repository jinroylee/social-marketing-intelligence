# 22: Enforce the shared daily unique-post allowance

**What to build:** Scheduled discovery admits at most the configured daily total of unique eligible new posts across all keywords and competing workers.

**Blocked by:** 21: Schedule offline discovery for registered keywords.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Atomic new-post admission at the established scheduled ingestion boundary; do not treat request counts, refreshes, or costs as the same allowance.

- [x] The initial configurable total is fifty unique eligible new posts per workspace/day across all registered keywords, not fifty per keyword.
- [x] Overlapping query results and competing tasks cannot admit the same eligible new post twice or collectively exceed the day's allowance; invalid/denied records do not count as successful new-post admission, and failed admission/ingestion releases or reconciles reservations safely.
- [x] Known-record refreshes remain distinct from new-post admission and cannot be disguised as additional new eligible posts.
- [x] Restarts, keyword edits, and configuration revisions preserve consumption under the recorded accounting-day/timezone boundary.
- [x] Task and schedule views show used/remaining allowance, deduplication, limits, and legitimate fewer-record outcomes without promising a fill target.
- [x] Real competing public operations test overlapping identities, exhausted allowance, day rollover, and configuration changes without paid I/O.

**Spec coverage:** user stories 40, 41, 44; acceptance scenarios T07, T18, T20 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

- All six technical criteria are proven in [the ticket 22 report](../reports/ticket-22.md): final 38-test schedule/allowance public/HTTP coverage, preserved 201-test compatibility pass, frozen shared checks with 549 tests in 532.33 seconds and exact 27-entry offline wheel verification. Initial runtime `41e10cba9ef741c355a17b6ea3301e6e336759e1`; final runtime/frozen checked head `cfceca281bcf0310cd16350707fdc36d7a1df4f7`. Status stays claimed for merger-owned integrated validation/resolution.
- New-post admission commits atomically with fenced canonical effects. Known refreshes, deduplication, invalid/denied/excluded records, cap edits, restart, stable day rollover and pre-tick reads retain separate observable semantics. Existing authority, policy, cost/no-reissue, session ownership and receipt recovery remain intact. Verification uses real local PostgreSQL and simulated I/O; no live route, daemon, paid execution, guaranteed fill, readiness or human-quality claim is made.

## Completion

- Final corrected runtime and frozen checked commit: `cfceca281bcf0310cd16350707fdc36d7a1df4f7` (includes the before-first-tick view fix after initial implementation `41e10cba9ef741c355a17b6ea3301e6e336759e1`). Final worker head and root integrated checked commit: `5cc5aa245d77e66f9bb739d3b9eda8d425b210ec`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **549 tests in 510.97 seconds**; log `/tmp/smi-ticket-22-integrated-shared.log`. All acceptance criteria are checked. The earlier interrupted/superseded gate at the initial runtime is not a full PASS and is not used for completion.
- Independently verified the final wheel size (**278200 bytes**), SHA-256 and all 27 packaged entries against integrated bytes, sizes, hashes and declared symlink targets. [The implementation report](../reports/ticket-22.md) retains exact corrected-worker and root evidence.
- Verification used real PostgreSQL and simulated external I/O. Scheduled unique-post enforcement remains distinct from requests, refreshes and costs; no live activation, actual provider/model/paid call, readiness or human-quality claim, external message, push, PR or deployment occurred.
