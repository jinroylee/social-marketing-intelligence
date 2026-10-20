# 06: Recover interrupted tasks and expose partial outcomes

**What to build:** An operator can resume an interrupted task and see which knowledge became usable, which phase failed, and what remains incomplete.

**Blocked by:** 04: Run one authorized offline acquisition task.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Single-worker recovery and the outcome matrix for one bounded route; worker competition and notification delivery are separate tickets.

- [x] Persist phase/attempt progress so restarting after evidence, canonical, or publication commit reuses committed effects rather than starting a fresh acquisition.
- [x] Tasks expose usable update, partial update, no usable update, and failure with sanitized phase-specific reasons and actual coverage.
- [x] One valid and one failed input preserve the valid committed publication while reporting the failed remainder; unpublished material stays unavailable to KB queries.
- [x] Unchanged already-published evidence and empty eligible results are reported without inventing a newly usable update or market-absence claim.
- [x] Pending provider state is representable as waiting/resumable progress; an ambiguous chargeable operation cannot be blindly reissued.
- [x] Fault-injection tests at public worker boundaries verify restart behavior and stable support/attempt identities using real persistence.

**Spec coverage:** user stories 20, 31, 35, 36, 37, 38; acceptance scenarios T03, T04, T05, T06 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

- Implementation and local validation are recorded in [the ticket 06 report](../reports/ticket-06.md). All acceptance criteria are implemented and locally verified; status remains claimed for integration verification and resolution by the merger.
