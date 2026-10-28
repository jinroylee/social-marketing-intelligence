# Social Marketing Intelligence

The product supports evidence-backed market investigation and marketer-led campaign decisions. It acquires source observations, prepares supported caption interpretations, and saves independent snapshot investigations, campaign decisions, proposed measurement plans and human feedback over immutable evidence sets. A local browser exposes both workflows.

See the [product documentation](docs/README.md) for the accepted requirements, architecture, ERDs, interface contracts and ADRs. The [source integration guide](docs/source-integrations.md) records implemented acquisition capabilities and unresolved readiness work.

The local pilot includes bounded current-KB answers, exact human-approved assistant gap enrichment, task/schedule discovery, configured cost controls and bounded offline X evidence with configured volume and provisional quality-controversy alerts with local notifications and bounded existing-KB investigations, plus governed one-hop graph entity search and relationship details. The [target functional requirements](docs/functional-requirements.md) add broader autonomous research, semantic shift and broader explanation, multi-hop graph/lineage interfaces and broader operational control. The browser saves deterministic current-KB shortlists and, through explicitly configured model transport, bounded validated model-ordered shortlists automatically with actual automation attribution and no human review or approval; human selections remain a separate workflow.

Run `uv run --locked python tools/check.py` for lint, documentation consistency and tests. See [development verification](docs/development.md) for PostgreSQL prerequisites and static-only checks.

## Run locally

You need Python 3.12+, `uv`, and Docker with Compose. The Compose database binds only to `127.0.0.1:6543`; its password is a local development placeholder. Set `SMI_DATABASE_URL` if using another local PostgreSQL instance. No TikTok login, paid API, cloud account, or LLM key is needed.

If a local PostgreSQL instance already occupies that port, reuse it through the connection setting rather than starting another service. Tests create and drop their own isolated schemas.

## Import and inspect frozen evidence

After starting PostgreSQL, the default development workflow is entirely offline with respect to source providers and models:

```bash
uv sync
uv run smi-ingest migrate
uv run smi-ingest import-snapshot examples/curated/jp-kbeauty-tiktok-2026-10-05/snapshot-manifest.json
uv run smi-ingest inspect-set jp-kbeauty-tiktok-public-video-sample-2026-10-05
```

The import reproduces 19 selected posts from 17 accounts in a fresh database. Repeating it returns `duplicate`; changed content under the same dataset ID is rejected. Original capture times and source UUIDs are retained as lineage, with newly created local bindings. No live manifest is executed. The [evidence-set contract](docs/evidence-sets.md) describes provenance, permissions, exact support references and errors.

`inspect-set --purpose process` applies processing permissions; the default applies display permissions. Both reflect current expiry/revocation. Use `--actor NAME` for attributable local operator context. This CLI is a trusted local administration surface, not a hosted login system.

## Prepare shared knowledge

After importing the frozen sample, register the local catalog and prepare provisional caption interpretations:

```bash
uv run smi-ingest migrate
uv run smi-ingest register-catalog examples/catalogs/beauty-v1.json
uv run smi-ingest prepare-knowledge jp-kbeauty-tiktok-public-video-sample-2026-10-05 beauty-caption-lexicon-v1
uv run smi-ingest inspect-knowledge RUN_ID
uv run smi-ingest review-packet RUN_ID
```

Use the returned `run_id`. The rules identify literal mentions, kana script, topics and PR/Qoo10 markers with original caption spans. Interpretations remain provisional; translation and human evaluation fields are pending. Source policy is rechecked, with denied support redacted and withdrawn retained copies purged. See the [shared knowledge contract](docs/knowledge.md).

For an explicit new preparation after permissions recover, add `--request-id refresh-1` (or another new ID). Reuse that ID for retries; earlier runs retain their original results.

## Publish ingested knowledge

Publication is explicit and separate from fetching or interpretation preparation:

```bash
uv run smi-ingest publish-knowledge INGESTION_RUN_ID --request-id publication-1 --observation-id OBSERVATION_ID
uv run smi-ingest inspect-publication PUBLICATION_ID
```

