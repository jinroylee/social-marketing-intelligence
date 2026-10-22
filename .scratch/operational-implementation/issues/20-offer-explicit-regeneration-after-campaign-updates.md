# 20: Offer explicit regeneration after campaign updates

**What to build:** A campaign discovery completion notification offers regeneration, and only a marketer's explicit action creates a newly assessed saved shortlist revision.

**Blocked by:** 08: Deliver durable task completion notifications; 19: Queue discovery when campaign coverage is insufficient.

**Status:** resolved

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Reuse the configured recommendation method and completion inbox; no silent rerank, automatic replacement, or new ranking method.

- [x] Usable or partial published updates link the campaign notification to exact task/publication outcomes and an explicit regeneration action.
- [x] No-update/failure messages do not imply new evidence is available for a better recommendation.
- [x] Before the action, the saved shortlist's membership, order, methods, and support remain unchanged.
- [x] The explicit action uses the current campaign context, performs the configured assessment, and automatically saves an attributed successor under concurrency checks.
- [x] Duplicate action submission returns the same successor; a changed brief or stale version produces a visible conflict/recovery path.
- [x] A restart-capable HTTP journey verifies notification, no background mutation, regeneration, and both historical revisions.

**Spec coverage:** user stories 18, 19, 20, 33; acceptance scenarios T09, T15 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Comments

- All technical acceptance criteria are demonstrated in [the ticket 20 report](../reports/ticket-20.md). Runtime/tests/docs commit `c81b5e02cd052bf66f317dd53abdbe9a2ff51ba6`; frozen checked merge `44409a4e42a2281aed19837e903ba628adb97e85` includes latest integration metadata. Final focused compatibility passed **133 tests in 122.03s** after correcting the pre-inbox fixture's new foreign-key dependency. Frozen shared offline check passed **511 tests in 358.85s** with real isolated PostgreSQL. Offline wheel byte verification passed all **23** required packaged entries; the report preserves exact hashes/files/logs. Status remains claimed for root integrated verification and resolution. No actual source/model/paid execution or human-usefulness validation is claimed.

## Completion

- Runtime implementation: `c81b5e02cd052bf66f317dd53abdbe9a2ff51ba6`. Frozen worker checked merge: `44409a4e42a2281aed19837e903ba628adb97e85`. Final worker head and root integrated checked commit: `b22bdf316710f161f092b2959f113ea1285e06ef`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **511 tests in 369.33 seconds**; log `/tmp/smi-ticket-20-integrated-shared.log`. All acceptance criteria are checked.
- Independently verified the wheel hash and all 23 packaged entries against integrated source bytes, sizes, hashes and declared symlink targets. [The implementation report](../reports/ticket-20.md) preserves existing worker gates and precise integrated evidence.
- Regeneration requires explicit human action and preserves original history; verification used real PostgreSQL and simulated external I/O. No actual source/model/paid call, readiness or human-quality claim, external message, push, PR or deployment occurred.
