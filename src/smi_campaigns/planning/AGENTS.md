# Campaign planning records

Own proposed measurement-plan revisions and attributable decision-note revisions. Public interfaces are `CampaignPlanning`, `MeasurementPlan` and `DecisionNote`; campaign and shortlist identity remains with `CampaignStore`.

Plans pin campaign, exact current brief and relevant shortlist. Keep proposed outcome definitions, source/owner, product/listing/currency, period/baseline, matching/attribution assumptions and gaps separate from observed results. No attributed revenue, lift or conversion is computed here.

Notes pin a historical shortlist and human actor/time. Explicit citations must belong to that selected set; all selected candidate dependencies govern the copied note conservatively, even for uncited human wording. Source withdrawal hides notes and retention withdrawal purges their text. Preserve revision/reviewer/support metadata; permission recovery cannot reconstruct purged notes.

Lock the campaign while checking expected per-record version heads and request retries. Do not call another store's private methods or weaken the human-only write boundary. Update `docs/planning.md`, architecture and ERD with changes. Verify missing outcomes, unrelated references, competing writes, history, policy cleanup and restart behavior.
