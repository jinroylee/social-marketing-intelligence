# 05: Approve an exact assistant enrichment proposal

**What to build:** A marketer can review a saved enrichment proposal, explicitly approve that exact scope, and submit an attributable offline task.

**Blocked by:** 04: Run one authorized offline acquisition task.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** A direct local proposal/review/approval interaction using a supplied proposal; defer conversational generation of the proposal.

- [ ] A proposal revision visibly states purpose, refresh/fill/expansion intent, subject/search scope, and workspace before any acquisition task is submitted.
- [ ] Only an attributable human action approves the exact proposal revision and scope; generated text or submitted actor kind is not approval.
- [ ] Approval and retry-safe task submission bind one logical task to that approval; an identical retry cannot mint another task.
- [ ] Changed or materially broader scope, missing approval, foreign workspace, and forged campaign/schedule origin are rejected before dispatch.
- [ ] Approved on-demand scope may go beyond registered scheduled keywords while still honoring task limits.
- [ ] The local approval and resulting task pages reopen exact attribution and scope after restart with existing form/Origin/CSRF protection.

**Spec coverage:** user stories 25, 26, 27, 28, 29, 30, 34; acceptance scenarios T01, T02, T03, T17 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
