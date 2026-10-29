# 36: Traverse and filter governed graph relationships

**What to build:** A marketer can traverse multiple permitted graph relationships and narrow the view without losing relationship basis or evidence.

**Blocked by:** 35: Search graph entities and inspect supported neighbors.

**Status:** resolved

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
- At worker handoff, status was **claimed** pending independent merger/root full checking and resolution; completed evidence follows. Technical checks establish neither language accuracy nor marketer usefulness. No persistent artifact or worktree was removed.


## Completion

- Runtime/frozen implementation: `fcb0b7d33cf6df40ec020b32cc9293b0a94052f3`. Final worker handoff/root checked commit: `4035859588d73dbdf21b02e9484f3926a0e702a8`, fast-forward integrated from clean `3de24dfe8d810a6f463b029391476ff231718dc8`. Frozen-to-final changes are exactly four own scratch files; all 300 protected bytes/sizes/hashes/relative targets independently match integrated root.
- Required independent root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **846 tests in 580.41 seconds**, exit **0**, session `78206`. Durable root `verification/ticket-36-integrated/shared.{started,finished,head,runtime,worker-frozen,command,session,log,exit}` retains exact identity/status. Worker 846/579.23s and prior completed gates were preserved without rerun; all six criteria are checked.
- Existing wheel independently matches **427532 bytes**, SHA-256 `273c7cf95fffb0e6ea87a2f5082410678702601b2c99e88253d29d9139b69c01`, **204 unique entries**, all **86 source/archive pairs**, all **7 changed packaged paths**, eighteen SQL schemas, both assets and all 31 guidance pairs plus root guidance. [Report](../reports/ticket-36.md), [manifest](../reports/ticket-36-wheel-manifest.json), [verifier](../reports/verify-ticket-36-wheel.py) and durable root wheel/freeze JSON retain precise evidence; no wheel was rebuilt.
- Root review found no blocking bug. Public RED/GREEN coverage, final focused **48/28.62s** (including all 17 graph cases) and root **846/580.41s** verify cycles, direction, each budget/truncation, exact observation/shared-node filtering, current denial and HTTP/back/reopen/error context. Observation filters narrow the whole transient projection, including shared root/neighbor labels, attributes, support and relationships. Source-filtered membership remains separate from current availability/original query coverage. Ticket 35 exact publication/claim/source-subject date provenance remains intact.
- Traversal is finite over the existing bounded projection: 1–3 hops, 1–100 nodes, 1–50 returned relationships and 1–5,000 traversal-edge inspections. The work budget starts after finite support projection/adjacency construction and is not a total database-work SLA. Current-policy reads hide affected labels/details/edges/counts; filters cannot create hidden bridges, cached withdrawn wording or immutable campaign membership. No new ontology, datastore, raw-fact cache, inferred Creator association, source/model/provider I/O or campaign decision is introduced; complete KB/market coverage, source truth, language accuracy and human usefulness remain unestablished.
- Coordinator root archive 36 is preserved and independently identity-verified: **407615 bytes**, **37 entries**, SHA-256 `fdcb6d3c84cf00b4776091e79a0e8296f27ed8f8a5df54ccbb7d129f2b1b3ffa`; relocation-index.json retains original paths/member hashes. Existing committed 26–35 relocation report is untouched and all worker files remain. Only metadata follows PASS; no runtime/test edit, repeated gate/build, actual source/model/paid call, external message, push, PR, deployment, archive/index mutation, worktree removal or cleanup occurred in merger work.
