# Operational functional requirements

This is the accepted target contract for the flows in [`FR.md`](../FR.md) and the [product proposal](../POPOSAL.md). It incorporates automatically saved recommendations, incomplete-profile eligibility, a lightweight X evidence path and hybrid spending control. Requirements described as target behavior are not claims of implemented functionality.

## Current implementation and target coverage

| Area | Implemented now | Missing target behavior |
| --- | --- | --- |
| Campaign criteria and results | Typed criteria, free-text context, literal judgments, human-only saved selections over a chosen frozen dataset | Natural-language interpretation, current-KB retrieval, LLM assessment/ranking and automatically saved shortlist revisions |
| Knowledge | Source identities/observations, business vocabulary, provisional span-supported caption interpretations, atomic publication, bounded literal current-KB queries and exact saved result manifests with explicit capture-age freshness | Semantic retrieval, attribute-specific freshness profiles, continuous acquisition and agentic question answering |
| Acquisition | Bounded adapters for supplied TikTok references, snapshot import, replay/resume, canonical history and durable campaign-authorized and exactly human-approved supplied-proposal synthetic offline tasks with per-task competing-worker fencing, recovery, partial outcomes and simulated waiting | Query discovery and scheduled authority, progressive acquisition and retrieval avoidance |
| Monitoring | Independent saved snapshot investigations with literal counts and source support | Recent X collection, quantitative/semantic anomaly methods, separate light evidence path and alerts |
| Permissions | Trusted local human/automation actors, purpose-aware evidence reads, exact task-specific human enrichment approval and human-only shortlist writes | Authority for automated shortlist persistence |
| Visibility | Original-source panels, saved revision history, committed publication/search details, task commit/wait progress, partial outcomes, durable local completion inbox, exact support/lineage and CLI run reports | Knowledge graph explorer and pipeline/lineage view |
| Spending | Acquisition bounds and source-free synthetic accounting with forecasts/uncertainty; no monetary admission/limiter | Actual-spend derivation, enforceable ceilings for metered costs and forecasts for the remainder |

No A/B/C flow is implemented end to end. The physical tables and current interfaces remain those documented in [architecture](architecture.md), [data model](data-model.md) and the individual module contracts.

## A — Campaign-based recommendations and shortlists

1. A marketer initiates a campaign using structured criteria with natural-language descriptions, predefined options or both. Any interpretation into executable criteria/ranking profiles is visible and versioned. Criteria distinguish requirements, preferences and unknown handling.
2. Search the current permitted KB and filter/rank candidates using deterministic rules and method-versioned LLM assessment. Results expose supporting rationale, evidence, unknowns and freshness. A rank expresses fit to the stated criteria; it does not establish sales effectiveness or verify source claims.
3. An account is eligible for ranked output when its stable platform identity and at least one supporting permitted source observation are already ingested into the KB. A complete profile, complete post history, known fee or measured audience is not a prerequisite. Missing or stale attributes remain explicit and affect the stated assessment/coverage. Unregistered URLs or handles can seed discovery but do not appear as ranked KB candidates.
4. The agent may save its ranked recommendation as a shortlist automatically. Human review, confirmation or approval is not required to persist it. Record the actual producer, method/ranking versions, ordered membership, reasons, gaps, exact brief and pinned supporting knowledge. Saving does not claim that a human reviewed the result. Optional human curation creates an attributable successor; it is not a mandatory gate.
5. Assess candidate quantity, relevance and data freshness against an explicit versioned coverage profile. Insufficient coverage automatically queues bounded discovery associated with that campaign. Return the current KB-supported result, even if insufficient, with its limits; do not fill the result with un-ingested discoveries.
6. When discovery has produced usable KB updates, notify the user and offer regeneration. Only an explicit regeneration action creates and saves a successor result. Acquisition completion does not silently alter an existing recommendation or shortlist.
7. A result pins its actual input membership, assertion/support versions, ranking profile and method. Retrieving current knowledge must not rewrite old decisions or change imported evidence-set membership.

