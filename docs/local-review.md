# Local marketer review

[`smi_review`](../src/smi_review/__init__.py) provides independent investigation and campaign workflows over public monitoring, campaign/planning, knowledge and frozen-evidence interfaces. PostgreSQL owns saved revisions; browser state is not durable.

This document describes the current local browser, including automatic deterministic and bounded model-ordered shortlist saves and separate human selections. The [target operational UI](functional-requirements.md) will add an enrichment assistant, X alerts and graph/lineage explorers.

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

The assistant accepts free-form KB questions and displays scoped enrichment proposals for approval. Approval precedes task submission and binds its scope server-side. Show acknowledgment/status and completion notifications; answers use published knowledge rather than raw newly fetched tool responses. Spending-ceiling pauses and partial/failed ingestion are visible independently of approval state.

An X alert surface shows recent-window findings, existing-KB context, detection/support history and uncertainty. A graph explorer searches, filters and traverses permitted entities/relationships with source details. A pipeline/lineage view connects tasks, attempts, runs, failures, observations, transformations, KB publications and attributable cost information. These are product requirements, not names for existing hidden screens.

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

Start with `smi-review --schedule-operator --offline-manifest examples/synthetic/keyword-discovery-manifest.json --offline-route-version offline-keyword-v1` to grant the named local human the schedule operator role. Default startup does not grant this role. `/schedules` displays the explicitly offline route, disabled live activation, immutable settings/history and current task links; it remains independent of monitoring. The operator can save timezone/daily local time/lookback/allowance and up to ten keyword JSON objects with stable keys, literal queries and explicit subjects. Stale versions preserve escaped submitted edits; authority/route/origin/clock fields are rejected. Initial UI suggestions are UTC, 09:00, seven calendar days and an allowance of 50; these become authority only after an explicit save. The timezone is fixed on the first save.

`POST /schedules/tick` acknowledges due tasks using only the server clock/configured human and CSRF token. It never executes the worker; use the existing separate bounded task command for each link. Repeated or concurrent ticks preserve task identity/status, earlier missed dates are not replayed, and refusals remain visible for that keyword/day. The configurable daily new-post admission allowance is atomically enforced at scheduled canonical ingestion. The panels distinguish used/remaining allowance, known refreshes, deduplicated identities and exclusions from throughput, costs, request counts and per-keyword yield. Existing same-origin/Host/CSRF controls apply to both POSTs. No daemon, provider activation or external cron is configured. See [the owning contract](tasks.md#registered-offline-keyword-schedule).

The registered offline schedule and task detail panels show the shared day’s configured new-post limit, used/remaining allowance, deduplicated/known-refresh/ineligible/limit-excluded counts and actual task limits. Fewer records can result from overlap, source coverage, invalid/denied records or independent caps. A cap decrease preserves earlier usage; task authority remains immutable while the separate allowance panel reopens current enforcement. See [the schedule contract](tasks.md#registered-offline-keyword-schedule).

Task details show discovery retrieval history, decision-time freshness/policy, exact query/processing context and governed capture identity/time metadata. Prior task/publication navigation is labeled separately from this task's actual publication links. A skip explicitly reports that it created no new publication; current permissions may withhold its old basis. Policy and processing revision are trusted Python configuration, absent from submitted form fields. See [capture-based avoidance](tasks.md#capture-based-discovery-avoidance).
