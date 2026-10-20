# 35: Search graph entities and inspect supported neighbors

**What to build:** A marketer can search permitted KB entities and inspect their immediate relationships and source evidence in a graph-oriented view.

**Blocked by:** 03: Search current knowledge and pin result support.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One-hop entity/relationship projection over existing governed knowledge; no graph database, inferred Creator merging, or multi-hop exploration yet.

- [ ] A public projection and local graph surface search/filter supported entities and show a selected entity's immediate permitted relationships.
- [ ] Relationship details distinguish observed, derived, and human bases and link to relevant source support/methods/dates.
- [ ] Uncorroborated matching handles cannot create cross-platform Creator associations.
- [ ] Process/display and withdrawal rules govern both graph labels and evidence details, including relationships whose support becomes unavailable.
- [ ] Projection work uses owning public read interfaces and does not become another raw-fact store.
- [ ] Public/HTTP tests cover empty search, bounded neighbors, differing relationship bases, foreign workspace, and denied support without leaks.

**Spec coverage:** user stories 64, 65, 68; acceptance scenarios T08, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
