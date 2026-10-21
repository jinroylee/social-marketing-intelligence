# 15: Automatically save an attributed ordered shortlist

**What to build:** A campaign's supported deterministic recommendation is saved automatically as an ordered shortlist revision that can be reopened without a human-review step.

**Blocked by:** 14: Compare eligible accounts from current knowledge.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Implement automated save authority and ordered persistence using the existing deterministic assessment; semantic LLM ranking and optional human curation are separate.

- [x] A recommendation operation automatically persists the actual automation producer, exact brief/profile/method, candidate order, rationale, gaps, and pinned support.
- [x] An empty eligible result is saved explicitly; no un-ingested account or fabricated evidence is inserted to avoid an empty shortlist.
- [x] Saving requires no human approval/review/confirmation and never fabricates human authorship or endorsement.
- [x] Identical requests reopen the original saved revision without reassessment; changed payload under a request identity and stale revision updates conflict.
- [x] Existing human shortlist records and their statuses/attribution survive schema upgrade and restart unchanged.
- [x] Saved explanations enforce current policy and retention withdrawal while permitted historical membership and producer attribution remain pinned.

**Spec coverage:** user stories 8, 11, 12, 14, 20, 69; acceptance scenarios T03, T09, T13, T14, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Completion

- Runtime implementation commit: `a80da4dca903b95d2c9aa9fe6bf8f845a6415a4c`. Final worker head and integrated checked commit: `567236079b3573daacbef9bd67379d793e7261f2`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **404 tests in 262.27 seconds**. All acceptance criteria are checked.
- The worker wheel matches all nine changed packaged files in the integrated tree byte for byte. [The implementation report](../reports/ticket-15.md) retains the existing focused/frozen-worker gates and integrated result.
- Automatic deterministic save retains actual automation authorship without human endorsement. Verification used real PostgreSQL and simulated external I/O; no actual provider/source call, external message, push, PR or deployment occurred.
