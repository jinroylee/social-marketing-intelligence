# 08: Deliver durable task completion notifications

**What to build:** A marketer can reopen an in-application inbox and follow task completion messages to the actual usable update, partial result, or failure.

**Blocked by:** 06: Recover interrupted tasks and expose partial outcomes.

**Status:** claimed

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Local durable inbox and task completion delivery only; defer campaign regeneration actions and external message transports.

- [x] Task completion and its logical notification are persisted consistently so interruption after a committed outcome cannot permanently hide completion.
- [x] Usable, partial, no-update, and failed outcomes have distinct concise messages with task/publication links and actual coverage.
- [x] Repeated delivery/resumption references one logical event; it does not invent multiple completed updates.
- [x] Inbox and task/publication navigation survive application restart and remain workspace scoped.
- [x] Notification text and source-dependent links apply current display/retention policy; unavailable support does not leak copied wording.
- [x] No email, Slack, push transport, or unrequested external messaging is introduced.

**Spec coverage:** user stories 18, 30, 31, 33, 36, 38, 68; acceptance scenarios T01, T03, T04, T05, T06 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Comments

Implemented locally with **56 focused tests** and **291 shared tests** passing. [Ticket 08 report](../reports/ticket-08.md) records public interfaces, TDD evidence, real process/transaction completion recovery, current-policy navigation, upgrade/reconciliation and limits. Status remains claimed for integration validation and resolution by the merger.