See the [campaign contract](campaigns.md) for the implemented human-only workflow and its separate future extension. [Automatic shortlist persistence](adr/0003-automatic-shortlist-persistence.md) records the accepted authority decision.

## B — Agentic knowledge assistant

1. Accept free-form natural-language questions and requests. Answer from current permitted KB knowledge with supporting references, relevant dates, uncertainty and coverage limits. Reading existing knowledge does not require enrichment approval.
2. When information is missing, stale or incomplete, propose a scoped enrichment task: refresh outdated records, fill attributes or expand around specified accounts, posts, brands or topics. Show purpose and search/subject scope before submission.
3. Every assistant-origin enrichment submission requires explicit user approval bound to that proposal and workspace/actor. Approved tasks may go beyond the registered scheduled keywords. A materially broader task needs a corresponding approval; model-generated text is not approval.
4. Submit approved work asynchronously through the normal ingestion pipeline. Newly fetched results must be persisted, normalized and published as usable KB knowledge before supporting answers. Do not return raw fetch results as the answer or use them before ingestion/publication.
5. Return the approved task's acknowledgment/status and later a completion notification. Updated knowledge is available to subsequent queries. A successful fetch followed by failed ingestion/publication is not a successful KB update.
6. Server-side task authorization distinguishes assistant approval from automatic campaign/scheduled acquisition. An agent cannot bypass approval by claiming another task origin.

## C — Lightweight X monitoring and anomaly detection

1. Periodically fetch recent X posts for configured monitoring topics. Keep monitoring-topic configuration distinct from scheduled KB-discovery keywords; the two may overlap intentionally.
2. Detect quantitative anomalies such as post-volume or engagement spikes and semantic anomalies such as sentiment shifts or emerging controversies. Use explicit comparison windows/baselines, versioned methods and coverage limits; no comparable baseline means no unsupported quantitative change claim.
3. Investigate significant anomalies using existing KB context only. This investigation may not trigger additional external searches, automatically create campaigns or silently expand the configured monitoring scope.
4. Use a separate bounded collection of recent monitoring observations. Full ontology/entity/relationship ingestion of every fetched post is not a prerequisite for timely detection. Retain necessary source evidence and detection context for alerts; selectively promote useful material into the full KB through the normal ingestion/publication pipeline.
5. Notify users with a concise explanation and supporting evidence; retain relevant alert history with its source support, windows, baseline/method versions and uncertainty. Alert evidence remains subject to source retention/display policy, expiry and withdrawal. Saved alerts must indicate when support becomes unavailable.
6. The light path remains bounded by acquisition settings, source constraints and applicable spending controls. “Lightweight” does not remove provenance or permit untraceable alert claims. Exact collection cadence, evidence retention windows and significance parameters are explicit operating configuration, not guarantees inferred from the current snapshot fixture.

See [monitoring](monitoring.md) and the [light-path ADR](adr/0004-lightweight-monitoring-evidence.md). Current snapshot investigations remain independently useful and are not presented as continuous X monitoring.

## Shared acquisition and worker pipeline

