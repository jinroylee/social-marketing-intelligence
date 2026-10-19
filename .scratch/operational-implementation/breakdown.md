# Proposed operational implementation tickets

Status: draft for breakdown review. None of these tickets has been published or marked ready-for-agent.

Source: [Operational implementation specification](../../docs/implementation-spec.md). Read the accepted requirements and ADRs referenced there when implementing a slice. This breakdown covers the whole spec; it is not permission to implement it during ticket generation.

## Sizing and sequence

There are 39 proposed tickets. Each feature ticket completes one narrow user-visible journey or extension through its owning persistence, public operations, local surface, and meaningful integration checks. No ticket is a standalone schema, endpoint, UI, generic framework, or test-only work package.

- **S** means a bounded repair or extension of an established journey. **M** means one new bounded journey or one material operational invariant. These are relative scope labels, not time estimates. Both must fit a fresh agent context with the source contract and direct blockers.
- The largest slices are publication (02), the first offline task (04), recovery (06), the first metered model journey (13), query discovery (18), and recent-X evidence (29). Their scope guards exclude broad search, concurrency, new providers, or adjacent features until the corresponding later ticket.
- Repair the existing ingestion completion contract first (01). No broad prefactor is justified by the current code: reuse collectors/mappers, checkpoints, public stores, actor context, form protections, and the isolated-schema test setup.
- A feature changes only the layers needed for its behavior. Baseline repair (01) and genuine human validation (39) are bounded nonfeature activities, not artificial database/API/UI construction.
- Store/runtime concurrency (07), cost admission (10), and uncertain-charge handling (11) have separate tickets because each has a different externally visible failure mode and must be reviewable independently.
- Each numbered blocker below is a **direct hard dependency**. The ordering is topological, not a requirement to execute unrelated tickets serially. Work any ticket whose own blockers are complete.

## Proposed breakdown

1. **[Restore ingestion completion and safe resume](drafts/01-restore-ingestion-completion-and-safe-resume.md)** (S). **Blocked by:** None. **Delivers:** An operator can ingest bounded input and resume a completed capture without another collector call or losing prior run history.

2. **[Publish and inspect permitted ingested support](drafts/02-publish-and-inspect-permitted-ingested-support.md)** (M). **Blocked by:** 01. **Delivers:** An operator can publish a bounded selection of already-ingested evidence and reopen a knowledge-publication detail page with exact usable support.

3. **[Search current knowledge and pin result support](drafts/03-search-current-knowledge-and-pin-result-support.md)** (M). **Blocked by:** 02. **Delivers:** A marketer can search published knowledge, inspect coverage and freshness, and reopen the exact support selection behind a result.

4. **[Run one authorized offline acquisition task](drafts/04-run-one-authorized-offline-acquisition-task.md)** (M). **Blocked by:** 02. **Delivers:** A marketer can submit one bounded offline acquisition for an existing campaign, receive a task identity immediately, and inspect its ingestion and publication outcome.

5. **[Approve an exact assistant enrichment proposal](drafts/05-approve-an-exact-assistant-enrichment-proposal.md)** (M). **Blocked by:** 04. **Delivers:** A marketer can review a saved enrichment proposal, explicitly approve that exact scope, and submit an attributable offline task.

6. **[Recover interrupted tasks and expose partial outcomes](drafts/06-recover-interrupted-tasks-and-expose-partial-outcomes.md)** (M). **Blocked by:** 04. **Delivers:** An operator can resume an interrupted task and see which knowledge became usable, which phase failed, and what remains incomplete.

7. **[Coordinate competing workers without duplicate effects](drafts/07-coordinate-competing-workers-without-duplicate-effects.md)** (M). **Blocked by:** 06. **Delivers:** Multiple workers can process the durable task frontier while an interrupted or stale worker cannot duplicate or overwrite completed work.

8. **[Deliver durable task completion notifications](drafts/08-deliver-durable-task-completion-notifications.md)** (S). **Blocked by:** 06. **Delivers:** A marketer can reopen an in-application inbox and follow task completion messages to the actual usable update, partial result, or failure.

9. **[Show attributable actual costs and forecasts](drafts/09-show-attributable-actual-costs-and-forecasts.md)** (M). **Blocked by:** 04. **Delivers:** An operator can inspect a task's measured usage and derived charges separately from forecasts and outstanding commitments.

