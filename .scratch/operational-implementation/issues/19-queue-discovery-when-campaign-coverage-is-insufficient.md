# 19: Queue discovery when campaign coverage is insufficient

**What to build:** A marketer receives the current supported shortlist immediately while inadequate quantity, relevance, or freshness automatically queues bounded campaign discovery.

**Blocked by:** 15: Automatically save an attributed ordered shortlist; 18: Execute bounded offline keyword discovery.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One visible versioned coverage policy and its automatic task submission; do not regenerate or replace saved results.

- [x] Assess actual candidate quantity, relevance, and freshness against a recorded coverage profile and show the reasons/coverage with the saved result.
- [x] Insufficient coverage establishes campaign task authority server-side and submits an associated bounded discovery task without asking for assistant approval.
- [x] Repeated coverage evaluation does not duplicate the same logical discovery request; forged campaign origin still cannot bypass assistant approval.
- [x] The current supported shortlist remains available, including an empty result, while the task is queued/running.
- [x] Source/cost admission failure is shown as blocked/refused enrichment without losing or fabricating the recommendation.
- [x] Public application tests demonstrate sufficient, thin, stale, empty, repeated, and refused cases through shortlist and task views.

**Spec coverage:** user stories 15, 16, 17, 34, 43; acceptance scenarios T02, T03, T14 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

- All technical acceptance criteria are demonstrated in [the ticket 19 report](../reports/ticket-19.md). Runtime/tests/docs commit `f715f4151460e64adcc8e69a6548db8018e4a885`; frozen checked merge `c1fdf76f0c88a0388f6f3f3e0de6b3e0676d21bc` includes latest integration metadata. Shared offline check passed **490 tests in 327.81s** with real isolated PostgreSQL; wheel byte verification passed all 24 required packaged entries. Status remains claimed for root integrated verification and resolution. No actual source/model/paid execution or human-usefulness validation is claimed.

## Completion

- Runtime implementation: `f715f4151460e64adcc8e69a6548db8018e4a885`. Frozen worker checked merge: `c1fdf76f0c88a0388f6f3f3e0de6b3e0676d21bc`. Final worker head and root integrated checked commit: `4c2d844418115c239bcadca4c93a378b9b4f7bae`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **490 tests in 321.22 seconds**; log `/tmp/smi-ticket-19-integrated-shared.log`. The gate completed during the usage interruption and was preserved without rerun. All acceptance criteria are checked.
- The independent wheel hash and 24-entry byte/size/hash/declared-symlink verification passed before the interruption and remains valid for the unchanged integrated tree. [The implementation report](../reports/ticket-19.md) preserves exact worker and root evidence.
- Verification used real PostgreSQL and simulated external I/O. Existing saved recommendations remain immutable; no real source/model/paid call, readiness or human-quality claim, external message, push, PR or deployment occurred.
