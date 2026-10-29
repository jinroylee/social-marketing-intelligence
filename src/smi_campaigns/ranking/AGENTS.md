# Supported candidate ranking

Own the single bounded ranking schema, request mapping and independent validation. `CampaignStore.recommend_ranked` owns claim identity, comparison/input persistence, revision fencing and automatic save; shared `responses` owns transport and accounting. Read [ranked recommendation behavior](../../../docs/campaigns.md#bounded-supported-llm-ranking) before changing this flow.

Input is the exact eligible current-KB comparison batch, brief, selected criteria and fixed ranking profile. Deterministic exclusions/deferred unknowns run first. Require an exact candidate permutation and one constrained reason per criterion: positive fit cites only that candidate/criterion's satisfied support; contradicted optional preferences cite their own observed exclusion support; unknown limited evidence has no citations. Server-generated explanation templates and immutable gaps keep model judgments distinct from verified facts. Free factual prose, invented/cross-candidate citations and authority-bearing fields invalidate the assessment.

Forward the campaign-owned exact-input `dispatch_guard` through the public Responses port. The campaign owner locks/revalidates prepared inputs after cost contention through dispatch commit; external I/O follows commit. A refused guard must not dispatch or create liability.

No discovery, tool loop, new provider, model-based fact judge or deterministic success fallback belongs here. Empty batches need no dispatch. Unknown audience, fees, availability, contracts, sales and history survive ranking. Inputs and judgments inherit candidate dependencies and current policy/retention cleanup; retries reopen saved attempts without reconstituting purged data or reissuing calls.
