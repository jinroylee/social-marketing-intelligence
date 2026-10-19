# Functional Requirements — Core Flows & Data Pipeline

## 1. Core Flows

### User-triggered

**Feature A — Campaign-Based Influencer Shortlist**

1. **Input:** Structured campaign criteria; fields accept natural-language descriptions and/or predefined options.
2. **Process:** Search creators in the knowledge base (KB), then filter and rank using rules and LLM-based assessment.
3. **Coverage check:** Assess candidate quantity, relevance, and data freshness. If insufficient, automatically queue additional creator discovery in the background.
4. **Output:** Ranked recommendation drawn only from the current KB, with supporting rationale, saved automatically as a shortlist without human review or approval. Human curation is optional. An eligible account needs a stable platform identity and at least one permitted supporting observation ingested into the KB; full profile information is not required, and missing or stale attributes remain explicit. When discovery completes, notify the user and offer to regenerate the shortlist; do not change it automatically.

**Feature B — Agentic Knowledge Assistant**

1. **Input:** Free-form natural-language questions or requests.
2. **Process:** Query the KB to answer questions. If information is missing, stale, or incomplete, suggest an enrichment task and require user approval before submission.
    - Refresh outdated information.
    - Fill attributes marked unknown or incomplete.
    - Expand searches around specific creators, posts, brands, or topics.
    - Approved searches may go beyond registered keywords.
3. **Enrichment behavior:** Submit asynchronous requests to update the KB through the ingestion pipeline; do not directly return newly fetched results as the answer or use them before ingestion.
4. **Output:** KB-grounded answer and/or enrichment proposal; after approval, task acknowledgment/status and completion notification. Updated knowledge is available for later queries.

### Automated

**Feature C — X Monitoring & Anomaly Detection**

1. Periodically fetch recent X posts for configured monitoring topics.
2. Detect quantitative anomalies (e.g., volume or engagement spikes) and semantic anomalies (e.g., sentiment shifts or emerging controversies).
3. Investigate significant anomalies using **existing KB context**, without triggering additional external searches.
4. Notify users with a concise explanation and supporting evidence; retain relevant alert history.
5. **Data-path decision:** Use recent API/scraped data for timely detection; consult the KB selectively for context rather than requiring full ontology ingestion of every post.
6. This monitoring should be a light path with separately retained, bounded recent observations and alert evidence. Selectively promote useful material into the full KB rather than fully modeling every fetched post.

## 2. Additional Features

- **Knowledge Graph Explorer:** Interactive graph UI (Obsidian/Neo4j-inspired) to search, filter, and traverse KB entities and relationships; inspect entity details and evidence.
- **Pipeline & Data Lineage View:** Visualize ingestion jobs, status, failures, source provenance, transformations, and KB update history.

## 3. Worker Data Pipeline

- **Scheduled discovery:** Users register up to **10 keywords** (e.g., `aprilskin`, `hero cushion`, `night routine`). Each day, discover and ingest up to **N** relevant recent/trending posts, prioritizing recency, engagement, and trend signals. Initial configurable default: **N = 50 unique eligible new posts per day total across the scheduled keywords**, not per keyword; this is not a validated source-cost or throughput claim.
- **Progressive acquisition:** Start with broad discovery (e.g., Bright Data); selectively use supplementary APIs, oEmbed, or web scraping to fill missing fields or expand valuable records. Stop when further retrieval is not worth the cost.
- **Incremental updates:** Track known posts/entities, freshness, and prior retrievals to avoid duplicate searches and unnecessary reprocessing. Reconcile new observations with existing KB records.
- **On-demand enrichment:** Accept background discovery from Feature A and **user-approved** enrichment from Feature B, including searches beyond the scheduled keyword list.
- **Agent-accessible operations:** Expose structured search/enrichment task submission and status through internal endpoints or MCP-compatible tools; enforce approval requirements server-side.
- **X monitoring:** Use X APIs/scraping for recent posts; keep fast anomaly detection separate from full KB enrichment.
- **Spending:** Derive actual spend and enforce configured ceilings wherever the costs can be measured or calculated reliably. Use clearly labeled forecasts for costs that cannot be derived; do not imply those portions have enforced monetary limits. Keep spending controls distinct from task approval, per-job acquisition bounds and value-based stopping.

The [operational functional requirements](docs/functional-requirements.md) define these accepted contracts and distinguish target functionality from the implemented local pilot.
