# 35: Search graph entities and inspect supported neighbors

**What to build:** A marketer can search permitted KB entities and inspect their immediate relationships and source evidence in a graph-oriented view.

**Blocked by:** 03: Search current knowledge and pin result support.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One-hop entity/relationship projection over existing governed knowledge; no graph database, inferred Creator merging, or multi-hop exploration yet.

- [x] A public projection and local graph surface search/filter supported entities and show a selected entity's immediate permitted relationships.
- [x] Relationship details distinguish observed, derived, and human bases and link to relevant source support/methods/dates.
- [x] Uncorroborated matching handles cannot create cross-platform Creator associations.
- [x] Process/display and withdrawal rules govern both graph labels and evidence details, including relationships whose support becomes unavailable.
- [x] Projection work uses owning public read interfaces and does not become another raw-fact store.
- [x] Public/HTTP tests cover empty search, bounded neighbors, differing relationship bases, foreign workspace, and denied support without leaks.

**Spec coverage:** user stories 64, 65, 68; acceptance scenarios T08, T28 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

- Runtime implementation: `324ee32a640aba7828fa4d4c2fa1644a42cdc726`; merged latest integration `d5bb24a59ae71009b9648f1b54523d2564ad6857` before clean freeze `bf526f6fa7a8b740fc678b2b084f1a807a2581d5`.
- Required frozen worker `UV_OFFLINE=1 uv run --locked python tools/check.py` passed **840 tests in 576.66 seconds**, exit **0**, session **54373**, finished `2026-10-28T23:27:00.280994+00:00`; completed unchanged gate preserved without rerun. Focused compatibility **42/21.82s**, final graph **11/7.18s**, static checks passed.
- Offline wheel build and separate exact record/replay passed: **423844 bytes**, **204 unique entries**, SHA-256 `b08c6c523dda3b87fe29aa81de5188de0e0e32294cad53c573a18481a2a1915a`. Exact **89 pairs** cover all **13 changed packaged paths**, **18 schemas**, both assets, **31 packaged guidance pairs** and root guidance; all **300 protected files** match freeze.
- [Implementation report](../reports/ticket-35.md), [exact manifest](../reports/ticket-35-wheel-manifest.json), [standalone verifier](../reports/verify-ticket-35-wheel.py); excluded `verification/ticket-35` retains logs, execution IDs, frozen hashes, artifact and handoff metadata. Both root provenance findings have explicit RED/GREEN public regressions and are closed.
- At worker handoff, status was **claimed** pending independent merger-owned integration/root checking and resolution; completed evidence follows. No network/source/model execution, inferred Creator association, multi-hop expansion, new raw-fact store, external message, push, PR, deployment or cleanup occurred. Language/usefulness and complete market coverage remain unestablished.


## Completion

- Runtime implementation: `324ee32a640aba7828fa4d4c2fa1644a42cdc726`; frozen worker checked merge: `bf526f6fa7a8b740fc678b2b084f1a807a2581d5`. Final worker handoff/root checked commit: `bd5dca9d7e3ba179e0fc1d5fb25c573cc596472d`, fast-forward integrated from clean `d5bb24a59ae71009b9648f1b54523d2564ad6857`. Frozen-to-final changes are exactly four own scratch files; all 300 protected bytes/sizes/hashes/relative targets independently match integrated root.
- Required independent root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **840 tests in 568.46 seconds**, exit **0**, session `72805`. Durable root `verification/ticket-35-integrated/shared.{started,finished,head,runtime,worker-frozen,command,session,log,exit}` retains exact evidence. Worker 840/576.66s and prior completed gates were preserved without rerun; all six criteria are checked.
- Existing wheel independently matches **423844 bytes**, SHA-256 `b08c6c523dda3b87fe29aa81de5188de0e0e32294cad53c573a18481a2a1915a`, **204 unique entries**, all **89 source/archive pairs**, all **13 changed packaged paths**, eighteen SQL schemas, both assets and all 31 guidance pairs plus root guidance. [Report](../reports/ticket-35.md), [manifest](../reports/ticket-35-wheel-manifest.json), [verifier](../reports/verify-ticket-35-wheel.py) and durable root wheel/freeze verification JSON retain exact identities/results; no wheel was rebuilt.
- Both root provenance findings are closed with public RED/GREEN regressions, final graph 11/7.18s, compatibility 42/21.82s and root 840-test PASS. Repeated source-only then interpreted publication of one observation binds claims/edges to exact supporting publication+manifest membership, using the first/newest permitted exact edge context rather than an overwritten observation bundle. Multi-post dates resolve by exact source subject; author-reference-only and ambiguous dates remain unknown. Public tests reopen the exact supporting publication/interpretation and check distinct subject dates and null reference-only time.
- The bounded one-hop projection composes public query/catalog interfaces and rechecks process/display/current retention/derivation for labels, relationships and evidence. It retains source-free manifests, not another raw-fact store. Native identities remain distinct despite matching handles; no Creator association inference, multi-hop expansion, new source/model I/O or campaign decision is added. Bounded sample/entity limits establish no complete KB/market coverage, source truth, language accuracy or human usefulness.
- Coordinator root archive 35 is preserved and independently identity-verified: **406294 bytes**, **39 entries**, SHA-256 `9bde6094793f7a93527d868350d251bd53f19a8c5a5946792ee6b58ebb9084dd`; relocation-index.json retains original paths/member hashes. Existing committed 26–34 relocation report is untouched and all worker files remain. Only metadata follows PASS; no runtime/test edit, repeated gate/build, external source/model/paid call, external message, push, PR, deployment, archive/index mutation, worktree removal or cleanup occurred in merger work.
