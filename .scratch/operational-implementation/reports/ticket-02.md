# Ticket 02: publish and inspect permitted ingested support

Status: implemented locally; ticket remains claimed for integration validation.

## Behavior and public interfaces

- `smi_ingestion.support.SupportReference(observation_id, derivation_id, assertion_ids, metric_ids=())` pins exact source membership. `IngestedEvidence(db, workspace_id).select_run(run_id, actor, include_synthetic=False)` selects at most 100 applied observations, independent of frozen imports. `read(references, actor, purpose="display", include_synthetic=False, connection=None)` validates workspace and assertion/metric ownership, returns policy-aware exact values or tombstones, and holds source/derivation share locks through caller-owned commits. Each reference is bounded to 1,000 assertion/metric IDs.
- `EvidenceStore.start_run(..., workspace_id="local")` establishes the trusted run owner. Existing callers remain local; snapshot import supplies its configured workspace. Ingestion migration restores existing imported run ownership from evidence sets. No canonical identity or frozen membership is rewritten.
- `smi_knowledge.KnowledgePublications(db, workspace_id).publish(support, actor, request_id=..., interpretation_ids=(), include_synthetic=False)` atomically commits validated source-only support and optional existing caption interpretations. Process permission and current derivations are mandatory. Stable source-backed accounts can retain unknown profile attributes. It stores exact membership/count metadata with the actual human or automation producer and publication method/time; no new source text copy is stored.
- `KnowledgePublications.list(actor, include_synthetic=False)` and `read(publication_id, actor, purpose="display", include_synthetic=False)` expose committed metadata and exact pinned support. Original publication coverage/time remains fixed, while `current_coverage` counts permitted/unavailable/superseded members. Source capture, source-as-of, ingestion, source-publication assertions, mapper versions and interpretation versions retain their separate meanings. Identical concurrent retries return one logical publication; changed support, interpretations, producer, method or synthetic mode under that request identity conflicts.
- `KnowledgeStore.read_interpretations(interpretation_ids, actor, purpose="display", include_synthetic=False, connection=None)` provides exact-ID reads through the interpretation owner. It reconciles retention-dependent copies and supports caller-owned publication transactions. Purged interpretations stay tombstones after permission restoration or a duplicate publication request.
- Operator commands: `smi-ingest publish-knowledge INGESTION_RUN_ID --request-id ID [--observation-id UUID ...] [--interpretation-id UUID ...]` and `inspect-publication PUBLICATION_ID`. The trusted CLI records its named human; programmatic workers supply their actual automation actor.
- Local GET surfaces: `/knowledge/publications` and `/knowledge/publications/PUBLICATION_ID`, linked from the main navigation. Detail rendering escapes values and withholds denied/superseded source text. Existing form-Origin/CSRF/actor protections remain intact; publication is an explicit trusted API/CLI operation.

## Red and green evidence

The TDD skill was applied at the approved public-operation/HTTP seams with real isolated-schema PostgreSQL and simulated source inputs.

1. Source-only fresh-ingestion publication: red on missing `smi_ingestion.support`; green with the exact-support reader and publication owner (**1 passed**).
2. Concurrent retry/producer integrity: red because a changed producer reused the publication; green after binding producer into the request digest (**2 passed**).
3. Existing caption interpretation selection: red on missing `interpretation_ids`; green with exact owner reads and source-assertion matching (**3 passed**).
4. Explicit synthetic visibility: red on missing `include_synthetic`; green with persisted synthetic publication gating (**4 passed**).
5. Policy-aware reopening: red on missing current support coverage; green with separate current/original counts (**5 passed**).
6. Local publication detail: red on HTTP 404; green with escaped list/detail routes, restart/reopen and source redaction (**6 passed**).
7. Operator CLI: red on missing `publish-knowledge`; green with bounded run/subset publication and separate-process inspection (**7 passed**).

Additional public-operation regressions verify whole-request refusal for an un-ingested member or withdrawal between selection and commit; superseded support never substitutes newer values; foreign-workspace publication/read denial; permanent interpretation-copy purge after restored permissions; imported-set immutability; legacy migration preserving a non-default workspace and exact source IDs; source-only publication without retaining a new copy; and display permission failing to authorize processing/publication.

## Validation

- `UV_OFFLINE=1 uv run --locked pytest -q tests/test_publications.py --tb=short --maxfail=1`: **14 passed**, 7.77 seconds.
- First shared `UV_OFFLINE=1 uv run --locked python tools/check.py`: **passed**, Ruff, document links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **220 passed**, 138.79 seconds.
- Final expanded `UV_OFFLINE=1 uv run --locked python tools/check.py`: **passed**, including Ruff, documentation/ERD/instruction checks, PostgreSQL preflight and **223 passed**, 140.70 seconds.
- `git diff --check`: passed.
- `UV_OFFLINE=1 uv build --wheel --out-dir /tmp/smi-ticket-02-wheel`: passed; archive inspection confirms the new exact-support/publication packages, knowledge SQL and local detail view are present.

Product documentation, physical ERD, table dictionary and local owner instructions describe the installed publication contract. New substantial `support` and `publications` submodules have `AGENTS.md` plus relative `CLAUDE.md -> AGENTS.md`. Existing wheel package roots already include these child packages; no packaging-root change is needed.

## Following tickets and limits

Ticket 03 can use publication list/read metadata and exact `SupportReference` membership to build bounded current-KB queries and separately pinned results. Ticket 04 can select support directly from its fresh ingestion run, then publish with its durable request identity and actual worker actor; no frozen dataset import is required. Creating an explicit new publication request can publish the same membership again; it does not by itself establish a new knowledge benefit, freshness, or task-success outcome. Callers must retain their task/query meanings.

General search, task submission/execution, background work, new ontology, embeddings and live provider/model calls are outside this slice. Existing caption preparation remains dataset-bound; source-only publication works for fresh observations. Source-owner canonical-value retention and synchronous interpretation cleanup preserve their existing documented lifecycle rather than claiming universal physical deletion. Language/marketer usefulness has not been evaluated by these technical tests.

The integration tip remains `7ba1a79`, already included in this branch; no advanced integration changes require merging. All work is offline/local. No later ticket was claimed, no external messages were sent, and no push/PR occurred. No genuine external blocker remains. Integration validation and ticket resolution belong to the merger.
