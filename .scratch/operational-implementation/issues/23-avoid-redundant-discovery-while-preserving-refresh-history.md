# 23: Avoid redundant discovery while preserving refresh history

**What to build:** An operator can see unnecessary repeated retrieval skipped while legitimate stale-record refreshes and new observations retain their provenance.

**Blocked by:** 18: Execute bounded offline keyword discovery.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One discovery route's query/retrieval history and explicit freshness/processing policy; no global cross-provider identity merge or automatic fallback.

- [x] Persist prior query/retrieval scope, source identity, capture time, failures, usable publication, and method/version context needed for an explicit avoidance decision.
- [x] Repeated unchanged work within the configured freshness policy can be skipped with an inspectable reason rather than re-fetched or re-published as a new update.
- [x] Stale captures, changed source observations, required mapper revisions, and recoverable failed work remain eligible for appropriate new processing.
- [x] Unknown or unavailable freshness stays explicit; import/publication time cannot make old captures current.
- [x] Source namespaces, metric definitions, conflict history, and old result pins remain separate across refresh and deduplication.
- [x] Public task/KB tests count simulated retrievals and verify skip/refresh/failure behavior and historical support after restart.

**Spec coverage:** user stories 43, 44, 45, 46; acceptance scenarios T06, T19, T20 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Implementation validation

Worker runtime/frozen head `195eb279a1ce5a4bab52347fcd890c0c8699eee2` passed 291 focused compatibility tests in 274.77 seconds and the shared locked check with 577 tests in 583.94 seconds (exit 0). Exact report and retained artifact/byte-manifest evidence: [ticket 23 report](../reports/ticket-23.md). Status remains **claimed** pending the merger's separate integrated shared gate and resolution.

## Completion

- Runtime implementation and frozen worker checked commit: `195eb279a1ce5a4bab52347fcd890c0c8699eee2`. Final worker head and root integrated checked commit: `74ac5997380b67c6a417b72475a9be9b4f483b10`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **577 tests in 615.05 seconds**; log `/tmp/smi-ticket-23-integrated-shared.log`. All acceptance criteria are checked. Existing passing worker gates are preserved without rerun.
- Independently verified final wheel size (**288380 bytes**), SHA-256 and all 31 packaged entries against integrated bytes, sizes, hashes and declared symlink targets. [The implementation report](../reports/ticket-23.md) retains exact worker and root evidence.
- Avoidance is conservative exact query/input/context comparison with capture-based freshness; no concurrent cross-task exactly-once retrieval or semantic-overlap guarantee is claimed. Verification used real PostgreSQL and simulated external I/O, with no live provider/source execution, readiness or human-quality claim, external message, push, PR or deployment.
