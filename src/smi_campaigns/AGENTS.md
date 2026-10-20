# Campaign decisions

Own campaign briefs, comparison drafts and human shortlist revisions. Public entry points are `CampaignStore`, `Brief`, `Criterion` and `Selection`. Knowledge and ingestion keep their existing ownership; use their public readers for validation and evidence access.

`require_current_brief` validates and share-locks an exact current workspace brief in the caller transaction; dependent admission joins that transaction. Human actions start/revise campaigns and save selections. Automation may prepare comparisons only for an existing human-initiated campaign. Actor context is trusted local application context, not client authentication. Confirmation requires supported relevance, acknowledged unknowns and current brief/selection versions.

Keep historical membership, actors and revision IDs immutable. Request IDs identify retries; changed request bodies conflict. A new request makes a successor revision. Rule-based comparisons retain exact observation/assertion/interpretation dependencies and explicit coverage rather than global creator scores.

Save original human prose and the executable structured-profile snapshot atomically with each new brief. Preserve criterion IDs for unchanged needs; pin profile identity to its exact brief/version. Profile versions describe installed behavior: current ordering is unranked and coverage descriptive. Legacy null profiles stay unrecorded; readers must not synthesize historical versions. Prose and structured needs are human input, never source facts. Keep the profile's criteria consistent with the exact persisted brief; current comparisons reopen that pinned profile.

Source-dependent comparison bodies and human reasons inherit all cited support's policy. Denied or superseded support is withheld; retention withdrawal purges copied bodies/reasons. Permitted account references and decision metadata remain. Do not rebuild a purged explanation from other stores.

Core criteria and identities remain category/market independent. Product/language semantics must match the knowledge method actually used; literal script evidence cannot become audience or sales evidence. Update `docs/campaigns.md`, architecture and the physical ERD with behavior/schema changes.