- **Scheduled discovery:** register at most ten keywords per workspace. The initial configurable default is **N = 50 unique eligible new posts per day total across the scheduled keywords**, not per keyword. Prioritize recency, engagement and trend evidence. This is an admission allowance, not a provider request count, a target that must be filled or a verified cost/throughput estimate. Source and operational limits can yield fewer records.
- **Progressive acquisition:** start with a configured broad discovery route and selectively use supplementary APIs, oEmbed or permitted web collection for valuable records/missing fields. Choose routes using coverage, source capability, freshness, cost and expected information value. Stop when allowed scope/limits are exhausted or further retrieval is not worthwhile. Bright Data is an example route, not a claim that its current supplied-profile adapter performs query discovery or has validated access.
- **Incremental updates:** track native identities, prior queries/retrievals, capture times, freshness, failed attempts and processing/method versions. Avoid redundant searches and unnecessary unchanged processing, while preserving legitimate new observations and separate source metric semantics. Reconcile KB updates with their supporting observations.
- **Task origins:** scheduled work uses its configured authorization; Feature A may automatically submit campaign coverage discovery; Feature B requires its approved proposal. The ten-keyword scheduled limit does not prohibit explicitly scoped on-demand enrichment.
- **Structured operations:** expose search, task submission and task status through internal endpoints or MCP-compatible tools over the same domain contracts. Authorization/approval and spending checks live server-side, independent of the caller's prompts. A second protocol must not create a bypass.
- **Durability and completion:** persist task identity, scope, origin/approval, attempts, status, partial failures, actual coverage and resulting KB publication. Retries/resumption must not duplicate effects. Completion notifications distinguish usable updates, partial results and failure; queue acceptance is not acquisition completion.
- **Separate X path:** recent-X polling and detection use the light monitoring evidence owner. Full KB enrichment must not become a prerequisite for every detection window.

## Hybrid spending control

Costs whose actual spend can be derived receive configured ceilings. Costs that cannot be derived reliably remain forecast-only. The original approximate all-in operating target remains a planning target; this contract does not invent provider prices, currencies, numerical ceilings or billing periods.

For metered cost scopes:

- Record attributable usage or charges with units, versioned rates where applicable, currency, accounting period, provider/service, task/attempt and measurement source/time. Separate actual derived spend, outstanding commitments and estimates; unknown cost is not zero.
- Apply configured ceilings server-side across competing workers and tools. Before starting further chargeable work, account for actual spend and in-flight bounded commitments; pause or refuse further work when the scope's allowance is exhausted. Reconcile actual charges and retries without double-counting.
- Use known charge bounds or provider-side limits where strict pre-call enforcement is required. Delayed billing or unbounded charges cannot support a promise of zero overshoot; make the meter lag and enforcement limits visible.
- A failure of an expected meter is a visible control failure, not permission to silently switch that scope to unlimited forecast-only operation. Keep the metered/forecast classification explicit.

For unmeterable scopes, retain forecast amounts and assumptions with their incomplete coverage clearly shown. Do not claim an enforced monetary ceiling there. Per-job request/byte/record limits, source quotas, task approval and value-based stopping remain separate controls and still apply. Assistant approval does not override a spending ceiling; automatic shortlist saving does not authorize external expenditure.

The [offline accounting contract](costs.md) implements attributable synthetic unit/rate derivation, separate forecasts/declared commitments and explicit uncertainty. Commercial charge derivation, coordinated ceiling admission and commitment reconciliation remain future capabilities; the application makes no enforced monetary ceiling claim.

## Graph explorer and pipeline lineage

The **knowledge graph explorer** supports searching, filtering and traversing permitted KB entities/relationships and inspecting entity details and source evidence. It distinguishes observed, derived and human associations. Obsidian/Neo4j-inspired interaction does not mandate a graph database: the graph is a governed read model/projection of shared knowledge.

The **pipeline and data-lineage view** exposes acquisition tasks/jobs, status/failures, source provenance, transformations and KB update history. It connects tasks to runs, observations, derivations and publications. Source restrictions apply to displayed payloads/excerpts; secrets and unrestricted provider responses are not UI content.

Both interfaces are target behavior. Current evidence panels and run reports are supporting foundations, not implementations of these explorers.

## Evaluation and delivery boundaries

Validate ranking relevance, language interpretation and monitoring methods against attributable reviewed examples, while testing approval, budget, versioning, policy and publication boundaries independently. Human evaluation of product quality remains necessary evidence of usefulness; it is not mandatory review before each runtime shortlist save.

Model/provider choice, coverage/freshness thresholds, anomaly parameters, ceiling amounts/periods and retention settings need explicit configuration and validation during implementation. Their precise values are not fixed by these requirements. No creator contact, publishing, media buying, external campaign activation or claim of measured sales lift is introduced. Existing measurement plans/notes remain supported; actual outcomes, attribution and causal estimation remain longer-term work.
