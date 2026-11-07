# S12. Complete brief to saved recommendation and explicit regeneration

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. L-sized headline journey spanning about nine owner operations and many UI states. Decisions to chart before implementation: read models for brief/shortlist version history and comparison; conflict and interrupted-admission recovery UX; presentation of unknowns, coverage and method; regeneration successor flow.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_campaigns owns briefs, criteria, comparisons and shortlists; smi_tasks.campaigns owns discovery composition
Direct spec blockers: [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (C1 renders evidence through the shared inspector and campaign index.), [Select question-, brief- and graph-scoped governed support at pilot scale](07-pilot-scale-retrieval.md) (The candidate pool must reach eligible creators beyond the newest 100 members.), [Publish catalog-scoped caption interpretations from automated tasks](06-automated-interpretation.md) (Brand/product criteria need published interpretations on discovered support.), [Compose the local pilot from one validated configuration](02-pilot-configuration.md) (Model ranking and criteria interpretation must be operable from the shipped server.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer creates a campaign, receives an automatically saved supported shortlist, optionally curates it and deliberately regenerates after new knowledge.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_campaigns/store.py](../../src/smi_campaigns/store.py)
- [src/smi_tasks/campaigns/](../../src/smi_tasks/campaigns/)
- [tests/test_ranked_recommendations.py](../../tests/test_ranked_recommendations.py)
- [tests/test_recommendations.py](../../tests/test_recommendations.py)

## Scope and non-goals

Implement C1 forms/read models for brief versions, visible additive interpretation selection, deterministic comparison, constrained model ranking, coverage disposition, curation and history. Rich audience, fee and sales-effectiveness factors remain unknown until later evidence contracts.

## Owners, interfaces and data shapes

Compose CampaignStore.start/revise_brief/interpret_criteria/prepare_current_comparison/recommend/recommend_ranked/save_shortlist and CampaignRecommendations.regenerate. Commands carry request_id, exact brief/profile IDs and expected brief/shortlist heads. Return saved shortlist before task-owned discovery disposition, preserving an interrupted admission link.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Reuse campaign schemas and request claims. Add indexes or public paginated history only where needed. Do not replace immutable revisions. Update docs/campaigns.md, docs/local-review.md and data-model.md for any actual schema change.

## UI reads, commands and agent integration

C1 shows original human constraints, automated method/order, support and gaps, quantity/relevance/freshness, queued or refused discovery, and explicit successor selection. Tools may request a recommendation under configured automation authority; they cannot confirm human review. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Stable platform identity plus one permitted ingested observation admits an incomplete account. Save empty outcomes. Human curation is separately attributed, including an empty selection. Neither completion nor new publication mutates history.

## Failure and recovery

Version conflicts preserve edits and exact retry IDs. Model/configuration/usage failure is visible without a successful deterministic fallback. Approval is unnecessary for shortlist persistence and cannot bypass discovery source or cost gates.

## Acceptance

### S12-A01

Through public HTTP, create, revise, interpret, explicitly select and recommend; reopen the exact saved inputs and order after restart.

### S12-A02

Observe an incomplete eligible account and explicit unknown fee/audience fields. Empty selection saves an empty automated or human revision with correct authorship.

### S12-A03

Fail discovery admission after the shortlist commit, retry and observe one disposition and at most one task.

### S12-A04

Publish new evidence, observe unchanged historical shortlist, then regenerate explicitly and observe one successor. Test stale heads and withdrawal of an unselected model input.

### S12-A05

A shortlist over task-discovered support shows real supported or unknown brand/product judgments from published interpretations.

### S12-A06

A comparison over a KB of more than 100 publications reports its scan bounds and includes an older eligible creator.

### S12-A07

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A01, FR-A02, FR-A03, FR-A04, FR-A05, FR-A06, FR-A07, FR-P07, OFR-A01, OFR-A02, PROP-04, PROP-06, PROP-07, PROP-11, PROP-17, PROP-35, UD-01, UD-08. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
