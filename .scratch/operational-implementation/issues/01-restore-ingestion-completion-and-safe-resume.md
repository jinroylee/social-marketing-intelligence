# 01: Restore ingestion completion and safe resume

**What to build:** An operator can ingest bounded input and resume a completed capture without another collector call or losing prior run history.

**Blocked by:** None (can start immediately).

**Status:** resolved

**Size:** S — one bounded baseline repair in a fresh implementation context.

**Scope guard:** Repair the existing evidence-save completion contract and its caller compatibility only; introduce no task queue or unrelated refactor.

- [x] The evidence-save operation accepts an explicit final-input marker and a backward-compatible default for callers that do not provide it.
- [x] Observation persistence, checkpoint advancement, and final-input marking commit together, including caller-owned transactions.
- [x] At the request/record limit, a saved final capture resumes into canonical processing without another collector call; an interrupted nonfinal capture remains resumable.
- [x] Existing run migration and retained/transient replay scenarios preserve IDs and prior observations.
- [x] The shared repository check is green with the test database available; the current undefined-completion and unexpected-argument failures are resolved.

**Spec coverage:** user stories 35, 36, 38, 69; acceptance scenarios T04, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Completion

- Implementation commit: `11bc6cbe9c25fde9443b2785dbf5482b2ae18c0a`, fast-forward integrated into `integration/operational-tickets-01-10`.
- Integrated verification: `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **209 tests in 132.74 seconds**.
- All acceptance criteria are checked. Delivery remained offline and local, with real PostgreSQL and simulated external I/O; no push or PR occurred.
