# 05: Approve an exact assistant enrichment proposal

**What to build:** A marketer can review a saved enrichment proposal, explicitly approve that exact scope, and submit an attributable offline task.

**Blocked by:** 04: Run one authorized offline acquisition task.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** A direct local proposal/review/approval interaction using a supplied proposal; defer conversational generation of the proposal.

- [x] A proposal revision visibly states purpose, refresh/fill/expansion intent, subject/search scope, and workspace before any acquisition task is submitted.
- [x] Only an attributable human action approves the exact proposal revision and scope; generated text or submitted actor kind is not approval.
- [x] Approval and retry-safe task submission bind one logical task to that approval; an identical retry cannot mint another task.
- [x] Changed or materially broader scope, missing approval, foreign workspace, and forged campaign/schedule origin are rejected before dispatch.
- [x] Approved on-demand scope may go beyond registered scheduled keywords while still honoring task limits.
- [x] The local approval and resulting task pages reopen exact attribution and scope after restart with existing form/Origin/CSRF protection.

**Spec coverage:** user stories 25, 26, 27, 28, 29, 30, 34; acceptance scenarios T01, T02, T03, T17 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Completion

- Implementation commit: `7ba1c46fe1b355afb6f2e42e703e0079fc359f3d`, fast-forward integrated into `integration/operational-tickets-01-10`.
- Integrated verification: `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **256 tests in 148.43 seconds**.
- All acceptance criteria are checked. See [the implementation report](../reports/ticket-05.md) for public interfaces and focused verification. Delivery remained offline and local, with real PostgreSQL and simulated external I/O; no push or PR occurred.
