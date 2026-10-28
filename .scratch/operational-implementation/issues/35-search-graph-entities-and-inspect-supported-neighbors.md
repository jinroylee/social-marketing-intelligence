# 35: Search graph entities and inspect supported neighbors

**What to build:** A marketer can search permitted KB entities and inspect their immediate relationships and source evidence in a graph-oriented view.

**Blocked by:** 03: Search current knowledge and pin result support.

**Status:** claimed

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
- Status remains **claimed**. Independent merger-owned integration/root checking and resolution remain. No network/source/model execution, inferred Creator association, multi-hop expansion, new raw-fact store, external message, push, PR, deployment or cleanup occurred. Language/usefulness and complete market coverage remain unestablished.