10. **[Enforce shared monetary admission before work](drafts/10-enforce-shared-monetary-admission-before-work.md)** (M). **Blocked by:** 09. **Delivers:** An operator can configure a metered ceiling and see competing chargeable operations admitted or refused before their simulated external calls.

11. **[Reconcile delayed charges and failed meters](drafts/11-reconcile-delayed-charges-and-failed-meters.md)** (M). **Blocked by:** 10. **Delivers:** An operator can reconcile delayed or uncertain charges after retries and restarts without double-counting or accidentally reopening an exhausted allowance.

12. **[Save visible executable campaign criteria](drafts/12-save-visible-executable-campaign-criteria.md)** (S). **Blocked by:** 01. **Delivers:** A marketer can save and inspect a versioned executable criteria/ranking profile for a campaign using structured inputs.

13. **[Interpret natural-language criteria with one metered model](drafts/13-interpret-natural-language-criteria-with-one-metered-model.md)** (M). **Blocked by:** 11, 12. **Delivers:** A marketer can turn natural-language campaign criteria into a visible, versioned executable interpretation using one explicitly configured model route.

14. **[Compare eligible accounts from current knowledge](drafts/14-compare-eligible-accounts-from-current-knowledge.md)** (M). **Blocked by:** 03, 12. **Delivers:** A marketer can compare current-KB accounts against a campaign's recorded criteria with exact supporting evidence and explicit unknowns.

15. **[Automatically save an attributed ordered shortlist](drafts/15-automatically-save-an-attributed-ordered-shortlist.md)** (M). **Blocked by:** 14. **Delivers:** A campaign's supported deterministic recommendation is saved automatically as an ordered shortlist revision that can be reopened without a human-review step.

16. **[Rank campaign candidates with supported LLM assessment](drafts/16-rank-campaign-candidates-with-supported-llm-assessment.md)** (M). **Blocked by:** 13, 15. **Delivers:** A marketer receives an automatically saved campaign shortlist ordered by validated LLM assessment of a bounded current-KB candidate set.

17. **[Curate generated shortlists without rewriting history](drafts/17-curate-generated-shortlists-without-rewriting-history.md)** (S). **Blocked by:** 15. **Delivers:** A marketer can optionally curate a generated shortlist and save an attributable successor while preserving the original automated recommendation.

18. **[Execute bounded offline keyword discovery](drafts/18-execute-bounded-offline-keyword-discovery.md)** (M). **Blocked by:** 03, 06. **Delivers:** An authorized task can search a scoped offline discovery route, ingest newly found records, and expose the resulting published KB updates.

19. **[Queue discovery when campaign coverage is insufficient](drafts/19-queue-discovery-when-campaign-coverage-is-insufficient.md)** (M). **Blocked by:** 15, 18. **Delivers:** A marketer receives the current supported shortlist immediately while inadequate quantity, relevance, or freshness automatically queues bounded campaign discovery.

20. **[Offer explicit regeneration after campaign updates](drafts/20-offer-explicit-regeneration-after-campaign-updates.md)** (S). **Blocked by:** 08, 19. **Delivers:** A campaign discovery completion notification offers regeneration, and only a marketer's explicit action creates a newly assessed saved shortlist revision.

21. **[Schedule offline discovery for registered keywords](drafts/21-schedule-offline-discovery-for-registered-keywords.md)** (M). **Blocked by:** 18. **Delivers:** An operator can register scheduled keywords and inspect due offline discovery tasks created under the schedule's recorded authority.

22. **[Enforce the shared daily unique-post allowance](drafts/22-enforce-the-shared-daily-unique-post-allowance.md)** (M). **Blocked by:** 21. **Delivers:** Scheduled discovery admits at most the configured daily total of unique eligible new posts across all keywords and competing workers.

23. **[Avoid redundant discovery while preserving refresh history](drafts/23-avoid-redundant-discovery-while-preserving-refresh-history.md)** (M). **Blocked by:** 18. **Delivers:** An operator can see unnecessary repeated retrieval skipped while legitimate stale-record refreshes and new observations retain their provenance.

24. **[Enable one verified live on-demand discovery route](drafts/24-enable-one-verified-live-on-demand-discovery-route.md)** (M). **Blocked by:** 07, 11, 23. **Delivers:** An authorized on-demand task can use one explicitly configured live TikTok query-discovery route and report the actual usable KB update and attributable cost.

