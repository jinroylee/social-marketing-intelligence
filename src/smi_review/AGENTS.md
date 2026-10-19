# Local review application

Own localhost HTTP handling, form parsing and escaped HTML evidence panels. `ReviewApp` composes public monitoring, campaign/planning, knowledge and frozen-evidence interfaces; `make_server` binds the application to loopback. Database writes and decision rules remain in their domain stores.

Construct the named human and preparation-worker actors on the server. Forms carry request IDs and expected versions; preserve submitted edits on recoverable errors, and require an explicit human confirmation. Recheck display policy through public readers when rendering. Render captions only for available/current candidate support, and keep provisional interpretations, human reasons and unknowns visibly distinct.

Allow only the server's loopback Host and same-origin writes with its CSRF token. Escape all data; source URLs are validated external links, never fetched or embedded. Serve only fixed bundled assets. Keep browser state out of durable decisions: PostgreSQL revisions own save/reopen behavior.

Keep investigations, knowledge search and publication list/detail pages independently reachable from campaigns. Search forms use `KnowledgeQueries` to preserve actual result membership; result pages reopen current display policy and show explicit scan/result limits and freshness. Publication pages read committed membership through `KnowledgePublications`, showing denied/superseded support metadata without source text. Proposed measurement and human feedback stay distinct from observed outcomes. Feedback error pages withhold submitted source-dependent text when support is unavailable.

Submit configured offline campaign tasks through `AcquisitionTasks` and render source-free task/run/publication lineage independently through task list/detail routes. The server chooses the synthetic fixture route, actor and origin; form fields cannot grant origin, approval or live-collector authority. Acknowledgment does not execute the worker.

Update `docs/local-review.md` when changing routes or operator behavior. Verify server-bound actor identity, stale saves, policy withdrawal, error-state preservation and restart/reopen using isolated schemas. The application does not acquire live evidence, run paid models or translate captions.