The selection may come from a fresh ingestion or a frozen import. Repeat `--observation-id` to choose a subset, or omit it to select the bounded run; add `--interpretation-id` for an existing supported caption interpretation. The CLI records its named human operator, while workers use their actual automation context. The browser's **Knowledge** link reopens exact committed support under current policy. See the [publication contract](docs/knowledge.md#explicit-knowledge-publication).

Search committed permitted knowledge and reopen the exact saved support:

```bash
uv run smi-ingest search-knowledge --text APRILSKIN --platform tiktok --max-age-seconds 604800 --request-id search-1
uv run smi-ingest inspect-query RESULT_ID
```

The browser’s **Ask knowledge** link accepts free-form questions through a bounded extractive model selection over current published support. It shows exact findings/dates, full input/model context and missing/stale/ambiguous limits, with no enrichment approval required to read existing knowledge. A supported gap offers separate exact keyword/subject/time scope, saved proposal review, actual human approval and task/completion follow-up; only a later explicit question can use newly published updates. Explicit trusted model configuration is required; default startup shows unavailable configuration. Reopening applies current policy without redispatch. See [the answer contract](docs/knowledge.md#bounded-free-form-knowledge-answers) and [the enrichment journey](docs/tasks.md#assistant-knowledge-gap-enrichment).

The browser’s **Knowledge search** link provides the same bounded filters, capture-age freshness, unknowns and saved result. New searches require process permission plus their output-purpose permission; reopening applies current read policy without changing membership. At most 100 recent publications and 100 support members are included, with scan/result truncation explicit. Semantic search remains future work; campaign model ranking is a separate bounded operation verified with simulated I/O, and bounded [campaign and approved-proposal offline tasks](docs/tasks.md) is installed. See the [query contract](docs/knowledge.md#bounded-current-knowledge-queries).

## Offline acquisition tasks

For an existing campaign and its current brief, configure a synthetic local manifest and acknowledge work before running it separately:

```bash
uv run smi-ingest submit-campaign-task CAMPAIGN_ID --brief-id BRIEF_ID --purpose "Fill campaign coverage" --request-id task-1 --offline-manifest examples/synthetic/json-manifest.json
uv run smi-ingest inspect-task TASK_ID
uv run smi-ingest run-offline-task TASK_ID --worker-id local-offline-task-worker
```

Start the browser with `smi-review --offline-manifest examples/synthetic/json-manifest.json` to expose the campaign submission form. **Tasks** reopens exact scope, actors, limits, runs and publication outcomes after restart. The **Proposals** form saves supplied purpose, refresh/fill/expansion intent and subject/search scope for exact named-human approval before one task is submitted. Proposal/task pages retain scope, approval and attribution after restart. CLI `save-proposal`, `inspect-proposal`, `approve-proposal --approve-exact-scope` and `submit-approved-task` provide the same separated actions. Repeat `run-offline-task` with the same ID to resume committed work. Valid subsets publish as partial updates with explicit gaps; simulated pending/ambiguous operations expose waiting status. Competing workers use per-task PostgreSQL ownership sessions and fence late local writes after disconnect. This path is fixture-json-only; conversation generation, live acquisition and monetary admission remain separate work. **Inbox** reopens durable usable/partial/no-update/failure completions with actual coverage and current-policy publication links; `list-inbox`, `inspect-completion EVENT_ID` and `reconcile-completions` provide the same local operator surface. See [the task contract](docs/tasks.md). **Costs** reopens operator-configured synthetic usage, attributable task/model operations, forecasts, declared commitments and explicit unknown/meter-failure coverage. Configure/record through [the public accounting operations](docs/costs.md); there are no commercial charges or enforced monetary ceilings.

## Campaign persistence

Use the [sample brief](examples/campaigns/hero-cushion-brief.json) after preparing knowledge. `start-campaign`, `prepare-comparison` and `save-shortlist` persist exact revisions in PostgreSQL; `inspect-campaign`, `inspect-comparison` and `inspect-shortlist` reopen them. Saves require request IDs, shortlist saves require an expected version, and `--confirm` records a human-confirmed revision. The [campaign contract](docs/campaigns.md) describes the commands, selection JSON and evidence/unknown requirements.

## Campaign browser review

After migrating, importing the frozen sample and registering its catalog, run:

```bash
uv run smi-review --actor local-marketer
```

Open `http://127.0.0.1:8765` to create a brief, prepare a rule-based comparison, inspect original captions/provenance, save a draft and explicitly confirm a shortlist. Campaign history reopens exact revisions after server restarts. Translation and semantic review remain provisional. See the [local review contract](docs/local-review.md) for setup, versions, actors and source-policy behavior.

**Investigations** saves independent product/topic questions and pinned literal snapshot findings without creating campaigns. The campaign's **Measurement plans and decision notes** page saves proposed outcome definitions/prerequisites and attributable feedback, with no fabricated commercial results. See [monitoring](docs/monitoring.md), [planning](docs/planning.md) and the [quality review procedure](docs/evaluation.md).

## Synthetic ingestion checks

```bash
docker compose up -d --wait postgres
uv sync
uv run smi-ingest migrate
uv run smi-ingest ingest examples/synthetic/json-manifest.json
uv run smi-ingest ingest examples/synthetic/html-manifest.json
uv run smi-ingest inspect tiktok fixture:public content fixture-post-1 --include-synthetic
uv run pytest -q
```

The two fixture ingests create **one** canonical content identity with two source observations. The inspected content shows each field's source and two dated `synthetic.views.v1` measurements. Without `--include-synthetic`, inspection hides fixture evidence. The supplied real TikTok URL was separately resolved through TikTok oEmbed; its response was not mixed with the synthetic examples or written as canonical creator evidence.

Run `uv run smi-ingest migrate` when updating an existing database. The migration adds a durable input-completion flag while preserving existing runs and evidence. Newly saved final captures can resume at their request/record limit without another collector call; canonical application and its completion marker commit together.

An ingest result includes a `run_id`, `status`, requested-input coverage, counts, missing fields, unresolved identities, latest source capture time, limits, and sanitized issues. `complete_for_requested_input` means the provided manifest was processed; it makes no claim about platform-wide coverage. A partial run uses exit code 2.

To replay one retained observation, copy an `observation_id` from an `inspect --include-synthetic` result:

```bash
uv run smi-ingest replay OBSERVATION_ID
uv run smi-ingest resume RUN_ID
```

Replaying the same mapper version reports `duplicate` without adding another account, post, or metric measurement. A newer mapper version can supersede its earlier derivation for the same raw observation. A new collection run is a separate capture and may append a dated metric observation. Resume checks that the request file has not changed before using its stored checkpoint.

The evidence store checks payload hashes before replay. `revoke OBSERVATION_ID` or policy expiration removes an observation from current reads and replay. `expire` deletes payloads whose retention deadline has passed; `reconcile` removes old unreferenced evidence files left by an interrupted file/database write. Non-retained evidence can be processed once if its policy permits processing, but cannot be replayed.

## Resolve supplied TikTok URLs

TikTok [documents oEmbed](https://developers.tiktok.com/docs/en/embed-videos) for converting a supplied public video or profile URL into attributed embed data. With the local database migrated, run the live example:

```bash
uv run smi-ingest ingest examples/live/tiktok-oembed-manifest.json --max-requests 10
```

The example normally makes two network calls to TikTok's documented `/oembed` endpoint; transient retries can raise that to four. The adapter accepts only direct HTTPS TikTok video/profile URLs, normalizes away URL tracking parameters, and caps each run at ten references and ten HTTP attempts including retries, even if the CLI limit is raised. Each response has an 8-second timeout and 64 KiB maximum. A transient network/server failure gets at most one retry; a 429 stops the run without retrying. A 400/403/404/410 is recorded as `unavailable_or_private`, not as proof of deletion. The report includes `source_results` with per-URL outcome, mapping status, HTTP status, capture time, attempts, and fields oEmbed cannot supply. `requests_used` counts actual HTTP attempts.

For the local pilot, rerun the same command on demand or approximately once a week and compare the run reports. Each run is a new point-in-time URL check; it does not enumerate historical posts or schedule itself while the machine is off. The profile embed may render follower figures in a browser, but those are **not** machine-readable fields in the oEmbed JSON and this adapter never parses rendered markup or ordinary TikTok pages.

The fixed `tiktok-oembed-reference-only` policy passes the response transiently to a validating mapper. PostgreSQL retains only the supplied canonicalized URL, operational outcome/timing, a one-way payload hash, and generic identity uncertainty; no raw response, title, author name/URL, thumbnail, embed HTML, account identity, post assertion, or engagement metric is stored. Replaying these non-retained responses is unavailable. TikTok's documented embed use does not establish permission for a commercial historical creator database; any broader retention or comparison-grade collector needs its own access and use-rights review. No developer login, paid API, cloud server, or LLM key is required for this narrow local check.

## Explicit live-source operations

The Bright Data and direct-web adapters use separate manifests and preserve separate source provenance. The blank `BRIGHTDATA_API_TOKEN` entry in `.env.example` is a placeholder for Bright Data's API credential; with no token, the adapter stops before any provider request. Keep actual credentials outside committed files. These operations make live requests and may consume provider credits. They are separate from the default offline workflow and require source-specific access and policy configuration.

```bash
uv run smi-ingest ingest examples/live/tiktok-web-manifest.json --max-requests 2
uv run --env-file .env smi-ingest ingest examples/live/brightdata-tiktok-manifest.json --max-requests 12
```

The web collector reports bot challenges and partial results explicitly, even when HTTP succeeds. It uses at most ten HTTP attempts per run, including one transient retry per reference, with an eight-second and 1 MiB response cap; it retains derived evidence but not raw page HTML. Successfully reading individual posts does not establish complete creator history.

Bright Data uses at most two paid scrape requests per creator, up to three creators and ten requested posts each. A scrape can return a pending snapshot; if the CLI reports `partial` with `pending_snapshot` or `snapshot_running`, run `uv run --env-file .env smi-ingest resume RUN_ID` later (at least 30 seconds after `snapshot_running`) rather than starting a new ingest. The collector resumes with bounded progress and snapshot reads and never retries a paid scrape automatically. Its local policy retains successful provider responses for replay. Routes run separately; no automatic provider fallback is implemented. Adapter tests establish parsing and bounds, not live source coverage.

The [curated Japanese K-beauty TikTok sample](examples/curated/jp-kbeauty-tiktok-2026-10-05/README.md) is the default input for downstream development. Its source URLs and capture times support selected post evidence; complete creator histories and audience geography remain unknown.

## Add a source

Create a collector that implements `Collector.collect` and a deterministic mapper that implements `Mapper.normalize` in `src/smi_ingestion/adapters/`. Register the pair with `AdapterRegistry.register`. The runner accepts a JSON acquisition request with an `adapter` key and passes the remaining configuration to the selected collector. A collector returns one bounded raw observation and an opaque next checkpoint per call. The mapper returns canonical candidates, field/metric provenance, and unresolved identities. Neither module writes canonical tables; `CanonicalWriter` owns those rules. Tests include a third synthetic collector whose request has no file `items`, demonstrating that the runner does not depend on the fixture manifest shape.

Every new route needs real response/schema tests, source-specific identity namespaces, and cost/limit measurement. The local prototype defers publication/use-rights review; it does not treat technical access as a release grant. No route is yet verified as a comparison-grade performance feed. The application intentionally does not infer audience location or sales from language, a title, or engagement.

## Local data

Raw payloads are stored under `.evidence/`, which is ignored by Git. PostgreSQL data lives in the Compose volume. `.env.example` shows local configuration; do not commit real credentials. Tests create and drop only their own uniquely named PostgreSQL schemas. `docker compose stop postgres` stops the local database while retaining its volume.
