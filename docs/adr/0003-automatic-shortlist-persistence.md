# Allow automated shortlist persistence without human review

Status: accepted; implementation pending

An agent's ranked recommendation may be saved as a campaign shortlist without human review, confirmation or approval. Requiring a human click merely to preserve an internal recommendation would obstruct the requested workflow; persistence does not execute a campaign or assert that a person endorsed the result.

Record automated or human authorship, ranking/method versions, ordered account membership, rationale, gaps and pinned support. Optional human curation/review is distinct from saving and must not be fabricated by an automation actor. Discovery completion offers regeneration rather than replacing saved results. Assistant-origin external enrichment still requires its own approval, and chargeable work remains subject to spending controls.

The current local store permits only human shortlist saves and confirmations. It remains documented as implemented behavior until a future persistence interface supports the [target requirements](../functional-requirements.md); this ADR does not claim that existing actor checks have changed.
