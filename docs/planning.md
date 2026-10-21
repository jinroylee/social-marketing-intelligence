# Campaign measurement and decision feedback

[`smi_campaigns.planning`](../src/smi_campaigns/planning/__init__.py) owns `CampaignPlanning`, `MeasurementPlan` and `DecisionNote`. It extends internal decisions without activating campaigns, acquiring commerce data or computing outcomes.

Plan/note writes below are the implemented human-only interfaces. The [automatic-shortlist operation](campaigns.md#automatic-deterministic-shortlist-persistence) allows generated saved recommendations to be referenced without requiring human review first. Its automation authority does not turn proposed plans or human notes into observed results, or change the current plan/note write permissions.

## Proposed plans

`save_plan(campaign_id, brief_id, shortlist_id, plan, human_actor, expected_version=..., request_id=...)` appends a plan for the exact current brief and a relevant saved shortlist. A draft or empty/deferred shortlist is valid. Unrelated references fail, and products must fit the brief's brand/product scope.

A plan requires an objective, proposed outcome definition and known gaps. Optional fields record product/listing/currency, intended source/owner, period/baseline, account-to-campaign/order matching and attribution assumptions/window. Missing prerequisites remain unknown. See the [example plan](../examples/campaigns/sales-measurement-plan.json).

Plans remain `proposed`, with outcome access `not_verified` and `outcomes=null`. Input cannot add revenue, conversion or lift results. Source/owner text is human intent rather than verified access. No default attribution window is adopted, and engagement counts do not become sales. Future attributed outcomes still would not establish causal lift.

## Human notes

`add_note(campaign_id, shortlist_id, note, human_actor, expected_version=..., request_id=...)` appends feedback or learning for a historical shortlist. Notes are `human_supplied` with original actor/time. Optional interpretation citations must belong to the selected set's available cited evidence; they do not independently verify the prose.

All selected candidate dependencies govern copied note text even without an explicit note citation. Saving requires permitted/current support and a readable shortlist. A note on an empty selection has no source dependencies and remains purely human input.

Current reads hide text under display denial or stale support. Retention withdrawal, expiry or revocation purges text while preserving revision, shortlist link, reviewer/time and permitted support IDs. Permission recovery or retries cannot reconstruct a purged note. Measurement-plan intent has no copied source excerpts and is not represented as a source observation.

## Versioned actions

Plan and note heads are separate per-campaign sequences. Saves lock the campaign, check expected versions and commit atomically. Identical requests return original IDs; changed retries/stale saves fail. Successors preserve history.

`CampaignPlanning.read(campaign_id, actor)` returns both histories and version heads with note cleanup. Public `CampaignStore.shortlist_support(..., connection=...)` supplies content-free pinned dependencies and current source-policy/derivation statuses for either frozen or current-KB comparisons, holding source locks through note commits; metric-only support needs no field assertion; callers do not query ingestion tables. Writes are human-only and reads are workspace-scoped.

The [browser application](local-review.md) links measurement/notes from the campaign page, showing proposals/unknowns, human feedback and revision history separately. Recoverable errors preserve edits/version intent; note text is withheld under unavailable support. The HTTP boundary supplies the named human actor.
