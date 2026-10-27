# Local marketer review

[`smi_review`](../src/smi_review/__init__.py) provides independent investigation and campaign workflows over public monitoring, campaign/planning, knowledge and frozen-evidence interfaces. PostgreSQL owns saved revisions; browser state is not durable.

This document describes the current local browser, including automatic deterministic and bounded model-ordered shortlist saves and separate human selections. The installed browser also offers bounded extractive KB answers and explicit gap-to-approved-enrichment follow-up; the [target operational UI](functional-requirements.md) will add broader autonomous research, X alerts and graph/lineage explorers.

## Knowledge search

The navigation links `GET /knowledge/search`, a bounded literal query form with text, platform, subject UUID and capture-time filters, an optional freshness threshold and a 1–100 member limit. **Search and preserve result** submits a same-origin CSRF-protected `POST /knowledge/search`, then redirects to `GET /knowledge/results/RESULT_ID`. New computation requires process permission and display permission through `KnowledgeQueries`; the browser supplies neither actor identity nor process authority. No external research or approval is triggered.

A result page reopens exact actual support after restart and shows its producer, query method, original scope/coverage, publication and source versions, individual missing fields and current health. Capture-age freshness remains separate from withdrawal/supersession. Results show both publication-scan and result truncation, with an explicit incomplete-market-coverage limit. Later publications can appear in a new search while an old result keeps its membership. Denied/superseded sources display IDs and status without source text. Synthetic inputs require the explicit development checkbox and `?include_synthetic=yes` on reopening. See the [query contract](knowledge.md#bounded-current-knowledge-queries) for limits and filter semantics.

## Knowledge publications

The main navigation links `/knowledge/publications`, which lists only committed, nonsynthetic publications in the local workspace. `/knowledge/publications/PUBLICATION_ID` reopens the exact selected observations, derivations, assertion/metric IDs and optional existing caption interpretations. It shows actual producer, publication/source times, mapper and interpretation versions, original coverage, current support health and unknown fields. Denied or superseded support displays metadata without source text; later publications do not replace this historical selection.

Publication is an explicit trusted operation through `KnowledgePublications.publish` or the `smi-ingest publish-knowledge` CLI described in the [knowledge contract](knowledge.md#explicit-knowledge-publication). Reading a detail page does not acquire evidence or publish anything. Existing form protections and actor boundaries apply unchanged.

## Bounded model ranking

**Rank and save automatically** posts to same-origin CSRF-protected `/campaigns/CAMPAIGN_ID/ranked-recommendations`. It accepts only exact brief/profile/request identity and both expected heads. The server supplies the automation actor. Deterministic eligibility runs first; one configured bounded Responses call orders eligible supported accounts with constrained candidate-scoped judgments. Valid results redirect to a saved generated shortlist showing actual model/profile/method/schema, exact assessed inputs, generated rationale and unchanged gaps. No human endorsement or acknowledgement is claimed. Empty batches save without a call; failures/unavailable/stale/uncertain attempts remain visible on the campaign, with no deterministic success fallback. Exact retries reopen the original across restart; interrupted claims never redispatch. Stale forms preserve exact retry/profile/head context. Current policy hides or purges governed inputs, judgments and reasons while permitted order/provenance remains. See [the ranking contract](campaigns.md#bounded-supported-llm-ranking).

## Automatic deterministic recommendations

A campaign page offers **Recommend and save automatically**. Same-origin CSRF-protected `POST /campaigns/CAMPAIGN_ID/recommendations` accepts only request/brief identity, an explicitly selected saved criteria interpretation and expected brief/shortlist heads. The server calls `CampaignStore.recommend` using its actual `local-rule-preparation` automation actor. This action immediately redirects to the saved `generated` shortlist; there is no review/approval/confirmation checkbox. Forms cannot claim human authorship, confirmation, origin or method.

The saved page shows deterministic unranked comparison order, actual producer/method, exact brief/profile, rationale, explicit gaps, pinned support and empty-result counts/reasons. Required exclusions and deferred unknown requirements remain unselected; source-only incomplete profiles can be selected. Generated gaps are never presented as human acknowledgements. Identical retries reopen the original across restart and newer knowledge; changed payloads and stale new requests conflict. Recoverable errors retain exact request, brief, profile and both expected heads. Current policy withholds/purges source-dependent explanations while retaining permitted order, membership and producer.

## Current-KB campaign comparisons

A campaign page offers **Compare current knowledge**, independently of imported datasets. Same-origin CSRF-protected `POST /campaigns/CAMPAIGN_ID/current-comparisons` accepts only request/brief identity and optional explicitly selected saved criteria interpretation. Server actors prepare through `CampaignStore.prepare_current_comparison`; forms cannot choose actors, methods, source/model routes or task authority. Recoverable errors preserve request, exact brief and profile selection.

`GET /comparisons/COMPARISON_ID` reopens the pinned comparison and its current display-policy view. It shows actual retrieval manifests, source dates/freshness, unknowns, discovery gaps, required exclusion/defer assessments, empty outcomes and the unranked deterministic method. Source-only support exposes provenance even without a caption. Historical membership/order/explanations stay fixed after later publications; denied/superseded support withholds dependent explanation text. Preparation does not save a shortlist or call a source/model. Existing frozen comparison forms and explicit human draft/confirmation remain available.

## Run the application

Start PostgreSQL and load the offline inputs once:

```bash
docker compose up -d --wait postgres
uv sync --locked
uv run smi-ingest migrate
uv run smi-ingest import-snapshot examples/curated/jp-kbeauty-tiktok-2026-10-05/snapshot-manifest.json
uv run smi-ingest register-catalog examples/catalogs/beauty-v1.json
uv run smi-review --actor local-marketer
```

Open `http://127.0.0.1:8765`. `--port` selects another local port. `SMI_DATABASE_URL` and `SMI_DATABASE_SCHEMA` select an existing local database/schema, as with the ingestion CLI. Starting the server does not migrate, import or contact a source; missing setup produces a visible setup/error state. Preparation uses deterministic caption rules without a provider/model request.

The server binds only to `127.0.0.1`. The named reviewer is trusted local application context, not a hosted account login. Human actions use that server-configured actor; caption/comparison preparation uses a separate automation actor. Browser input cannot supply actor identity/kind or directly set persisted confirmation status.

## Marketer workflow

1. **Create a brief.** Choose a registered catalog, brand/products, objective, target market, platforms and visible criteria. A brand-level brief can leave products empty. Optional dates, budget, currency and audience detail remain human inputs or unknowns. Known accounts require exact platform/namespace/native IDs, not mutable handles.
2. **Prepare a comparison.** Choose a loaded frozen dataset. The application prepares a new rule-based knowledge run and comparison tied to the exact brief. Request identities make retries safe. The screen identifies the method, dataset/digest, preparation time and actual scoped observation count.
3. **Inspect account support.** Candidate origins are campaign-relative known/retrieved/both. Criterion judgments separate literal support, contradicted exclusions and unknowns. Expand evidence panels to inspect original permitted captions, highlighted supported spans, source links, publication/capture dates, capture age and acquisition lineage. Support-reference details expose the exact observation/assertion IDs. External sources are links; they are not embedded or fetched by the application.
4. **Save a draft or confirm.** Select accounts and write human inclusion reasons. Cite relevance interpretations and individually acknowledge the recorded unknowns. An explicit reviewer acknowledgement enables confirmation. The store also enforces current support, required criteria and expected versions; manipulating browser controls does not bypass those checks. An empty selection can record deferral.
5. **Reopen or revise.** The campaign page lists comparisons and every saved shortlist revision. A saved page retains the exact brief, selected account set, reviewer, time and references. “Create successor revision” loads the permitted saved reasons/citations/acknowledgements into a new review form. A revised brief requires a new comparison before another shortlist save. Older records remain available in the history.

Catalog reference values identify the meaning requested by a criterion. Product-family mentions do not establish a variant; `script_evidence` with `kana` does not establish Japanese language or audience geography. Fees, availability, sales effectiveness and complete account history remain unknown under this method. Human reason text is labeled human supplied rather than independently verified.

Translations and language adjudication are pending. The application shows originals and provisional status without implying a translator or validated Japanese-original semantics. Actual marketer usefulness is evaluated separately.

## Independent investigation and campaign planning

Open **Investigations** without starting a campaign. Save product/topic/market/platform scope and optional publication/language constraints, choose a dataset and prepare a pinned snapshot insight. Findings show distinct-post/account counts, literal support, original captions and limits. Scope/answer history survives restarts. A language requirement that cannot be assessed is visible rather than silently ignored; unavailable finding support also withholds aggregate matching counts. See [monitoring](monitoring.md).

From a campaign, open **Measurement plans and decision notes**. A proposed plan pins the current brief and a relevant saved shortlist, with source/owner, product/listing/currency, period/baseline, matching/attribution and gaps. A note records human feedback for any relevant historical shortlist, including a generated revision without first requiring human review. Plans remain proposed with no outcomes; notes inherit selected-source policy. Separate expected version heads and request IDs protect both histories. See [planning](planning.md).

## Optional shortlist curation

On any saved generated or human shortlist, **Create successor revision** reopens its exact comparison and source shortlist context. Generated/model order is the initial display order; reasons show their original basis. Select accounts, give each selected account a distinct positive position, edit human reasons, cite permitted relevance support and acknowledge declared unknowns. **Save draft** creates an attributable ordered human successor without requiring review. **Confirm shortlist** separately requires the review checkbox and the existing support/unknown checks. Neither action changes the original recommendation or invokes a model/source.

The existing `POST /comparisons/COMPARISON_ID/shortlists` carries the source shortlist ID, retry identity and expected source head. Reopening an older source does not retarget the form to the current head. Invalid order and stale saves preserve permitted edits and original retry/head context; unavailable/purged reasons are withheld from both saved pages and error forms. Saved curation pages link their source revision and show human order/method and whether confirmation actually occurred. Existing human records without a source/order keep their historical meaning.

## Save, failure and support behavior

Forms carry a stable request ID and the expected prior version. Successful actions redirect to the saved database record. Retries return the original revision; stale or changed requests fail visibly. Recoverable brief/selection errors preserve submitted edits and their original expected version, so a conflict cannot silently become an overwrite. Open the campaign history to review the current head before making a successor save.

Rendering uses current display-policy readers. Denied/superseded candidate support withholds captions, copied explanations and saved reasons. A retention withdrawal purges copies through campaign/knowledge reconciliation. An error page also withholds source-dependent submitted reasons when support is unavailable. Selected references, saved order and producer metadata remain; a permission recovery does not reconstruct purged explanations. The [campaign contract](campaigns.md) defines the durable policy/version invariants.

The server accepts only its loopback Host, same-origin form writes and its CSRF token. Requests have bounded body/field counts; data is HTML-escaped, source links are limited to HTTP(S), and responses use `no-store` and a restrictive content policy. Static routes serve only bundled CSS/JavaScript. A server restart rotates the form token: reopen the saved record to obtain a new form. These are local application boundaries; remote hosting/authentication is not implemented.

Responses use `Referrer-Policy: same-origin`: same-origin form submissions retain the Origin required by the server, while external navigation receives no referrer. `no-referrer` would serialize non-CORS form POST origins as `null` under the [Fetch Origin-header algorithm](https://fetch.spec.whatwg.org/#append-a-request-origin-header). Null and foreign origins remain rejected; they are not exceptions to the same-origin check. Reload forms after a server policy change to obtain the current document policy and token.

HTTP boundary errors explain that the request was not saved and provide **Open campaign workspace** and **Create a brief** recovery actions. These links use the server's configured loopback address, independently of submitted Host, Origin, Referer or path values. Rejected form contents are not reflected or automatically resubmitted.

## Implemented routes and ownership

| Route | Purpose |
| --- | --- |
| `GET /proposals`, `GET /proposals/new`, `POST /proposals`, `GET /proposals/{id}` | Supply and reopen an immutable purpose/intent/subject/search/configuration scope before acquisition |
| `POST /proposals/{id}/approve` | Explicit named human exact-scope approval and retry-safe task acknowledgment |
| `GET /costs`, `GET /costs/{id}`, `GET /tasks/{id}/costs` | Source-free synthetic usage detail, forecasts, unresolved commitments, final reconciliations and meter recovery |
| `GET /inbox/{id}/regenerate`, `POST /inbox/{id}/regenerate` | Inspect current campaign needs and saved method, then explicitly assess/save a successor with exact retry/head protection |
| `GET /inbox`, `GET /inbox/{id}` | Workspace-scoped durable completion messages, actual coverage and current-policy publication links |
| `GET /tasks`, `GET /tasks/{id}`, `GET /campaigns/{id}/tasks/new`, `POST /campaigns/{id}/tasks` | Durable task status, exact scope/approval/attribution and configured campaign submission |
| `GET /knowledge/search`, `POST /knowledge/search`, `GET /knowledge/results/{id}` | Bounded knowledge query and exact saved support under current display policy |
| `GET /knowledge/publications`, `GET /knowledge/publications/{id}` | Committed publication metadata and exact permitted support |
| `GET /` | Workspace campaign heads and loaded input metadata |
| `GET /campaigns/new`, `POST /campaigns` | Human brief form and campaign start |
| `GET /campaigns/{id}`, `GET /campaigns/{id}/edit`, `POST /campaigns/{id}/briefs` | Current brief, history and successor brief |
| `POST /campaigns/{id}/interpretations` | Save one exact-brief bounded natural-language interpretation and show its outcome/profile |
| `POST /campaigns/{id}/current-comparisons` | Pin a deterministic current-KB comparison independently of dataset imports |
| `POST /campaigns/{id}/comparisons` | Rule-based knowledge/comparison preparation with optional explicit selection of a visible saved interpretation |
| `GET /comparisons/{id}` | Exact comparison, current evidence and versioned selection form |
| `POST /comparisons/{id}/shortlists` | Human draft/confirmation, optionally ordered curation of an exact source revision |
| `POST /campaigns/{id}/ranked-recommendations` | Apply deterministic eligibility, assess one bounded model batch and automatically save valid order; failures remain visible |
| `POST /campaigns/{id}/recommendations` | Compare current KB and automatically save an attributed ordered generated shortlist |
| `GET /shortlists/{id}` | Exact saved revision with current support health |
| `GET /investigations`, `GET /investigations/new`, `POST /investigations` | Independent investigation list and human scope creation |
| `GET /investigations/{id}`, `GET /investigations/{id}/edit`, `POST /investigations/{id}/scopes` | Scope/answer history and revised question |
| `POST /investigations/{id}/insights`, `GET /insights/{id}` | Rule-based snapshot preparation and permitted finding panels |
| `GET /campaigns/{id}/planning`, `POST /campaigns/{id}/plans`, `POST /campaigns/{id}/notes` | Proposed measurement and human feedback revisions |

`CampaignStore.list_campaigns` and the comparison/shortlist metadata in `read_campaign` provide navigation without copied reasons. `KnowledgeStore.list_catalogs` lists human configuration. `EvidenceSetReader.list_sets` lists dataset metadata and excludes synthetic data by default. Each interface checks the configured workspace. The application does not query or write another module's tables.

The HTTP boundary returns visible validation errors, `409` version/request conflicts, `404` missing records and sanitized `503` database/setup failures. Host/origin failures use `403`; oversized/unsupported request bodies use `413`/`415`. Domain-store checks remain authoritative after every form submission.

Create/revise brief forms save optional original marketer prose alongside stable structured criteria. Campaign and historical brief panels reopen the exact saved executable profile, brief ID/version, criteria policies, installed caption method, unranked ordering and descriptive coverage versions. Prose and structured needs remain human input; audience, commercial terms and sales remain unknown without source support. Stale revisions retain submitted prose, criterion IDs and retry/version context. Historical pre-profile briefs visibly report that no profile was recorded. See the [campaign profile contract](campaigns.md#implemented-briefs-and-actors).

## Accepted future application surfaces

Campaign results support bounded validated LLM ranking alongside deterministic automatic save, retaining KB support, rationale, unknowns/freshness and exact attribution. Live receipts and human usefulness are not established by simulated verification. Optional richer human curation/review is distinct. Insufficient coverage shows the automatically queued discovery status; completion offers explicit regeneration rather than replacing the saved result.

The installed assistant accepts free-form KB questions as described below. A saved gap can generate a fixed purpose template with exact human-supplied keyword/subject/time scope for review and approval; supplied proposals retain their separate surface. Approval precedes task submission and binds its scope server-side. Show acknowledgment/status and completion notifications; answers use published knowledge rather than raw newly fetched tool responses. Spending-ceiling pauses and partial/failed ingestion are visible independently of approval state.

The installed bounded X volume and provisional quality-controversy alert surfaces show original window support, method/model configuration, history and uncertainty. Existing-KB explanation and semantic shift remain future work. A graph explorer searches, filters and traverses permitted entities/relationships with source details. A pipeline/lineage view connects tasks, attempts, runs, failures, observations, transformations, KB publications and attributable cost information. These are product requirements, not names for existing hidden screens.

## Offline acquisition submission and status

Start with `smi-review --offline-manifest examples/synthetic/json-manifest.json` to configure supplied-reference fixture JSON, or use `examples/synthetic/keyword-discovery-manifest.json` for bounded offline keyword discovery. A campaign links `/campaigns/CAMPAIGN_ID/tasks/new`; the form displays exact current brief, configured references, digest and limits. `POST /campaigns/CAMPAIGN_ID/tasks` accepts purpose/request identity/current brief only. The server constructs its named human actor and campaign origin; supplied origin, actor, approval or collector fields are rejected. Existing Origin/Host/CSRF protection applies. Submission redirects immediately to `/tasks/TASK_ID` without fetching. Recoverable validation/request/version errors redisplay escaped purpose and the original request identity. A stale form retains its recognized historical campaign brief and links to the current brief for a new submission; an unrecognized brief is replaced by server-read current scope, with a visible error. Submitted origin/actor/approval/route fields never become hidden authority.

`/tasks` lists at most 100 newest workspace tasks. Details survive restart without configured route access and distinguish queued/collecting/ingesting/publishing/waiting phases and exact commit progress, usable update, partial update, no usable update and failure, with actual coverage/remainder counts, recovery actors, stable worker/run/support IDs and synthetic publication links. Run `smi-ingest run-offline-task TASK_ID` separately to execute at most one admitted task. Published source values reopen through current policy; task pages hold no copied source text. Repeat the same worker command/task ID to recover interrupted committed work. Execution metadata distinguishes queued, running, recoverable, waiting and completed ownership independently of the committed phase. Waiting progress shows its sanitized reason and whether resume is safe. Competing workers retain one task owner while other tasks progress independently; a disconnected worker cannot commit late local effects. **Inbox** reopens one durable completion per terminal task at `/inbox` or `/inbox/EVENT_ID`. It distinguishes usable/partial/no-update/failure, historical publication coverage and current permitted support; unavailable publication links are withheld while task history remains navigable. It stores no copied source wording or purpose text. Migration/reconciliation covers older terminal tasks. External transports remain subsequent work; configured synthetic monetary admission exposes waiting reasons and allowance in task progress, while **Costs** exposes the separate source-free synthetic accounting below. See [the owning task contract](tasks.md).


**Proposals** opens the supplied-proposal list and form. Saving purpose, refresh/fill/expansion intent and subject/search fields commits an immutable revision with the configured fixture route, exact references and limits; it submits no task. `/proposals/ID` visibly reopens workspace, proposer, scope digest and bounds. Search scope can extend outside scheduled keywords. The supplied-reference capability reports why keyword discovery is unavailable. With the keyword fixture capability, the form requires one caption query, exact subjects and explicit inclusive/exclusive publication timestamps, and review displays the saved method/scope/configuration before approval. The campaign task form links to this explicit proposal journey when a query route is configured. See [the discovery contract](tasks.md#bounded-offline-keyword-discovery).

The approval POST accepts only CSRF/request identity, the displayed scope digest and an explicit checked `reviewed=yes` action. The server's named human must have its configured approver role; model text or submitted origin/actor/scope fields grant no authority. Approval and task commit separately with safe identical retries; an approval-only restart keeps the original request identity so the human can finish submission. A saved approval cannot mint a second task using a new request ID. Proposal/task pages retain exact attribution and bidirectional links after restart with no route configuration. Materially different scope requires a new proposal and approval. Recoverable proposal errors retain escaped purpose, intent, subjects, searches, discovery time window and request identity in editable fields. Approval/submission errors reopen the immutable server-read scope/digest, preserve the reviewed action and retain the durable original approval request identity when present. The CSRF token and authority remain server-derived. Conversation generation remains future work.


## Synthetic cost detail

**Costs** lists the newest 100 recorded workspace operations, with direct detail available by operation identity after restart. Each task links its own cost list, after reopening the exact task through its owner. Details show provider/service, fixed metered or forecast-only classification, currency/period, actual operation actor/method, optional exact task/attempt, units/versioned rate and measurement provenance/time. Values are escaped and independent of restricted source values.

Synthetic measured amounts are labeled as development measurements with **No commercial charge**. Forecasts/assumptions and declared outstanding commitments have separate amounts; missing amounts are **Unknown**. Explicit unknown coverage and meter failures remain visible without changing classification. Controlled metered details report **Enforced synthetic monetary ceiling** with authoritative scope allowance and one-use operation admission status. Forecast/uncontrolled details report **No enforced monetary ceiling**. Cost and relevant task detail reopen known charge bounds, current billing state and meter health, with no zero-overshoot guarantee for delayed/unbounded charges. Cost detail retains original entries, named final reconciliations, unresolved identities and separate health-recovery attestations. Task waiting progress is historical; accounting resolution alone does not recover a missing response or complete the task. There are no browser configuration/measurement/recovery forms and no paid calls or worker execution from these pages. Configure and record through the trusted public [accounting operations](costs.md); migration installs their schema.

## Bounded campaign criteria

The campaign page displays generated criteria and original human constraints with exact brief/model/method/schema and cost links. A separate selector explicitly chooses a succeeded current-brief interpretation for comparison. Generation never starts comparison or acquisition. Trusted `ReviewApp` composition accepts `ResponsesRoute`, `ResponsesTransport` and credential. `ResponsesHTTPTransport` is disabled by default and only explicit `enabled=True` provider configuration with verified model bounds can dispatch. No environment credential or browser field enables it. Standard startup shows **Model route unavailable**. All verification uses simulated external connections; no live receipt/account readiness or human quality result is claimed.

Forms retain Origin/CSRF/server actor controls and only CSRF/request/brief/version inputs; authority/configuration fields are rejected. Recoverable errors preserve stale retry context, saved outcomes reopen after restart, and synthetic/provider-reported costs remain distinct. Failure/blocked/refused/incomplete/stale/meter/uncertain states are visible, including interrupted attempts with no silent reissue. See [the exact contract](campaigns.md#bounded-natural-language-interpretation).

Both recommendation POSTs now compose save-first automatic coverage discovery. Saved shortlist pages show the immutable coverage policy/clock/reasons and exact task link/current progress, or the durable source/configuration refusal. The server assigns its preparation automation a distinct configured campaign role; forms cannot select authority, scope, route, cost controls or coverage thresholds. GETs reopen without submitting or reevaluating. Existing supported and empty results remain visible during queued/running/cost-waiting work; task completion never changes shortlist history. See [automatic coverage](campaigns.md#automatic-coverage-and-discovery).


## Explicit discovery regeneration

A usable/partial automatic campaign-discovery completion links the exact task, original shortlist and currently permitted publication. **Offer to regenerate** opens `/inbox/EVENT_ID/regenerate`, showing the current human brief/executable criteria, inspected generated-profile choices and provenance, saved actual deterministic/ranked method and action history. No-update/failure or unavailable exact publication support offers no new evidence. Inbox/offer GETs never assess or replace a shortlist.

**Regenerate and save successor** is one explicit same-origin, CSRF/Host-protected POST. It accepts only request/current-brief identity, expected brief/shortlist heads and an optional explicitly selected saved interpretation. The server retains the actual named human and preparation automation and derives the method from the original saved recommendation. Successful assessment saves automatically and opens the new revision; human confirmation remains separate. Model unavailability/failure/uncertainty stays visible with no deterministic fallback, and costs link to the existing accounting view.

Exact duplicate actions reopen the same outcome after restart, even after later brief/support changes. Stale brief/head errors retain their request, heads and profile; **Reload current context for a new request** permits deliberate recovery. An unfinished browser request has **Reopen exact request**, preserving its original body rather than creating another assessment. The original and successor remain reachable in campaign history and the completion's action history. Publication/support policy is rechecked; no source wording is copied into notification, action records or retry forms. See [the operation contract](campaigns.md#explicit-regeneration-after-discovery).


## Offline registered keyword schedule

Start with `smi-review --schedule-operator --offline-manifest examples/synthetic/keyword-discovery-manifest.json --offline-route-version offline-keyword-v1` to grant the named local human the schedule operator role. Default startup does not grant this role. `/schedules` displays default offline authority, recorded activation, immutable settings/history and current task links; it remains independent of monitoring. The operator can save timezone/daily local time/lookback/allowance and up to ten keyword JSON objects with stable keys, literal queries and explicit subjects. Stale versions preserve escaped submitted edits; authority/route/origin/clock fields are rejected. An explicit execution-mode selection can activate the configured verified live keyword route only with the trusted live mutation opt-in; each save pins its exact route/version/manifest/limits/policy. See [recorded live activation](tasks.md#recorded-live-keyword-schedule-activation). Initial UI suggestions are UTC, 09:00, seven calendar days and an allowance of 50; these become authority only after an explicit save. The timezone is fixed on the first save.

`POST /schedules/tick` acknowledges due tasks using only the server clock/configured human and CSRF token. It never executes the worker; use the existing separate bounded task command for each link. Repeated or concurrent ticks preserve task identity/status, earlier missed dates are not replayed, and refusals remain visible for that keyword/day. The configurable daily new-post admission allowance is atomically enforced at scheduled canonical ingestion. The panels distinguish used/remaining allowance, known refreshes, deduplicated identities and exclusions from throughput, costs, request counts and per-keyword yield. Existing same-origin/Host/CSRF controls apply to both POSTs. No daemon, provider activation or external cron is configured. See [the owning contract](tasks.md#registered-offline-keyword-schedule).

The registered offline schedule and task detail panels show the shared day’s configured new-post limit, used/remaining allowance, deduplicated/known-refresh/ineligible/limit-excluded counts and actual task limits. Fewer records can result from overlap, source coverage, invalid/denied records or independent caps. A cap decrease preserves earlier usage; task authority remains immutable while the separate allowance panel reopens current enforcement. See [the schedule contract](tasks.md#registered-offline-keyword-schedule).

Task details show discovery retrieval history, decision-time freshness/policy, exact query/processing context and governed capture identity/time metadata. Prior task/publication navigation is labeled separately from this task's actual publication links. A skip explicitly reports that it created no new publication; current permissions may withhold its old basis. Policy and processing revision are trusted Python configuration, absent from submitted form fields. See [capture-based avoidance](tasks.md#capture-based-discovery-avoidance).


The [live keyword route](source-integrations.md#bounded-live-tiktok-keyword-discovery) requires the trusted server's `--enable-live-discovery` before proposal save/new task submission. This is admission only; the separate worker still requires operation/source-use/credential/cost gates. Existing task/history/publication navigation does not read a manifest at app construction and survives removed source inputs. Live pages distinguish provider fields and unknown capture/final charges from synthetic fixture data; browser fields cannot enable execution.

The optionally configured live proposal form can include one exact profile URL/native ID for nickname supplementation. Review shows the pinned field/value policy before human approval; form fields cannot grant runtime profile authorization or select another field/route. Task detail displays the durable selection/stopping reason, known source outcome and current supplementary support health separately from historical results. Publication pages retain separate namespaces, nickname support and explicit unknown profile attributes/equivalence. See [the bounded contract](tasks.md#one-missing-profile-nickname).

## Free-form KB questions and exact supported findings

**Ask knowledge** opens `GET /knowledge/questions`. `POST /knowledge/questions` accepts only CSRF/request, a free-form `question`, optional literal support `text` and explicit `include_synthetic=yes`. No approval is required to read existing knowledge. The trusted constructor supplies the same optional model route/transport/credential used by campaign generation; default startup has none. Forms cannot supply model, rates, actor, tools, approval or acquisition authority. Invalid/conflicting edits preserve escaped question/filter/request context.

The action redirects to `/knowledge/answers/ANSWER_ID` (with explicit synthetic visibility when selected). The saved page labels its bounded extractive selection, requesting human, generated authorship/basis, actual model/method/bounds, full actual input IDs/query manifest, usage/cost link, exact source values/citations/dates and explicit missing/stale/ambiguous/unsupported limits. Default scope examines at most 100 recent publications/20 members, sends at most 100 exact facts and assesses capture age against 30 days. It supplies neither semantic search nor fluent uncited synthesis. A valid selection is not independent verification or a complete answer.

Empty support, absent model/configuration, cost refusal, invalid/incomplete output, interrupted calls and unknown usage remain visible. Exact retries reopen without another model call; in-progress/interrupted pages make that uncertainty explicit. Reopening after restart requires no transport. Current permission/health for every input, including unselected inputs, governs the derived selection; withdrawal withholds it while preserving historical IDs/model/method/accounting. Later publications require a new question. The page uses current public evidence panels, never a raw provider response or a source-text cache. The answer operation performs no acquisition or external search. Its supported gaps offer the separate follow-up below, without granting approval or changing the answer. See [the answer contract](knowledge.md#bounded-free-form-knowledge-answers).


## Assistant gap to approved enrichment

A question's original human requester can follow **Propose bounded enrichment** from a saved empty/missing/ambiguous/stale or currently unsupported answer. Model/configuration/accounting failures alone offer no gap proposal. The installed template asks for refresh/fill/expansion intent, exact subject IDs, one keyword query and inclusive/exclusive publication timestamps. It uses the configured bounded keyword capability and promises only research within that scope, not that an absent field will be returned. A save creates an immutable proposal for review without approval or acquisition; the page shows exact workspace, proposer, query/window, route/configuration digest and limits. It can exceed scheduled keywords only under its own exact approval.

| Route | Action |
| --- | --- |
| `GET /knowledge/answers/{id}/enrichment/new` | Render current gap and explicit bounded scope form for the original asker |
| `POST /knowledge/answers/{id}/enrichments` | Save one source-free journey claim and exact proposal revision for review |
| `GET /assistant-enrichments/{id}` | Reopen original answer, exact review, actual task status and durable completion |
| `POST /assistant-enrichments/{id}/approve` | Require actual human checkbox action on the saved digest, then acknowledge one exact approved task |

Protected POSTs retain Host/Origin/CSRF checks and strict field allowlists. Scope forms accept only request, intent, subjects, query, window and explicit synthetic visibility; approval forms accept only request/digest/reviewed/synthetic context. Actors, origin, route, limits, models and cost controls remain server-owned. Recoverable errors preserve escaped scope. Restart can reopen an interrupted proposal's exact original scope/request and recover its saved revision even when route inputs are absent. An approval-only interruption retains the original approval request for retry; identical approvals acknowledge the same logical task. Materially broader work receives a new proposal and fresh approval.

The journey page immediately displays **Task acknowledged** with queued/running/waiting status and exact task link. The independent worker owns execution; GET, save and approval do not collect evidence. Later **Actual completion** shows the durable usable/partial/no-update/failure message and exact inbox link. Current publication support controls its navigation separately from historical counts. The **Original answer** stays pinned; **Ask again** starts an explicit new KB question, and raw or pending-unpublished fetches never answer it. Source withdrawal withholds dependent findings and current publication links without inventing another event or replacing historical support. This local journey adds no external notification, source/model provider, or autonomous tool loop. See [the contract](tasks.md#assistant-knowledge-gap-enrichment).


## Bounded offline recent X topics

**Recent X** opens `/monitoring/topics` independently of campaigns, scheduled keywords and frozen snapshot investigations. Run migrations with the existing `smi-ingest migrate`; its monitoring migration additively installs the separate recent schema. Configure the current source policy through trusted Python `RecentMonitoring.set_policy` using the exact fields in [the monitoring contract](monitoring.md#topic-and-policy-operations). The default source-policy suggestion is `offline-x`; it grants no policy until explicitly created.

Start `smi-review --monitoring-operator --recent-x-fixture examples/monitoring/recent-x.json` to grant the named human topic configuration and explicit bounded offline poll authority. Default startup permits reading saved data and grants no monitoring operator role. The route path, actor, clock and permission mutations are server/operator configuration; forms cannot select them. The fixture contains fixed synthetic source dates, so update deliberate local test input/window settings as needed; importing it later never makes it recent source evidence. No provider/model request or daemon is enabled.

The topic form saves stable key, literal query, cadence/window, record cap, retention and existing policy context as explicit JSON, with request identity and expected revision. Initial form suggestions are query `cushion`, 60-minute cadence, 120-minute window, 50 records and 24-hour retention; they become configuration only on save. A poll requires an exact timezone-aware window end aligned to the saved UTC cadence. The same topic/end reopens the same historical window after edits, retries or restart. Recoverable errors preserve escaped settings, expected version/request and window end; forged actor, policy-write, route or clock fields fail. Host/same-origin/CSRF protections remain unchanged.

| Route | Behavior |
| --- | --- |
| `GET /monitoring/topics`, `POST /monitoring/topics` | List bounded independent topics; operator saves the first revision |
| `GET /monitoring/topics/{key}`, `POST /monitoring/topics/{key}` | Reopen timeline/latest 100 windows/configuration history; operator saves a successor |
| `POST /monitoring/topics/{key}/poll` | Collect/reopen one explicit bounded offline logical window |
| `GET /monitoring/windows/{id}` | Original configuration/acquisition/coverage and currently available member copies |
| `GET /monitoring/observations/{id}` | Original native capture/detail with current process/display/retention overlay |

Timeline pages show up to 50 captures by default with bounded next-page navigation. Original capture/publication/measurement/import/deadline times, unknown fields, metric meanings and synthetic acquisition context are labeled separately. Partial/missing fixture coverage and unknown market coverage stay visible; empty results establish no absence or trend. Current retention loss/expiry/native withdrawal permanently withholds text/metric copies in topic, window and detail views, including after restart; source-free lineage remains. Policy mutation and native withdrawal remain explicit trusted Python operations. See [the owner contract](monitoring.md#reopen-and-lifecycle) for all finite limits and cleanup behavior. Live X readiness, KB promotion, language quality and marketer usefulness are unestablished; the separate configured quantitative alert path is described below.


## Quantitative X assessments and alert inbox

**Recent X** topic/window pages link `/monitoring/assessments`. Migrations install the independent alert schema along with recent evidence; existing task-only inboxes still work before optional monitoring migration. Read-only startup reopens assessment/alert history and `/inbox` without a fixture route or detection configuration. The inbox composes the latest 100 task completions and latest 100 notifications per monitoring method separately through their owning public readers.

Detection requires the trusted `--monitoring-operator` opt-in and an explicit configuration, for example `--monitoring-volume-threshold '{"minimum_baseline_posts":1,"minimum_increase_posts":3,"minimum_ratio":3}'`. These example values are local sample signal choices, not statistically calibrated thresholds or production recommendations. The constructor equivalent is `monitoring_threshold=VolumeThreshold(...)`. The form shows that server configuration and accepts only exact detection/baseline window IDs, request identity and CSRF; an empty baseline records its absence. Window pages expose their stable IDs and original times/coverage. GET never detects or collects. The protected POST saves a comparison/limitation and redirects to its durable assessment.

| Route | Behavior |
| --- | --- |
| `GET /monitoring/assessments` | Latest 100 assessments, including no-change and limitations; operator/configuration-gated form |
| `POST /monitoring/assessments` | Assess exact frozen window pair with the configured distinct-post volume method |
| `GET /monitoring/assessments/{id}` | Exact saved method/configuration/outcome and current original support |
| `GET /monitoring/alerts/{id}` | Exact retained alert and local notification identity, even beyond newest-100 lists |
| `GET /inbox` | Concise governed monitoring messages beside independent task completions |

A supported threshold crossing creates one alert/local notification atomically. Exact retries reopen the saved assessment; new requests for the same pair/method/configuration retain its first result and notification. Changed inputs/configuration/actor under a request conflict; recoverable errors preserve the original request/window IDs. Forms reject threshold, actor, query/scope, policy, search and campaign authority. No detection action submits tasks, creates campaigns or acquires source/model evidence.

Detail shows method version, exact threshold configuration, original windows/query/revisions/sampling/limits/coverage, original source capture/publication/measurement/import times and governed evidence. Complete synthetic fixture coverage is not complete market coverage or independent statistical proof. Inadequate/missing/partial/incomparable baseline has no numerical spike claim; missing engagement fields remain explicit and do not become zero metrics. Withdrawal, expiry or current process/display/retention denial withholds the whole numerical comparison while retaining historical alert identity/outcome and visible support limitations. Inbox messages contain no copied captions or source metrics. Source-free lineage and dynamic evidence rendering follow [the monitoring contract](monitoring.md#configured-quantitative-volume-assessments); no external notification transport is installed.

## Provisional semantic X assessments and alerts

**Recent X** links `/monitoring/semantic-assessments` independently of volume measurements. Trusted Python construction selects `monitoring_operator=True`, `monitoring_controversy_threshold=ControversyThreshold(...)` and the existing explicit shared `model_route`, `model_transport`, `model_credential` configuration. Default startup has no model route or semantic thresholds and enables no paid call. Migrations install semantic history with shared cost prerequisites; restart reads need neither model nor fixture access. The CLI can configure volume thresholds, while semantic model execution uses the trusted constructor.

| Route | Behavior |
| --- | --- |
| `GET /monitoring/semantic-assessments` | Latest 100 claims and operator/threshold-gated exact-window form |
| `POST /monitoring/semantic-assessments` | One bounded provisional quality-controversy assessment or saved no-call/failure outcome |
| `GET /monitoring/semantic-assessments/{id}` | Original method/model/bounds, all prepared input IDs/digest, exact governed excerpts, source timing/coverage and attributable cost |
| `GET /monitoring/semantic-alerts/{id}` | Exact retained semantic alert, with unavailable history preserved |
| `GET /inbox` | Distinct semantic/volume messages beside task completions, up to 100 notifications per method |

POST accepts only `window_id`, `request_id` and CSRF; current server actor, topic, threshold, model/rates, policy, tools and research authority cannot come from forms. Validation/conflict pages preserve only permitted escaped retry/window fields. GET reopens policy-aware history and makes no model or collection request. Identical retries and new requests for the same configured window never reissue, including after a lost response or failed final alert commit.

The page labels all positions as **provisional automated interpretations**, shows exact source spans with original governed excerpts, records no-baseline `change_status=not_assessed`, and distinguishes possible controversy from a quantitative measurement or independently verified sentiment. Labels and quotations establish neither semantic entailment nor Japanese-original/human usefulness. Original configuration, collection bounds, source times, incomplete/unknown market coverage, unresolved inputs and all method limitations remain inspectable. Missing comparison is never hidden behind a change claim.

Loss of any actual input, including unresolved text, withholds and permanently clears dependent judgments through the public reader. Retained outcome/alert identities remain visible with unavailable derived findings; retries and later support cannot recreate them. Inbox messages are fixed source-free provisional/unavailable templates, with no copied source wording. Model/accounting failure can retain real usage or uncertain liability independently of usable results. See [the owner contract](monitoring.md#bounded-provisional-quality-controversy-assessments). These local operations neither submit research/tasks nor create campaigns, expand topics or promote recent evidence into the KB.
