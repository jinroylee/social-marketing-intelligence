# 17: Curate generated shortlists without rewriting history

**What to build:** A marketer can optionally curate a generated shortlist and save an attributable successor while preserving the original automated recommendation.

**Blocked by:** 15: Automatically save an attributed ordered shortlist.

**Status:** resolved

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Extend existing human selection/history forms to generated ordered revisions; do not add a mandatory review gate.

- [x] Human curation can select/reorder accounts and record supported reasons/acknowledged unknowns as a new revision with actual human attribution.
- [x] The original automated rank, producer, support, and lack of human review remain unchanged.
- [x] Stale heads and conflicting retry identities fail visibly; an identical human save retries safely.
- [x] Current source-policy restrictions and inherited support apply to copied human reasons and submitted forms.
- [x] Existing historical human selections, confirmations, plans, and notes reopen with their original meaning after upgrade.
- [x] HTTP and public-store tests demonstrate optional curation and history without requiring a curation action before automated saving.

**Spec coverage:** user stories 12, 13, 14, 19, 20, 69; acceptance scenarios T09, T13, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Completion

- Runtime implementation: `f6c0380741b1e0126c0d0864166e1fdb5ff1c14e`. Frozen worker checked merge: `9fc164fca493a43bc15e26da42a7033bd73fd1c6`. Final worker head and root integrated checked commit: `4a879845fc9b6aba0ad8dc0b600d4daea67fe8d5`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **452 tests in 290.70 seconds**; log `/tmp/smi-ticket-17-integrated-shared.log`. All acceptance criteria are checked.
- Independently verified the wheel hash and all eight packaged-file bytes/hashes against the integrated tree and worker byte-verification manifest. [The implementation report](../reports/ticket-17.md) preserves existing worker gates and exact integrated evidence.
- Verification used real PostgreSQL and simulated external I/O. Optional human curation preserves original automated history; no real source/model/paid call, external message, push, PR or deployment occurred. Technical tests do not establish human-language or marketer-usefulness quality.
