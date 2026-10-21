# Allow automated shortlist persistence without human review

Status: accepted; deterministic persistence implemented

An agent's ranked recommendation may be saved as a campaign shortlist without human review, confirmation or approval. Requiring a human click merely to preserve an internal recommendation would obstruct the requested workflow; persistence does not execute a campaign or assert that a person endorsed the result.

Record automated or human authorship, ranking/method versions, ordered account membership, rationale, gaps and pinned support. Optional human curation/review is distinct from saving and must not be fabricated by an automation actor. Discovery completion offers regeneration rather than replacing saved results. Assistant-origin external enrichment still requires its own approval, and chargeable work remains subject to spending controls.

The local store implements this authority through `CampaignStore.recommend`: a current-KB deterministic comparison and its ordered `generated` shortlist commit together with actual automation attribution and version checks. Exact retries reopen the original without reassessment. Human draft/confirmation operations retain their distinct human-only contract, and migration preserves their historical status and unrecorded ordering. LLM ranking and richer optional curation remain separate [target work](../functional-requirements.md).
