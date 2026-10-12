# Social Marketing Intelligence: local ingestion slice

This repository contains a local source-to-canonical ingestion foundation. Two **synthetic** formats exercise retained evidence, mapping, and canonical writes. A live TikTok oEmbed adapter resolves supplied public URLs without retaining TikTok-returned content. Experimental Bright Data and direct-web adapters are separate source routes for the local creator-evidence prototype; neither has yet passed a live ten-post creator comparison check. The fixture data is not evidence about a real creator.

For a visual code tour, open the [HTML architecture guide](docs/ingestion-architecture.html). The approved design and broader pilot context are in [the wayfinder map](.scratch/beauty-intelligence-pilot/map.md) and [source-to-canonical design](.scratch/beauty-intelligence-pilot/source-to-canonical-design.md).

## Run locally

You need Python 3.12+, `uv`, and Docker with Compose. The Compose database binds only to `127.0.0.1:6543`; its password is a local development placeholder. Set `SMI_DATABASE_URL` if using another local PostgreSQL instance. No TikTok login, paid API, cloud account, or LLM key is needed.

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

## Prototype creator-evidence routes

The Bright Data and direct-web adapters use separate manifests and preserve separate source provenance. The blank `BRIGHTDATA_API_TOKEN` entry in `.env.example` is a placeholder for Bright Data's API credential; the TikTok sandbox client key and secret cannot authenticate that provider. Do not paste actual key values into a manifest or commit them. With no Bright Data token, its adapter stops before any provider request. A live Bright Data call may consume account credits, so configure the provider's free tier or a hard spend cap first.

The local `.env` now has a Bright Data token, but two bounded profile calls for the supplied creator returned HTTP 400. A later direct API request returned `Customer is not active`, so account access remains unresolved. They produced no Bright Data creator rows. **Pause further Bright Data scrape calls** until the account is active and free-balance details are checked; the command below is for use after that issue is resolved.

```bash
uv run smi-ingest ingest examples/live/tiktok-web-manifest.json --max-requests 2
uv run --env-file .env smi-ingest ingest examples/live/brightdata-tiktok-manifest.json --max-requests 12
```

The web example uses the supplied profile and video references. A successful HTTP response can still be a bot challenge; the collector reports challenge and partial results explicitly. A persistent local run mapped the supplied video's post ID, caption, date, URL, and four public engagement counts; its profile fetch was challenged. No ten-post comparison has passed. Direct-web collection uses at most ten HTTP attempts per run, including one transient retry per reference, with an eight-second and 1 MiB response cap; it retains derived evidence but not raw page HTML.

Inspect that real post in the local database with:

```bash
uv run --env-file .env smi-ingest inspect tiktok web:public content 7632620458235530504
```

Bright Data uses at most two paid scrape requests per creator, up to three creators and ten requested posts each. A scrape can return a pending snapshot; if the CLI reports `partial` with `pending_snapshot` or `snapshot_running`, run `uv run --env-file .env smi-ingest resume RUN_ID` later (at least 30 seconds after `snapshot_running`) rather than starting a new ingest. The collector resumes with bounded progress and snapshot reads and never retries a paid scrape automatically. Its local policy retains successful provider responses for replay. Bright Data has documented profile and recent-post APIs, but no successful Japan sample is available in this workspace yet. Synthetic adapter tests verify parsing and bounds only. The [live sample ticket](.scratch/beauty-intelligence-pilot/issues/21-validate-bright-data-live-sample.md) and [fallback decision](.scratch/beauty-intelligence-pilot/issues/20-decide-tiktok-source-fallback-policy.md) remain open; these commands currently run routes separately and do not automatically choose between them.

For downstream work while Bright Data is unavailable, use the [curated Japanese K-beauty TikTok sample](examples/curated/jp-kbeauty-tiktok-2026-10-05/README.md). It includes a portable offline JSON snapshot of 19 real public video observations and three manifests that were successfully ingested through the direct-web adapter. The snapshot is a selected development sample with source URLs and capture times, not complete creator histories or Japan-audience evidence.

## Add a source

Create a collector that implements `Collector.collect` and a deterministic mapper that implements `Mapper.normalize` in `src/smi_ingestion/adapters/`. Register the pair with `AdapterRegistry.register`. The runner accepts a JSON acquisition request with an `adapter` key and passes the remaining configuration to the selected collector. A collector returns one bounded raw observation and an opaque next checkpoint per call. The mapper returns canonical candidates, field/metric provenance, and unresolved identities. Neither module writes canonical tables; `CanonicalWriter` owns those rules. Tests include a third synthetic collector whose request has no file `items`, demonstrating that the runner does not depend on the fixture manifest shape.

Every new route needs real response/schema tests, source-specific identity namespaces, and cost/limit measurement. The local prototype defers publication/use-rights review; it does not treat technical access as a release grant. No route is yet verified as a comparison-grade performance feed. The application intentionally does not infer audience location or sales from language, a title, or engagement.

## Local data

Raw payloads are stored under `.evidence/`, which is ignored by Git. PostgreSQL data lives in the Compose volume. `.env.example` shows local configuration; do not commit real credentials. Tests create and drop only their own uniquely named PostgreSQL schemas. `docker compose stop postgres` stops the local database while retaining its volume.
