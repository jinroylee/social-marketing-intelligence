# Current knowledge queries

Own bounded literal knowledge retrieval and immutable actual-support result manifests through `KnowledgeQueries` and `QueryScope`. Read committed publications through `KnowledgePublications`; source observations and interpretation values stay with their existing owners. Store exact observation/derivation/assertion/metric/interpretation IDs and transformation/publication versions, never a second source-value cache.

New search computation requires current process permission plus the requested output-purpose permission. Hold the publication readers' source/derivation locks through result commit. Reopening uses the saved membership with its requested current read permission; it does not rerun filters, require a fresh enrichment approval or substitute later support. Preserve original coverage, order, method and actual producer while reporting current unavailable/superseded support separately.

Keep capture-age freshness independent of policy and derivation health. An omitted threshold means not assessed; ingestion and publication times do not refresh a capture. Report publication-scan and result bounds explicitly, including incomplete-market coverage. Unknown profile attributes and absent interpretations remain unknown.

Workspace/request identity pins the query, purpose, synthetic mode, method and producer. Changed retries conflict; identical retries reopen the original result. Synthetic inputs require explicit development visibility on search and reopen. Semantic/vector retrieval, ranking, acquisition authority and graph traversal belong to later workflows.

When changing query filters, persistence, policy or bounds, update the [knowledge contract](../../../docs/knowledge.md), architecture, physical ERD and local search surface together. Verify behavior through public operations and HTTP with real PostgreSQL and simulated source inputs.

Search/read accept caller transactions so dependent comparison writes retain source and publication-frontier locks through commit. `account_support` projects stable account subjects and observed author identities from an exact permitted result, including missing-state profile assertions and metric-only support; handles/URLs confer no identity. `statuses` exposes content-free pinned source-policy/derivation health without locking interpretation copies, preventing nested dependent reads from blocking on their own interpretation locks. Keep account selection decisions with campaigns.
