# 36: Traverse and filter governed graph relationships

**What to build:** A marketer can traverse multiple permitted graph relationships and narrow the view without losing relationship basis or evidence.

**Blocked by:** 35: Search graph entities and inspect supported neighbors.

**Status:** claimed

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Bounded multi-hop navigation, filters, and entity detail expansion on the existing projection; no new ontology or datastore.

- [ ] Graph navigation supports explicit bounded traversal and filters for applicable entity/relationship/source context, with visible truncation or empty results.
- [ ] Each traversed relationship remains inspectable with its observed/derived/human basis and supporting evidence.
- [ ] Cycles, hidden nodes, and large neighborhoods cannot cause unbounded expansion or reveal denied labels through counts/details.
- [ ] Policy changes invalidate/redact affected displayed detail without reconstructing withdrawn source wording.
- [ ] Navigation and back/reopen behavior retain meaningful selection/filter context without implying historical graph membership is an immutable campaign decision.
- [ ] HTTP/public-read tests exercise multi-hop navigation, cycles, bounded results, filters, and policy changes.

**Spec coverage:** user stories 64, 65, 68; acceptance scenarios T08, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementation context

- Worker branch `smi/operational-ticket-36`, based on integration `3de24dfe8d810a6f463b029391476ff231718dc8`; blocker 35 is resolved. Root retained the completed 840-test gate.
- Approved TDD seams: public `KnowledgeGraph.search/read` for exact governed traversal and current-policy behavior; local HTTP graph journey for navigation, filters, back/reopen and recoverable errors. Real isolated PostgreSQL; simulated source inputs.
- Traversal remains transient over the saved exact support sample. No new persistence, ontology, source/model/provider I/O or campaign decision.