25. **[Activate live scheduled discovery within daily bounds](drafts/25-activate-live-scheduled-discovery-within-daily-bounds.md)** (S). **Blocked by:** 22, 24. **Delivers:** An operator can enable a verified live route for scheduled keyword discovery while the shared daily new-post allowance and spending controls remain enforced.

26. **[Supplement one valuable missing field and stop by value](drafts/26-supplement-one-valuable-missing-field-and-stop-by-value.md)** (M). **Blocked by:** 24. **Delivers:** A discovery task can selectively retrieve one configured missing field from an existing supplementary route and explain why it continued or stopped.

27. **[Answer free-form questions from permitted knowledge](drafts/27-answer-free-form-questions-from-permitted-knowledge.md)** (M). **Blocked by:** 03, 13. **Delivers:** A marketer can ask a free-form KB question and receive an answer with inspectable support, dates, uncertainty, and explicit missing information.

28. **[Turn assistant knowledge gaps into approved enrichment](drafts/28-turn-assistant-knowledge-gaps-into-approved-enrichment.md)** (M). **Blocked by:** 05, 08, 27. **Delivers:** A marketer can turn an unanswered or stale assistant question into a scoped proposal, approve it, follow the task, and use published updates in a later query.

29. **[Collect bounded recent X evidence offline](drafts/29-collect-bounded-recent-x-evidence-offline.md)** (M). **Blocked by:** 01. **Delivers:** An operator can configure an X monitoring topic, run a bounded offline collection window, and inspect retained recent observations independently of the full KB.

30. **[Detect quantitative X anomalies with retained alerts](drafts/30-detect-quantitative-x-anomalies-with-retained-alerts.md)** (M). **Blocked by:** 08, 29. **Delivers:** A marketer receives an inspectable alert when a configured quantitative method finds a justified X volume or engagement anomaly.

31. **[Detect supported semantic X anomalies](drafts/31-detect-supported-semantic-x-anomalies.md)** (M). **Blocked by:** 13, 30. **Delivers:** A marketer can inspect semantic-shift or controversy alerts supported by retained recent X evidence and a versioned assessment method.

32. **[Explain X alerts using existing KB context only](drafts/32-explain-x-alerts-using-existing-kb-context-only.md)** (S). **Blocked by:** 03, 30. **Delivers:** A marketer can open an X alert and see relevant existing KB context separately from the recent evidence that triggered detection.

33. **[Promote selected monitoring evidence into knowledge](drafts/33-promote-selected-monitoring-evidence-into-knowledge.md)** (M). **Blocked by:** 02, 29. **Delivers:** An operator can deliberately promote selected permitted recent X observations through normal ingestion and publication, with traceable origins.

34. **[Enable one verified live recent-X route](drafts/34-enable-one-verified-live-recent-x-route.md)** (M). **Blocked by:** 07, 11, 29. **Delivers:** An operator can enable one configured live recent-X collection route for monitoring topics and inspect bounded recent windows without full KB ingestion.

35. **[Search graph entities and inspect supported neighbors](drafts/35-search-graph-entities-and-inspect-supported-neighbors.md)** (M). **Blocked by:** 03. **Delivers:** A marketer can search permitted KB entities and inspect their immediate relationships and source evidence in a graph-oriented view.

36. **[Traverse and filter governed graph relationships](drafts/36-traverse-and-filter-governed-graph-relationships.md)** (S). **Blocked by:** 35. **Delivers:** A marketer can traverse multiple permitted graph relationships and narrow the view without losing relationship basis or evidence.

37. **[Trace tasks through publications and attributable costs](drafts/37-trace-tasks-through-publications-and-attributable-costs.md)** (M). **Blocked by:** 06, 09. **Delivers:** An operator can trace an acquisition task through attempts, runs, observations, transformations, publications, failures, and attributable usage in one lineage view.

38. **[Prepare and validate operational quality-review packets](drafts/38-prepare-and-validate-operational-quality-review-packets.md)** (M). **Blocked by:** 16, 27, 31. **Delivers:** A reviewer can obtain and record attributable language/relevance review packets for a saved recommendation, a KB answer, and an X semantic alert.

39. **[Conduct one attributable operational marketer review](drafts/39-conduct-one-attributable-operational-marketer-review.md)** (S). **Blocked by:** 20, 28, 32, 38. **Delivers:** A named human reviewer completes one bounded evaluation of the operational campaign, assistant-enrichment, and X-alert journeys with recorded evidence and limitations.

## Why these blocking edges

