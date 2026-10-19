# 21: Schedule offline discovery for registered keywords

**What to build:** An operator can register scheduled keywords and inspect due offline discovery tasks created under the schedule's recorded authority.

**Blocked by:** 18: Execute bounded offline keyword discovery.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Keyword configuration and durable due-task creation/execution through the offline discovery route; keep live schedule activation disabled.

- [ ] A local configuration surface and public operation allow up to ten registered scheduled keywords per workspace, independently from monitoring topics.
- [ ] Schedule records include configuration version and explicit day/timezone/cadence context; scheduled tasks retain their actual schedule/keyword authority.
- [ ] A due tick creates bounded offline tasks once per logical scheduled occurrence and exposes status through the existing task surface.
- [ ] Assistant/client input cannot choose schedule origin to bypass approval, and on-demand approved scope is not restricted to the registered list.
- [ ] Restarts and concurrent due ticks do not create duplicate occurrences or reset recorded schedule history.
- [ ] The UI labels the route offline and the daily target as a configurable admission allowance rather than measured throughput or per-keyword yield.

**Spec coverage:** user stories 34, 39, 40, 41; acceptance scenarios T02, T18 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
