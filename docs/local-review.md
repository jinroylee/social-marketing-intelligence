# Local marketer review

[`smi_review`](../src/smi_review/__init__.py) provides independent investigation and campaign workflows over public monitoring, campaign/planning, knowledge and frozen-evidence interfaces. PostgreSQL owns saved revisions; browser state is not durable.

This document describes the current local browser, including its human-only shortlist saves. The [target operational UI](functional-requirements.md) will add automatically saved ranked recommendations without human review/approval, an enrichment assistant, tasks/notifications, X alerts and graph/lineage explorers. Those routes and controls do not exist yet.

## Knowledge search

The navigation links `GET /knowledge/search`, a bounded literal query form with text, platform, subject UUID and capture-time filters, an optional freshness threshold and a 1–100 member limit. **Search and preserve result** submits a same-origin CSRF-protected `POST /knowledge/search`, then redirects to `GET /knowledge/results/RESULT_ID`. New computation requires process permission and display permission through `KnowledgeQueries`; the browser supplies neither actor identity nor process authority. No external research or approval is triggered.

A result page reopens exact actual support after restart and shows its producer, query method, original scope/coverage, publication and source versions, individual missing fields and current health. Capture-age freshness remains separate from withdrawal/supersession. Results show both publication-scan and result truncation, with an explicit incomplete-market-coverage limit. Later publications can appear in a new search while an old result keeps its membership. Denied/superseded sources display IDs and status without source text. Synthetic inputs require the explicit development checkbox and `?include_synthetic=yes` on reopening. See the [query contract](knowledge.md#bounded-current-knowledge-queries) for limits and filter semantics.

## Knowledge publications

The main navigation links `/knowledge/publications`, which lists only committed, nonsynthetic publications in the local workspace. `/knowledge/publications/PUBLICATION_ID` reopens the exact selected observations, derivations, assertion/metric IDs and optional existing caption interpretations. It shows actual producer, publication/source times, mapper and interpretation versions, original coverage, current support health and unknown fields. Denied or superseded support displays metadata without source text; later publications do not replace this historical selection.

Publication is an explicit trusted operation through `KnowledgePublications.publish` or the `smi-ingest publish-knowledge` CLI described in the [knowledge contract](knowledge.md#explicit-knowledge-publication). Reading a detail page does not acquire evidence or publish anything. Existing form protections and actor boundaries apply unchanged.

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

From a campaign, open **Measurement plans and decision notes**. A proposed plan pins the current brief and a relevant saved shortlist, with source/owner, product/listing/currency, period/baseline, matching/attribution and gaps. A note records human feedback for any relevant historical shortlist. Plans remain proposed with no outcomes; notes inherit selected-source policy. Separate expected version heads and request IDs protect both histories. See [planning](planning.md).

## Save, failure and support behavior

Forms carry a stable request ID and the expected prior version. Successful actions redirect to the saved database record. Retries return the original revision; stale or changed requests fail visibly. Recoverable brief/selection errors preserve submitted edits and their original expected version, so a conflict cannot silently become an overwrite. Open the campaign history to review the current head before making a successor save.

Rendering uses current display-policy readers. Denied/superseded candidate support withholds captions, copied explanations and saved reasons. A retention withdrawal purges copies through campaign/knowledge reconciliation. An error page also withholds source-dependent submitted reasons when support is unavailable. Selected references and reviewer metadata remain; a permission recovery does not reconstruct purged explanations. The [campaign contract](campaigns.md) defines the durable policy/version invariants.

The server accepts only its loopback Host, same-origin form writes and its CSRF token. Requests have bounded body/field counts; data is HTML-escaped, source links are limited to HTTP(S), and responses use `no-store` and a restrictive content policy. Static routes serve only bundled CSS/JavaScript. A server restart rotates the form token: reopen the saved record to obtain a new form. These are local application boundaries; remote hosting/authentication is not implemented.

Responses use `Referrer-Policy: same-origin`: same-origin form submissions retain the Origin required by the server, while external navigation receives no referrer. `no-referrer` would serialize non-CORS form POST origins as `null` under the [Fetch Origin-header algorithm](https://fetch.spec.whatwg.org/#append-a-request-origin-header). Null and foreign origins remain rejected; they are not exceptions to the same-origin check. Reload forms after a server policy change to obtain the current document policy and token.

HTTP boundary errors explain that the request was not saved and provide **Open campaign workspace** and **Create a brief** recovery actions. These links use the server's configured loopback address, independently of submitted Host, Origin, Referer or path values. Rejected form contents are not reflected or automatically resubmitted.

## Implemented routes and ownership

| Route | Purpose |
| --- | --- |
| `GET /knowledge/search`, `POST /knowledge/search`, `GET /knowledge/results/{id}` | Bounded knowledge query and exact saved support under current display policy |
| `GET /knowledge/publications`, `GET /knowledge/publications/{id}` | Committed publication metadata and exact permitted support |
| `GET /` | Workspace campaign heads and loaded input metadata |
| `GET /campaigns/new`, `POST /campaigns` | Human brief form and campaign start |
| `GET /campaigns/{id}`, `GET /campaigns/{id}/edit`, `POST /campaigns/{id}/briefs` | Current brief, history and successor brief |
| `POST /campaigns/{id}/comparisons` | Rule-based knowledge/comparison preparation |
| `GET /comparisons/{id}` | Exact comparison, current evidence and versioned selection form |
| `POST /comparisons/{id}/shortlists` | Unconfirmed draft or explicit human confirmation |
| `GET /shortlists/{id}` | Exact saved revision with current support health |
| `GET /investigations`, `GET /investigations/new`, `POST /investigations` | Independent investigation list and human scope creation |
| `GET /investigations/{id}`, `GET /investigations/{id}/edit`, `POST /investigations/{id}/scopes` | Scope/answer history and revised question |
| `POST /investigations/{id}/insights`, `GET /insights/{id}` | Rule-based snapshot preparation and permitted finding panels |
| `GET /campaigns/{id}/planning`, `POST /campaigns/{id}/plans`, `POST /campaigns/{id}/notes` | Proposed measurement and human feedback revisions |

`CampaignStore.list_campaigns` and the comparison/shortlist metadata in `read_campaign` provide navigation without copied reasons. `KnowledgeStore.list_catalogs` lists human configuration. `EvidenceSetReader.list_sets` lists dataset metadata and excludes synthetic data by default. Each interface checks the configured workspace. The application does not query or write another module's tables.

The HTTP boundary returns visible validation errors, `409` version/request conflicts, `404` missing records and sanitized `503` database/setup failures. Host/origin failures use `403`; oversized/unsupported request bodies use `413`/`415`. Domain-store checks remain authoritative after every form submission.

## Accepted future application surfaces

Campaign results show ranked KB-backed accounts, supporting rationale, unknowns/freshness and automatic save attribution. Saving does not require a human approval checkbox. Optional human curation/review is distinct. Insufficient coverage shows the automatically queued discovery status; completion offers explicit regeneration rather than replacing the saved result.

The assistant accepts free-form KB questions and displays scoped enrichment proposals for approval. Approval precedes task submission and binds its scope server-side. Show acknowledgment/status and completion notifications; answers use published knowledge rather than raw newly fetched tool responses. Spending-ceiling pauses and partial/failed ingestion are visible independently of approval state.

An X alert surface shows recent-window findings, existing-KB context, detection/support history and uncertainty. A graph explorer searches, filters and traverses permitted entities/relationships with source details. A pipeline/lineage view connects tasks, attempts, runs, failures, observations, transformations, KB publications and attributable cost information. These are product requirements, not names for existing hidden screens.

## Offline acquisition submission and status

Start with `smi-review --offline-manifest examples/synthetic/json-manifest.json` to configure the only supported task route: local synthetic fixture JSON. A campaign links `/campaigns/CAMPAIGN_ID/tasks/new`; the form displays exact current brief, configured references, digest and limits. `POST /campaigns/CAMPAIGN_ID/tasks` accepts purpose/request identity/current brief only. The server constructs its named human actor and campaign origin; supplied origin, actor, approval or collector fields are rejected. Existing Origin/Host/CSRF protection applies. Submission redirects immediately to `/tasks/TASK_ID` without fetching.

`/tasks` lists at most 100 newest workspace tasks. Details survive restart without configured route access and distinguish queued/collecting/ingesting/publishing phases, usable update, no usable update and failure, with actual counts, worker/run IDs and synthetic publication links. Run `smi-ingest run-offline-task TASK_ID` separately to execute at most one admitted task. Published source values reopen through current policy; task pages hold no copied source text. Assistant approval, recovery/partial completion, notifications and spending are subsequent work. See [the owning task contract](tasks.md).
