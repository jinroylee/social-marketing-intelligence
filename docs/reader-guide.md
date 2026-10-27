# Understanding the application

This guide connects the browser workflow, Python modules and database using the repository's Hero Cushion sample. It describes implemented behavior; the linked contracts and SQL define the precise interfaces.

The [target functional requirements](functional-requirements.md) add ranked recommendations that agents can save as shortlists without human review, an enrichment assistant, background acquisition, lightweight X alerts, graph/lineage interfaces and hybrid spending controls. Bounded extractive knowledge answers and explicit gap/proposal/approval/task follow-up are installed; bounded offline X volume and provisional quality-controversy alerts with their local inbox and bounded existing-KB investigations are installed; autonomous research, semantic shift/richer explanation and explorer surfaces remain future work. The browser offers automatic deterministic shortlists and bounded supported model ranking through an explicitly configured route, verified with simulated I/O; the human save/confirmation steps below describe the separate human-selection workflow.

## What the application is today

The application is a working local pilot for evidence-backed marketing decisions. Browser forms perform real validation and save durable PostgreSQL records. Closing the browser or restarting the server does not erase saved work. One Python application contains the modules below; they are not separately deployed services.

It can help a marketer ask a question of a selected sample, compare accounts against explicit criteria, automatically save a deterministic or validated model-ordered shortlist, or save a reviewed exploratory selection, and document measurement intentions and decision notes. Its source interpretations use conservative caption rules; the optional model supplies relative fit order over those supported criterion states. It does not yet establish market representativeness, creator quality, audience location or sales performance.

Calling it a prototype is reasonable when discussing product maturity. Calling it a working local pilot is more precise: the workflow and persistence exist, while usefulness and original-language interpretation still need human evaluation. The browser application is not an embedded AI agent.

## The three kinds of information

| Kind | Example | What it means |
| --- | --- | --- |
| Observed source information | A captured caption contains `ヒーロークッション`; the post displayed 1,875 views | The source reported this information at a particular time. It is not independent verification of the author's claims. |
| Derived interpretation | A configured alias maps that caption span to the Hero Cushion product family | A named method interpreted source text. Its evidence, configuration and provisional status remain visible. |
| Human input or decision | A marketer selects the account for further investigation and acknowledges unknown audience geography | An attributable human judgment. It does not become an observed fact or a measured outcome. |

Keeping these separate is the reason for many of the tables. A caption, an interpretation of that caption and a decision based on that interpretation need different owners and histories.

```mermaid
flowchart TD
    A[Captured source observations] --> B[Account and post identities, fields and metrics]
    B --> C[Evidence set: exact observations and normalization versions]
    C --> D[Rule-based caption interpretations]
    E[Human reference catalog] --> D
    D --> F[Independent investigation and snapshot findings]
    D --> G[Campaign account comparison]
    H[Human campaign brief] --> G
    G --> I[Human draft or confirmed shortlist]
    I --> J[Proposed measurement plan and human notes]
```

Investigations and campaigns are separate uses of shared evidence. An investigation does not automatically start a campaign, and a campaign does not require a preceding investigation.

## Follow one real sample post

The first record in [the frozen sample](../examples/curated/jp-kbeauty-tiktok-2026-10-05/observations.json) provides these values:

| Item | Captured sample value |
| --- | --- |
| TikTok handle | `guga9791` |
| Native account ID | `6819904612390634498` |
| Native post ID | `7549049550934166804` |
| Published | 2025-09-12 04:07:52 UTC |
| Captured | 2026-10-05 04:15:22 UTC |
| Caption fragments | `APRILSKINのヒーロークッション（21）`, `#pr` |
| Sampled metrics | 1,875 views, 27 likes, 1 comment, 0 shares |

These are historical sample values, not current TikTok counts. Zero shares is an observed zero. An unknown fee would remain unknown, not zero.

For the examples below, `O1`, `D1`, `P1`, `A1` and similar labels are explanatory shortcuts for database UUIDs, not literal stored IDs.

