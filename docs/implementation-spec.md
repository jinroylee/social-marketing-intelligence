# Operational Social Marketing Intelligence — implementation specification

Status: all 39 tickets and their public-interface testing boundaries are approved; tickets 01–10 are resolved, and tickets 11–39 are published for sequential dependency-ordered continuation. Execution remains offline/local with simulated I/O; current primary-contract verification, live readiness and actual human review retain their explicit external prerequisites. The product requirements below are already accepted. New implementation choices proposed by this synthesis are identified separately; this document does not claim that the target features are implemented.

## Problem Statement

Marketers need to investigate accessible market evidence, find suitable platform accounts for campaigns, and notice significant changes without manually coordinating source collection, interpretation, spreadsheets, and historical decisions. They need to understand why a result was produced, what information is missing, how recent its support is, and whether additional research actually improved the knowledge available to them.

The current local pilot preserves source observations, supported caption interpretations, campaign decisions, snapshot investigations, proposed measurement plans, and human decision notes. It has real persistence and a browser application. A bounded current-publication query and campaign-authorized and exactly human-approved supplied-proposal synthetic offline task paths are now implemented, including bounded approved offline keyword discovery, competing-worker effect fencing, checkpoint recovery, partial outcomes and simulated waiting; see [the task contract](tasks.md) for its installed limits. Source-free synthetic usage accounting, separate forecasts/declared commitments/uncertainty, coordinated bounded synthetic monetary admission through public adapters and configured fixture workers, and explicit final synthetic reconciliation with separate failed-meter recovery are also installed; see [the accounting contract](costs.md). Its campaign analytical workflow uses frozen evidence or bounded current-KB support and deterministic rules; it now also supports operator-configured registered daily keyword authority and due offline task creation, with immutable configuration/occurrence/day context. Atomic shared scheduled new-post admission and explicit recorded activation of the verified live keyword route are installed with simulated HTTP verification and independent runtime/spending gates; see [recorded live schedules](tasks.md#recorded-live-keyword-schedule-activation). Bounded current-KB answers, exact approved gap enrichment, separate offline X collection and configured comparable-window volume and provisional quality-controversy alerts/local notifications with bounded existing-KB context investigations and explicit selected-capture promotion are installed; actual live receipts/readiness, broader autonomous research and continuous live X detection remain unimplemented. See [the quantitative monitoring contract](monitoring.md#configured-quantitative-volume-assessments).

Those gaps prevent the accepted workflows from operating end to end. A supplied-reference ingestion run is not an authorized enrichment task; a fetched response is not published knowledge; and a saved recommendation is not human approval or evidence of campaign effectiveness. The implementation must make these differences visible while reusing the existing evidence and decision foundations.

## Solution

Extend the existing application into an evidence-backed operational product with three connected workflows:

- **Campaign recommendations:** a marketer creates a campaign brief, receives a ranked recommendation from current permitted KB knowledge, and gets an automatically saved shortlist revision. Inadequate coverage queues bounded discovery. Usable updates produce a notification and an offer to regenerate; existing results remain unchanged until explicit regeneration.
- **Knowledge assistant:** a marketer asks a free-form question and receives a supported KB answer or an explanation of missing information. The assistant can propose scoped enrichment, but submission requires explicit approval for that proposal. Background work updates the KB before newly collected material can support subsequent answers.
- **Independent X monitoring:** configured topics drive bounded recent-post collection and quantitative/semantic anomaly detection. Alerts retain their evidence, comparison context, and uncertainty. Investigation uses existing KB context without initiating additional external research or campaigns.

Shared acquisition tasks, knowledge publication, source-policy enforcement, notifications, and hybrid spending control make these workflows inspectable and recoverable. A knowledge graph explorer and pipeline/lineage view expose the same governed records through public read interfaces.

The first delivery is a working offline task-to-knowledge path: authorize and submit a task, execute bounded input, ingest and publish usable support, inspect the result after restart, and receive an accurate completion record. Subsequent milestones add ranking, live discovery, the assistant, and X monitoring without replacing that contract.

Structured campaign profiles are installed: a human brief save records original prose when supplied and an immutable executable criteria snapshot with exact brief/version, stable criteria IDs, requirements/preferences/exclusions and unknown policies. Its ranking version is explicitly unranked and its coverage version descriptive; a bounded explicitly configured Responses interpretation and disabled-by-default provider HTTP adapter are also installed (verified through simulated external I/O), preserving structured human constraints with exact model/method/schema/cost provenance and explicit later selection. A bounded current-KB comparison is also installed, pinning exact retrieved support and the selected profile while retaining incomplete supported accounts and explicit reference gaps. `CampaignStore.recommend` composes this deterministic comparison with an automatically saved ordered `generated` shortlist, recording actual automation producer, rationale, gaps, exact support, explicit empty outcomes and retry/concurrency protection without human review. That operation remains deterministic and unranked. `recommend_ranked` adds one bounded validated model order after deterministic eligibility, with exact governed inputs/judgments, shared admission, truthful failures/no-call empties and no-reissue retries. Optional human select/reorder curation now extends `save_shortlist` and its successor form, preserving the exact source revision and generated history while recording separate human attribution and optional confirmation. Versioned quantity/literal-relevance/capture-freshness sufficiency and save-first automatic bounded campaign discovery are installed; source refusal and actual worker cost waiting remain visible beside the saved result. Usable/partial campaign-discovery completion now offers explicit attributed regeneration through the existing deterministic/ranked assessment; current human/profile context and protected retry/head recovery preserve both histories. Live model receipts/account readiness and human ranking usefulness remain future work. See the [implemented profile contract](campaigns.md#implemented-briefs-and-actors).

## User Stories

1. As a marketer, I want to create a campaign brief with brand/product scope, objective, target market, platforms, and selection criteria, so that recommendations answer my actual campaign question.
2. As a marketer, I want to combine predefined options and natural-language criteria, so that I can express both routine requirements and campaign-specific needs.
3. As a marketer, I want to inspect the executable interpretation of my criteria, so that I can understand what the system will assess.
4. As a marketer, I want requirements, preferences, exclusions, and unknown handling distinguished, so that an attractive preference cannot silently override a hard constraint.
5. As a marketer, I want recommendations to search current permitted KB knowledge, so that I can use the knowledge the system has actually acquired and published.
6. As a marketer, I want eligible accounts with incomplete profiles included, so that missing fees or audience details do not eliminate every potentially useful candidate.
7. As a marketer, I want un-ingested handles and URLs treated as discovery seeds, so that unverified references do not appear as supported recommendations.
8. As a marketer, I want deterministic rules and versioned LLM assessment to rank accounts against my criteria, so that I receive an explained campaign-specific ordering.
9. As a marketer, I want supporting source references, relevant dates, rationale, and explicit gaps for each account, so that I can judge the basis of its rank.
10. As a marketer, I want stale evidence distinguished from unavailable or withdrawn evidence, so that I can understand different reasons for uncertainty.
11. As a marketer, I want a ranked recommendation saved automatically as a shortlist revision, so that the result is preserved without a mandatory review step.
12. As a marketer, I want automated authorship distinguished from human review, so that saved results do not imply an endorsement I never gave.
13. As a marketer, I want to curate a saved recommendation optionally, so that my judgment can create an attributable successor without blocking automated persistence.
14. As a marketer, I want historical shortlists to retain their exact brief, order, methods, and supporting inputs, so that I can understand earlier decisions after the KB changes.
15. As a marketer, I want insufficient candidate quantity, relevance, or freshness reported explicitly, so that a thin result is not presented as comprehensive research.
16. As a marketer, I want inadequate campaign coverage to queue bounded discovery automatically, so that improving the evidence does not require manually recreating the campaign question.
17. As a marketer, I want the current supported result returned while discovery runs, so that background work does not prevent me from using existing knowledge.
18. As a marketer, I want notification when campaign discovery produces usable KB updates, so that I know when regeneration may be useful.
19. As a marketer, I want regeneration to require an explicit action and create a successor revision, so that background acquisition cannot silently change my saved shortlist.
20. As a marketer, I want retries and competing saves to preserve one consistent history, so that refreshes and stale forms cannot duplicate or overwrite results.
21. As a marketer, I want to ask free-form questions about brands, products, accounts, and topics, so that I can investigate without constructing a campaign first.
22. As a marketer, I want assistant answers to cite permitted KB support and relevant dates, so that explanations are inspectable.
23. As a marketer, I want unsupported questions to expose missing information, so that a plausible answer is not substituted for evidence.
24. As a marketer, I want to read existing KB knowledge without approving enrichment, so that ordinary investigation remains immediate.
25. As a marketer, I want enrichment proposals to state their purpose and subject/search scope, so that I can assess the work before authorizing it.
26. As a marketer, I want each assistant-origin submission bound to my explicit approval of that proposal, so that the assistant cannot submit external work on its own authority.
27. As a marketer, I want approved enrichment to refresh stale records, fill missing attributes, or expand around specified subjects, so that research can address the actual knowledge gap.
28. As a marketer, I want approved on-demand scope to extend beyond scheduled keywords, so that the background schedule does not restrict my investigation.
29. As a marketer, I want materially broader enrichment to need corresponding approval, so that approval of a narrow proposal cannot authorize unrelated research.
30. As a marketer, I want an acknowledged task identity and inspectable status after submission, so that I can follow asynchronous work.
31. As a marketer, I want a completion notification distinguishing usable updates, partial results, and failure, so that I know what became available.
32. As a marketer, I want newly fetched material to support answers only after ingestion and knowledge publication, so that a raw provider response cannot bypass evidence governance.
33. As a marketer, I want later questions to use newly published knowledge, so that approved enrichment improves subsequent investigations.
34. As an operator, I want task origin and actor authority checked server-side, so that an assistant cannot bypass approval by claiming to be a schedule or campaign.
35. As an operator, I want task scope, origin, approval, attempts, coverage, and publications persisted, so that work can be audited and resumed after interruption.
36. As an operator, I want bounded workers to resume without duplicate canonical effects, publications, or logical completion events, so that recovery is safe.
37. As an operator, I want transient retries distinguished from permanent failures and exhausted limits, so that tasks stop for understandable reasons.
38. As an operator, I want collection, ingestion, and publication progress distinguished, so that an HTTP success cannot masquerade as a usable KB update.
39. As an operator, I want to register up to ten scheduled discovery keywords per workspace, so that recurring acquisition has a defined scope.
40. As an operator, I want the initial scheduled allowance to admit at most fifty unique eligible new posts per day in total across those keywords, so that overlapping keywords and concurrent workers do not multiply the allowance.
41. As an operator, I want the scheduled allowance configurable and clearly separate from request counts and spending ceilings, so that it is not mistaken for a guaranteed throughput or cost estimate.
42. As an operator, I want progressive acquisition to start with a configured broad route and selectively supplement useful records, so that additional retrieval has an explicit purpose.
43. As an operator, I want route selection to consider capability, coverage, freshness, cost, and expected information value, so that expensive or irrelevant follow-up work can stop.
44. As an operator, I want native identities, prior queries, captures, failures, and method versions tracked, so that redundant retrieval and unchanged processing can be avoided.
45. As an operator, I want legitimate new observations retained without conflating source-specific metrics or identities, so that deduplication does not destroy history or invent equivalence.
46. As an operator, I want live discovery routes verified independently from supplied-reference collectors, so that the system does not claim capabilities its adapters lack.
47. As a marketer, I want X monitoring topics configured separately from scheduled KB keywords, so that timely monitoring has its own deliberate scope.
48. As a marketer, I want recent X observations collected periodically within configured bounds, so that monitoring can operate without my starting an investigation each time.
49. As a marketer, I want quantitative anomalies assessed against explicit comparable windows and baselines, so that ordinary sampling differences are not reported as spikes.
50. As a marketer, I want semantic shifts and emerging controversies assessed using versioned methods with supporting posts, so that alerts explain what changed and why it matters.
51. As a marketer, I want missing or inadequate baselines disclosed, so that the system does not invent quantitative change claims.
52. As a marketer, I want significant anomalies investigated with existing KB context, so that alerts can be informative without triggering unapproved scope expansion.
53. As an operator, I want X detection to use bounded recent observations without full KB modeling of every post, so that publication latency does not block detection.
54. As a marketer, I want alert history to retain evidence, method, window, baseline, coverage, and uncertainty, so that I can inspect an alert later.
55. As an operator, I want selected useful monitoring observations promoted through normal ingestion/publication, so that the KB can benefit without automatically ingesting the entire feed.
56. As a marketer, I want alerts to show when their evidence becomes unavailable, so that retained history cannot conceal withdrawn support.
57. As an operator, I want X investigation prevented from submitting external searches or automatically creating campaigns, so that monitoring remains within its accepted authority.
58. As an operator, I want actual derivable spending attributed to service, task, attempt, units, rates, currency, period, and measurement provenance, so that spending can be explained and reconciled.
59. As an operator, I want configured monetary ceilings coordinated across concurrent workers and tools, so that individually bounded tasks cannot collectively bypass a spending limit.
60. As an operator, I want outstanding commitments accounted for before chargeable work begins, so that in-flight work is included in admission decisions.
61. As an operator, I want retries and delayed billing reconciled without double-counting, so that the ledger reflects actual attributable charges.
62. As an operator, I want unmeterable cost portions shown as forecasts with assumptions, so that unknown cost is not represented as zero or as an enforced ceiling.
63. As an operator, I want meter failures and enforcement limits made visible, so that a failed control cannot silently become unlimited operation.
64. As a marketer, I want knowledge-graph search, filtering, traversal, entity details, and evidence, so that I can explore relationships without losing their source basis.
65. As a marketer, I want observed, derived, and human associations distinguished in the graph, so that visual proximity does not imply a verified relationship.
66. As an operator, I want pipeline lineage from task through attempts, runs, observations, transformations, and publications, so that I can diagnose failures and explain KB updates.
67. As an operator, I want lineage to show task status, partial failures, coverage, and attributable spending without secrets or unrestricted payloads, so that operational visibility remains safe and useful.
68. As a marketer, I want all generated explanations, graph details, and alert copies to honor current source permissions, expiry, and withdrawal, so that saved text cannot bypass its supporting evidence's policy.
69. As a marketer, I want the existing frozen-evidence, snapshot-investigation, campaign-history, measurement-plan, and decision-note workflows preserved, so that operational improvements do not erase prior work.
70. As a product evaluator, I want technical behavior, language interpretation, and marketer usefulness evaluated separately against attributable examples, so that passing automated checks does not fabricate product-quality evidence.

## Implementation Decisions

### Accepted constraints and existing foundations

- Keep the existing modular Python application and PostgreSQL foundation. This spec does not require separate deployments, a graph database, a distributed broker, or a framework migration.
- Acquisition owns source observations, canonical account/content identities, assertions, metric observations, mapping, replay, and source-policy enforcement. Shared knowledge owns business references, supported interpretations, current-KB reads, and knowledge publication. Campaigns own briefs, assessments, ranked recommendations, shortlist revisions, measurement intent, and human notes. Monitoring owns independent investigations and the separate recent-X/alert lifecycle.
- Preserve the existing collector/mapper contracts and the ingestion runner's bounded I/O, durable checkpoints, retained-payload replay, and canonical idempotency. Add task-level authorization and orchestration around those interfaces rather than treating the runner as an existing task queue.
- Keep source namespaces and native string IDs in identity contracts. Mutable handles and URLs are references, not sufficient evidence of cross-source identity. Source-specific metric definitions and time semantics remain distinct.
- Preserve frozen evidence-set membership and its exact derivation pins. Current-KB retrieval is an additional public interface; it must not append new posts to imported sets or substitute current values into historical results.
- Preserve the trusted local actor boundary. The application constructs workspace/actor authority; submitted actor kinds, task origins, or model-generated approval text are not authentication or authorization. Hosted identity infrastructure is outside this delivery.
- Follow accepted ADRs: canonical evidence has a different owner from business decisions; historical inputs stay pinned while source policy remains current; shortlist persistence may be automated without review; X detection has its own bounded recent-evidence path.

### Public operations and authorization

The following are semantic contracts, not fixed endpoint names or wire schemas. Thin local UI, internal endpoint, CLI, or MCP-compatible adapters must delegate to the same owning public operations and permission checks.

| Operation | Required context/input | Observable result and invariant |
| --- | --- | --- |
| Query current knowledge | Trusted workspace/actor, purpose, subject/search scope, relevant time/freshness constraints | Permitted knowledge with exact support references, relevant times, method/publication versions, coverage, and explicit missing states; no pending raw fetch output |
| Propose enrichment | Workspace/actor context, purpose, subject/search scope, requested refresh/expansion | Immutable identifiable proposal revision that can be reviewed; no acquisition submission |
| Approve and submit assistant enrichment | Actual human approval of an exact proposal revision/scope, workspace/actor, request identity | Durable task acknowledgment tied to that approval; changed scope, wrong workspace, or unsupported origin is rejected before work is dispatched |
| Submit configured acquisition | Server-established schedule or campaign context, bounded scope, request identity | Durable task with recorded configuration/coverage basis; an assistant cannot select this authority by changing an input field |
| Execute/resume task | Trusted worker authority and an admitted durable task | Bounded progress through existing ingestion and publication, with recoverable attempts and accurate coverage; logical effects remain retry-safe |
| Inspect task and updates | Trusted workspace/actor and task identity | Sanitized phase/outcome, attempts, failures, coverage, publication links, and attributable usage; acknowledgment is distinguishable from completion |
| Recommend and save | Exact campaign brief, executable criteria/ranking/coverage profile versions, request identity and revision concurrency context | Ordered supported KB candidates and an automatically saved attributed shortlist revision; incomplete coverage is explicit |
| Regenerate recommendation | Explicit user action and current campaign revision context | A newly assessed, automatically saved successor; discovery completion alone cannot invoke it |
| Inspect alert or graph/lineage | Trusted workspace/actor, purpose, selected records/filters | Governed views of permitted records and unavailable-support markers; no unrestricted source or secret exposure |

Submission request identities are scoped to the operation and workspace. An identical retry returns the original logical result; reuse with a materially different payload is rejected. Human-edited revision heads retain expected-version conflict behavior. Approval binds to one proposal revision and its resulting task; a retry must not turn one approval into multiple distinct tasks.

### Acquisition tasks, execution, and completion

- Persist a task's identity, workspace, initiating actor, server-established origin, immutable scope/configuration version, approval or configured authority, request identity, limits, attempts, associated runs, progress, failures, actual coverage, and publication outcomes. Link campaign tasks to their coverage assessment and scheduled tasks to their keyword configuration.
- Distinguish task progress from outcome. Progress exposes queued, executing, ingestion, publication, and waiting/blocked conditions where applicable. Outcomes distinguish usable updates, partial updates, no usable update, and failure. These are required meanings; exact status enums are a proposed implementation detail to finalize in the first milestone.
- Queue acceptance returns a task identity immediately and does not wait for provider work. Waiting for an asynchronous provider snapshot is resumable progress, not proof of ingestion or publication.
- A successful collection followed by normalization, policy validation, interpretation, or publication failure must expose the failed phase. It cannot emit a successful-KB-update outcome. Preserve successfully published subsets when a task is partial and state the remaining gaps.
- A successful search with no eligible new evidence reports no usable update with its scope and coverage; it does not establish that no relevant market activity exists. Retrieving an already-published unchanged record does not count as a newly usable KB update.
- Retry/resume reuses durable runs, observations, and prior commits where appropriate. It must not reissue paid scrape requests merely because a worker lost its response or a provider snapshot is still pending. Unknown remote-call outcomes remain explicit and require reconciliation or a bounded route-specific policy.
- Coordinate workers so two claimants cannot independently perform the same logical phase or admit the same bounded work. Recovery must preserve completed effects when interrupted after a commit and before a status acknowledgment. The exact claiming/lease implementation is proposed, not a mandate for a new queue service.
- Persist completion events with task outcomes and publication references so a crash cannot permanently hide a completed update. Delivery retries refer to the same logical event. The exact delivery mechanism is proposed; initial delivery may use a local in-application notification/status surface and does not require email, Slack, or push infrastructure.

### Knowledge publication and current-KB reads

- Introduce an explicit knowledge-publication contract that binds the usable update to exact observations, derivations, assertions/interpretations, transformation versions, relevant source times, and publication context. An ingestion run becoming complete does not publish knowledge by itself.
- Publish only valid, permitted, attributable support. Any claimed interpretation must retain its method, basis, review status, and source dependencies. Eligible source-only knowledge may retain explicit unknown interpretation fields; complete profiles and full semantic enrichment are not publication prerequisites.
- Make a committed publication and its declared usable support available consistently to current-KB reads. A reader must not see half of a declared publication or use records still being prepared. Partial task updates may consist of separately committed usable publications with explicit coverage.
- Current-KB retrieval returns a materialized support/result identity or equivalent immutable membership manifest for consequential uses. Record the actual inputs used for a recommendation or supported answer, not merely its search text. This contract extends the evidence interface without creating another owner of raw source facts.
- Apply process permissions before model/rule assessment and display permissions before presenting output. Dependent retained copies also need applicable retention rights. Recheck support at consequential writes and reads so a withdrawal race cannot publish an explanation with denied support.
- Distinguish capture time, publication time, ingestion/import time, and knowledge-publication time. Importing or publishing old evidence does not make it fresh. Age-based freshness and source/derivation support health are separate result attributes.
- New queries can select new publications, while saved results retain their actual historical support and versions. Superseded support is flagged for reassessment rather than silently replaced. Withdrawal hides or purges governed dependent copies while preserving permitted history/metadata; it does not authorize reconstructing purged text on retry.

### Campaign recommendations and shortlist revisions

- Keep campaigns marketer-initiated. Natural-language interpretation produces a visible, versioned executable criteria/ranking profile attached to the brief; the assessment uses that recorded interpretation. Required criteria, exclusions, preferences, and unknown handling must have observable effects.
- Candidate admission requires a stable platform identity and at least one permitted supporting observation already ingested and usable through the KB. Requested but un-ingested references can seed discovery and appear as gaps, but cannot be ranked as supported candidates. An empty eligible result is valid.
- Evaluate permitted candidates with deterministic filtering and method-versioned LLM assessment. Record model/method/ranking-profile versions, actual assessed inputs, rationale, explicit unknowns, and ordering. A failed or invalid model assessment reports its limitation/failure; deterministic output cannot be mislabeled as a completed LLM assessment.
- Treat generated source text as evidence, never as authority to change scope, approve tasks, call tools, or override spending. Validate generated judgments against the allowed criterion/result contract and candidate support before saving.
- Incomplete information affects the stated fit and coverage. Missing audience geography, fees, availability, full history, or sales outcomes does not automatically reject every account. A required criterion's explicit unknown policy can still defer that account; this is distinct from a universal full-profile prerequisite.
- Extend shortlist persistence to preserve actual automated or human producer attribution, exact brief and assessed support, rank order, reasons, gaps, and method versions. Human review/confirmation is optional and separate. Preserve existing human historical records and do not retroactively label them as automated or reviewed.
- Save recommendation results automatically, including an explicitly empty result where no accounts qualify. Successful retries reopen the original saved revision instead of calling the model again and appending a duplicate. A new requested generation uses a new request identity and creates a successor under concurrency checks.
- Assess candidate quantity, relevance, and freshness against an explicit versioned coverage profile. Insufficiency automatically requests bounded campaign discovery under server-established campaign authority, subject to source and spending controls. A denied or blocked acquisition submission leaves the supported recommendation intact and visibly reports why enrichment is not progressing.
- Discovery completion records usable updates and offers explicit regeneration. It cannot rerank in place, replace account membership, or mutate the saved shortlist. Optional human curation also creates an attributable successor.
- A rank expresses evidence-backed fit to the campaign criteria. It does not verify creator claims, establish audience geography from caption language, establish a contract from a PR marker, or predict sales effectiveness.

### Knowledge assistant

- Answer free-form questions through current permitted KB reads, with relevant evidence, dates, explicit uncertainty, and limits. Unsupported claims remain unanswered or qualified. Existing-KB reads require no enrichment approval.
- For missing, stale, or incomplete information, present an identifiable proposal with purpose and subject/search scope before submission. Approval must be an attributable human action for that exact proposal in the workspace; neither a generated statement nor client-supplied origin constitutes approval.
- Approved on-demand tasks may exceed the scheduled keyword list, but may not exceed the approved scope or operational/spending limits. Material scope expansion creates a new proposal/approval obligation.
- Keep task submission asynchronous. Return acknowledgment/status, then a durable completion notification with usable publication links or partial/failure information. Subsequent queries can use published updates. No direct provider result may be substituted for a KB answer while ingestion/publication is pending or failed.
- Agent-accessible operations expose the same approved task and knowledge contracts as the UI. Tool availability does not confer schedule authority, campaign authority, spending exemption, or permission to use denied evidence.

### Scheduled discovery and progressive acquisition

- Persist at most ten registered scheduled keywords per workspace. The initial configurable allowance is fifty unique eligible new posts per day total across those keywords. It is a new-post admission allowance, not fifty requests, fifty posts per keyword, a guaranteed yield, or a measured cost estimate.
- Record the configured accounting-day boundary/timezone and allowance version; coordinate unique-post admission across overlapping queries and concurrent tasks. Changed configurations and restarts must not accidentally reset the day's consumed allowance. On-demand approvals remain independently scoped; existing-record refreshes do not become fictitious new posts.
- Prioritize recency, engagement, and trend evidence using an explicit selection policy. Retain the actual route, query, time/coverage, and selection-method context so the resulting sample is explainable.
- Start with a configured broad discovery route and selectively supplement valuable records or missing fields. Capability, permission, scope, freshness, cost, and expected information value constrain route selection and stopping. Persist why further work stopped, including limits, insufficient value, source failure, or cost admission.
- Separate query discovery from the existing supplied-reference adapters. A past profile scrape or oEmbed success is not a discovery benchmark, complete history, supported identity merge, or verified commercial usage right. Verify current route schemas/access and bounded results when enabling a real integration.
- Track known identities, earlier retrieval/query attempts, source capture times, missingness, failures, and processing versions. Avoid repeated unchanged work while preserving legitimate new observations, independent provider provenance, and source-specific metric semantics.

### Lightweight X monitoring

- Configure monitoring topics, collection cadence, evidence retention, window/baseline definitions, quantitative/semantic methods, and significance parameters explicitly. Topics are separate records from scheduled KB keywords, even when their text overlaps.
- Retain bounded recent monitoring observations with source identity/reference, relevant times, coverage, permitted uses, and detection context. Timely detection must not require full ontology/entity/relationship ingestion of every post.
- Quantitative detection uses comparable sampling/measurement windows and an explicit baseline. Insufficient baseline or incomparable coverage yields an unsupported/unavailable change assessment, not a numerical spike claim. Semantic assessment retains its versioned method and supporting observations with explicit uncertainty.
- Significant detections create retained alerts with finding, evidence, windows, baseline/method versions, coverage, and an attributable notification. Existing KB context can enrich the explanation but must be distinguishable from the recent monitoring evidence.
- The anomaly investigation has no authority to initiate further external searches, expand configured monitoring scope, or create campaigns. Scheduled collection remains separate authorized work; an investigation cannot masquerade as a new schedule.
- Selected observations can be promoted through normal source ingestion and KB publication with lineage back to the monitoring input. Promotion is deliberate and retry-safe, not an automatic full-feed publication requirement or permission bypass.
- Apply source permissions, expiry, withdrawal, and bounded retention to monitoring observations and copied alert text. Preserve permitted alert history with unavailable-support indicators after support is removed. Existing fixed-snapshot investigations remain available and are not relabeled as continuous X detection.

### Hybrid spending control

- Classify configured service/cost scopes explicitly as derivable actual spending or forecast-only. Include model as well as source costs where applicable. Unknown charges are not zero, and a failed expected meter is a visible control failure rather than a silent classification change.
- Record actual attributable usage/charges with units, versioned rates where used, currency, provider/service, accounting period, task/attempt or equivalent operation identity, and measurement source/time. Keep estimates, outstanding commitments, and actual charges separate.
- Before chargeable work in metered scopes, coordinate admission against configured ceilings using actual spend plus bounded outstanding commitments. Shared workers, endpoints, and tools must use the same control; task approval cannot bypass it.
- Reconcile actual charges and commitments idempotently across retries, pending calls, billing delays, and restarts. Do not release an uncertain commitment as if an ambiguous remote call were free. Pause or refuse further metered work when allowance is exhausted or its required control is unavailable.
- Use known charge bounds or provider-side limits where strict pre-call enforcement is required. If a route has delayed or unbounded charges, show the lag and enforcement limits; this spec does not promise zero overshoot where it cannot be guaranteed.
- Unmeterable scopes retain forecasts and assumptions with incomplete cost coverage visible. They do not claim an enforced monetary ceiling. Request/byte/record bounds, acquisition approval, and value-based stopping continue to apply independently.
- The first milestone uses offline/simulated I/O and no real chargeable calls. Connect and verify cost admission before enabling live chargeable acquisition or model work; this specification does not grant a provider budget or live-execution authorization.

### Persistence, visibility, and policy

- Extend the existing relational ownership model with durable concepts for keyword subscriptions, acquisition tasks/attempts, enrichment proposal revisions and approvals, knowledge publications and support membership, ranked recommendations/coverage assessments, completion notifications, monitoring topics/windows/observations/alerts, and spend measurements/commitments/ceilings/forecasts.
- These are logical records, not a requirement for a separate table for every noun. Exact physical schema and migrations belong to each bounded implementation milestone. Preserve existing IDs, historical attribution, request identities, source policies, and frozen memberships during upgrades; update physical ERDs when schema is implemented.
- The graph is a governed read projection of permitted entities and relationships. Support search, filtering, traversal, details, and evidence; distinguish observed, derived, and human bases. Do not infer cross-platform Creator associations from similar handles.
- The pipeline view connects tasks to attempts, ingestion runs, observations, transformations, publications, completion records, failures, coverage, and attributable cost context. A successful provider response must remain visibly distinct from a usable publication.
- Source-dependent text in answers, saved shortlists, graph details, lineage excerpts, notifications, and alerts follows its support's permissions and withdrawal lifecycle. Content-free status/history may remain where permitted. Do not surface credentials, unrestricted provider payloads, or redacted wording through errors or retry forms.
- Preserve local form/Host/Origin/CSRF checks and escaped rendering. Protocol wrappers resolve actors at the trusted boundary and cannot weaken domain authorization. Existing proposed measurement plans and human decision notes retain their current meaning; no actual outcomes are fabricated.

### Proposed delivery boundaries

The following sequence turns the accepted product into bounded implementation work. It is proposed sequencing, not a claim of an existing backlog or a requirement to build the entire product in one change.

| Milestone | Deliverable | Exit condition |
| --- | --- | --- |
| 1 — Offline task to published knowledge | Durable origin/approval enforcement, submission/status, bounded worker execution using existing ingestion, minimal publication/query contract, accurate completion records | Approved task survives restart, retries without duplicate effects, publishes inspectable support, and exposes partial/failure/no-update outcomes; unapproved/forged submissions do no acquisition work |
| 2 — Shared operational controls | Concurrent admission/reconciliation for metered scopes, explicit forecasts elsewhere, schedule configuration/admission and verified discovery-route contracts | Competing work cannot bypass configured admissions; fifty-post daily total and ten-keyword limit hold; simulated accounting/retrieval is verified before enabling a configured live route |
| 3 — Campaign recommendations | Visible criteria interpretation, current-KB rule/LLM assessment, automatic shortlist persistence, coverage-triggered acquisition and regeneration offer | Incomplete supported accounts can rank; un-ingested references cannot; history remains exact; discovery completion cannot change a shortlist without explicit regeneration |
| 4 — Knowledge assistant | Grounded questions/answers, enrichment proposals and approval interaction, shared task submission/status and completion display | Existing knowledge is immediately queryable; approved work can expand beyond scheduled keywords; new results support answers only after publication |
| 5 — Lightweight X monitoring | Recent evidence owner, configured collection/detection, KB-only investigation, alerts, retention and selective promotion | Comparable-baseline and semantic scenarios are supported, full KB ingestion is unnecessary for detection, and investigation cannot trigger external searches or campaigns |
| 6 — Explorer completion and quality review | Full graph/lineage navigation over governed reads and attributable language/usefulness evaluation | Users can trace visible claims and operational failures; withdrawal is respected across views; quality findings come from actual review |

Basic task/status/publication visibility is part of milestone 1; full explorer work is not a reason to postpone it. Milestones 3–5 reuse the earlier contracts and can be broken into smaller issues without redefining their authority. Appropriate evidence and quality evaluation accompany each milestone; the final milestone does not defer all evaluation until the end.

## Testing Decisions

### Testing seams approved for tickets 01–10

- Use the highest public boundary that exposes the behavior under test. The primary new seam for milestone 1 is a cohesive task-to-knowledge application interface: submit/inspect a task, drive its bounded worker entry point, and query its published result. Keep real task persistence, ingestion, knowledge preparation/publication, and source-policy handling behind that seam.
- Reuse public campaign and monitoring interfaces for their owned behavior, with local HTTP journeys for user-visible orchestration and untrusted-input rejection. Avoid a universal catch-all service merely to force all three workflows through one object.
- Use the existing isolated PostgreSQL schema and temporary evidence-directory setup. Restart tests reconstruct application/worker objects or use a separate process against persisted state. Concurrency tests use genuinely competing connections/operations; calling a sequential helper twice is not evidence of coordination.
- Replace only external provider/model/notification transport and controllable time/failure boundaries with deterministic doubles. Use existing collector/mapper registration and simulated transport conventions. Do not mock stores to declare task completion, publication, budget enforcement, or source permissions successful.
- Test observable contracts and durable outcomes, not private helper calls, incidental SQL layout, enum spelling, or a specific queue library. An operation's returned support and subsequent public reads should establish whether knowledge is usable.

### Acceptance scenarios

The scenarios below are required observable behavior, not a claim that tests already exist or pass.

| ID | Scenario | Required observation |
| --- | --- | --- |
| T01 | Submit approved offline enrichment, execute it, restart, and query | Same durable task and actual producer/approval remain visible; declared published support is queryable and completion links to it |
| T02 | Submit missing approval, changed proposal scope, foreign workspace, or forged schedule/campaign origin | Submission is rejected; no collector/model acquisition work is dispatched |
| T03 | Retry the same submission, publication, and completion delivery concurrently | One logical task/publication/event per request; changed payload under that identity conflicts; transport retries do not invent a second update |
| T04 | Interrupt after raw evidence persistence, canonical commit, publication commit, or completion commit | Resume uses committed work, preserves exact support, and does not repeat chargeable work or duplicate effects |
| T05 | Fetch succeeds but mapping, permission validation, interpretation, or publication fails | Accurate failed/partial phase is visible; unpublished records cannot support KB answers and no usable-update success is asserted |
| T06 | Search yields no usable new records or only unchanged published support | Coverage and no-update outcome are explicit; no fictitious publication benefit or market-absence claim is returned |
| T07 | Competing workers claim/resume the same task | Shared coordination prevents duplicate logical execution and preserves completed effects after a worker loses acknowledgment |
| T08 | Withdraw or supersede support during preparation and after publication | Consequential stale writes fail or exclude invalid support consistently; current readers redact/flag dependencies without substituting new evidence into history |
| T09 | Query after a later publication while reopening an older result | New queries can see the update; the old result retains exact membership, methods, times, order, and authorship under current policy |
| T10 | Rank an incomplete supported account alongside a handle-only seed | Supported account remains eligible subject to criterion unknown policy; un-ingested seed is not ranked; all gaps are visible |
| T11 | Interpret structured/natural-language criteria and assess a constrained candidate set | Recorded criteria/profile versions determine filtering/order; rationale references permitted assessed support; missing information is not invented |
| T12 | Model returns malformed, unsupported, scope-expanding, or authority-forging content | Output cannot approve acquisition, override controls, introduce unsupported candidates, or masquerade as a valid completed assessment |
| T13 | Generate, automatically save, retry, and optionally curate a shortlist | Automation can persist without human approval, exact rank and support reopen, retries return the original result, and curation creates an attributed successor |
| T14 | No candidate qualifies or campaign coverage is insufficient | Explicitly empty/thin supported result is saved, coverage reasons are shown, and bounded discovery is queued or its admission failure is visible |
| T15 | Campaign discovery publishes new knowledge | Notification offers regeneration; the old shortlist is unchanged until explicit regeneration saves a successor |
| T16 | Ask a supported and an unsupported assistant question | Supported claims cite current permitted KB support; unsupported information stays explicit; existing reads require no enrichment approval |
| T17 | Approve expansion outside scheduled keywords, then request broader work | Exact approved scope is accepted independently of keyword subscriptions; material expansion cannot reuse that approval |
| T18 | Repeat/overlap scheduled queries across keywords and workers at a day boundary | At most ten registered scheduled keywords; initial fifty-new-post allowance is shared across the configured day; duplicate posts consume no extra new-post admission; restart does not reset usage |
| T19 | Source route lacks discovery capability, returns partial coverage, or has pending/ambiguous paid work | Capability/coverage limitation is reported; supplied-reference success is not called query discovery; paid scrape is not blindly repeated |
| T20 | Refresh known evidence or run a new mapper while prior queries are recorded | Unnecessary unchanged work is avoided while legitimate new observations, separate namespaces, metric semantics, and older pins survive |
| T21 | Concurrent metered work approaches a configured ceiling | Actual spend plus bounded commitments is coordinated before calls; refused/paused work makes no additional chargeable call |
| T22 | Billing arrives late, an attempt is retried, or an expected meter fails | Commitments and actuals reconcile once; uncertainty and lag remain visible; meter failure does not silently permit unlimited work |
| T23 | Cost is unmeterable or strict charge bounds are unavailable | Forecast assumptions and enforcement limits are shown; unknown is not zero and no unsupported zero-overshoot claim is made |
| T24 | X collection has comparable baseline, missing baseline, and changed sampling coverage | Justified quantitative changes expose their context; inadequate/incomparable baselines cannot produce unsupported spike claims |
| T25 | Recent X evidence contains an attributable semantic anomaly | Versioned semantic assessment and relevant recent evidence support the alert; existing KB context is labeled separately |
| T26 | Detect/investigate without full KB publication and attempt external search/campaign creation | Alert can use permitted recent evidence, while investigation authority rejects additional external acquisition and campaign creation |
| T27 | Promote selected monitoring evidence, retry, then expire/withdraw original support | Promotion is traceable and retry-safe; both monitoring/alert and KB dependents honor the applicable policy lifecycle |
| T28 | Traverse graph and pipeline across visible and denied support | Permitted entities/relationships and task-to-publication links are navigable; denied text and secrets do not leak through details, errors, or notifications |
| T29 | Upgrade an existing local database and reopen pilot records/forms | Existing evidence IDs, historical human decisions, snapshot investigations, proposed plans/notes, and form-origin/CSRF protections retain their meaning |
| T30 | Evaluate relevance, translations, and usefulness | Attributable reviewed examples record membership, methods, denominators, and corrections; automated test success cannot manufacture human evaluation |

### Prior art and verification

- Existing pipeline tests establish safe replay, checkpoint recovery after a saved observation, interrupted transient derivations, concurrent canonical application, bounded collection, policy denial, and schema upgrades.
- Existing frozen-evidence and knowledge tests establish atomic publication-like visibility, concurrent idempotency, immutable membership, exact source spans, separate process/display permissions, and withdrawal between preparation and commit. Reuse their patterns without treating snapshot import as the finished current-KB publication interface.
- Existing campaign tests establish retry identities, concurrent version conflicts, exact historical reopening, support withdrawal, and unknown handling. Update the old blanket prohibition on automated shortlist saves deliberately; preserve restrictions on fabricating human-authored actions and confirmations.
- Existing HTTP tests establish complete form journeys, restart persistence, stale saves, actor-forgery rejection, source-dependent redaction, escaped rendering, and the form-Origin regression. Add corresponding operational journeys at that boundary when each surface exists.
- Existing source-adapter tests use fake transports to prove asynchronous provider resume, pending-snapshot handling, no automatic paid retries, identity semantics, and request bounds. These are test patterns, not live-access validation.
- Each implementation milestone runs the shared locked repository check command, including lint, documentation/ERD/instruction consistency, and isolated-schema tests. No real provider/model calls belong in the default test suite. Live route readiness and human language/usefulness review are separately recorded evidence.

## Out of Scope

- Implementing runtime features as part of this specification-writing task; this document defines work to be delivered by bounded implementation issues.
- Sending creator outreach, publishing content, purchasing media, contracting creators, or activating campaigns in external systems.
- Actual commercial-outcome ingestion, attribution, causal lift estimation, or claims of sales improvement. Existing proposed measurement plans and human notes remain supported.
- Full profiles or complete creator histories as universal recommendation prerequisites; unsupported audience, fee, identity, availability, or efficacy claims.
- Requiring every X post to become fully modeled KB knowledge before detection, or allowing anomaly investigation to expand external research scope.
- A mandatory human-review gate before an automatically saved shortlist. Approval of assistant-origin enrichment remains required.
- Replacing PostgreSQL with a graph database, deploying microservices, selecting a broker/cloud stack, or replacing the local server merely to enable these contracts.
- Hosted authentication/multitenancy rollout, a full CRM, external email/Slack/push delivery, or an arbitrary universal agent tool platform.
- Fixed provider/model choices, invented current prices or usage rights, unsupported throughput promises, monetary ceiling amounts/currencies/periods, numeric ranking/freshness/anomaly thresholds, or retention durations not established by the accepted requirements.
- A claim that all physical deletion propagation, language validation, marketer usefulness, or live source readiness is already complete.

## Further Notes

### Authority and source material

This spec consolidates the accepted operational requirements; it does not supersede their behavioral constraints or reopen settled ADRs. Where the source documents distinguish current implementation from accepted future design, this spec preserves that distinction. The broader product proposal's longer-term commercial measurement and Creator-association goals are not silently added to the operational delivery.

| Source | Role in this specification |
| --- | --- |
| [Core functional requirements](../FR.md) | A/B/C workflows, explorer surfaces, and shared worker pipeline |
| [Operational functional requirements](functional-requirements.md) | Detailed authority, eligibility, publication, scheduling, spending, and coverage contract |
| [Product proposal](../POPOSAL.md) | Product destination and external-action boundaries |
| [Glossary](../GLOSSARY.md) | Domain vocabulary and distinctions among references, observations, tasks, publications, and decisions |
| [Architecture](architecture.md) and [data model](data-model.md) | Existing owners, installed persistence, and explicitly conceptual future records |
| [Canonical evidence ADR](adr/0001-canonical-evidence-ownership.md) and [pinned-support ADR](adr/0002-pinned-support-current-policy.md) | Dependency direction, historical support, and current-policy invariants |
| [Automatic shortlist ADR](adr/0003-automatic-shortlist-persistence.md) and [lightweight X ADR](adr/0004-lightweight-monitoring-evidence.md) | Accepted automated-save authority and separate monitoring evidence path |
| [Evidence](evidence-sets.md), [knowledge](knowledge.md), [campaign](campaigns.md), [monitoring](monitoring.md), [planning](planning.md), and [local review](local-review.md) contracts | Existing public behavior to reuse and preserve |
| [Source integrations](source-integrations.md) | Implemented route capability and remaining readiness work |
| [Quality review](evaluation.md) and [development verification](development.md) | Separate technical, language, usefulness, and shared-check requirements |

### Configuration and implementation readiness

Before a milestone enables its real operation, record the relevant configuration: source capability/policy, model/method versions, executable ranking and coverage profiles, freshness criteria, schedule day/timezone and limits, X collection/window/baseline/retention/significance settings, and cost classification/rates/ceilings/periods. Missing required configuration is an explicit unavailable/blocked capability, not permission to invent a default claim or run unbounded work.

Only the ten-keyword maximum and initial configurable fifty-unique-new-post daily total are fixed numerically here. Other operating values are chosen and validated during their bounded implementation work, without requiring another product interview unless a material conflict with accepted behavior emerges.

### Specification and issue handling

Publish the implementation spec to the configured project tracker with the `ready-for-agent` label after the to-spec test-boundary check. Keep the issue and this durable product specification aligned. Separate bounded implementation issues should reference this contract and the acceptance scenarios they deliver; their status and execution chronology belong in the tracker or scratch records.
