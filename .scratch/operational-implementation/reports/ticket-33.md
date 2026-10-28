# Ticket 33 — Selected monitoring evidence promotion

Implemented only the authoritative ticket in persistent worktree `/Users/makinarocks/workspace/personal/.smi-agent-worktrees/ticket-33`, branch `smi/operational-ticket-33`. Clean assigned base `e7a65d3edf9fda4f628a2ad6a2383c83deb619c7` and resolved blockers 02/29 were confirmed; prior root 775-test gate was preserved. Ticket remains **claimed** for independent merger resolution. No other ticket/subagent, shared planning edit or cleanup.

## Delivered behavior

- `MonitoringPromotion` owns one trusted explicit selection of 1–20 recent capture IDs from an original window, source-free exact request/results and one normal source/publication receipt per capture. It composes public recent/ingestion/publication interfaces in a local caller transaction, with no extra provider/model request, task or campaign. Unselected captures remain in the recent path.
- Normal source observations, `IngestionRunner.map_observation`, deterministic X `public` content mapping and ordinary `KnowledgePublications` are committed with dependencies/results. Transferred captures record **zero new requests** and no additional raw payload file. Source capture/publication/metric-measurement/import times, original acquisition/policy context, native metric definitions and mapper versions stay distinct. Missing source-as-of/account/creator/product associations stay unknown; status URLs and topic matches infer none.
- Exact request retries recover original effects/results; changed identity reuse conflicts. Fresh requests reuse source/publication IDs, checking current ordinary KB availability. Partial invalid selections retain item-level lineage; existing denied publications report `publication_unavailable`, never a new usable publication. Source-free original outcomes and current usability remain distinct.
- Ingestion-owned `SourceDependencies` receives parent policy/withdrawal/shortened-deadline mutations atomically with monitoring writes. Independent direct `KnowledgePublications`/`KnowledgeQueries` reads enforce mirrored source policy and permanent scoped expiry cleanup without any promotion-reader prerequisite. Retention loss/expiry/withdrawal clears copied canonical values and keeps tombstones. Parent recovery, fixture aliases, fresh requests and re-promotion cannot reconstruct purged selected or previously unselected support. Ingestion imports no monitoring private SQL or callbacks.
- Protected HTTP checkboxes start unchecked, preserve permitted request/selection context on errors and reject actor/source-policy/route/clock/campaign authority. Saved source-free result pages reopen after restart with exact monitoring/source/run/publication links and original outcomes; ordinary KB pages decide current availability. Offline evidence remains synthetic and requires explicit development visibility.
- Product contracts, architecture, physical ERD, glossary, ADR 0022 and owner guidance align. New promotion guidance has the required relative `CLAUDE.md -> AGENTS.md` sibling. Live X, broader promotion frameworks, automatic feed publication, semantic expansion and human language/marketer usefulness remain outside this slice.

## Verification

Applied implement-spec, TDD and references, domain-modeling and writing-for-agents at the previously authorized public promotion/monitoring/ingestion/KB/loopback HTTP seams. Real isolated PostgreSQL and counted forbidden acquisition/model/external transports; no internal collaborator mocks, private-method tests or SQL business-outcome assertions. Fault-only DDL and PostgreSQL blocker metadata establish rollback and in-flight mutation ordering.

Nineteen new journey cases cover provenance/unknown identity, zero-request transfer, partial selection/exact and concurrent reuse, direct KB policy/withdrawal/pinned-result behavior, deadline shortening, elapsed expiry, cross-workspace lock isolation, source mutation before mapping and queued during source insertion, atomic receipt failure, alias reconstruction denial, independently revoked source copies, missing times and protected HTTP/restart.

- Final focused compatibility: **87 passed in 56.03s**, exit **0**, completed session **83711**; exact command/head/start/finish/log in `verification/ticket-33/focused-final.{json,log}`. Runtime bytes were committed unchanged afterward.
- Final locked static check: **exit 0**, Ruff/documentation links/physical ERD/relative instruction links, `static-final.{json,log}`. `git diff --check` and stale-summary scan passed.
- Runtime implementation: **`67c58b6dab6bfa0db7a0a02693d7be9c6d96ad02`**. Latest integration metadata `8a519ff` merged before clean freeze: **`48cc8052cb604c6c5872ccdc1a7215a8e8c1556e`**. `freeze.json` hashes all **285** protected runtime/test/product-doc/tool/guidance files, including symlink targets.
- Required **`UV_OFFLINE=1 uv run --locked python tools/check.py` PASS**, exit **0**, **794 tests in 731.13s**, completed session **78065**. Started **2026-10-28T04:25:22.147638+00:00**, finished **2026-10-28T04:37:33.959398+00:00**. `shared.{json,log}` records exact command, frozen head, start/finish/session/exit and full output. This completed gate was preserved without rerun.

## Artifact and handoff

All **285 protected files** remained byte-for-byte unchanged through the frozen gate and offline build, including relative instruction targets (`freeze.json`, `freeze-verified.json`). After PASS, only this report, ticket checklist and exact manifest/verifier metadata changed. The final metadata commit cannot name itself; its SHA is supplied in the handoff.

Offline `UV_OFFLINE=1 uv build --wheel --out-dir .scratch/operational-implementation/verification/ticket-33/wheel` passed exit **0**, with exact build evidence in `wheel-build.{json,log}`. Artifact: `/Users/makinarocks/workspace/personal/.smi-agent-worktrees/ticket-33/.scratch/operational-implementation/verification/ticket-33/wheel/smi_ingestion-0.1.0-py3-none-any.whl`, **397759 bytes**, **192 unique archive entries**, SHA-256 **`890aeafc00bd710601770833479d2b32742a42dfbf911c01023fb741da02441a`**.

The committed [exact manifest](ticket-33-wheel-manifest.json) and [standalone verifier](verify-ticket-33-wheel.py) cover **88 exact source/archive pairs**: every changed packaged file, **16 SQL schemas**, both review assets and all **29 packaged guidance target/sibling pairs**, plus root guidance identity. Source/archive bytes, sizes, SHA-256 and relative sibling targets match. Record and independent non-record verification passed exit **0** (`wheel-record.{json,log}`, `wheel-verify.{json,log}`). Reproduce:

```sh
UV_OFFLINE=1 uv run --locked python .scratch/operational-implementation/reports/verify-ticket-33-wheel.py --root . --wheel .scratch/operational-implementation/verification/ticket-33/wheel/smi_ingestion-0.1.0-py3-none-any.whl
```
 Original final-review baseline **`6220fff49b5b8e982ef5a8d54b7c788e45b0f648`** remains preserved. Artifacts stay in this persistent worktree for independent verification and root archival/relocation before eventual cleanup.

No live source/model/paid call, message to another person, push, PR, deployment or cleanup occurred. Software verification establishes no live readiness, original-language quality or marketer usefulness. Merger-owned integration gate, exact artifact verification and ticket resolution remain required.