1. **Capture:** `source_observations` stores O1's acquisition metadata, capture time, permission policy and retained-payload reference. Permitted payload bytes live in the evidence directory. For this offline import, the payload is the exported JSON record, not original TikTok HTML.
2. **Identity:** `canonical_entities` contains account A1 and post P1. `external_identities` connects them to TikTok's native string IDs. A mutable handle is recorded separately; it does not define account identity.
3. **Normalization:** `derivations` records that mapper `snapshot-json:v1`, using canonical policy `canonical-v1`, interpreted O1 as D1. `field_assertions` records the caption, URL, publication time and author account for P1, plus the observed handle for A1. `metric_observations` contains four count records; the views record uses definition `tiktok.web.views.v1` and value `1875`.
4. **Fixed input:** `evidence_set_members` pins O1 and D1 inside the selected dataset. Original export observation/run IDs are retained as lineage alongside the new local IDs.
5. **Interpretation:** When preparation is requested, the catalog maps `ヒーロークッション` to product `aprilskin-hero-cushion`. The current rules identify the first occurrence at caption character range `[66, 75)`, meaning start inclusive and end exclusive. They record a product-family mention with stance `not_assessed`. A second occurrence in a hashtag is another supported span. The caption also contains a literal PR marker. This method does not turn `(21)` into a verified shade interpretation.
6. **Campaign use:** With the [example brief](../examples/campaigns/hero-cushion-brief.json), the account has literal support for product mention and kana-script criteria. Japan audience geography remains unknown. Because the brief supplies this account and the dataset also contains it, its comparison origin is `both`.
7. **Human decision:** A marketer could write “Investigate this account because its sampled post mentions Hero Cushion,” cite support, acknowledge unknowns and confirm an exploratory shortlist. That wording is an illustrative decision, not a decision already saved by the sample import.
8. **Planning:** A subsequent plan could propose checking matched orders once seller data is available. A note could say to defer commercial commitment pending audience and fee information. Neither creates sales results.

Importing the sample loads source evidence and curation annotations. It does not automatically prepare knowledge, create a campaign or save a decision. Curation annotations are separately labeled development annotations; the extraction rules read source captions and the registered catalog.

## What an evidence set does

An **evidence set is a named, fixed collection of inputs for an analysis**. Think of it as an analysis's input manifest: “Use precisely these captured observations, with these normalization versions.”

For the repository sample:

```text
evidence_sets
  workspace_id: local
  dataset_id: jp-kbeauty-tiktok-public-video-sample-2026-10-05
  digest: fingerprint of the exact exported file bytes
  manifest: format, namespace, expected membership and import information

evidence_set_members
  member 0 -> observation O1 + derivation D1 + original source IDs
  member 1 -> observation O2 + derivation D2 + original source IDs
  ...19 selected observations from 17 accounts in total
```

The set row describes the collection; member rows specify its exact contents. They reference the imported evidence rather than storing another complete caption copy per campaign. The current importer creates those local observations and member bindings together.

Without fixed membership, a result that queried “all posts currently in the database” could change whenever new posts arrived. Without a pinned derivation, a parser update could silently change what an old analysis meant. The set prevents both substitutions. A changed export requires an explicit new dataset ID; the importer rejects changed bytes under the existing ID.

One evidence set can support many knowledge runs, investigations and campaign comparisons. Each result records which subset its scope actually used. An ingestion run answers **which acquisition/import job ran**; an evidence set answers **which exact inputs this analysis may use**. A shortlist answers **which accounts were recommended or selected for the campaign**; the current pilot records automatic deterministic/model-ordered recommendations and human selections. They are different objects.

Fixed membership does not freeze permission to display evidence. Current source permissions can make a member unavailable; downstream explanations must respect that change. Corrections can also mark pinned support as requiring review rather than silently replacing it. See the [evidence-set contract](evidence-sets.md) and [policy ADR](adr/0002-pinned-support-current-policy.md).

## Browser screens and their code

The browser sends a form to [`ReviewApp`](../src/smi_review/app.py). That application calls the public domain stores; those stores own decisions and transactions. View files render HTML. The browser itself is not the durable database.