- After 01, publication (02), structured campaign criteria (12), and recent-X collection (29) can proceed independently.
- KB comparisons (14) require query support (03) and executable criteria (12), but do not wait for live discovery, assistant enrichment, X alerts, or graph UI.
- Automated shortlist persistence (15) is established using the existing deterministic method before LLM assessment (16). Intermediate results remain honestly labeled.
- One metered model transport is introduced through the natural-language criteria journey (13), then reused by ranking (16), KB questions (27), and semantic alerts (31). There is no horizontal generic-model-framework ticket.
- Campaign coverage (19) and schedules (21) can run against offline query discovery (18). Their business behavior does not wait for paid-source access.
- Live on-demand discovery (24) requires worker coordination, reconciled spending control, and retrieval avoidance. It does not wait for keyword schedules. Live scheduled activation (25) additionally requires the daily unique-post allowance (22).
- Optional human curation (17) does not block recommendation generation, coverage discovery, or regeneration.
- Assistant proposal approval (05) can be delivered without the conversational assistant. The final assistant enrichment journey (28) composes approved tasks, KB answers, and the completion inbox.
- Recent-X evidence (29) does not depend on KB publication or campaign features. Quantitative alerting (30) uses the shared local inbox, while each monitoring observation remains independent of full KB ingestion. Existing-KB investigation (32) and selected promotion (33) are separate optional paths.
- Graph work (35–36) cannot block core tasks, recommendations, answers, or alerts. Lineage (37) extends established task/status/cost data without requiring graph implementation.
- The human quality review (39) waits for the actual campaign-regeneration, approved-assistant-enrichment, and contextual-alert journeys and review packets. It does not wait for every provider, graph view, or operating-scale claim.

## Shared implementation rules

Every implementation ticket follows the source spec and repository instructions: use cohesive public owners, real PostgreSQL for behavior/atomicity tests, deterministic external transports by default, exact support manifests, current source permissions, immutable historical membership, actual producer attribution, visible unknowns, safe request retries, and appropriate conflict handling. Update durable interface/architecture/schema documentation with the implemented changes and run the shared locked checks. Do not broaden a task into an unspecified platform redesign.

For new substantial owners/submodules, add responsibility/interface/invariant guidance with the required relative instruction symlink. Existing human actions and form/Origin/CSRF protections remain compatible as automated save authority is deliberately expanded.

## External prerequisites and publication

These are not pretend completed tickets or hidden code dependencies:

- **Tracker:** setup was not supplied and GitHub CLI is signed out. Run `/setup-matt-pocock-skills` if a real tracker is desired, and authenticate the selected tracker. Local files are a supported destination if explicitly selected during breakdown approval.
- **Live source/model tickets:** 13, 24–26, 27, 31, and 34 require applicable source/provider/model configuration, permitted use, actual cost classification and ceilings where derivable, and explicit live-operation authorization for any real validation. Reuse established provider configuration where applicable. Missing external inputs remain visible prerequisites; simulated tests never fabricate a live readiness pass.
- **Human validation:** 39 requires a named actual reviewer and permitted reviewed examples. Review packets (38) can be implemented without inventing that person's judgments. Unavailable human input leaves quality pending.
- **Prior spec review:** the source spec still marks its testing-boundary check pending. This draft preserves the proposed public-operation/real-PostgreSQL/simulated-I/O seams; this ticket breakdown does not manufacture a response to the earlier check.

The [to-tickets skill](/Users/makinarocks/.agents/skills/to-tickets/SKILL.md) requires: “Iterate until the user approves the breakdown.” Before publication, review whether the granularity is too coarse/fine, whether these blockers are genuine gates, and whether any tickets should be merged or split.

On approval, publish one ticket per file under the local issues directory or one real tracker issue per ticket, in dependency order, with `ready-for-agent`. Keep direct blocking numbers/titles locally or native blocking links where supported. The source is a local spec, so there is no parent tracker issue to modify or close.

## Story traceability

The per-ticket coverage below identifies the behavior delivered or extended by each slice; a shared invariant is intentionally exercised by more than one ticket.

