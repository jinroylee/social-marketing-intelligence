# User and operator guide

This is the end-to-end manual for the **installed local application**. It explains what to run, what to save, what appears in the browser and how each action reaches storage. The [architecture](architecture.md), [physical data model](data-model.md) and linked owner contracts describe the implementation in greater depth. The [roadmap](roadmap.md) separates remaining validation from future product capabilities.

## 1. Find a workflow

Start with [installation and process operation](#2-install-configure-start-and-stop), then the [offline smoke walkthrough](#4-offline-smoke-walkthrough). All commands run from the repository root. `uv run --locked` uses the committed dependency lock. Uppercase names such as `CAMPAIGN_ID` below mean **replace with the exact returned value**, not a literal example UUID. Request IDs such as `guide-campaign-1` are names you choose; retain them for retries.

| Feature | Entry point | Installed / configuration / limits |
| --- | --- | --- |
| Frozen sample and direct ingestion | [4](#4-offline-smoke-walkthrough), [5](#5-direct-ingestion-replay-resume-and-source-policy) | Offline import and bounded adapters; live manifests can perform external I/O |
| Catalog, caption interpretations and publication | [6](#6-catalog-interpretations-and-explicit-publication) | Deterministic local rules; interpretations stay provisional |
| Current-KB search | [7](#7-search-and-reopen-current-knowledge) | Literal bounded search of committed publications |
| Campaign briefs and visible executable criteria | [8](#8-create-and-revise-a-campaign-brief) | Human structured needs; optional configured model additions |
| Frozen and current-KB comparisons | [9](#9-compare-frozen-or-current-knowledge) | Deterministic unranked comparisons with explicit gaps |
| Automatically saved recommendations, model order, human curation | [10](#10-save-recommendations-and-optionally-curate-them) | Automatic generated revisions; human draft/confirmation are separate |
| Coverage discovery and explicit regeneration | [11](#11-coverage-triggered-discovery-and-explicit-regeneration) | Saves first, acknowledges a bounded task, never runs it implicitly |
| Supplied proposals, queued work, worker recovery and inbox | [12](#12-proposals-task-acknowledgment-worker-and-recovery) | Explicit one-task execution; local durable completion messages |
| Free-form KB questions and approved gap enrichment | [13](#13-ask-knowledge-and-follow-a-gap-to-a-new-answer) | Extractive model selection; exact human acquisition approval |
| Registered keyword configuration, due ticks and day allowance | [14](#14-configure-keywords-and-acknowledge-due-work) | At most ten registrations; shared unique-new-post admission |
| Independent frozen investigations | [15](#15-investigate-a-frozen-snapshot-without-a-campaign) | Literal snapshot summaries, no trend baseline |
| Recent X topics, windows and timelines | [16](#16-configure-and-poll-recent-x-offline) | Separate bounded synthetic route, policy and retention |
| Quantitative and provisional semantic alerts | [17](#17-assess-volume-and-provisional-quality-positions) | Explicit thresholds; model setup only for semantic positions |
| Alert KB context and selected promotion | [18](#18-investigate-alerts-and-promote-selected-captures) | Existing KB only; explicit 1–20 capture promotion |
| Periodic live X polling | [19](#19-configure-separate-periodic-live-x-authority) | Gated Python worker; no daemon or verified live readiness |
| Graph search/traversal and task lineage | [20](#20-explore-the-graph-and-task-lineage) | Bounded governed read projections |
| Proposed measurement and decision notes | [21](#21-record-measurement-intent-and-human-learning) | Human intent/feedback; no commercial outcome ingestion |
| Usage, forecasts, ceilings, reconciliation and meter recovery | [22](#22-configure-and-inspect-costs) | Explicit scope/rates; synthetic or provider-reported basis |
| Quality packet export, annotation and reopening | [23](#23-export-record-and-reopen-quality-review) | Software installed; actual human validation remains pending |
| Model composition, source gates, verification and troubleshooting | [24](#24-configure-model-and-live-source-operations), [25](#25-check-build-and-troubleshoot) | Trusted operator configuration; no fictional CLI model flags |

## 2. Install, configure, start and stop

### 2.1 Prerequisites and settings

Use Python **3.12 or newer**, `uv`, and a working Docker/Compose installation, or an existing PostgreSQL development instance. The project depends on Psycopg; development tools add pytest and Ruff. No LLM key is needed for the deterministic offline path. There is no Node/frontend build step.

| Setting / option | Default and effect |
| --- | --- |
| `SMI_DATABASE_URL` / `--dsn` | `postgresql://smi:local_only_change_me@127.0.0.1:6543/smi`; application connection |
| `SMI_DATABASE_SCHEMA` / `--schema` | Unset: PostgreSQL's normal search path. When set, select an **existing** schema; the CLI does not create it |
| `SMI_EVIDENCE_DIR` / `smi-ingest --evidence-dir` | `.evidence`, relative to the working directory; permitted retained payloads |
| `SMI_TEST_DATABASE_URL` | Separate test/preflight DSN; defaults to the same local development URL, independently of `SMI_DATABASE_URL` |
| `smi-review --actor` | `local-marketer`, the trusted local human attribution |
| `smi-review --port` | `8765`, bound to `127.0.0.1` only |

The Python entry points read the **process environment**. They do not load `.env` themselves. For an optional operator-managed env file, explicitly use `uv run --env-file .env ...`; another option is exporting selected variables in the shell. `.env.example` is a template, not an active configuration or a source of credentials. Do not print or commit real credentials. CLI global connection/schema/evidence options go **before** the subcommand; action-specific `--actor` goes after it. Python examples below construct `Database` explicitly because its constructor has no environment defaults.

Compose creates PostgreSQL 16 with local database/user `smi` and the development password shown above. Host processes use `127.0.0.1:6543`; `5432` is PostgreSQL's port inside its container. A future application container on the Compose network would use `postgres:5432`, but **no such web or worker service exists in this Compose file**. The repository contains no complete Docker deployment for the application.

### 2.2 First startup

```bash
docker compose up -d --wait postgres
uv sync --locked
uv run --locked smi-ingest migrate
uv run --locked smi-review --actor local-marketer
```

Open <http://127.0.0.1:8765>. Migrate explicitly on first setup and after pulling schema changes. Migration is idempotent and installs ingestion, knowledge/query/graph, campaign/planning, monitoring, task/assistant/inbox and cost prerequisites. It preserves historical records; it does not populate the sample. Starting `smi-review` neither migrates nor imports nor contacts a source. Complete [section 4](#4-offline-smoke-walkthrough) to populate it.

The server prints its URL and configured reviewer. It uses a standard-library threaded HTTP server and bundled CSS/JavaScript. Missing database/schema setup produces an actionable unavailable/setup page. A default server has no model transport, no offline task manifest, and no schedule/monitoring mutation role. Read histories remain available when optional execution configuration is removed.

### 2.3 Processes, restart and persistence

| Process / operation | How to start | How it stops / what survives |
| --- | --- | --- |
| PostgreSQL | `docker compose up -d --wait postgres` | `docker compose stop postgres`; named volume preserves database |
| Browser server | `uv run --locked smi-review --actor local-marketer` | Ctrl-C; restart the same command and reopen saved URLs |
| One offline task | `uv run --locked smi-ingest run-offline-task TASK_ID` | Exits after that task's bounded execution/wait/outcome |
| Keyword due check | `ScheduledDiscovery.tick(actor)` or **Acknowledge due tasks** | Returns task acknowledgments; it does not collect |
| Periodic recent-X work | `RecentPolling.run_due(automation)` | Handles at most one due interval per invocation |

There is **no continuous queue consumer, automatic dispatcher, cron service or scheduler daemon**. Leaving the web server running does not execute queued tasks, tick keyword schedules or poll X. An operator must invoke the worker/tick explicitly or supply an external scheduler under the documented authority. PostgreSQL revisions and task receipts survive process restarts. Raw evidence also needs the same retained evidence directory when replay is required. Server restart rotates CSRF tokens: reload forms before saving. Do not use `docker compose down -v` as a routine stop; it removes the database volume.

## 3. Understand actors, IDs and time

The local default workspace is `local`. Python public interfaces take `ActorContext(workspace_id, actor_id, kind)` with `kind="human"` or `"automation"`. The trusted CLI/server constructs these identities; typing a human name, an `approved` field, or a model instruction does not grant a role. Hosted accounts, authentication and tenant administration are future work. Configure campaign automation, proposal approvers, schedule operators and monitoring operators separately.

| Identity | Where it comes from / where it is used |
| --- | --- |
| `dataset_id` | Human manifest ID: `jp-kbeauty-tiktok-public-video-sample-2026-10-05`; frozen membership, not a mutable KB |
| Catalog / Brand / Product IDs | Human configuration: `beauty-caption-lexicon-v1`, `aprilskin`, `aprilskin-hero-cushion` |
| Ingestion `run_id` | UUID returned by `ingest` or `import-snapshot`; collects/maps raw evidence. Task attempts also name one |
| `observation_id`, `derivation_id`, assertion/metric IDs | Exact local source capture, mapper application and supported values; inspect-set/query/publication exposes them |
| Knowledge preparation `run_id` | UUID returned by `prepare-knowledge`; owns provisional interpretations. **Not** the import/ingestion run UUID |
| `publication_id`, query `result_id` | UUIDs returned by explicit publication/search; pin exact committed membership |
| `campaign_id`, `brief_id`, `comparison_id`, `shortlist_id` | UUIDs returned by corresponding saves; brief and shortlist also have independent version heads |
| `interpretation_id` | Campaign criteria interpretation UUID; distinct from caption-interpretation IDs in a knowledge run |
| `proposal_id`, `scope_digest`, `approval_id`, `task_id` | Saved executable proposal, exact scope hash, actual approval and durable queued work |
| Task `attempt_id`, `execution_id`, `event_id` | Durable attempt, temporary worker ownership and terminal completion event; recovery keeps attempt/run |
| Topic key / revision, `window_id`, monitoring `observation_id` | Separate recent monitoring identities. A monitoring capture is not an ingestion observation until explicit promotion |
| Assessment / alert / notification / investigation / promotion IDs | Separate durable monitoring results; a snapshot investigation and an alert investigation have different owners |
| `operation_id`, measurement/reconciliation/recovery IDs | Cost-operation UUID plus caller-chosen stable ledger identities; not an acquisition approval |
| `packet_id`, review-record IDs | Exact operational review selection and attributed annotation history |

External account/content identity is `(platform, namespace, resource kind, native string ID, synthetic flag)`. For example, `tiktok / web:public / content / 7632620458235530504` is a supplied sample post. Handles/URLs are mutable references, not identity keys. An account is not yet a corroborated cross-platform Creator/person. Graph adjacency cannot establish that association.

Keep source **publication**, **capture**, **source-as-of**, metric **measurement**, local **ingestion/import**, knowledge **publication** and decision **assessment** times separate. Importing an October capture in November does not refresh it. Digests identify unchanged bytes/configuration, not relevance. New request IDs mean new logical work; changing a payload under an old ID conflicts. Expected versions reject stale edits. Historical support remains pinned, while **current** process/display/retention permission and derivation health determine what may be computed or shown now. See [glossary](../GLOSSARY.md) and [current-policy ADR](adr/0002-pinned-support-current-policy.md).

```mermaid
flowchart LR
    Local[Local export / bounded collector] --> Ingest[Ingestion run and source observations]
    Ingest --> Canonical[Exact assertions / metrics / derivation]
    Canonical --> Frozen[Frozen dataset membership]
    Frozen --> Rules[Provisional caption interpretations]
    Canonical --> Publish[Explicit knowledge publication]
    Rules --> Publish
    Publish --> Query[Saved current-KB query]
    Query --> Decision[Comparison / shortlist / answer / graph]
    Frozen --> Snapshot[Independent snapshot investigation]
    Recent[Separate recent X window] --> Alert[Volume / provisional semantic alert]
    Query --> Context[Existing-KB alert context]
    Alert --> Context
    Recent -->|selected promotion| Ingest
```

## 4. Offline smoke walkthrough

This path uses local files, PostgreSQL and deterministic rules. It makes no provider/model calls. Follow it after `uv sync --locked` and PostgreSQL startup. Save each JSON response; shell variables below contain values you copy from those responses.

### 4.1 Migrate and import the exact curated sample

```bash
uv run --locked smi-ingest migrate
uv run --locked smi-ingest import-snapshot examples/curated/jp-kbeauty-tiktok-2026-10-05/snapshot-manifest.json --actor local-marketer
uv run --locked smi-ingest inspect-set jp-kbeauty-tiktok-public-video-sample-2026-10-05 --actor local-marketer
```

The first import returns `status="imported"`, the exact dataset ID, digest, **ingestion** `run_id`, `posts=19` and `accounts=17`. A repeat returns `status="duplicate"` and the original run/digest. The pinned export SHA-256 is `86d5ef8d706266cf256b45683ddb0565a09687f118dbda396f45374ba1f935e8`. It is a fixed real-world public-page sample captured on **2026-10-05 UTC**, not synthetic or a representative Japan-market survey. Source posts span 2023–2026; full histories, audience geography and sales are absent. Original export IDs remain lineage; use the returned **local** IDs in later commands.

```bash
SAMPLE_INGESTION_RUN_ID='REPLACE_WITH_IMPORT_run_id'
uv run --locked smi-ingest register-catalog examples/catalogs/beauty-v1.json --actor local-marketer
uv run --locked smi-ingest prepare-knowledge jp-kbeauty-tiktok-public-video-sample-2026-10-05 beauty-caption-lexicon-v1 --actor local-marketer --request-id guide-knowledge-1
```

Capture the preparation's `run_id` separately as `KNOWLEDGE_RUN_ID`. Inspect its actual interpretation IDs and coverage:

```bash
KNOWLEDGE_RUN_ID='REPLACE_WITH_PREPARATION_run_id'
uv run --locked smi-ingest inspect-knowledge "$KNOWLEDGE_RUN_ID" --actor local-marketer
```

### 4.2 Publish source support for current-KB workflows

```bash
uv run --locked smi-ingest publish-knowledge "$SAMPLE_INGESTION_RUN_ID" --request-id guide-publication-1 --actor local-marketer
uv run --locked smi-ingest search-knowledge --text APRILSKIN --platform tiktok --max-age-seconds 2592000 --request-id guide-search-1 --actor local-marketer
```

Copy publication `publication_id` and search `result_id`. Source-only publication makes observed facts available; it does **not** automatically include prepared caption interpretations. To assess literal Brand/Product/script criteria in **current-KB** recommendations, explicitly select the permitted caption interpretation IDs returned by `inspect-knowledge`:

```bash
uv run --locked smi-ingest publish-knowledge "$SAMPLE_INGESTION_RUN_ID" --request-id guide-publication-with-claims-1 --interpretation-id CAPTION_INTERPRETATION_ID --actor local-marketer
uv run --locked smi-ingest inspect-publication PUBLICATION_ID --actor local-marketer
uv run --locked smi-ingest inspect-query RESULT_ID --actor local-marketer
```

Repeat `--interpretation-id` for each intended claim, up to the owner's selection bounds. Do not reuse `guide-publication-1` with changed membership. Alternatively, the public Python selection in [6](#6-catalog-interpretations-and-explicit-publication) publishes all supported claims from this bounded run. The already saved `guide-search-1` stays pinned; use a new request ID for a query that includes the later claims.

### 4.3 Make a campaign and inspect a pinned comparison

```bash
uv run --locked smi-ingest start-campaign examples/campaigns/hero-cushion-brief.json --actor local-marketer --request-id guide-campaign-1
uv run --locked smi-ingest prepare-comparison CAMPAIGN_ID BRIEF_ID "$KNOWLEDGE_RUN_ID" --actor local-marketer --request-id guide-comparison-1
uv run --locked smi-ingest inspect-comparison COMPARISON_ID --actor local-marketer
uv run --locked smi-review --actor local-marketer --offline-manifest examples/synthetic/keyword-discovery-manifest.json --offline-route-version offline-keyword-v1
```

Capture `campaign_id`, `brief_id`, `brief_version` from start and `comparison_id` from comparison. Open the campaign from `/`, inspect the frozen comparison, then try **Compare current knowledge** and **Recommend and save automatically**. The latter saves a generated shortlist immediately. Its source capture freshness and any coverage-triggered discovery refusal/task remain explicit; the synthetic discovery corpus does not guarantee a match for the sample product. Default model actions show unavailable configuration. Do not interpret that as a live/model smoke failure.

### 4.4 Acknowledge and execute one independent offline task

With those returned campaign/brief IDs, this supplied-reference fixture demonstrates the complete queue-to-publication path:

```bash
uv run --locked smi-ingest submit-campaign-task CAMPAIGN_ID --brief-id BRIEF_ID --purpose 'Exercise local fixture acquisition' --request-id guide-task-1 --offline-manifest examples/synthetic/json-manifest.json --actor local-marketer
uv run --locked smi-ingest inspect-task TASK_ID --actor local-marketer
uv run --locked smi-ingest run-offline-task TASK_ID --worker-id local-offline-task-worker
uv run --locked smi-ingest list-inbox --actor local-marketer
uv run --locked smi-ingest inspect-completion EVENT_ID --actor local-marketer
```

Submission returns `task_id` and `status="accepted"` before collection. Inspect before running: queued work has no attempt. The worker returns the same task with its attempt/run, actual coverage, outcome and publication metadata. Inbox supplies `event_id`. In the browser, open **Tasks**, the exact task's **Lineage**, and **Inbox**. Synthetic source values require explicit development visibility (`include_synthetic=yes` where offered); metadata remains visible by default. Existing identical usable captures can produce `no_usable_update`, so a new publication is not guaranteed on repeat demonstrations. Restart the server and reopen saved IDs to verify persistence. [Section 25](#25-check-build-and-troubleshoot) describes automated verification separately.

## 5. Direct ingestion, replay, resume and source policy

**Prerequisites and actions.** Migrate PostgreSQL and choose a bounded manifest. These direct fixture operations bypass task admission and do not publish to the KB:

```bash
uv run --locked smi-ingest ingest examples/synthetic/json-manifest.json
uv run --locked smi-ingest ingest examples/synthetic/html-manifest.json
uv run --locked smi-ingest inspect tiktok fixture:public content fixture-post-1 --include-synthetic
uv run --locked smi-ingest replay OBSERVATION_ID
uv run --locked smi-ingest resume INGESTION_RUN_ID
```

Both fixtures describe one canonical content identity with separate observations and dated `synthetic.views.v1` measurements. Copy `run_id` from ingest and an exact local `observation_id` from inspection. `inspect` is an administrative current-value projection; it does not save a decision or authorize an application actor. Without `--include-synthetic`, fixture evidence is hidden.

**Result and technical path.** CLI → `IngestionRunner` → registered collector → `EvidenceStore` observation/checkpoint/usage/final-input commit → deterministic mapper → `CanonicalWriter` assertions/metrics/derivation commit. Reports distinguish requested-input coverage, collected/applied/quarantined counts, unresolved identities, missing fields, request/byte limits and sanitized issues. `complete_for_requested_input` means the manifest was processed, never platform completeness. `status="partial"` exits 2; failed actions/task failure exit 1. Default direct ingest bounds are 10 HTTP/collector requests, 100 records and 1 MiB total bytes; adapters can impose stricter bounds. `--max-requests`, `--max-records`, `--max-bytes` are direct-ingest options.

**Recovery.** Resume validates the original request-file digest and uses saved pending evidence before collecting again. A durably saved final capture can finish at its request/record limit without another call. Replay hash-checks retained bytes; the same mapper/policy reports a duplicate, while a later mapper may supersede an earlier derivation. A new capture/run can append a new dated metric; it is not the same as replay. Missing non-retained payload cannot be reconstructed by replay. Keep the original files/evidence root for operations that still need them. [Evidence sets](evidence-sets.md) explains frozen imports; [source integrations](source-integrations.md) describes per-adapter bounds.

Frozen snapshot import is atomic and retries through `import-snapshot`; its import run does **not** use the acquisition runner's `resume`. Retained individual imported observations may still be replayed without changing frozen membership.

**Withdrawal and cleanup.** These are explicit operator mutations, not ordinary read-only inspection:

```bash
uv run --locked smi-ingest revoke OBSERVATION_ID
uv run --locked smi-ingest expire
uv run --locked smi-ingest reconcile
uv run --locked smi-ingest reconcile-knowledge jp-kbeauty-tiktok-public-video-sample-2026-10-05 --actor local-marketer
```

Revoke makes that observation unavailable. `expire` removes due retained payloads; `reconcile` removes old unreferenced evidence files after interrupted writes. Knowledge reconciliation clears no-longer-retainable derived copies. Public readers apply current permission/supersession, and downstream owners synchronously hide/purge dependent wording under their contracts. Recovery of permission does not recreate purged text. There is no universal background deletion service; operator-saved exports/input files require their own handling. A pinned manifest grants no permanent display right.

To add a source, implement public `Collector.collect` and deterministic `Mapper.normalize`, register them with `AdapterRegistry.register`, and preserve native namespaces, coverage, source times, metrics, policy and cost bounds. Collectors/mappers do not write canonical tables. This is a developer extension, not a browser feature or general source editor.

## 6. Catalog, interpretations and explicit publication

**Prerequisites/action.** Import the frozen set and register the catalog as in section 4. Catalog registration is a named-human configuration operation; changes under the same catalog ID conflict. Use a new catalog ID for a different document. Brand/Product references are human configuration, not observed platform facts. Preparation uses dataset/catalog/request identity; default request is `initial`, while a new named request explicitly prepares again.

**Observe/capture.** Save knowledge `run_id`, method/catalog/dataset digest, actual processed/unavailable counts and caption interpretation `id` values. `inspect-knowledge` and `review-packet KNOWLEDGE_RUN_ID` reopen them. Rules produce exact Unicode `[start,end)` caption spans for literal Brand/Product/topic, kana and PR/Qoo10 markers. They establish no stance, efficacy, Japanese audience, paid contract or sales. Translations and human semantic review start pending. Browser frozen comparison preparation can create its own deterministic knowledge run.

For a bounded sample, the following public Python operations explicitly publish all currently supported interpretations from its prepared run. This is an alternative to repeated CLI `--interpretation-id` arguments; replace the two run IDs from section 4. Run Python with `uv run --locked python`, then use this setup for subsequent examples:

```python
import os
from pathlib import Path
from smi_ingestion.db import Database
from smi_ingestion.evidence_sets import ActorContext

db = Database(
    os.environ.get("SMI_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi"),
    os.environ.get("SMI_DATABASE_SCHEMA"),
)
human = ActorContext("local", "local-marketer", "human")
automation = ActorContext("local", "local-rule-preparation", "automation")
evidence_root = Path(os.environ.get("SMI_EVIDENCE_DIR", ".evidence"))

from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgeStore, KnowledgePublications

source_run_id = "REPLACE_WITH_IMPORT_run_id"
knowledge_run_id = "REPLACE_WITH_PREPARATION_run_id"
knowledge = KnowledgeStore(db)
prepared = knowledge.read(knowledge_run_id, human)
claim_ids = tuple(i["id"] for i in prepared["interpretations"] if i["state"] == "supported")
support = IngestedEvidence(db).select_run(source_run_id, human)
published = KnowledgePublications(db).publish(
    support, human, request_id="guide-publish-all-claims-1", interpretation_ids=claim_ids,
)
print(published)
```

**Technical path/boundary.** `KnowledgeStore.prepare` reads public process-permitted frozen evidence, performs pure caption rules and commits support-linked provisional interpretations. `IngestedEvidence.select_run` supplies exact applied observation/derivation/assertion/metric membership; `KnowledgePublications.publish` validates it and selected existing interpretations, then commits all membership atomically under source locks. Import, preparation and publication are different stages and UUIDs. Publishing source support alone requires no extra copied interpretation body; selected interpretations need their own permitted/current dependencies. Invalid members reject the publication. Request identity binds ordered selection and actual producer; changed retries conflict. Reopening never silently substitutes newer derivations or restores purged claims. There is no general catalog editor or translation UI. See [knowledge contract](knowledge.md).

## 7. Search and reopen current knowledge

**Action.** Open **Knowledge search** at `/knowledge/search`, supply literal text/platform/subject/capture filters, optional freshness seconds and a 1–100 member limit, then **Search and preserve result**. The exact page is `/knowledge/results/RESULT_ID`. CLI equivalence:

```bash
uv run --locked smi-ingest search-knowledge --text APRILSKIN --platform tiktok --limit 20 --max-age-seconds 2592000 --request-id guide-search-2 --actor local-marketer
uv run --locked smi-ingest inspect-query RESULT_ID --actor local-marketer
```

Use repeatable `--platform`/`--subject-id`, `--captured-from` inclusive and `--captured-to` exclusive timezone-aware bounds where needed. Python callers use `KnowledgeQueries(db).search(QueryScope(...), human, request_id=..., purpose="display")`; `read(result_id, human)` reopens. Source-backed account identities can match even when profile/caption fields are missing.

**Observe/path.** Capture `result_id`, exact manifest, original/current coverage and each source's freshness/health. `KnowledgeQueries` scans at most the 100 newest committed publications, selects at most 100 distinct support bundles in publication/member order, and saves only source IDs/methods/versions/times. It performs no semantic/vector retrieval, model or source request. No task approval is needed. Literal filters combine at observation-member scope; results are neither a creator ranking nor a complete KB/market inventory.

**Permissions/retry.** A new query requires process plus output-purpose permission. A display-only grant cannot authorize computation. Stale but permitted captures remain visible as stale; missing/future captures remain unknown. Exact retries return the same result before newer publications are considered. Reopen never reruns search; use a new request to see new publications. Current read policy returns unavailable/superseded metadata without source text. Synthetic mode must be explicitly enabled both on creation and reopen. Publication browsing at `/knowledge/publications/PUBLICATION_ID` shows its distinct historical support and current health. [Contract](knowledge.md#bounded-current-knowledge-queries).

## 8. Create and revise a campaign brief

**Prerequisites/action.** Register a catalog. Open **Create a brief** at `/campaigns/new`, choose Brand/Product scope, objective, intended market, platforms and at least one visible criterion. Brand-level scope may omit products. Supply exact native known-account identities where applicable. Original prose, dates, budget/currency and audience needs are human inputs; missing commercial values stay unknown. CLI:

```bash
uv run --locked smi-ingest start-campaign examples/campaigns/hero-cushion-brief.json --request-id guide-campaign-2 --actor local-marketer
uv run --locked smi-ingest inspect-campaign CAMPAIGN_ID --actor local-marketer
uv run --locked smi-ingest revise-brief CAMPAIGN_ID YOUR_SUCCESSOR_BRIEF.json --expected-version BRIEF_VERSION --request-id guide-brief-2 --actor local-marketer
```

`YOUR_SUCCESSOR_BRIEF.json` is an operator-supplied JSON document with the same [Brief fields](../examples/campaigns/hero-cushion-brief.json), edited for the new question; keep criterion IDs for unchanged needs. `CampaignStore.start` / `revise_brief` are public Python equivalents. Capture `campaign_id`, `brief_id`, `brief_version`; use current values from campaign history for new work.

**Observable result/path.** `/campaigns/CAMPAIGN_ID` shows exact original input, immutable executable profile, actual author/time, brief history and independent comparison/shortlist histories. `CampaignStore` validates catalog scope and transactionally appends the human brief/profile in PostgreSQL. Criteria retain label, typed value, include/exclude, required/preference and `unknown_handling`. `acknowledge` leaves an explicit exploratory gap; `defer` on a required unknown blocks confirmation/automatic eligibility. Model-generated additions require [section 24](#24-configure-model-and-live-source-operations) and explicit later selection; they never replace human constraints.

**Boundaries.** Creating a campaign neither discovers a source nor contacts/hires a creator or activates an external campaign. Human-only writes and expected heads prevent role forgery/stale overwrite. Identical request/body/actor retries reopen the original; use a new ID for a genuinely revised brief. Pre-profile historical records honestly show no recorded profile. Audience geography, fees, availability, contracts, sales and complete history remain unknown without support. [Contract](campaigns.md#implemented-briefs-and-actors).

## 9. Compare frozen or current knowledge

| Choice | Action / prerequisite | Captured result and behavior |
| --- | --- | --- |
| Frozen snapshot | Campaign page → choose dataset → **Prepare a comparison**, or `prepare-comparison CAMPAIGN_ID BRIEF_ID KNOWLEDGE_RUN_ID --request-id ...` | Exact dataset/digest/knowledge run and enumerated observations; known/retrieved/both origins |
| Current KB | Campaign page → **Compare current knowledge** | Independent of frozen datasets; exact bounded query, stable supported accounts and discovery seeds |

Both open `/comparisons/COMPARISON_ID`; `inspect-comparison` reopens the same ID. Optional explicitly selected successful campaign `interpretation_id` must belong to that exact brief. The normal CLI frozen comparison has no interpretation flag; use its browser form or public API for selection:

```python
from smi_campaigns import CampaignStore
campaigns = CampaignStore(db)
comparison = campaigns.prepare_current_comparison(
    "CAMPAIGN_ID", "BRIEF_ID", automation, request_id="guide-current-comparison-1",
    interpretation_id=None, max_age_seconds=2592000,
)
print(comparison)
```

**Inspect.** Open evidence panels for exact observation/assertion/interpretation IDs, original caption/spans, source links, source publication/capture/as-of/ingestion times and unknowns. Judgments are `satisfied`, `not_satisfied_on_evidence` or `unknown`; a missing mention is not a negative fact. Current-KB candidates require one stable supported platform account and at least one permitted published observation; full profiles/history/captions are not required. Handle-only or unsupported known references remain discovery seeds. Platform and human publication bounds apply; unknown publication dates cannot satisfy a configured publication window. Current-KB bounds are 100 publications/support bundles/accounts, independently reported.

**Technical path.** Browser/CLI → `CampaignStore` → frozen `KnowledgeStore`/`EvidenceSetReader` or current `KnowledgeQueries.search`/`account_support` → deterministic caption judgments → pinned comparison. Preparation calls no model/source and saves no shortlist. Required observed exclusions become excluded; required unknowns with `defer` become deferred; otherwise candidates are eligible with explicit gaps. Both methods are unranked deterministic comparisons, not performance/creator scores.

**Retry/policy.** Same request returns exact original membership/order/profile even after new knowledge. A new request against an old brief fails; revise then prepare a new comparison. Source locks protect commit; policy/correction races can reject it as changed support. Reopen applies current policy, hides dependent wording conservatively and purges no-longer-retainable explanations/reasons. Use a new successor for newly permitted inputs; old wording is not reconstructed. Empty comparisons record no supported candidates in scope, not an empty market. [Contract](campaigns.md#current-kb-comparison).

## 10. Save recommendations and optionally curate them

### 10.1 Automatic generated revisions

On the campaign page, **Recommend and save automatically** saves a generated shortlist using deterministic current-KB order. **Rank and save automatically** uses the separately configured bounded Responses route after deterministic eligibility. There is no human review/confirmation checkbox on either automatic action. Capture `shortlist_id`, version, exact comparison/profile, producer/method, selected/excluded/deferred counts, coverage and any ranking assessment/cost-operation ID.

Python direct owner operations are `CampaignStore.recommend` and `recommend_ranked`; both take campaign/brief/automation actor and `expected_brief_version`, `expected_shortlist_version`, `request_id`, optional `interpretation_id`, synthetic mode and freshness. Use head values returned by `read_campaign`, including shortlist head 0 before any save. For save-first coverage discovery use [the composition in section 11](#11-coverage-triggered-discovery-and-explicit-regeneration), as the browser does.

Deterministic selection preserves eligible comparison encounter order. Model ranking accepts exactly one permutation of eligible candidates, with one constrained criterion reason each: supported fit with its own citations, observed contradicted optional preference with citations, or limited evidence for unknowns without citations. Reasons render server-side from codes; arbitrary factual prose or invented IDs invalidate the result. It cannot admit excluded/deferred candidates, remove gaps or create human acknowledgments. This is generated relative fit over provisional support, not independent semantic verification.

The campaign owner saves comparison/support/order/revision atomically for deterministic work, or commits a one-use ranking claim before model I/O and finalizes only a validated current result. Successful empty batches save an empty revision without a model call. Failed, blocked, invalid, stale, in-flight or uncertain model outcomes remain visible with no deterministic success fallback. Exact retries reopen the same result/claim, never redispatch a lost response. Current policy governs **all** actual model inputs and dependent judgments, not only chosen citations. [Automatic persistence](campaigns.md#automatic-deterministic-shortlist-persistence), [ranking](campaigns.md#bounded-supported-llm-ranking).

### 10.2 Optional human draft, order and confirmation

Open `/shortlists/SHORTLIST_ID` and **Create successor revision**. Inspect the exact source revision/comparison, select accounts, set distinct positive positions, write human reasons, cite permitted relevance interpretations and acknowledge recorded unknowns. **Save draft** creates a human successor without review endorsement. **Confirm shortlist** additionally requires the separate explicit reviewer checkbox and current support/required-criterion/unknown checks. Both preserve the original generated revision and its model/deterministic basis.

The basic frozen-comparison CLI supports a user-created selections file:

```bash
uv run --locked smi-ingest save-shortlist COMPARISON_ID selections.json --expected-version SHORTLIST_VERSION --request-id guide-human-draft-1 --actor local-marketer
uv run --locked smi-ingest save-shortlist COMPARISON_ID selections.json --confirm --expected-version NEXT_SHORTLIST_VERSION --request-id guide-human-confirm-1 --actor local-marketer
```

`selections.json` is a list of `candidate_id`, human `reason`, `support_ids` and `acknowledged_unknowns` from that comparison; `[]` records deliberate deferral. For source-revision ordered curation use the browser or public `save_shortlist(..., source_shortlist_id=..., selections=..., ...)`: the submitted `Selection` tuple's order determines saved zero-based positions. `Selection` has no position field; the browser sorts its positive position controls before calling the owner. The basic CLI exposes no source-successor flag. Use returned/current shortlist version, not the brief version. A revised brief needs a new comparison. Stale/changed requests conflict instead of replacing history; recoverable browser errors preserve permitted edits and original retry/head context. Unavailable support withholds saved and submitted reasons. Saving/confirming performs no outreach, contract or campaign activation. [Curation contract](campaigns.md#human-shortlist-persistence).

## 11. Coverage-triggered discovery and explicit regeneration

**Prerequisites/action.** Browser recommendations use `CampaignRecommendations`, combining a `CampaignStore` with configured `AcquisitionTasks` and a specific authorized campaign automation. To configure the same offline journey in the Python session, reuse `campaigns` from section 9:

```python
from smi_tasks import AcquisitionTasks, OfflineRoute, TaskAuthority
from smi_tasks.campaigns import CampaignRecommendations

tasks = AcquisitionTasks(db, route=OfflineRoute(
    Path("examples/synthetic/keyword-discovery-manifest.json"), "offline-keyword-v1",
), authority=TaskAuthority(
    campaign_automations=frozenset({automation.actor_id}),
    proposal_approvers=frozenset({human.actor_id}),
))
recommendations = CampaignRecommendations(campaigns, tasks)
saved = recommendations.recommend(
    "CAMPAIGN_ID", "BRIEF_ID", automation, ranked=False,
    expected_brief_version=1, expected_shortlist_version=0,
    request_id="guide-recommend-1", max_age_seconds=2592000,
)
print(saved)
print(recommendations.read(saved["shortlist_id"], human))
```

The numeric heads above apply only to a newly created campaign; use actual current heads for an existing one. `ranked=True` requires a model-configured `campaigns` from section 24.

**Observe/path.** First, the campaign owner commits its supported generated shortlist, even if empty. Saved coverage policy `supported-campaign-coverage-v1` requires three eligible accounts, three with a satisfied supported include criterion, and three whose entire support has known, nonfuture captures within 30 days. These are local operational thresholds, not validated marketing targets. Task-side composition then records exactly one disposition per shortlist: `not_needed`, `refused` plus reason, or `submitted` plus `task_id`. The saved recommendation remains readable during refusal/wait/failure. Task admission and disposition commit together, separately from the first save.

Discovery scope is deliberately narrow: first human product's exact catalog name and `product:ID`, otherwise exact brand name and `brand:ID`; 30 days before the saved assessment instant intersected with human publication bounds. It uses the configured TikTok keyword capability, not objective/model prose or every alias/platform. Non-TikTok briefs, empty windows, missing capability/route, stale brief, unavailable support or denied policy can refuse it. Mixed-platform scope labels the unsearched platforms. The offline corpus may return nothing; importing old captures cannot satisfy freshness.

**Execute and regenerate.** Copy the disposition's returned `task_id`, then run `run-offline-task TASK_ID` separately. A usable/partial durable completion with current usable publication links offers **Regenerate** at `/inbox/EVENT_ID/regenerate`. Inspect current human brief/profile, explicitly select any successful current-brief interpretation, then submit the protected action. It saves a successor generated shortlist using the original actual deterministic/ranked method; it can remain unchanged or empty. It never modifies the old shortlist or upgrades a deterministic method just because a model is now configured.

`regeneration_offer(event_id, human)` reads context. `regenerate(event_id, human, producer=automation, brief_id=..., expected_brief_version=..., expected_shortlist_version=..., request_id=..., interpretation_id=None)` is the public action. Capture its request/outcome/successor/cost IDs. Missing ranked configuration has no fallback. Exact retries recover nested request/claim identities without model reissue; stale new heads fail visibly. No-update/failure or lost publication permission removes the regeneration offer, while historical completion remains. Cost exhaustion leaves a resumable waiting task; fixing control can resume the same task, but a historical source/configuration refusal is not silently re-admitted. [Coverage](campaigns.md#automatic-coverage-and-discovery), [regeneration](campaigns.md#explicit-regeneration-after-discovery).

## 12. Proposals, task acknowledgment, worker and recovery

### 12.1 Save scope, approve it, then acknowledge a task

Campaign-configured work and schedule authority are distinct from assistant-origin work. Assistant proposals always need exact named-human approval. For a supplied offline query proposal, use the provided scope and keyword manifest:

```bash
uv run --locked smi-ingest save-proposal examples/synthetic/keyword-discovery-proposal.json --offline-manifest examples/synthetic/keyword-discovery-manifest.json --offline-route-version offline-keyword-v1 --request-id guide-proposal-1 --actor local-assistant
uv run --locked smi-ingest inspect-proposal PROPOSAL_ID --actor local-marketer
uv run --locked smi-ingest approve-proposal PROPOSAL_ID --scope-digest SCOPE_DIGEST --request-id guide-approval-1 --approve-exact-scope --actor local-marketer
uv run --locked smi-ingest submit-approved-task PROPOSAL_ID --approval-id APPROVAL_ID --scope-digest SCOPE_DIGEST --request-id guide-approved-task-1 --actor local-assistant
```

Capture the actual `proposal_id`, inspect its entire saved scope/digest/limits, capture approval `approval_id`, then capture submission `task_id`. The CLI records proposal/submission as automation and approval as its configured human. In the browser, **Proposals** → supply scope → saved exact review → explicit human approval performs the separated approval/task acknowledgment; it does not execute the task. Changed scope requires another saved immutable proposal and fresh approval, never editing the approved revision.

The example queries `sunscreen review`, subject `product:sunscreen`, publication interval `[2026-10-01, 2026-10-10)` UTC. Those subject strings are exact discovery labels in the local corpus, not knowledge canonical-subject UUIDs or a free-form research agent. Keyword discovery requires exactly one query, 1–30 subjects and timezone-aware inclusive-from/exclusive-before bounds up to 366 days. Every query term must literally occur in the caption, any subject must match and publication time must fit. Results follow source response order, one simulated record/page/request. Invalid selection fields quarantine; valid subsets may publish partially. Fixture corpus bounds are 1 MiB/100 records. A `fixture-json` route only reads supplied references: purpose/search metadata does not convert it into keyword discovery.

### 12.2 Execute one returned task

```bash
uv run --locked smi-ingest inspect-task TASK_ID --actor local-marketer
uv run --locked smi-ingest run-offline-task TASK_ID --worker-id local-offline-task-worker
uv run --locked smi-ingest inspect-task TASK_ID --actor local-marketer
```

Python equivalence is `OfflineTaskWorker(db, evidence_root).run_one(task_id, ActorContext("local", "local-offline-task-worker", "automation"))`. A task must exist first. Default task hard limits are ten requests/pages/records and 1 MiB bytes; trusted `OfflineRoute(..., limits=RunLimits(...))` may configure positive request/page/record bounds up to 100 and bytes up to 10 MiB before admission. Saved scope/digests/limits cannot be broadened at recovery. There is one durable attempt/run, even across recovery.

```mermaid
sequenceDiagram
    participant H as Human / configured service
    participant T as AcquisitionTasks
    participant W as Explicit run_one worker
    participant I as Ingestion owners
    participant K as KnowledgePublications
    participant N as CompletionInbox
    H->>T: admit exact authorized scope
    T-->>H: task_id, queued (no collection)
    W->>T: own task session; save attempt and run
    W->>I: bounded collection, evidence and canonical commits
    W->>T: persist exact prepared support
    W->>K: validate and publish permitted selection
    K->>T: atomic task-owned publication receipt
    W->>T: terminal outcome + completion event
    H->>N: reopen event, historical coverage, current links
```

**Observe.** Task detail shows queued/running/waiting/terminal state, immutable authority, initiator/approver, actual attempt producer/recovery actors, ingestion run, phase/counts, prepared support and publication receipt. Outcome distinguishes `usable_update`, `partial_update`, `no_usable_update`, `failure`. Partial collection/normalization can publish a valid subset; pending/unpublished records are not KB knowledge. Empty/unchanged currently usable captures make no new publication and establish no market absence.

### 12.3 Recovery, inbox and stopping boundaries

After process interruption, inspect and invoke **the same `task_id`** again. A PostgreSQL session advisory lock/execution ID fences competing workers and all dependent local effects. A disconnected worker loses authority; recovery retains committed attempt/run/prepared support/publication producer rather than starting over. A connected paused worker still owns the task. No transaction spans source/model I/O. Publication plus task receipt is atomic; terminal outcome plus one completion event is a later atomic commit. A publication may therefore be committed while completion is pending. A public request string alone cannot manufacture a task-owned receipt.

`provider_pending` can resume its existing bounded operation if the adapter explicitly supports it. `provider_operation_ambiguous` is nonresumable and never reissues a possibly charged operation. An exhausted cost allowance, operator pause or other reversible pre-dispatch gate can remain waiting. A lost dispatched response/cost identity cannot be made safe by another request ID. No general task cancellation/requeue/reset command is installed; stop invoking undispatched work, or interrupt a process and inspect committed state. Interruption cannot cancel an external request already sent.

```bash
uv run --locked smi-ingest list-inbox --actor local-marketer
uv run --locked smi-ingest inspect-completion EVENT_ID --actor local-marketer
uv run --locked smi-ingest reconcile-completions --actor local-marketer
```

`CompletionInbox.read_task(task_id, human)` finds an exact event beyond recent-list bounds. `/inbox` and `/inbox/EVENT_ID` show durable source-free messages and original actual counts separately from current publication usability. Reconciliation repairs missing local completion events; it does not execute acquisition. Source withdrawal can remove current links without changing historical outcome. There is no email/Slack delivery transport. [Full task contract](tasks.md).

## 13. Ask knowledge and follow a gap to a new answer

**Prerequisites.** Committed permitted publications support a question. Nonempty model-based answers require an explicit model route/transport/credential/cost setup ([24](#24-configure-model-and-live-source-operations)); default startup reports that configuration unavailable. Empty published support can produce an explicit no-call missing-information result. A model/configuration/cost failure alone is not a research gap.

**Answer action and result.** Open **Ask knowledge**, `/knowledge/questions`, enter a free-form question and optional literal narrowing, then submit. Capture `answer_id`, exact query/input IDs, status/limitations, method/model/bounds, usage and `operation_id`. `/knowledge/answers/ANSWER_ID` reopens it after restart without a transport. Public operation:

```python
from smi_assistant import KnowledgeAssistant
assistant = KnowledgeAssistant(db, model_route=route, model_transport=transport, model_credential=credential)
answer = assistant.ask("Which Hero Cushion mentions are supported?", human, request_id="guide-answer-1")
print(answer)
```

Here `route`, `transport`, `credential` are explicitly constructed in section 24, not ambient configuration. `ask` uses up to 20 selected members from at most 100 recent publications, with a default 30-day capture-age threshold. An optional `scope=QueryScope(...)` can narrow but cannot exceed 20 members; the question is not automatically a literal query filter. It projects at most 100 original assertion/metric/interpretation facts; one tool-free model selects up to 20 exact IDs plus a fixed uncertainty code. The application renders owner-sourced **extractive findings**, not arbitrary generated factual prose. All actual model inputs, including unselected facts, govern reopening. Newer publications never change the saved answer.

**Exact gap-to-update sequence.** For the original human requester, a supported missing/ambiguous/stale/unavailable gap offers **Propose bounded enrichment**:

1. Inspect the original answer's gap and input coverage. Open `/knowledge/answers/ANSWER_ID/enrichment/new`.
2. Supply human `refresh`/`fill`/`expansion` intent, one exact query, exact subjects and bounded publication window. The configured keyword capability/route/limits remain server-owned.
3. Save the proposal. Capture `journey_id`, `proposal_id`, `scope_digest`. `/assistant-enrichments/JOURNEY_ID` shows the exact immutable scope and actual automation proposer. Saving grants no approval and creates no task.
4. If scope needs changing, save a **new** proposal revision with a new request and review its new digest. Prior approval cannot cover it. Do not mutate/reuse the prior proposal identity.
5. Separately check the displayed exact-scope review acknowledgment and approve as the actual configured human. Capture `approval_id` and immediate queued `task_id`; no collection occurs in this POST.
6. Invoke the independent one-shot worker for that exact task. Reopen the journey/task while queued, running or waiting.
7. Reopen **Actual completion** and its exact event/publication links. Fetch success or prepared support alone is insufficient; only committed publication is usable knowledge.
8. Use **Ask again** to submit a **new explicit question/request**. It can read newly published support. The original answer and its empty/old membership remain unchanged.

`AssistantEnrichment(assistant, tasks)` provides `context`, `propose`, `read`, `approve`. `propose(answer_id, human, request_id=..., intent=..., subject_ids=(...), search_query=..., published_from=..., published_before=...)` saves linkage with a fresh nested proposal request. `approve(journey_id, human, scope_digest=..., request_id=...)` uses the existing stored approval/submission owners. Materially broader work needs fresh scope and approval, even outside registered keywords. Same request/actor/body retries recover exact claims, proposal/approval identities and task acknowledgment without minting another task or model call. One approval authorizes at most one logical task. A source-policy loss can withhold findings/current links without erasing the completion. No autonomous research/tool loop is installed. [Answer contract](knowledge.md#bounded-free-form-knowledge-answers), [journey contract](tasks.md#assistant-knowledge-gap-enrichment).

## 14. Configure keywords and acknowledge due work

**Prerequisites/action.** Use a keyword-capable route, migrate, then start with explicit operator authority:

```bash
uv run --locked smi-review --actor local-marketer --schedule-operator --offline-manifest examples/synthetic/keyword-discovery-manifest.json --offline-route-version offline-keyword-v1
```

Open `/schedules`, save timezone, daily `HH:MM`, 1–30 lookback days, shared daily allowance and keywords JSON. Preserve stable keys while editing. Initial form suggestions are UTC/09:00/seven-day lookback/**50 total** new posts across at most ten registrations; they become authority only on save. To pause future registered occurrences, save an empty keyword list. This does not cancel acknowledged tasks. Trusted Python equivalent:

```python
from smi_tasks import AcquisitionTasks, OfflineRoute, TaskAuthority
from smi_tasks.schedules import ScheduledDiscovery
schedule_tasks = AcquisitionTasks(db, route=OfflineRoute(
    Path("examples/synthetic/keyword-discovery-manifest.json"), "offline-keyword-v1",
), authority=TaskAuthority(schedule_operators=frozenset({human.actor_id})))
schedules = ScheduledDiscovery(schedule_tasks)
configured = schedules.configure({
    "timezone": "Asia/Seoul", "daily_at": "09:00", "lookback_days": 7,
    "daily_allowance": 50,
    "keywords": [{"key": "sunscreen", "query": "sunscreen review", "subject_ids": ["product:sunscreen"]}],
}, human, expected_version=0)
print(configured)
print(schedules.tick(human))
```

Use expected version 0 only for first save; later use `schedules.read(human)["version"]`. Unlike most request-bound writes, schedule configuration is protected by `expected_version` and **has no `request_id` parameter**. A repeat successful save with its old version conflicts; reopen first.

**Observe/execute.** Save configuration version/digest, stable keyword keys, `accounting_day`, `occurrence_id`, disposition/reason and every returned `task_id`. **Acknowledge due tasks** (`POST /schedules/tick`) or `tick(human)` handles at most ten due current-day occurrences. It does not collect. Execute each returned task via `run-offline-task`. The fixed example corpus has historical October publication dates: a current seven-day scope later in time can truthfully return no matches. A schedule does not rewrite the corpus/window to manufacture yield.

**Technical path/boundaries.** `ScheduledDiscovery` pins original configuration/initiator/local day → `AcquisitionTasks.submit_scheduled` acknowledgment → explicit worker → normalized identity/current-policy check → atomic shared `ScheduledPostAllowance` admission with canonical writes → publication/completion. The first configured accounting timezone is fixed. Day boundaries are local midnight; edits/removal/re-registration/restart do not reset occurrence or consumption. Missed earlier days are not caught up. Duplicate known post identities and refresh captures consume no additional new-post debit; concurrent duplicate discoveries serialize. Unknown/quarantined/out-of-scope/cap-excluded records do not become admitted posts. Daily allowance, HTTP/request/byte/record bounds and money remain independent; 50 is neither per-keyword yield nor a throughput promise.

Offline optional avoidance uses `OfflineRoute(..., discovery_policy=DiscoveryPolicy(max_capture_age_seconds=86400, processing_revision="canonical-v1"))` from `smi_tasks.discovery`. It compares exact query/subjects/window/input/mapper/processing context and every original capture's current usable support. Fresh complete reuse creates **zero** source dispatch, cost dispatch, daily debit or new publication; inspect the task's persisted discovery decision and prior task/publication links. Unknown/stale captures, partial work and quota exclusions remain eligible; without configured freshness it records unconfigured policy. Local import/publication clocks never prove fresh capture. Changed policy/configuration requires new admission. Recorded live schedule activation uses explicit `live=True`, trusted enablement and pinned route authority; it remains independently gated at execution ([24](#24-configure-model-and-live-source-operations)). [Schedule contract](tasks.md#registered-offline-keyword-schedule), [avoidance contract](tasks.md#capture-based-discovery-avoidance).

## 15. Investigate a frozen snapshot without a campaign

**Prerequisites/action.** Import a dataset and register its catalog. Open **Investigations**, `/investigations/new`, choose product/brand/topic, intended market/platform scope, question and optional publication/language constraints. Save, choose a frozen dataset, then prepare the insight. No campaign is created. Public Python equivalent:

```python
import json
from smi_monitoring import InvestigationScope, MonitoringStore
monitoring = MonitoringStore(db)
scope = InvestigationScope.from_document(json.loads(Path("examples/monitoring/hero-cushion-scope.json").read_text()))
investigation = monitoring.start(scope, human, request_id="guide-investigation-1")
insight = monitoring.prepare_insight(
    investigation["investigation_id"], investigation["scope_id"], knowledge_run_id,
    automation, expected_version=0, request_id="guide-insight-1",
)
print(investigation, insight)
```

**Observe/path.** Capture `investigation_id`, `scope_id`, scope version and `insight_id`/insight version. `/investigations/ID` and `/insights/ID` retain histories. `MonitoringStore` reads the exact knowledge run/frozen evidence through public owners, applies literal scope, deduplicates content/account identities and saves pinned findings/counts/spans. Expand source evidence for originals, dates and limitations. Caption language cannot be established by the script method: an explicit language constraint yields `not_assessable`; leave it empty for literal scope without a language claim.

**Boundaries/retry.** Snapshot results have `baseline=null` and `trend_status="not_assessable"`; they cannot show growth or continuous market change. New scope/answer versions use separate expected heads and request IDs. New knowledge does not refresh old insights. Commit-time policy/correction changes can reject preparation. A withdrawn dependency withholds the whole dependent finding/aggregate, including matching count membership, instead of recomputing history; retention loss permanently purges finding bodies. Preparation makes no source/model request, and translations/human adjudication remain pending. [Contract](monitoring.md#scope-and-preparation).

## 16. Configure and poll recent X offline

### 16.1 Policy and topic setup

Recent X has its own topic/capture/window/retention storage; it needs no catalog, campaign, canonical post ingestion or per-post KB publication. A named monitoring operator and an existing source policy are required for mutation. Policy writes/withdrawal are public **Python** operations, not browser/CLI flags:

```python
from smi_monitoring.recent import RecentMonitoring, OfflineXRoute
recent = RecentMonitoring(db, route=OfflineXRoute(Path("examples/monitoring/recent-x.json")),
    operators=frozenset({human.actor_id}))
recent.set_policy({
    "context_id": "offline-x", "can_process": True, "can_display": True,
    "can_retain": True, "revoked": False, "expires_at": None,
}, human, expected_version=0)
topic = recent.configure("cushion", {
    "query": "cushion", "cadence_minutes": 60, "window_minutes": 120,
    "max_records": 10, "retention_hours": 24, "source_policy_id": "offline-x",
}, human, expected_version=0, request_id="guide-topic-1")
print(topic)
```

Use exact current policy/topic versions for successors. The word `offline-x` alone is no permission. Then expose browser topic configuration/manual poll:

```bash
uv run --locked smi-review --actor local-marketer --monitoring-operator --recent-x-fixture examples/monitoring/recent-x.json
```

Open **Recent X**, `/monitoring/topics`, or `/monitoring/topics/cushion`. New topics use expected version 0; later edits append immutable revisions. Topic settings require 1–200 character literal query, cadence 1–1,440 minutes, window 1–10,080 minutes, max records 1–100, retention 1–720 hours and existing policy ID. Forms cannot set clock, actor, source route or policy. Default startup is read-only for these mutations.

### 16.2 Window and deliberate historical demonstration

Manual poll accepts an explicit timezone-aware `window_end` aligned to the saved UTC-epoch cadence. A **new** window must end within the preceding seven days and no later than the trusted clock. `recent.poll("cushion", WINDOW_END, human)` or the protected browser poll creates/reopens one logical `(topic, normalized end)`. Capture `window_id`, topic revision and monitoring observation UUIDs. Original configuration and membership survive edits/retries; `read_window`, `read_observation`, `timeline(key, human, limit=50, offset=0)` and topic pages reopen them without the fixture route.

The bundled fixture has one **synthetic** post published `2026-10-28T10:30:00Z`, captured/measured `2026-10-28T11:00:00Z`, and declared **partial** coverage. It is historical input. With a real later clock, a current window can exclude it; selecting its old window can become too old to admit, and its 24-hour capture-based body deadline is already expired. Import time cannot fix these facts.

For a deliberate bounded demonstration, use a separate operator-created demo database/schema, migrate it explicitly, then compose **only that demo's** store/server with a fixed clock. Keep this same clock on readers; a later actual-clock read can permanently purge expired bodies:

```python
from datetime import datetime, timezone
demo_clock = lambda: datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
recent = RecentMonitoring(db, route=OfflineXRoute(Path("examples/monitoring/recent-x.json")),
    operators=frozenset({human.actor_id}), clock=demo_clock)
# Run the policy/topic setup above in this isolated demo using this recent object.
collected = recent.poll("cushion", "2026-10-28T12:00:00Z", human)
print(collected)
print(recent.read_window(collected["window_id"], human))
```

To serve the same bounded historical view, use `ReviewApp(db, actor_id=human.actor_id, recent_x_route=recent.route, monitoring_operator=True, monitoring_clock=demo_clock)` with `make_server` as in section 24. Do not freeze a production clock or describe the historical fixture as today's evidence. The bundled partial one-post fixture cannot establish an assessable volume baseline or mixed-position semantic alert. Use deliberately constructed local synthetic evidence or the relevant tests for those paths, retaining honest sample timestamps/coverage.

The fixed clock applies to the recent owner and explicitly composed alert/read views only. **Promotion crosses into ingestion, whose source-policy checks use actual UTC wall time.** A historical recent body can therefore display under the frozen clock while promotion fails `processing_not_permitted` because its inherited 24-hour deadline has actually expired. A frozen recent clock cannot authorize expired KB support. Use the separate current-time synthetic recipe below to exercise promotion.

### 16.3 Current-time synthetic demonstration for promotion

This optional recipe creates a new **operator-owned local demo file**, leaving the bundled fixture unchanged. Its text, native ID and metrics are deliberately synthetic; its generated dates describe a simulated capture now, not a refreshed real-world observation. Its declared coverage stays **partial**. Run it only when intentionally populating a local demo workspace; no source/model request occurs. Use the common `db`, `human`, `Path` and imported recent classes from the Python examples above:

```python
import json
from datetime import datetime, timedelta, timezone

demo_now = datetime.now(timezone.utc)
demo_end = demo_now.replace(minute=0, second=0, microsecond=0)
demo_capture = demo_end - timedelta(minutes=10)
demo_path = Path(".scratch/local-demo/recent-x-current.json")
demo_path.parent.mkdir(parents=True, exist_ok=True)
demo_path.write_text(json.dumps({
    "coverage": "partial",
    "records": [{
        "capture_id": "synthetic-current-demo-" + demo_end.isoformat(),
        "native_id": "11",
        "text": "Synthetic cushion current-clock promotion demo; no live X observation.",
        "published_at": (demo_end - timedelta(minutes=30)).isoformat(),
        "captured_at": demo_capture.isoformat(),
        "metric_measured_at": demo_capture.isoformat(),
        "metrics": {"like_count": 4},
    }],
}))
current_recent = RecentMonitoring(db, route=OfflineXRoute(demo_path),
    operators=frozenset({human.actor_id}))  # Actual clock, no frozen clock.
current_recent.set_policy({
    "context_id": "offline-x-current-demo", "can_process": True, "can_display": True,
    "can_retain": True, "revoked": False, "expires_at": None,
}, human, expected_version=0)
current_recent.configure("cushion-current-demo", {
    "query": "cushion", "cadence_minutes": 60, "window_minutes": 120,
    "max_records": 10, "retention_hours": 24, "source_policy_id": "offline-x-current-demo",
}, human, expected_version=0, request_id="guide-current-demo-topic-1")
current_collection = current_recent.poll("cushion-current-demo", demo_end.isoformat(), human)
current_window = current_recent.read_window(current_collection["window_id"], human)
print(current_window)
```

Capture the returned `window_id` and its local observation UUID. Execute promotion promptly within the actual retention deadline using section 18. Reopen existing policy/topic versions before rerunning configuration; do not repeatedly save version 0 or reuse a topic request with different settings. Reuse the same logical window for an exact retry, and retain the generated dates/file for this demonstration's provenance. Creating another deliberate simulated capture needs a new window/time identity; changing file bytes cannot replace a saved capture. Remove the operator-managed file when finished; product tombstones/retention remain governed by their owners.

### 16.4 What is saved and what expires

**Technical path.** `RecentMonitoring` operator/policy/window validation → one bounded local `OfflineXRoute` file read → literal query/publication-window selection → deduplicated capture ordering/cap → original window/capture/acquisition/coverage commit. Hard file limits are 262,144 bytes/200 records. Capture identity uses native post plus original capture time (or conservative original publication/measurement context when capture is unknown); renaming a fixture capture label cannot create freshness. Missing/invalid eligibility, unknown capture, withdrawal or truncation makes a nominally complete sample partial. Empty complete local selection establishes no market absence. Market coverage is always unknown.

Window/detail/timeline pages label publication/capture/measurement/import/deadline separately and preserve original source metric meanings. Counts missing from the fixture are unknown, not zero. Timeline default is 50 captures, bounded to 100 per page; topic pages show latest 100 windows, while exact older IDs reopen. Audit caps include 50 topics, 100 revisions/topic, 1,000 windows/topic and 20,000 workspace observations; exceeding them fails rather than silently erasing history.

**Lifecycle.** Current purpose permission and retention are rechecked on public operations. With known capture time, body deadline is `min(original_capture, first_import) + retention_duration`; with unknown capture it is `first_import + retention_duration`. Capture reuse can shorten but never extend it. `recent.withdraw("NATIVE_X_ID", human)` permanently removes every copied body for that post and blocks future captures. Policy denial/revocation/expiry/local expiry permanently clears text/metrics; retained safe times/IDs/coverage remain tombstones. Retry, permission recovery or later import cannot restore a purged body. The original local fixture file remains operator-managed. No daemon or live X request is enabled by the offline route. [Contract](monitoring.md#bounded-offline-recent-x-evidence).

## 17. Assess volume and provisional quality positions

### 17.1 Quantitative distinct-post volume

**Prerequisites/action.** Save two complete permitted comparable windows, with equal positive nonoverlapping durations, same topic/query/cadence/source-policy context, acquisition/schema/sampling and actual bounds. Baseline must end by detection start. Configure thresholds explicitly; no production defaults exist:

```bash
uv run --locked smi-review --actor local-marketer --monitoring-operator --monitoring-volume-threshold '{"minimum_baseline_posts":1,"minimum_increase_posts":3,"minimum_ratio":3}'
```

These values are sample signal choices, not statistical recommendations. Existing windows can be assessed without a collection route. Open `/monitoring/assessments`, select exact detection/baseline IDs and save. Python equivalent:

```python
from smi_monitoring.alerts import QuantitativeAlerts, VolumeThreshold
alerts = QuantitativeAlerts(recent, threshold=VolumeThreshold(1, 3, 3))
assessment = alerts.detect("DETECTION_WINDOW_ID", "BASELINE_WINDOW_ID", human, request_id="guide-volume-1")
print(assessment)
```

Pass `None` as baseline to record its absence. Capture `assessment_id`, outcome/limitations and, only on supported crossing, `alert_id`/`notification_id`. `/monitoring/assessments/ID`, `/monitoring/alerts/ID`, and **Inbox** reopen them.

**Path/boundaries.** `QuantitativeAlerts` reads both exact windows under current process/display/retention checks, counts distinct native posts and applies minimum baseline, absolute increase and ratio. Both increase and multiplicative thresholds must pass. Adequate below-threshold samples save `no_change`; missing/incomparable/partial/empty inadequate baseline saves `not_assessable` with no ratio/alert. Supported crossing atomically saves assessment/alert/source-free local notification. It is a sample-volume signal, not independently significant market growth; engagement is not used. Same pair/method/configuration cannot create duplicate alerts under new request IDs. Current support loss withholds the entire numerical comparison but preserves historical identity/outcome. No task, campaign or collection is started. [Contract](monitoring.md#configured-quantitative-volume-assessments).

### 17.2 Provisional quality-controversy positions

**Prerequisites/action.** A currently permitted recent window with bounded usable text (at most 20 captures), explicit `ControversyThreshold(minimum_concern_posts, minimum_counterposition_posts)` and model setup from section 24. Each threshold is 1–20 and their sum at most 20. CLI startup has **no semantic model/threshold flag**; use trusted Python construction:

```python
from smi_monitoring.semantic import SemanticAlerts, ControversyThreshold
semantic = SemanticAlerts(recent, threshold=ControversyThreshold(1, 1),
    model_route=route, model_transport=transport, model_credential=credential,
    clock=recent.clock)
assessment = semantic.detect("WINDOW_ID", human, request_id="guide-semantic-1")
print(assessment)
```

Or configure `ReviewApp(..., monitoring_operator=True, monitoring_controversy_threshold=ControversyThreshold(1, 1), model_route=route, model_transport=transport, model_credential=credential)` and use `/monitoring/semantic-assessments`. Capture assessment/alert/notification/cost IDs, all prepared input IDs/digest, model/method/bounds and limitations.

**Path/boundaries.** `SemanticAlerts` saves a claim, rechecks **all** actual input after cost contention, invokes one bounded Responses request and validates one exact span/position per input: quality concern, counterposition or unresolved. Distinct native posts meeting both configured position thresholds can create `possible_controversy` and a local notification. Invalid/incomplete/oversized/unavailable/configuration/meter/uncertain states remain visible with no reissue/fallback. Same configured window has one result across retries/new requests. Position labels/quotations are provisional automated judgments; they establish neither entailment, independently verified sentiment nor shared disputed claim. There is **no baseline**, `change_status=not_assessed`, and no semantic change-over-time claim. Loss of any original input, including unresolved text, permanently clears dependent judgments while preserving safe history/cost. Neither detection method translates, researches externally or creates a campaign. [Contract](monitoring.md#bounded-provisional-quality-controversy-assessments).

## 18. Investigate alerts and promote selected captures

### 18.1 Existing-KB alert context

**Action/prerequisites.** Open an exact retained quantitative/semantic alert with current usable recent support, then **Save existing KB investigation**. Explicit synthetic KB visibility is a development choice. No acquisition approval/model is required. Public operations:

```python
from smi_monitoring.context import AlertInvestigations
contexts = AlertInvestigations(recent)
context = contexts.investigate("quantitative", "ALERT_ID", human,
    request_id="guide-alert-context-1", include_synthetic=False)
print(context)
```

Use `"semantic"` for that method. Capture `investigation_id`, original alert/window/capture IDs and exact knowledge-query `result_id`; reopen `/monitoring/alert-investigations/ID` or `contexts.read(id, human)`.

**Observe/path/boundary.** `AlertInvestigations` uses the original detection topic query as one literal existing-KB query, at most 20 bundles from at most 100 publications. It pins that manifest and recent membership, then renders a bounded deterministic explanation alongside **Recent monitoring evidence** and **Existing KB context**. It performs no semantic retrieval, topic expansion, model, external search, task or campaign action. Empty KB context is an explicit unresolved gap. Later publications affect only new investigations. Similarity/co-occurrence does not establish causation or identity. Any required dependency loss permanently withholds dependent explanation; permitted IDs/attribution remain. [Contract](monitoring.md#existing-kb-alert-investigations).

### 18.2 Deliberately publish selected recent evidence

**Action/prerequisites.** A configured monitoring operator opens `/monitoring/windows/WINDOW_ID`, checks **1–20 exact capture IDs**, then promotes. Nothing is selected by default. The selected source deadline must still be valid under actual ingestion UTC checks. Use [the current-time synthetic demonstration](#163-current-time-synthetic-demonstration-for-promotion) for an end-to-end offline exercise; the frozen October window does not bypass an expired inherited source deadline. With `current_recent` and `current_window` returned by that recipe, this explicitly chooses its one synthetic capture:

```python
from smi_ingestion.evidence import EvidenceStore
from smi_monitoring.promotion import MonitoringPromotion
promotion = MonitoringPromotion(current_recent, EvidenceStore(db, evidence_root))
selected_capture_id = current_window["observations"][0]["observation_id"]
saved_promotion = promotion.promote(current_window["window_id"], (selected_capture_id,), human,
    request_id="guide-promotion-1")
print(saved_promotion)
```

Capture `promotion_id` and each item's exact monitoring/source run/observation/publication links. `/monitoring/promotions/ID` is a source-free receipt; open normal publication/query pages for current support (explicit synthetic visibility for the fixture).

**Technical path/boundary.** In one local transaction: recent permission/membership check → ingestion evidence save with zero new requests and no retained raw transfer payload → `monitoring-x:recent-x-content-v1` mapper/`CanonicalWriter` → `KnowledgePublications` → dependency/promotion receipt. X native content/caption/publication and supported source metric values are mapped; author account, Creator and Brand/Product associations remain unknown. It makes no source/model call and creates no task/campaign. Valid selected items can publish beside unavailable/not-in-window items; retries preserve exact receipt, and another request can reuse an existing logical publication. Parent policy/deadline/native withdrawal directly governs promoted canonical/KB copies, even without reopening the promotion page. Re-promotion cannot extend retention or reconstruct purged bodies. Unselected captures remain recent-only. [Contract](monitoring.md#selected-recent-evidence-promotion).

## 19. Configure separate periodic live X authority

**Status.** Installed software, disabled by default; live readiness and current account/use-rights/commercial acceptance are unverified. This is separate from offline manual poll, registered keyword schedules and acquisition task authority. There is no `smi-review --live-x` flag or continuous process supplied here.

**Prerequisites/setup.** A trusted operator needs a configured topic/policy, exact revision, separately cleared source use/display/storage/deletion obligations, authorized operation, transient credential and persisted `x-recent-search` provider-reported cost scope/binding/ceiling (section 22). Construction below keeps every runtime gate disabled and reads no credential:

```python
from smi_monitoring.polling import RecentPolling, LiveXConfig
poller = RecentPolling(recent, config=LiveXConfig(),
    workers=frozenset({"local-x-poll-worker"}))
```

When independently authorized and configured, the public operations are `activate(topic_key, human, expected_topic_version=..., first_window_end=..., request_id=...)`, `run_due(ActorContext("local", "local-x-poll-worker", "automation"))`, `deactivate(topic_key, human)` and `read(topic_key, human)`. Enabled runtime construction is `LiveXConfig(enabled=True, operation_authorized=True, source_use_authorized=True, bearer_token=credential_from_trusted_operator)`. Supplying those booleans represents real authority; they are not instructions to bypass missing prerequisites. Activation validates runtime prerequisites, exact source/topic bounds and records original operator/revision/route. Capture activation/attempt/window/cost IDs and state/reason from returned/read history. Topic browser pages show **Periodic X polling** history read-only.

**Execution/observable result.** An explicit invocation handles at most one interval ending at least 30 seconds ago, fairly considering at most 50 due topics. Success saves an ordinary governed recent window and advances pinned cadence. Topic edits need a successor activation; deactivation stops future admissions but cannot cancel/settle a sent request. It cannot acquire beyond the provider's last-seven-days range. One attempt has one official recent-search request, at most ten returned posts, 2,048 encoded URL bytes, less than 65,536 response bytes, finite socket/deadline/save limits and no pagination/redirect/retry/fallback. Additional `next_token` pages stay uncollected. Source capture/measurement times remain unknown; local retrieval is not source freshness. Every live sample is partial/unknown market coverage.

**Technical/recovery boundary.** Per-topic session ownership → current policy/revision guard → schema-wide route cooldown → scope-locked ten-unit commitment → one HTTPS request outside transaction → guarded recent save. Lost ownership, changed policy/activation/revision or overdue response discards source response while retaining original charge uncertainty. A dispatched/failed/ambiguous identity never redispatches, even after final cost reconciliation. Pre-dispatch refusal can retry after its gate is restored. Two-second schema-wide cooldown and bounded rate metadata/429 delays coordinate this installation only; other apps/installations can consume the same provider quota. No billing API, compliance feed or new alert method is installed. [Full polling contract](monitoring.md#gated-periodic-live-recent-x).

## 20. Explore the graph and task lineage

### 20.1 Governed entity graph

**Action/prerequisites.** Publish permitted source/interpretation support. Open **Graph**, `/knowledge/graph`, choose literal entity/source filters, bounds and explicit synthetic mode, then search. Capture `search_id`, exact knowledge query and opaque selected entity token. Saved `/knowledge/graph/SEARCH_ID?entity=OPAQUE_TOKEN` reopens after restart. Click nodes for immediate directed adjacency; use traversal controls for 1–3 hops, incoming/outgoing/both, predicates/bases, neighbor kinds/platforms/namespaces and exact source observation narrowing.

Public equivalents are `KnowledgeGraph(db).search(GraphScope(...), human, request_id=...)` and `read(search_id, human, entity_id=token, traversal=GraphTraversal(...))`. Omit `traversal` for one-hop behavior. Search bounds are 1–100 support members, default 50/maximum 100 entity matches and default 20/maximum 50 immediate relationships. Explicit traversal bounds are 1–3 hops, 1–100 nodes including root, 1–50 relationships and 1–5,000 inspected edges. Every truncation/empty subset is visible. Observation filters narrow labels/facts as well as edges; neighbor filters cannot bridge through excluded nodes. Links retain traversal controls/synthetic context; browser back/previous selection does not save copied labels.

**Path/boundary.** `KnowledgeGraph` pins a public query/filter manifest, then projects current permitted support/catalog context on each read. It stores no source values/labels/edges. Native accounts/content, provisional published Brand/Product mentions and human-configured catalog-brand relations retain different bases, exact spans/methods/dates/native namespaces. Breadth-first traversal deduplicates cycles; the edge work budget applies after the already bounded projection, not all DB work. Current process/display/retention/derivation checks remove denied labels/incident relationships; an unavailable token reconstructs nothing. New publications require new search. No graph operation calls a source/model, changes shortlist membership or infers cross-platform Creator identity. [Contract](knowledge.md#governed-entity-graph).

### 20.2 Task pipeline lineage

Open a task's **Lineage**, `/tasks/TASK_ID/lineage`, or `TaskLineage(db, "local").read(task_id, human, include_synthetic=False)` from `smi_tasks.lineage`. It needs the task ID, not its manifest, payload file or credential. Capture links to actual attempt/run/observation/derivation/prepared support/task-owned publication/completion and cost operations. The page separates queue acceptance, collection, canonical ingestion, publication and terminal completion, including partial/quarantined inputs, sanitized failure and actual recovery actors/counts.

`TaskLineage` composes public task/source/publication/accounting readers without its own persistence. It reads at most 100 run observations, 20 newest derivations/observation and 100 attributable cost operations, with explicit truncation and full persisted status counts. Owners' committed frontiers are read independently, not as an atomic audit snapshot. Historical published counts remain after policy loss, while current navigation requires permitted current support. Synthetic history is metadata-only unless explicitly enabled. Missing cost means unknown, never zero; scopes/currencies/periods are not totaled. GET executes no work. [Contract](tasks.md#read-only-task-pipeline-lineage).

## 21. Record measurement intent and human learning

**Action/prerequisites.** From a campaign with a saved shortlist, open **Measurement plans and decision notes**, `/campaigns/CAMPAIGN_ID/planning`. A generated revision can be referenced directly; human confirmation is not required first. Save the proposed objective/outcome definition, intended source/owner, product/listing/currency, period/baseline, matching/attribution assumptions and explicit gaps. Separately save human feedback/learning against a relevant historical shortlist.

Public operations are `CampaignPlanning(db).save_plan(campaign_id, brief_id, shortlist_id, MeasurementPlan.from_document(...), human, expected_version=..., request_id=...)`, `add_note(campaign_id, shortlist_id, DecisionNote(text=..., support_ids=()), human, expected_version=..., request_id=...)` and `read(campaign_id, human)`, imported from `smi_campaigns.planning`. Use the [sample plan](../examples/campaigns/sales-measurement-plan.json). Capture `plan_id`/`note_id`, independent plan/note version heads, exact brief/shortlist and actual human/time.

**Observe/path/boundary.** `CampaignPlanning` validates campaign/shortlist/catalog through public support, locks expected heads and saves separate proposed/human histories. Plans stay `proposed`, outcome access `not_verified`, `outcomes=null`; no sales/revenue/conversion/lift result may be submitted. No default attribution window or verified data access is invented. Notes are human supplied, not independent facts; all selected candidate dependencies govern note text even without explicit citations. Current denial hides it and retention loss purges it, while attribution/revision remains. Empty selections allow a purely human note. Same request retries reopen; changed/stale saves conflict. Actual commercial outcome ingestion, attribution and causal lift remain future work. [Contract](planning.md).

## 22. Configure and inspect costs

### 22.1 Explicit scope, rates, binding and allowance

**Status/entry point.** Accounting/configuration/reconciliation use trusted Python; **Costs**, `/costs`, `/costs/OPERATION_ID`, and `/tasks/TASK_ID/costs` are read-only views. There are no CLI rate/ceiling forms. Migrate first. These simulation figures are deliberately fictional, **not current commercial prices**. This setup writes local accounting configuration but dispatches nothing:

```python
from datetime import datetime, timedelta, timezone
from smi_costs import CostScope, UsageAccounting
from smi_tasks import AcquisitionTasks
cost_task_owner = AcquisitionTasks(db)
costs = UsageAccounting(db, task_attribution=cost_task_owner.resolve_cost_attribution)
now = datetime.now(timezone.utc)
period_start = (now - timedelta(days=1)).isoformat()
period_end = (now + timedelta(days=1)).isoformat()
costs.configure_scope(CostScope(
    "guide-fixture-simulation", "synthetic-local", "fixture-simulation", "metered", "USD",
    period_start, period_end, unit="request", rate_version="guide-fictional-v1", unit_rate="0.125",
), human)
costs.configure_ceiling("guide-fixture-simulation", human, amount="1", currency="USD",
    period_start=period_start, period_end=period_end)
costs.configure_route("fixture-json", "guide-fixture-simulation", human, max_units="1")
print(costs.allowance("guide-fixture-simulation", human))
```

Use an intentional new scope ID for different period/rates/currency/classification; recomputing the dynamic dates and rerunning the same ID conflicts. Preserve exact configured dates for retries. Route bindings are immutable: an existing workspace/adapter binding cannot silently move to a new scope. Installed period/binding rotation requires operator planning; there is no general rebinding UI. Offline unbound fixture reads remain local with no commercial charge; a persisted binding enables the shared guarded simulation for all workers in that workspace. Bind `offline-keyword-json` separately for keyword work.

**Path/allowance.** `UsageAccounting` validates immutable scope/rate/basis; the worker wraps dispatch in its public bounded adapter on the actual ownership connection. One scope lock covers all operations/declared liabilities, beyond the latest-100 display list:

```text
available = max(0, ceiling - measured usage - unresolved declared commitments - dispatched reservations)
```

Admission commits a one-use reservation before I/O; valid final measurement replaces its reservation with actual units × rate. Forecast-only scopes have resource bounds and one-use identities but no enforced monetary ceiling or derived actual cost. Missing controls, inactive period, pause, exhausted allowance, unknown coverage or failed meter can block before callback; task status remains waiting with exact reason/operation/allowance. A ceiling increase does not clear a failed meter or uncertain dispatch. Approval and source permission are independent of money.

### 22.2 Usage, forecasts, declared commitments and unknowns

For an operator-recorded local simulation, create an operation first, then separately record its actual/estimate/unknown portions:

```python
operation = costs.begin_operation("guide-fixture-simulation", human,
    request_id="guide-ledger-operation-1", method="manual-simulation-v1")
operation_id = operation["operation_id"]
measured_at = now.isoformat()
costs.record_usage(operation_id, human, measurement_id="guide-usage-1", units="1",
    rate_version="guide-fictional-v1", measured_at=measured_at, provenance="operator-simulation-v1")
costs.record_forecast(operation_id, human, measurement_id="guide-forecast-1", amount="0.25",
    currency="USD", measured_at=measured_at, provenance="operator-estimate-v1",
    assumptions="One separately estimated simulated portion")
print(costs.read(operation_id, human))
```

No call is dispatched by those recording operations. Use decimal strings/integers/`Decimal`, never binary floats. Measurement IDs are workspace-global stable identities. `record_commitment(..., measurement_id=..., amount=..., currency=..., measured_at=..., provenance=...)` records a declared outstanding portion without admitting work; `record_uncertainty(..., state="unknown"|"meter_failure", ..., reason=...)` records no invented amount. Task-linked `begin_operation` must supply both real `task_id`/`attempt_id` and the injected public attribution resolver. Actual human/automation, method/rates/period/provenance and dispatcher remain distinct.

Capture operation/entry/measurement IDs, separate actuals/forecasts/commitments, unresolved liabilities and admission/meter/billing states. Missing amounts are `null`/Unknown, not zero. Synthetic measured values are not commercial charges; provider-reported usage valued at operator rates is not an independently verified invoice. Cost metadata is source-free: no prompt/caption/response/credential. Source withdrawal does not erase historical resource usage. Do not total different scopes/currencies/periods or treat forecast as actual.

### 22.3 Final evidence and separate meter-health recovery

When an operation is uncertain, inspect `costs.read(operation_id, human)["unresolved"]` and obtain actual identified **final** measurement evidence. A failed call may still cost money; only explicit final measured zero can establish zero. `record_usage` arriving later does not by itself settle prior liabilities. Use:

```python
costs.reconcile_usage(
    "OPERATION_ID", human, reconciliation_id="YOUR_STABLE_RECONCILIATION_ID",
    measurement_id="YOUR_FINAL_MEASUREMENT_ID", units="FINAL_UNITS", rate_version="EXACT_SCOPE_RATE_VERSION",
    measured_at="USAGE_TIME_IN_ORIGINAL_PERIOD", provenance="FINAL_REPORT_METHOD",
    reconciled_at="ACTUAL_FINAL_ATTESTATION_TIME", evidence_id="SOURCE_FREE_REPORT_ID", outcome="failed",
    settle_admission=True, commitment_ids=(), uncertainty_ids=("EXACT_UNRESOLVED_ENTRY_ID",),
    measurement_basis="synthetic",
)
```

This is a signature template, not evidence to paste unchanged. Name only actual unresolved portions on that operation; at least one admission/commitment/uncertainty target is required. Provider scopes require `measurement_basis="provider_reported"`; default synthetic attestation cannot settle them. Original period/rates remain authoritative even after it closes; actual overage must remain visible. Reconciliation restores neither a missing response nor task/source authority and never reopens a dispatched identity.

If the expected meter failed, separately attest restored health after its named failures have final accounting: `recover_meter(operation_id, human, recovery_id=..., failure_ids=(...), recovered_at=..., provenance=..., evidence_id=..., measurement_basis=...)`. It clears only those health failures, releases no other liability, and grants no retry. Read `reconciliations`, `meter_recoveries`, `unresolved`, admission and allowance to verify. Changed IDs/bodies conflict; unknown charges do not expire automatically. There is no write-off/invoice API, guaranteed billing-lag bound or zero-overshoot guarantee for delayed/unbounded charges.

Provider model scopes require `openai`/`responses`/`weighted_token`, matching route rate version and explicit weights. Deferred TikTok keyword/profile scopes require `brightdata`/`tiktok-keyword`/`declared-record-bound` and maximum one unit per HTTP attempt; profile binds to the same primary scope. Official X requires `x`/`recent-search`/`declared-post-bound`, binding `x-recent-search` with `max_units="10"`. Every deferred response retains its commitment until final evidence; returned rows/posts never settle billing. Real rates/bounds are operator inputs, with no installed commercial defaults. [Full accounting contract](costs.md).

## 23. Export, record and reopen quality review

**Prerequisites/status.** Provision an actual currently permitted saved generated current-KB recommendation, KB answer or semantic alert through its normal workflow. A sample file alone is not a selected review corpus. Actual named human language/marketer validation is **still pending**; test actors/translations/packet creation do not pass it. The operational tool supports those three kinds, not quantitative alert packets. Record quantitative/journey feedback in the actual review procedure/session record.

```bash
uv run --locked python tools/operational_quality.py --help
uv run --locked python tools/operational_quality.py --actor ACTUAL_REVIEWER export answer ANSWER_ID --request-id YOUR_EXPORT_REQUEST
uv run --locked python tools/operational_quality.py --actor ACTUAL_REVIEWER record PACKET_ID HUMAN_REVIEW.json --request-id YOUR_REVIEW_REQUEST
uv run --locked python tools/operational_quality.py --actor ACTUAL_REVIEWER read PACKET_ID
```

Use `recommendation SHORTLIST_ID` or `semantic_alert ALERT_ID` for the other export kinds. `--include-synthetic` is a global option before the action, only for deliberate simulated evidence. Capture `packet_id`, complete frozen membership/dependencies, returned unanswered `review_template`, record IDs/revisions and all denominators. Copy **only** the template object into `HUMAN_REVIEW.json`, then supply actual reviewer/attestation/time/method, translations and human/automation translator/model attribution, item labels (`supported`, `unsupported`, `ambiguous`, `not_assessable`), ambiguity/material error/correction and optional real marketer usefulness/time/inspected-post counts. Keep the full denominator even for partial review; do not invent annotations.

**Technical path.** Tool → `OperationalReviews.export/record/read` → result-owner transactional readers → exact full input/source/interpretation dependencies → review packet/serial annotations in PostgreSQL. The CLI currently calls migration on **every action**, including `read`; for strictly no-migration inventory use `OperationalReviews(db, "local", recent=...).read(packet_id, human)` after schemas exist. A supplied `recent` must use the same workspace/database and deliberate retention clock. The review owner accepts no provider/model credential and calls no translation/model service. Safe IDs/method/attribution remain after support loss; any actual input, including unselected/unresolved inputs, controls derivative annotation visibility. Retention loss permanently clears stored annotation bodies. Operator-exported JSON/submission files require their own retention cleanup.

Exact request retries reopen the packet/record; new review IDs append corrections, bounded to 50 records/packet and 5,000 packets/workspace. Reopen before using an export. Inspect selected/submitted/currently countable/unavailable denominators and separate technical, translation-assisted, Japanese-original and marketer-usefulness dimensions. Recorded annotations do not establish source truth or generalization. Qualified Japanese-original adjudication is separate and remains `not_validated` here.

For the older same-corpus manual-before-assisted evaluation, use `tools/pilot_evaluation.py --help` and the [evaluation procedure](evaluation.md). Perform actual manual baseline **before** assistance, disclose prior exposure, retain real times/counts, useful observation/reusable candidate decision or deliberate deferral, missing evidence and corrections. If prior exposure invalidates the baseline, leave that gate pending. Proposed measurement/notes are not human-quality acceptance. [Packet contract](evaluation.md#operational-result-review-packets).

## 24. Configure model and live-source operations

### 24.1 Explicit local simulated model setup

The installed normal `smi-review` CLI has no model/key/rate flags and never discovers a model key from the environment. Model criteria, ranked shortlists, nonempty extractive answers and semantic X assessments require trusted Python constructor arguments. This completely local setup demonstrates the shared public transport port with an explicitly scripted output; it performs **no network I/O**. Run in the Python session from section 6 after migration. The rates/weights/token contract/model IDs below are fictional test configuration, not current commercial pricing or quality evidence.

```python
import json
from datetime import datetime, timedelta, timezone
from smi_campaigns.responses import ResponsesRoute
from smi_costs import CostScope, UsageAccounting

model_costs = UsageAccounting(db)
model_now = datetime.now(timezone.utc)
model_start = (model_now - timedelta(days=1)).isoformat()
model_end = (model_now + timedelta(days=1)).isoformat()
model_costs.configure_scope(CostScope(
    "guide-model-simulation", "synthetic-openai", "responses-simulation", "metered", "USD",
    model_start, model_end, unit="weighted_token", rate_version="guide-model-rates-v1", unit_rate="0.001",
), human)
model_costs.configure_ceiling("guide-model-simulation", human, amount="100", currency="USD",
    period_start=model_start, period_end=model_end)
route = ResponsesRoute(
    model="guide-synthetic-model-v1", model_version="guide-synthetic-revision-v1",
    scope_id="guide-model-simulation", rate_version="guide-model-rates-v1",
    input_weight="1", cached_weight="0.5", cache_write_weight="1", output_weight="2",
    max_input_tokens=4000, max_output_tokens=500, max_request_bytes=100000,
    max_response_bytes=20000, timeout_seconds=2,
    measurement_policy="synthetic-transport-input-bound-v1",
)

class ScriptedResponses:
    execution_mode = "simulated"

    def __init__(self, output):
        self.output = output

    def create(self, request, *, credential, timeout_seconds, max_response_bytes):
        output = self.output(request)
        response = {"model": request["model"], "status": "completed", "output": [{
            "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": json.dumps(output)}],
        }], "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140,
            "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0}}}
        raw = json.dumps(response).encode()
        if len(raw) > max_response_bytes:
            raise ValueError("scripted_response_too_large")
        return raw

credential = "synthetic-demo-value-not-a-provider-key"
transport = ScriptedResponses(lambda request: {
    "support_ids": [], "limitation": "missing_information",
})
```

This particular scripted output is valid for a KB-answer missing-information result, deliberately claiming no semantic judgment. Inject it into `KnowledgeAssistant` as in section 13. Choose a **separate schema-appropriate scripted transport** for another operation; arbitrary answer output cannot satisfy ranking/criteria/semantic validation. Real tests in section 25 provide complete fixture implementations for all four consumers.

For natural-language criteria on a brief with nonempty `original_input`, a valid explicit scripted addition is:

```python
from smi_campaigns import CampaignStore
criteria_transport = ScriptedResponses(lambda request: {"criteria": [{
    "id": "prefer-skincare", "label": "Prefer literal skincare topic support",
    "kind": "topic_mention", "value": "skincare", "required": False,
    "operator": "include", "unknown_handling": "acknowledge",
}]})
campaigns = CampaignStore(db, model_route=route, model_transport=criteria_transport, model_credential=credential)
interpreted = campaigns.interpret_criteria("CAMPAIGN_ID", "BRIEF_ID", human,
    expected_version=1, request_id="guide-criteria-1")
print(interpreted)
```

Inspect `interpretation_id`, exact original input/profile/model/method/schema/outcome/usage/operation. The browser action is `POST /campaigns/CAMPAIGN_ID/interpretations`; it displays the successful appended additions before a **separate explicit selection** for comparison/recommendation. It preserves unchanged human criteria/market/platform/product scope and grants no task authority. A concurrent brief successor can make a result stale. Claims commit before I/O; retries retain blocked/invalid/uncertain/in-progress outcomes without another dispatch.

To expose configured capabilities through the browser, use the public server constructor rather than fictional flags:

```python
from smi_review import ReviewApp
from smi_review.server import make_server
app = ReviewApp(db, actor_id=human.actor_id, model_route=route,
    model_transport=transport, model_credential=credential)
with make_server(app, 8765) as server:
    print(server.url, flush=True)
    server.serve_forever()
```

Select the schema-appropriate `transport` for the workflow being demonstrated, and pass optional offline/schedule/monitoring settings in the same constructor as documented above. Stop the existing server first if using the same port. A scripted response is a software demonstration, never actual language/usefulness validation.

### 24.2 Provider model boundary

Live Responses execution is installed behind `ResponsesHTTPTransport(enabled=False)` by default. Only independently authorized trusted construction with `enabled=True`, a transient credential and matching `execution_mode="provider"` route/scope can dispatch. The installed verified-contract allowlist is the exact model snapshot `gpt-5.4-mini-2026-03-17`, `model_version` equal to that snapshot, `model_contract_version="openai-gpt-5.4-mini-2026-03-17:2026-10-20"`, `measurement_policy="verified-model-context-v1"`, `max_input_tokens=272000`, finite output cap at most 10,000 under this journey, and cache-write weight equal to uncached-input weight. This records what **this code accepts**, not a claim that the snapshot/prices are the latest offering. Other provider models/aliases require a code/contract change; no model default or commercial price is installed.

The operator supplies all route byte/time/token bounds, rates/weights, provider-reported `openai`/`responses` scope and shared ceiling. The fixed HTTPS transport makes one `/v1/responses` request with strict schema, no tools/state/stream/background, `store=false`, default tier and disabled truncation. There is no paid preflight or automatic retry. Valid final usage can settle an invalid/refused/incomplete/stale result; missing/invalid usage/model/tier or lost response preserves liability/meter failure. Reconciliation cannot recover a response. No live acceptance receipt or actual human model-quality gate has been completed. [Model contract](campaigns.md#bounded-natural-language-interpretation), [cost basis](costs.md#responses-token-measurement-and-provider-provenance).

### 24.3 Direct live adapters and queued live keyword/profile work

**Direct adapter commands can contact external services and consume credits.** They are separate from the offline smoke path and are only appropriate after the operator has source access/use permission and accepts their scope/cost. Installed examples:

| Direct manifest | Exact operation and limits / recovery |
| --- | --- |
| `examples/live/tiktok-oembed-manifest.json` | `smi-ingest ingest MANIFEST --max-requests 10`; supplied direct TikTok URLs, at most ten references/attempts, 8-second/64 KiB response caps, one transient retry, no 429 retry. Reference-only transient policy stores no title/author/caption/metrics/raw response or canonical creator facts; replay unavailable |
| `examples/live/tiktok-web-manifest.json` | `smi-ingest ingest MANIFEST --max-requests 2`; direct pages, at most ten attempts including one transient retry, 8-second/1 MiB response caps, no retained raw HTML. Bot challenge/partial coverage explicit |
| `examples/live/brightdata-tiktok-manifest.json` | `uv run --env-file .env smi-ingest ingest MANIFEST --max-requests 12`; existing direct profile/posts adapter reads **`BRIGHTDATA_API_TOKEN`**. At most two paid scrapes/creator, three creators, ten requested posts each. Pending snapshot → `resume RUN_ID`, including saved minimum wait (at least 30 seconds after running response); no automatic paid scrape retry |

Here `MANIFEST` means the path in that row. A successful page/HTTP response proves neither complete history nor comparison-grade performance coverage. No automatic provider fallback is installed. The narrower oEmbed route needs no developer login/paid key but still performs network I/O and grants no broader retention/use rights. The [curated sample README](../examples/curated/jp-kbeauty-tiktok-2026-10-05/README.md) preserves the supplied URLs/manifests behind its historical export; rerunning them is fresh live collection, not reproducing offline input.

Queued live query work uses the separate `brightdata-tiktok-keyword` route and exact proposal approval or recorded live schedule authority. Admission may be enabled by `save-proposal ... --enable-live-discovery` with an operator-selected live manifest, then inspected/approved/submitted with the normal exact IDs; it never executes a request. Worker command `run-live-discovery-task TASK_ID --enable-live-discovery --authorize-live-operation --authorize-source-use` additionally reads **`BRIGHT_DATA_API_TOKEN`** (with underscore) only when all three switches are set. That variable is distinct from the older direct adapter's `BRIGHTDATA_API_TOKEN` placeholder in `.env.example`; do not assume one configures both. No credential is discovered by this guide. Use global `uv run --env-file ...` explicitly if an authorized operator manages that environment.

Live worker setup additionally requires current process/retention policy, exact saved route/hash/bounds, commercial provider cost binding/ceiling and actual external authority. New keyword scope returns at most one bounded TikTok post; pending snapshot progress/download retains independent one-use HTTP cost commitments and not-before fences. Unknown provider capture times remain unknown and cannot support freshness avoidance. Actual requests/usable fields/final charges/live language quality remain unverified here. Schedule `configure(..., live=True)` records the exact route authority; changing a file/runtime switch cannot activate an offline configuration. Due tick still only acknowledges work.

The optional **one missing nickname** extension has no CLI enablement flag. Trusted Python composition uses `OfflineRoute(..., supplementation=SupplementationPolicy(...))`, an exact human proposal `profile_supplement=ProfileSupplement(profile_url, native_id)` from `smi_tasks.supplementation`, and `LiveDiscoveryConfig(..., profile_supplementation_authorized=True)` on `OfflineTaskWorker(..., live_discovery=config)`. The target must be a canonical TikTok profile URL/numeric ID corroborated by primary support. It fills provider `nickname` only, stops for existing supported field/insufficient configured information value/capability/permission/limits/cost, and does not refresh an already supported stale field. Profile `tiktok:public` and keyword `brightdata:tiktok-posts` identities/provenance remain separate, with no inferred equivalence or profile metrics. Bind the profile route to the primary declared provider scope; original task limits remain cumulative. A 202 is pending-unresumed, and ambiguous/lost work never receives a paid reissue. [Source details and remaining gates](source-integrations.md), [task nickname contract](tasks.md#one-missing-profile-nickname).

## 25. Check, build and troubleshoot

### 25.1 Verification and packaging

```bash
uv sync --locked
uv run --locked python tools/check.py --static
docker compose up -d --wait postgres
uv run --locked python tools/check.py
```

The shared local/CI command runs Ruff correctness/syntax lint, local documentation links, physical ERD table coverage, relative instruction symlinks, one sanitized PostgreSQL preflight and pytest. `--static` omits database tests. PostgreSQL tests create/drop unique temporary schemas; they need a development/test database with schema-create/drop permission. Set **`SMI_TEST_DATABASE_URL`** explicitly for another test instance; setting only application `SMI_DATABASE_URL` does not select it. Tests do not seed a user's review workspace. Broad verification uses real PostgreSQL with simulated source/model I/O; a passing suite does not prove provider account readiness, Japanese semantics, marketer usefulness or live performance. Historical test counts are not a new run.

The [current freshness-fixture limitation](development.md#current-test-fixture-limitation) can fail the assistant-enrichment assertion as fixed sample captures age beyond their threshold. Keep that known baseline issue separate from documentation/static verification; do not treat an old green count as a current pass.

For focused investigation, run the relevant files (each still needs its stated PostgreSQL fixture):

| Concern | Useful test entry points |
| --- | --- |
| Import, exact support, publication and query | `tests/test_evidence_sets.py`, `tests/test_knowledge.py`, `tests/test_publications.py`, `tests/test_knowledge_queries.py` |
| Current comparisons, generated/model recommendations and curation | `tests/test_current_comparisons.py`, `tests/test_recommendations.py`, `tests/test_criteria_interpretation.py`, `tests/test_ranked_recommendations.py`, `tests/test_shortlist_curation.py` |
| Coverage/regeneration, worker fencing/recovery, inbox | `tests/test_campaign_coverage.py`, `tests/test_campaign_regeneration.py`, `tests/test_tasks.py`, `tests/test_task_concurrency.py`, `tests/test_completion_inbox.py` |
| Assistant gap journey and publication-before-answer | `tests/test_assistant.py`, `tests/test_assistant_enrichment.py` |
| Schedule/day accounting, avoidance and gated live work | `tests/test_schedules.py`, `tests/test_schedule_allowance.py`, `tests/test_discovery_history.py`, `tests/test_live_discovery.py`, `tests/test_live_schedules.py`, `tests/test_supplementation.py` |
| Recent X, both alert methods, context, promotion and periodic gates | `tests/test_recent_monitoring.py`, `tests/test_quantitative_alerts.py`, `tests/test_semantic_alerts.py`, `tests/test_alert_investigations.py`, `tests/test_monitoring_promotion.py`, `tests/test_live_recent.py` |
| Costs, explorers, HTTP safety and actual-review separation | `tests/test_cost_admission.py`, `tests/test_cost_reconciliation.py`, `tests/test_graph.py`, `tests/test_task_lineage.py`, `tests/test_review.py`, `tests/test_operational_reviews.py`, `tests/test_pilot_evaluation.py` |

For example, `uv run --locked pytest -q tests/test_assistant_enrichment.py tests/test_task_concurrency.py` exercises that bounded integration surface. Run the shared check before completing code changes. To produce distribution artifacts, `uv build` uses the configured Hatchling backend to build wheel/sdist into `dist/`; it packages all eight owners and runs no server/worker. No containerized application/web/worker build is supplied. [Development reference](development.md).

### 25.2 Troubleshooting by observed state

| Observation | Check / next operation |
| --- | --- |
| Database connection/setup unavailable | Start PostgreSQL, confirm host port **6543**, chosen existing schema and explicit `smi-ingest migrate`; do not paste DSNs/credentials into bug reports |
| Server cannot start | Check actor validity and occupied port; stop old server or use `--port 8766`; default is loopback only |
| Browser POST rejected after restart | Reopen the loopback page for current CSRF token; use exact local Host/same-origin form. Do not bypass 403 protections |
| 409 version/request conflict | Reopen history/current heads; retain the original request/body for retry, or deliberately begin a new successor with new request and current expected versions |
| Current KB empty although import succeeded | Import/normalization/preparation do not publish. Publish the **ingestion** run; include supported caption interpretations explicitly for literal derived criteria |
| Invalid publication/run ID | Distinguish import/ingestion `run_id` from knowledge preparation `run_id`; use actual local observation IDs, not original export IDs |
| Synthetic values missing | Opt into synthetic visibility on both creation and reopen; metadata can remain visible without values |
| Caption/profile/audience result unknown | Inspect exact source/method gaps; literals/kana/PR do not prove language, geography, contracts, sales or complete history |
| Generated shortlist exists but discovery refused/queued | Expected save-first behavior. Read disposition; configure capability/authority for new work, or explicitly execute the already returned task |
| Task stays queued | No consumer runs automatically. Invoke the one-shot worker with that **existing** task ID |
| Task running/recoverable after interruption | Inspect ownership and committed phase. Connected owner still holds lock; after disconnect resume same task, preserving original attempt/run/receipt |
| Task waits on money/policy/runtime | Inspect current control/gate reason and fix that prerequisite. Resume only a resumable same task; do not broaden saved scope or reissue uncertain paid work |
| Publication committed but completion pending | Same worker/task recovery validates the atomic receipt and finishes the later completion event without collecting again |
| `no_usable_update` | Inspect empty/unchanged/cap-excluded/unsupported coverage; it is neither a source failure nor proof of market absence |
| Model route unavailable | Normal CLI has no implicit model configuration. Use explicit Python composition; a key in `.env` alone enables nothing |
| Invalid/incomplete/uncertain model result | Read exact saved claim/cost/limitations. Same request never redispatches; final accounting and health recovery do not recreate result |
| Keyword tick makes no task | Check local due time, fixed accounting timezone, same-day occurrence history and refusal. Prior missed days are not replayed |
| Old monitoring fixture yields empty/unavailable result | Respect original timestamps, seven-day window admission and capture-based retention; use deliberate isolated fixed-clock demo or fresh permitted local test evidence |
| Alert not assessable/no alert | Check baseline comparability/coverage/threshold and current support; bundled partial fixture cannot prove a volume spike or semantic controversy |
| Historical text/reasons/counts vanish | Current source/derivation/retention policy governs copies. Reopen safe lineage; do not reconstruct purged bodies from exports or retries |
| Cost scope blocks despite higher ceiling | Inspect unresolved dispatched/declaration/unknown liabilities, active period and meter failure; obtain final evidence, reconcile named portions and separately recover meter health |
| Test preflight fails despite working app | Tests read `SMI_TEST_DATABASE_URL`, require schema permission and use separate temporary schemas; app DSN/schema settings are not test configuration |

Supported local error responses include validation failure, `409` conflict, `404` missing record, sanitized `503` setup/database failure, `403` Host/origin/CSRF rejection and `413`/`415` unsupported/oversized input. Keep IDs, method versions, source-free state/reason and exact command available for diagnosis; source text and secrets belong only in permitted views. For behavior not listed here, check the relevant owner contract and [readiness roadmap](roadmap.md) before assuming an automatic service, external action or future capability exists.
