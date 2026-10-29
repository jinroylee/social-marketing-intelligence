# 36: Traverse and filter governed graph relationships

**What to build:** A marketer can traverse multiple permitted graph relationships and narrow the view without losing relationship basis or evidence.

**Blocked by:** 35: Search graph entities and inspect supported neighbors.

**Status:** claimed

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Bounded multi-hop navigation, filters, and entity detail expansion on the existing projection; no new ontology or datastore.

- [x] Graph navigation supports explicit bounded traversal and filters for applicable entity/relationship/source context, with visible truncation or empty results.
- [x] Each traversed relationship remains inspectable with its observed/derived/human basis and supporting evidence.
- [x] Cycles, hidden nodes, and large neighborhoods cannot cause unbounded expansion or reveal denied labels through counts/details.
- [x] Policy changes invalidate/redact affected displayed detail without reconstructing withdrawn source wording.
- [x] Navigation and back/reopen behavior retain meaningful selection/filter context without implying historical graph membership is an immutable campaign decision.
- [x] HTTP/public-read tests exercise multi-hop navigation, cycles, bounded results, filters, and policy changes.

**Spec coverage:** user stories 64, 65, 68; acceptance scenarios T08, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementation context

- Worker branch `smi/operational-ticket-36`, based on integration `3de24dfe8d810a6f463b029391476ff231718dc8`; blocker 35 is resolved. Root retained the completed 840-test gate.
- Approved TDD seams: public `KnowledgeGraph.search/read` for exact governed traversal and current-policy behavior; local HTTP graph journey for navigation, filters, back/reopen and recoverable errors. Real isolated PostgreSQL; simulated source inputs.
- Traversal remains transient over the saved exact support sample. No new persistence, ontology, source/model/provider I/O or campaign decision.


## Implementer handoff

- Runtime/frozen implementation: `fcb0b7d33cf6df40ec020b32cc9293b0a94052f3`; latest integration `3de24dfe8d810a6f463b029391476ff231718dc8` merged before clean freeze (already an ancestor).
- Required frozen worker `UV_OFFLINE=1 uv run --locked python tools/check.py` passed **846 tests in 579.23 seconds**, exit **0**, session **91996**, finished `2026-10-29T00:01:37.127254+00:00`. Focused compatibility **48/28.62s**, static checks and diff checks passed. Completed unchanged PASS is preserved without rerun.
- Subsequent offline wheel build and separate exact record/replay passed. Existing wheel: **427532 bytes**, **204 unique entries**, SHA-256 `273c7cf95fffb0e6ea87a2f5082410678702601b2c99e88253d29d9139b69c01`. **86 exact pairs** cover all **7 changed packaged paths**, **18 schemas**, both assets, **31 packaged guidance pairs** and root guidance; all **300 protected files** match freeze.
- [Implementation report](../reports/ticket-36.md), [exact manifest](../reports/ticket-36-wheel-manifest.json), [standalone verifier](../reports/verify-ticket-36-wheel.py); excluded `verification/ticket-36` retains logs, exact execution metadata, frozen hashes, artifact and final handoff identity.
- Bounded traversal remains transient over the existing exact governed projection. Source observation filters narrow labels/details and edges; native neighbor filters apply at every step. Cycles and hop/node/relationship/edge-inspection limits are explicit. Existing exact publication/subject provenance and one-hop compatibility remain covered. No new datastore, inferred Creator association, source/model/provider I/O or campaign decision.
- Status remains **claimed** pending independent merger/root full checking and resolution. Technical checks establish neither language accuracy nor marketer usefulness. No persistent artifact or worktree was removed.