| User story | Ticket(s) |
| --- | --- |
| 1 | 12 |
| 2 | 12, 13 |
| 3 | 12, 13 |
| 4 | 12, 13 |
| 5 | 02, 03, 14 |
| 6 | 02, 14, 16 |
| 7 | 14 |
| 8 | 15, 16 |
| 9 | 02, 03, 14, 16, 38 |
| 10 | 02, 03, 14, 16 |
| 11 | 15, 16 |
| 12 | 15, 17 |
| 13 | 17 |
| 14 | 02, 03, 14, 15, 16, 17 |
| 15 | 19 |
| 16 | 04, 18, 19 |
| 17 | 14, 19 |
| 18 | 08, 20 |
| 19 | 17, 20 |
| 20 | 06, 07, 12, 15, 17, 20 |
| 21 | 27 |
| 22 | 03, 27, 32, 38 |
| 23 | 27 |
| 24 | 03, 27 |
| 25 | 05, 28 |
| 26 | 05, 28 |
| 27 | 05, 28 |
| 28 | 05, 28 |
| 29 | 05, 28 |
| 30 | 04, 05, 08, 28 |
| 31 | 06, 08, 28 |
| 32 | 02, 03, 28 |
| 33 | 03, 08, 20, 27, 28 |
| 34 | 04, 05, 19, 21, 28 |
| 35 | 01, 04, 06, 07, 18, 24, 37 |
| 36 | 01, 06, 07, 08 |
| 37 | 06, 07, 11, 24 |
| 38 | 01, 02, 04, 06, 08, 18, 37 |
| 39 | 21, 25 |
| 40 | 21, 22, 25 |
| 41 | 09, 21, 22, 25 |
| 42 | 18, 24, 25, 26 |
| 43 | 10, 18, 19, 23, 24, 26 |
| 44 | 22, 23, 24, 25 |
| 45 | 23, 24, 26, 33 |
| 46 | 18, 23, 24, 25, 26 |
| 47 | 29, 34 |
| 48 | 29, 34 |
| 49 | 30 |
| 50 | 31, 38 |
| 51 | 30, 31 |
| 52 | 32 |
| 53 | 29, 33, 34 |
| 54 | 29, 30, 31, 32, 34, 38 |
| 55 | 33 |
| 56 | 29, 30, 31, 33, 34 |
| 57 | 29, 30, 31, 32 |
| 58 | 09, 11, 13, 24, 34 |
| 59 | 10, 13, 24, 34 |
| 60 | 10, 11 |
| 61 | 09, 11 |
| 62 | 09, 11 |
| 63 | 09, 10, 11, 13, 24, 34 |
| 64 | 35, 36 |
| 65 | 35, 36 |
| 66 | 37 |
| 67 | 09, 37 |
| 68 | 02, 03, 08, 14, 16, 27, 29, 31, 32, 33, 35, 36, 37, 38 |
| 69 | 01, 02, 15, 17, 29 |
| 70 | 38, 39 |

## Acceptance-scenario traceability

References mean the relevant part of a scenario is exercised in that slice; they do not claim an earlier small ticket already completes a later composed journey.

| Scenario | Ticket(s) |
| --- | --- |
| T01 | 02, 03, 04, 05, 08, 18 |
| T02 | 04, 05, 19, 21, 28 |
| T03 | 02, 04, 05, 06, 07, 08, 15, 19, 28 |
| T04 | 01, 06, 07, 08, 11, 24, 37 |
| T05 | 02, 04, 06, 08, 18, 28, 37 |
| T06 | 04, 06, 08, 18, 23 |
| T07 | 07, 10, 22, 34 |
| T08 | 02, 03, 14, 27, 29, 32, 33, 35, 36, 37, 38 |
| T09 | 02, 03, 14, 15, 17, 20, 27, 32 |
| T10 | 14, 16 |
| T11 | 12, 13, 14, 16 |
| T12 | 13, 16, 27, 28, 31 |
| T13 | 15, 16, 17 |
| T14 | 15, 19 |
| T15 | 20 |
| T16 | 03, 27 |
| T17 | 05, 28 |
| T18 | 21, 22, 25 |
| T19 | 18, 23, 24, 25, 26, 34 |
| T20 | 22, 23, 24, 25, 26, 33 |
| T21 | 09, 10, 13, 24, 25, 26, 34 |
| T22 | 09, 11, 24, 34 |
| T23 | 09, 10, 11, 13, 24, 26, 34 |
| T24 | 29, 30 |
| T25 | 31 |
| T26 | 29, 30, 31, 32, 34 |
| T27 | 33 |
| T28 | 03, 35, 36, 37 |
| T29 | 01, 02, 12, 15, 17, 29 |
| T30 | 38, 39 |
