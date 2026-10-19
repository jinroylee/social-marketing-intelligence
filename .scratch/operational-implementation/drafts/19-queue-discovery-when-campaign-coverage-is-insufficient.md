# 19: Queue discovery when campaign coverage is insufficient

**What to build:** A marketer receives the current supported shortlist immediately while inadequate quantity, relevance, or freshness automatically queues bounded campaign discovery.

**Blocked by:** 15: Automatically save an attributed ordered shortlist; 18: Execute bounded offline keyword discovery.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One visible versioned coverage policy and its automatic task submission; do not regenerate or replace saved results.

- [ ] Assess actual candidate quantity, relevance, and freshness against a recorded coverage profile and show the reasons/coverage with the saved result.
- [ ] Insufficient coverage establishes campaign task authority server-side and submits an associated bounded discovery task without asking for assistant approval.
- [ ] Repeated coverage evaluation does not duplicate the same logical discovery request; forged campaign origin still cannot bypass assistant approval.
- [ ] The current supported shortlist remains available, including an empty result, while the task is queued/running.
- [ ] Source/cost admission failure is shown as blocked/refused enrichment without losing or fabricating the recommendation.
- [ ] Public application tests demonstrate sufficient, thin, stale, empty, repeated, and refused cases through shortlist and task views.

**Spec coverage:** user stories 15, 16, 17, 34, 43; acceptance scenarios T02, T03, T14 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