| Screen or control | Friendly meaning | Main code and stored records |
| --- | --- | --- |
| **Offline task submit / detail** | Submit configured synthetic work for an exact current campaign brief or reviewed proposal/human approval, then reopen exact scope, actors and outcomes. | [`AcquisitionTasks` / `OfflineTaskWorker`](../src/smi_tasks/__init__.py); six task/proposal/approval/completion tables, existing ingestion/publication owners |
| **Campaign workspace** (`/`) | Your saved campaigns and the available fixed input collections. “Loaded evidence” is sample coverage, not a complete market database. | [`views.home`](../src/smi_review/views.py); campaign, evidence-set and catalog listing interfaces |
| **Create / revise brief** | State brand/products, objective, target market, platforms and selection criteria; optionally keep your original prose. Reopen the exact saved structured profile and earlier versions. Optional commercial details may remain unknown. | `views.brief_form`; [`CampaignStore`](../src/smi_campaigns/store.py); `campaigns`, `campaign_briefs` |
| **Selection criterion** | A stable named requirement or preference with an evidence type, expected value, inclusion/exclusion rule and unknown handling. The saved profile labels current ordering unranked and coverage descriptive; free-text labels and original prose express your intent without asserting source facts. | [`Brief` / `Criterion`](../src/smi_campaigns/contracts.py); brief document and executable profile; [profile contract](campaigns.md#implemented-briefs-and-actors) |
| **Prepare rule-based comparison** | Run the fixed caption interpretation and account-comparison pipeline against the chosen brief and dataset. It does not search the internet. | [`KnowledgeStore.prepare`](../src/smi_knowledge/store.py), [`build_comparison`](../src/smi_campaigns/comparison.py), `CampaignStore.prepare_comparison`; knowledge and comparison tables |
| **Account comparison** | One card per known or dataset-supplied account in scope, showing criterion judgments and missing information. There is no universal quality score or sales ranking. | `views.comparison_page`; `comparison_candidates`, `comparison_support` |
| **Original captions and provenance** | Inspect the original wording, highlighted supporting spans, source link, publication/capture dates and exact source references. Translation remains pending. | `views.evidence_panel`; [`EvidenceSetReader`](../src/smi_ingestion/evidence_sets/reader.py) and supported knowledge assertions |
| **Rank and save automatically** | Apply deterministic eligibility, validate one bounded model order and save it with explicit gaps. Failed/unavailable attempts remain visible; empty batches save without a call. | `CampaignStore.recommend_ranked`; `campaign_ranking_assessments` |
| **Recommend and save automatically** | Compare current KB and save a generated ordered shortlist with actual automation, rationale, gaps and support. Saving requires no human review; encounter order is unranked. | `CampaignRecommendations.recommend`; `CampaignStore.recommend`; `shortlist_revisions`; `shortlist_selections.position` |
| **Human inclusion reason / cite relevance support / acknowledge unknowns** | Record why you selected an account, what supports that reason and what you still do not know. Checking an unknown box acknowledges a gap; it does not resolve it. | `views.comparison_page`; `CampaignStore.save_shortlist`; `shortlist_selections` |
| **Save draft / confirm shortlist** | Save working choices, or explicitly record your reviewed exploratory selection. Confirmation is an internal decision, not creator consent or campaign execution. | `shortlist_revisions`, `shortlist_selections` |
| **Saved shortlist / successor revision** | Reopen exact saved membership, order where recorded and actual producer. Optional curation selects/reorders into an attributable human draft or separately confirmed successor; original automated history remains unchanged. Current evidence availability is checked when reopening. | `views.shortlist_page`; `CampaignStore.read_shortlist` |
| **Costs** | Inspect synthetic measured usage separately from forecasts, declared outstanding commitments and unknown/meter-failure coverage. | [`UsageAccounting`](../src/smi_costs/store.py); scopes/operations/entries, ceilings, route controls, one-use admissions, final reconciliations and meter recoveries |
| **Completion inbox** | Reopen one durable completion per task with actual coverage and current permitted publication navigation; usable campaign discovery offers explicit current-context regeneration while keeping old revisions intact. | [`CompletionInbox`](../src/smi_tasks/notifications/store.py); source-free `task_completion_events` |
| **Knowledge search** | Filter current committed permitted publications, inspect freshness and unknowns, and reopen exact saved support. Scan/result limits are explicit. | [`query_views`](../src/smi_review/query_views.py), [`KnowledgeQueries`](../src/smi_knowledge/queries/store.py) |
| **Knowledge publications** | Reopen committed bounded selections, exact support and current unavailable/superseded states. Publish explicitly through the operator CLI. | [`publication_views`](../src/smi_review/publication_views.py), [`KnowledgePublications`](../src/smi_knowledge/publications/store.py) |
| **Recent X** | Configure a separate bounded offline topic, explicitly collect a logical window and reopen original capture/time/coverage with current policy tombstones. Select comparable original windows for explicitly configured volume assessment or one exact window for provisional quality-controversy positions, retained local alerts and distinct inbox messages; no live source or per-post KB publication. | [`RecentMonitoring`](../src/smi_monitoring/recent/store.py), [`recent_views`](../src/smi_review/recent_views.py), [`QuantitativeAlerts`](../src/smi_monitoring/alerts/store.py), [`SemanticAlerts`](../src/smi_monitoring/semantic/store.py); [`AlertInvestigations`](../src/smi_monitoring/context/store.py); separate topic/window/capture/assessment/alert/context tables |
| **Investigations / create investigation** | Ask a standalone question about selected brands/products/topics, with optional publication dates. Intended market describes the question, not proven audience location. Selected references match with OR. | [`monitoring_views`](../src/smi_review/monitoring_views.py), [`MonitoringStore`](../src/smi_monitoring/store.py); investigations and scope revisions |
| **Prepare rule-based insight / snapshot insight** | Count literal reference and PR/Qoo10 support within matching sample posts. “Snapshot” means a bounded answer, not continuous monitoring or a market trend. A required caption language is currently not assessable by script rules. | [`build_summary`](../src/smi_monitoring/summary.py); `insight_revisions`, `insight_findings`, `insight_support` |
| **Measurement plans and decision notes** | Propose what would be measured and record human feedback. Plans require a saved shortlist associated with the current brief; even an empty/deferred shortlist is valid. Notes can reference historical shortlists. | [`planning_views`](../src/smi_review/planning_views.py), [`CampaignPlanning`](../src/smi_campaigns/planning/store.py); plan, note and note-support tables |

Comparison vocabulary:

- **Satisfied:** literal evidence matches an inclusion criterion. Semantic review remains provisional.
- **Not satisfied on evidence:** literal evidence matches something the criterion excludes.
- **Unknown:** the selected evidence cannot establish the criterion. Absence of a mention is not proof that an account fails it.
- **Required:** a confirmation constraint. A required unknown with handling `defer` blocks confirmation; handling `acknowledge` allows an exploratory selection with explicit acknowledgement. A required exclusion contradicted by evidence blocks confirmation.
- **Marketer known / retrieved / both:** supplied in the brief, obtained from the chosen dataset, or both. “Retrieved” does not mean autonomously discovered online.
- **Provisional:** an interpretation still needs semantic review. It is separate from a shortlist's draft/confirmed status.
- **Review required:** supporting evidence is unavailable or superseded; historical identity and permitted audit information can remain while dependent wording is withheld.

The UI does not currently expose a general database browser, ingestion dashboard, catalog editor or translation tool. Source ingestion and catalog registration use the CLI. See [local review](local-review.md) for routes and operator setup.

## Table dictionary

Most implemented tables hold supporting records for evidence, versions and explanations rather than separate user workflows. JSONB columns hold structured documents such as a brief or candidate judgment; UUID references connect those documents to their exact sources.

The examples below describe row shapes. Campaign and investigation examples are illustrative; loading the sample alone does not create them. Full columns and relationships are in the [physical ERD](data-model.md) and linked SQL.

### Acquisition, normalization and fixed inputs — 11 tables

Owner: [`smi_ingestion`](../src/smi_ingestion/schema.sql), including [`evidence_sets`](../src/smi_ingestion/evidence_sets/__init__.py).

| Table | What one row stores | Example |
| --- | --- | --- |
| `ingestion_runs` | One workspace-owned acquisition/import job: adapter, input manifest, limits, resource use, checkpoint, optional provider wait reason/resumability and status. | The offline job that imports all 19 sample observations. Its local run differs from the export's original collection runs. |
| `source_observations` | One captured source response or imported record, with acquisition lineage, times, policy, payload hash/path and coverage. | O1: the captured `guga9791` post record. |
| `ingestion_issues` | A reported problem associated with a run and optionally an observation. | An adapter failure code and sanitized message. |
| `canonical_entities` | A stable internal UUID for an account or a content item. It does not hold a complete mutable profile. | A1 is an account; P1 is its post. There is no implemented Creator/person entity here. |
| `external_identities` | A native identity tuple mapped to an internal entity: platform, namespace, kind, native string ID and synthetic flag. | `tiktok / web:public / account / 6819904612390634498 / false` maps to A1. |
| `derivations` | One mapper/policy version's normalization of one observation, with current/history status. | D1 normalizes O1 using `snapshot-json:v1`. This is source normalization, not the product-mention extraction run. |
| `field_assertions` | One field value or explicit missing/removal state, tied to an entity, derivation and source location. | P1's caption from `$.caption`; A1's handle from `$.author.handle`. An assertion means “the source reported this.” |
| `metric_observations` | One sourced metric value, definition, native name, precision, unit and time. | P1's `tiktok.web.views.v1 = 1875` at capture. It is not a sales result. |
| `unresolved_candidates` | A normalization item that could not be established, including the reason and source location. | A source account reference without enough native identity information. These are not campaign candidate accounts. |
| `evidence_sets` | One named, immutable dataset registration: manifest, byte digest, local import run and actor/time. | The 19-post sample dataset. |
| `evidence_set_members` | One ordered dataset member, pinning its local observation and derivation plus original source IDs. | Member 0 binds O1/D1 to the original exported observation reference. |

### Offline task admission and outcomes — 8 tables

Owner: [`smi_tasks`](../src/smi_tasks/schema.sql); [public task contract](tasks.md).

| Table | What one row stores | Example |
| --- | --- | --- |
| `enrichment_proposals` | An immutable supplied revision with purpose, refresh/fill/expansion intent, subject/search and input scope (including explicit discovery publication window), exact route/limits digest and proposer. | Save a proposal without submitting acquisition. |
| `enrichment_approvals` | One configured human's exact workspace/revision/digest approval and original retry identity. | Approval A authorizes at most one task for proposal P. |
| `campaign_regeneration_requests` | An explicit human regeneration request, actual producer, exact completion/original-shortlist/body, server-owned assessment retry identity and source-free outcome links. | Reopen one saved successor after restart; a discovery completion alone leaves the old result intact. |
| `campaign_discovery_requests` | One immutable automatic enrichment disposition per saved shortlist, attributed initiator, source/configuration refusal or exact submitted task. | A thin/empty supported result stays available while its associated task is queued, running or cost waiting. |
| `keyword_schedules` | Stable workspace accounting timezone, current configuration head and last observed tick. | Separate from monitoring; midnight local days retain exact UTC bounds. |
| `keyword_schedule_configurations` | Immutable keyword/settings versions, digest and actual operator/time. | Up to ten current registered keywords; edits preserve earlier authority. |
| `scheduled_post_days` | Fixed workspace/day bounds, effective cap/version and shared admission identity. | Cap edits preserve used posts; historical days retain their applicable configuration. |
| `scheduled_post_admissions` | Per-observation new/refresh/dedup/excluded/ineligible disposition under a scheduled occurrence. | Successful new identities and canonical effects commit together; raw request/record/cost use stays independent. |
| `keyword_schedule_occurrences` | One workspace/day/keyword-key disposition, exact configuration/day/window/allowance context and optional task. | Refusals and task history survive restart/edits; missed days are not replayed. |
| `discovery_history` | Exact discovery query/input/processing context, policy, prior basis, capture-based avoidance decision and referenced support, usable publications and failure/outcome. | A fresh complete repeat can make zero source calls without a new publication; old/unknown capture time, quota exclusions and failures remain eligible. Current policy governs source identity/time detail. |
| `acquisition_tasks` | A workspace/request-bound configured schedule, campaign or approved assistant task, exact brief/approval/configuration scope, initiator, hard limits, latest execution ID/session owner, durable commit/wait progress, outcome and sanitized coverage/failure. | Accepted now, executed separately through configured local supplied-reference or keyword-discovery capability. Its active PostgreSQL ownership lock distinguishes running from recoverable work. |
| `acquisition_attempts` | One attributable worker attempt, exact ingestion run, total recovery count, most recent 20 recovery actors/100 phases, prepared support IDs and times. | Worker B resumes Worker A’s same run/support after a disconnected session; a late Worker A cannot commit local effects. A valid subset can publish with the failed remainder visible. |
| `acquisition_task_publications` | A task-owned receipt committed atomically with its exact knowledge publication. | Task T produced publication P; recovery checks prepared support/run lineage. Public request text and fetch-only input create no receipt. |
| `task_completion_events` | One source-free event identity/task/time, committed with a terminal outcome; one unique event per task. | Reopen usable, partial, no-update or failure in **Inbox** after restart, with historical coverage and current permitted publication links. |

### Offline cost accounting — 6 tables

Owner: [`smi_costs`](../src/smi_costs/schema.sql); [public accounting contract](costs.md).

| Table | What one row stores | Example |
| --- | --- | --- |
| `cost_scopes` | Immutable workspace/scope configuration: provider/service, classification, currency/period, unit/rate/version, synthetic default or explicit provider-reported basis, configuring human/time. | An operator's simulated unit rate for one accounting month; no invented commercial price. |
| `cost_operations` | Stable workspace/request identity with actual actor/method, configured scope and optional validated exact task/attempt pair. | A synthetic model operation with no task, or a measurement attributed to the original worker attempt. |
| `cost_entries` | Workspace-unique measurement identity, operation, distinct usage/forecast/declared-commitment/unknown/meter-failure kind, exact decimal inputs and provenance/time/recorder; provider usage adds source-free token/cache/reasoning counts. | Three synthetic units at 0.125 derive 0.375; forecasts and unresolved declared commitments remain separate. |

| `cost_ceilings` | Current trusted scope amount, pause state, configuring human/time; scope fixes currency/period. | 0.125 synthetic allowance admits one bounded request costing 0.125. |
| `cost_route_controls` | Immutable workspace offline-route binding, exact cost scope and one-request bound. | Every campaign/approved-assistant worker reopens the configured guard after restart. |
| `cost_admissions` | One bounded dispatch per operation, reserved amount, dispatched/settled/refused state, reason and actual dispatcher. | A lost response retains its commitment; final reconciliation keeps the operation settled without permitting another call. |
| `cost_reconciliations` | Immutable workspace/event identity, exact operation/final measurement and named liability targets, final outcome, operator, report evidence/provenance and time. | A final 0.125 report replaces a named 0.25 reservation; its bill cannot release another portion. |
| `cost_meter_recoveries` | Immutable workspace/health-check identity, exact operation and already-reconciled failure IDs, operator, health evidence/provenance and time. | Late usage settles accounting while the scope remains blocked until an explicit meter-health recovery. |

### Shared business vocabulary, interpretations, publication and queries — 10 tables

Owner: [`smi_knowledge`](../src/smi_knowledge/schema.sql).

| Table | What one row stores | Example |
| --- | --- | --- |
| `knowledge_brands` | A workspace's stable human-supplied brand reference and preferred name. | `aprilskin` → APRILSKIN. |
| `knowledge_products` | A human-supplied product reference, brand association and preferred name. | `aprilskin-hero-cushion`, associated with `aprilskin`. This is not automatically a purchasable SKU. |
| `knowledge_catalogs` | An immutable configuration document containing brand/product/topic references and aliases, with its digest and recorder. | `beauty-caption-lexicon-v1` maps `ヒーロークッション` to the Hero Cushion family. Topics are in this document; no separate topic table exists. |
| `knowledge_runs` | One preparation against an exact dataset, catalog, method and request identity, including coverage and recorder/time. | K1 ran `caption-literal-rules-v1` over the sample using the beauty catalog. |
| `knowledge_assertions` | One derived typed interpretation with a source caption assertion, exact character span, value, provisional review status and support state. | “Span `[66,75)` is a family-level Hero Cushion mention,” supported by P1's caption. |
| `knowledge_publications` | One committed bounded selection, with workspace/request identity, method, actual producer, coverage and publication time. | A source-only update can publish an ingested account while profile attributes remain unknown. |
| `knowledge_publication_support` | One ordered exact observation/derivation and its selected assertion/metric IDs. | Publication member 0 pins O1/D1 without extending its frozen dataset. |
| `knowledge_publication_interpretations` | One selected existing interpretation ID in publication order. | A provisional caption mention is usable with its exact original source dependency. |
| `knowledge_query_results` | One bounded current query with workspace/request identity, purpose, filters, producer, original coverage and time. | Q1 searches recent committed publications and preserves an explicit incomplete-market limit. |
| `knowledge_query_members` | One ordered actual source/interpretation selection plus method/publication/freshness versions, with no source-value copy. | Q1 member 0 pins O1/D1 and specific published assertion/interpretation IDs; withdrawal later redacts its values. |

These tables are shared vocabulary and supported interpretations. They are not a vector database, an LLM's memory or an agent's internal reasoning log.

### Campaign questions, comparisons and decisions — 8 tables

Owner: [`smi_campaigns`](../src/smi_campaigns/schema.sql).

| Table | What one row stores | Example |
| --- | --- | --- |
| `campaigns` | A human-owned campaign workspace with current brief/shortlist version counters. | C1: an investigation of potential Hero Cushion accounts for Japan. |
| `campaign_briefs` | One immutable human question, optional original prose and structured executable-profile snapshot pinned to this exact brief/version, with author/time. Older rows retain a null profile. | Brief v1: stable product/script/audience criteria and unknown policies, `structured-caption-criteria-v1`, unranked ordering and descriptive fixed-observation coverage. |
| `campaign_ranking_assessments` | One exact-brief/current-KB assessment claim, actual automation, bounded model/method/schema/ranking profile, usage/cost linkage, status and optional saved shortlist. | Completed retries reopen; interrupted attempts never redispatch. Required unknowns can defer all accounts without a model call. |
| `campaign_criteria_interpretations` | One exact-brief original-prose interpretation attempt, requesting human, generated provenance, sanitized outcome, explicit model/measurement-basis/weight/bounds, usage and logical cost-operation reference. Failed/interrupted attempts cannot be silently retried or assessed. | Responses generated additions preserve human constraints; concrete provider HTTP is opt-in, and all verification is simulated with no live receipt. |
| `comparison_drafts` | One prepared comparison's exact brief, optional explicitly selected immutable criteria interpretation, either a frozen knowledge run/dataset/digest or current-KB query-result link, actual method/execution profile, coverage and preparation actor/time. | Compare brief v1 against K1, using `campaign-caption-comparison-v1`. |
| `comparison_candidates` | One account within that comparison: native key, campaign-relative origin, order and structured criterion judgments/unknowns, plus governed exact ranking inputs and validated judgments when assessed. | A1: origin `both`; product mention satisfied; audience unknown. Order is not a quality ranking. |
| `comparison_support` | A candidate's dependencies on observations, field assertions and optional knowledge interpretations. | A1's judgment depends on O1's caption interpretation and author identity assertion; metric-only support can omit a field assertion while its query manifest pins metric IDs. |
| `shortlist_revisions` | One immutable generated, draft or confirmed event pinned to brief/comparison, with actual producer/time, optional method/order/selection outcome and a nullable exact curation-source revision. Generated coverage pins its explicit policy/clock, comparison input references, counts and reasons; legacy/human coverage stays unrecorded. Legacy human order/source stays unrecorded. | Shortlist v1, confirmed by a named marketer. |
| `shortlist_selections` | One selected candidate, with generated position/rationale or human curation position/reason, cited interpretation IDs and separate human acknowledgements. Legacy human positions remain null. Generated gaps/support reopen through the pinned comparison. | A1 selected for further investigation; fees and audience remain unknown. |

### Bounded free-form KB answers — 1 table

Owner: [`smi_assistant`](../src/smi_assistant/schema.sql).

| Table | What one row stores | Example |
| --- | --- | --- |
| `knowledge_answers` | Human question/request identity, pinned query and all actual model-input IDs, source-free selected IDs, fixed uncertainty, immutable model/method/bounds, attributable usage/cost and outcome. | A model selects observed source values relevant to a question; withdrawing any input withholds the derived selection without rewriting history. |

The browser's **Ask knowledge** form needs no enrichment approval. It selects exact published findings with dates and explicit limits; it provides no semantic search, unconstrained synthesis or independent verification. A supported gap offers separate exact keyword/subject/window scope, saved proposal review, actual human approval, immediate task status and durable actual completion. Model/configuration failure alone offers no acquisition gap; only a later explicit question uses newly usable publications. Read [the answer contract](knowledge.md#bounded-free-form-knowledge-answers).

### Recent X evidence, alerts and context — 14 tables

| Table | Purpose | Example |
| --- | --- | --- |
| `monitoring_source_policies` | Current source permission with version | Offline sample may be displayed until explicit denial/expiry. |
| `monitoring_topics` | Stable topic key and current revision | Cushion topic stays independent of campaign keywords. |
| `monitoring_topic_revisions` | Original query/cadence/window/record/retention settings | An edited query does not replace a prior window. |
| `monitoring_windows` | Explicit frozen interval, acquisition and original coverage | 10:00–11:00 sample is a selected baseline. |
| `recent_x_observations` | Original native/source-time capture with governed body/tombstone | Repeated captures of one post are not new volume. |
| `monitoring_window_members` | Original window/capture membership | Detail reopens original evidence rather than newer captures. |
| `monitoring_x_withdrawals` | Permanent attributable native-post withdrawal | Later fixture aliases cannot restore a removed post. |
| `monitoring_volume_assessments` | Source-free configured method, exact pair, outcome/limitations | Missing baseline is retained without a spike claim. |
| `monitoring_detection_requests` | Exact actor/input/configuration retry receipt | Repeating a browser request reopens its assessment. |
| `monitoring_alerts` | Atomic volume alert and durable local notification identities | A supported sample threshold crossing appears once in inbox. |
| `monitoring_semantic_assessments` | Exact original window, all prepared input IDs/digest, method/model/bounds, no-reissue claim, fixed positions/spans and usage | A provisional possible quality-controversy signal has no baseline or verified controversy claim. |
| `monitoring_semantic_requests` | Exact actor/window/configuration retry identity | Retrying cannot call the model again. |
| `monitoring_semantic_alerts` | Atomic semantic alert and unique local notification identity | A distinct semantic inbox message survives as unavailable history after any input is lost. |
| `monitoring_alert_investigations` | Exact alert kind/identity, KB query result, original recent dependencies and permanent explanation-withheld marker | New KB publications do not replace old context; missing context remains a gap. |

Current numerical comparisons and semantic quotations are derived from permitted original support; denied/expired/withdrawn evidence leaves visible unavailable history. See [quantitative](monitoring.md#configured-quantitative-volume-assessments) and [semantic](monitoring.md#bounded-provisional-quality-controversy-assessments) monitoring contracts.

### Independent questions and snapshot answers — 5 tables

Owner: [`smi_monitoring`](../src/smi_monitoring/schema.sql).

| Table | What one row stores | Example |
| --- | --- | --- |
| `monitoring_investigations` | A standalone human-owned investigation with current scope/insight version counters. | I1 asks which Hero Cushion mentions occur in the sample. |
| `investigation_scopes` | One immutable question, selected references, market context, platforms and optional date/language constraints. | Hero Cushion, TikTok, intended JP context, no required language filter. |
| `insight_revisions` | One prepared answer's exact scope, knowledge run, dataset/digest, method, coverage and limitations. | Answer v1 using `caption-snapshot-summary-v1`. |
| `insight_findings` | One structured, source-dependent finding within an answer. | The frozen fixture supports Hero Cushion mentions in six distinct selected posts; this is not a market-share or growth estimate. |
| `insight_support` | A finding's observation, field assertion and optional interpretation dependencies. | The caption mentions and author assertions used to count those distinct posts/accounts. |

### Measurement intent and human learning — 3 tables

Owner: [`smi_campaigns.planning`](../src/smi_campaigns/planning/schema.sql).

| Table | What one row stores | Example |
| --- | --- | --- |
| `measurement_plan_revisions` | A human proposed plan tied to an exact campaign brief and shortlist: outcome definition, intended source, matching/attribution assumptions and gaps. | Propose matched orders and returns-adjusted revenue if seller records become available. Status remains `proposed`; no measured results are stored. |
| `decision_note_revisions` | One human note tied to a historical shortlist, with author/time and optional citations. | “Defer commitment until audience and fee information is obtained.” |
| `decision_note_support` | The note's source dependencies, inherited from the selected candidates as well as explicit citations. | If the selected evidence becomes unavailable, copied note text cannot bypass its policy. |

Support tables answer “what does this explanation depend on?” They let the system inspect, hide or purge dependent copies when permissions change. They are not additional copies of the original source text. Permitted history and membership may remain while text is withheld; implemented deletion limits are documented in [architecture](architecture.md#policy-and-operational-limits).

## Versions and timestamps without the jargon

- A **capture time** says when the source was observed. A **publication time** says when the post was published. An **import time** says when the local application recorded the export. A **knowledge publication time** says when an exact ingested selection became available; it does not refresh a source capture. Importing an old post today does not make it a new post or a fresh measurement.
- A **derivation version** identifies how a source observation was normalized. A **knowledge run** identifies how its caption was interpreted using a catalog/method. A **brief revision** identifies which human question was asked. A **shortlist revision** identifies a saved set of recommendations or selections and its producer; the producer is explicitly automation or human. Legacy human ordering remains unrecorded. These are different histories.
- A **digest** is a fingerprint used to detect changed bytes or changed request/configuration content. It is not a relevance score.
- A **request ID** lets a retried save/preparation return its existing result instead of accidentally creating another one. An **expected version** makes an outdated form fail visibly rather than overwrite newer work.
- Historical references are stable; permission and support health remain current. Versioning does not grant permanent access to source wording.

## Automation, agents and the remaining product boundary

There is implemented automation: normalization, literal alias/marker matching, criterion matching, distinct-post counting, validation, versioned saving and permission checks. The **Prepare** buttons execute a predetermined sequence:

```text
read fixed evidence -> apply caption rules -> build comparison or summary -> save result
```

Explicit trusted model configuration enables one bounded criteria, supported ranking, extractive knowledge-answer or provisional semantic-monitoring call through the shared Responses route. Default startup has no model route; all verification uses simulated I/O. There is no translation model, model-driven tool selection, autonomous research loop or scheduled monitoring job. The application's `local-rule-preparation` actor has kind `automation` so attribution and write permissions are explicit; that label does not imply an AI agent. The coding assistant developing this repository is separate from the running application.

The accepted target adds broader autonomous assistant research, semantic shift/richer explanations and explorer views through evidence/knowledge interfaces. Derivable actual costs receive configured ceilings; unmeterable portions retain forecasts. The direct supplied-proposal and assistant-gap exact approval journeys, offline task path, atomic shared scheduled new-post allowance and source-free synthetic accounting/forecast surface are present; those broader capabilities remain future work. Creator/person associations, full account histories, actual outcome ingestion and attribution, and authenticated hosted operation also remain future work. Current plans and notes do not implement those capabilities.

Marketer evaluation is a human assessment of whether the findings and decisions are useful. It is not a runtime agent or a database workflow that can manufacture its own answers. The procedure is in [quality review](evaluation.md); execution records belong in `.scratch/`.

For a first reading, follow the real post through capture → source field → product interpretation → comparison → human decision. Then use the table dictionary to inspect the supporting records. You do not need to memorize all tables to understand the product.


The **Keyword schedule** navigation opens `/schedules`. A server started with `--schedule-operator` can save explicit keyword JSON/settings and acknowledge due offline tasks; ordinary startup can inspect history only. Tick acknowledges work without collecting, and links the existing task/status/publication surfaces. The initial configurable daily target is 50 unique eligible new posts total across up to ten keywords; atomic canonical admission enforces the shared allowance, independently of request/cost limits and per-keyword yield. Schedules default offline; the operator may explicitly activate the verified live keyword route under recorded exact authority and independent runtime/spending gates. See [the schedule contract](tasks.md#registered-offline-keyword-schedule) for day/timezone/cadence and immutable history.


One [live-capable TikTok keyword route](source-integrations.md#bounded-live-tiktok-keyword-discovery) is now implemented behind explicit server/worker/source/operation/cost gates. It accepts at most one returned post per approved query. All verification is simulated: actual source capture times, current live availability and final commercial charges remain unverified. Existing review/task pages still reopen without configured source inputs.

For the optional [one-field supplementation journey](tasks.md#one-missing-profile-nickname), an operator configures nickname policy and a marketer approves an exact profile URL/native ID with the discovery proposal. Task detail explains the choice to continue or stop. The KB shows an independently sourced `tiktok:public` nickname observation, unknown original capture time and unestablished equivalence to the primary keyword account; additional metrics or creator facts are not inferred. Existing permitted nickname support prevents another profile request. This is installed library-configured behavior with simulated verification; it establishes no actual source readiness or human-usefulness result.


Owner: [`smi_tasks.assistant`](../src/smi_tasks/assistant/schema.sql).

| Table | Meaning | Public use |
| --- | --- | --- |
| `assistant_enrichment_requests` | One human request links the original answer, fixed gap code and explicit keyword/subject/window input to a fresh nested proposal request and its exact immutable revision. | Reopen pending scope, review/approve once, follow task and actual completion without copying source values or changing the old answer. |
