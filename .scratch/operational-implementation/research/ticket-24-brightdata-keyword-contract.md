# Ticket 24: Bright Data TikTok keyword contract

Verified **2026-10-23**, Asia/Seoul (UTC clock also 2026-10-23). Read-only unauthenticated primary-document requests only. No provider scrape, model call, credential inspection, account action or paid operation occurred. All runtime responses below are simulated test data, not live receipts.

## Selected contract and exact primary sources

- [Documentation index](https://docs.brightdata.com/llms.txt) points to the public dataset catalogue and individual schemas, avoiding guessed IDs. [TikTok catalogue](https://docs.brightdata.com/scrapers/tiktok.com.json) and [individual TikTok Posts schema](https://docs.brightdata.com/scrapers/gd_lu702nij2f790tmv9h.json) identify `gd_lu702nij2f790tmv9h`, `discover_by_keyword`, required `search_keyword`, optional `num_of_posts`. This is distinct from supplied-profile Fast API `gd_m7n5v2gq296pex2f5m`.
- [Synchronous requests](https://docs.brightdata.com/api-reference/scrapers/synchronous-requests.md) describes Bearer authentication and JSON `POST https://api.brightdata.com/datasets/v3/scrape`, `dataset_id`, `type=discover_new`, `discover_by=keyword`, `format=json`, `include_errors=true`, and body `{input:[...],limit_per_input:1}`. A 200 returns records; after the documented 60-second wait, 202 returns `snapshot_id` and a seconds-valued `Retry-After`. Software uses one input, `num_of_posts=1`, a finite 75-second socket timeout and an 8192-byte request-body ceiling.
- [Asynchronous request contract](https://docs.brightdata.com/api-reference/rest-api/scraper/asynchronous-requests.md) verifies `keyword` as the discovery method and `limit_per_input` as the per-input returned-result cap. Software uses the synchronous entry point only, never an extra trigger, fallback or rerun endpoint.
- [Monitor progress](https://docs.brightdata.com/api-reference/scrapers/management-apis/monitor-progress.md) documents `GET /datasets/v3/progress/{snapshot_id}` and snapshot/dataset/status fields. [Download snapshot](https://docs.brightdata.com/api-reference/scrapers/delivery-apis/download-snapshot.md) documents `GET /datasets/v3/snapshot/{snapshot_id}?format=json`, retrieving an existing job. `starting`/`running` retain pending status, `ready` permits download; download HTTP 202 (not ready/building) retains the same snapshot/download phase and retry delay; and `failed`/`canceled` are terminal source failures. Unknown/mismatched states remain ambiguous. Each worker invocation makes at most one HTTP request. The source checkpoint retains the validated handle, phase, monotonic step and not-before time. Seconds-valued Retry-After is honored; absent delay defaults conservatively to ten seconds. Invalid/out-of-supported-range delays stop as ambiguous, never shorten provider delay.
- [Scraper FAQs](https://docs.brightdata.com/products/scrapers/scrapers-library/faqs.md) distinguishes discovery-only URL results from normal discovery followed by collection. The keyword schema itself guarantees only `url`/`discovery_input` output fields; full post fields are listed under `collect_by_url`. The mapper therefore conditionally validates full post fields and fails URL-only/minimal rows accurately rather than inventing native author IDs, caption, creation/capture times or engagement. Numeric post/profile IDs and a consistent HTTPS TikTok URL/optional username are mandatory for publication. Captions and creation times support local all-term/half-open-window filtering; approved subject IDs are investigation context, not source product assertions. No country/market inference is made.

## Charging and evidence limits

The [FAQs](https://docs.brightdata.com/products/scrapers/scrapers-library/faqs.md) describe per-delivered-record billing including incorrect-input failures. They do not provide a final charge/invoice response, independently verified rates, a finite billing-lag bound, paid-operation idempotency key, or a guarantee that a timeout is uncharged. The result cap bounds accepted records, not independently verified commercial liability. Every HTTP attempt conservatively reserves the configured shared one-unit declared commitment before dispatch. No source response fabricates billed units, charges or zero; all commitments remain dispatched/awaiting-final-measurement until explicit provider-basis final reconciliation. A timeout or lost response pauses the same stable operation. Accounting reconciliation never restores a missing response or grants a new POST.

The source schema provides post creation time but no guaranteed original capture/metric measurement timestamp. Both remain unknown. Retrieval time is separate metadata and cannot establish freshness. History is the existing exact query/context/mapper/publication seam; unknown capture prevents a fresh skip. No pinned offline response identity is attributed to future live results.

[Provider limits](https://docs.brightdata.com/products/scrapers/limits.md) describe the provider's much broader platform limits; software additionally accepts at most one row, reads less than a 65536-byte response cap (an exact-cap response is conservatively rejected), and persists no-observation response bytes against the task's cumulative byte budget. Existing independently pinned request/page/record limits remain active; no poll loop, redirect, retry, cancellation or rerun is hidden in transport.

## Runtime prerequisites and verification boundary

Explicit process enablement, exact human task approval, source-use authorization, live-operation authorization, credentials, current source policy and persisted provider-basis cost route/ceiling configuration are separate prerequisites. Review-server enablement permits admission only; the separate worker requires its own gates. Schedules remain offline. These prerequisites are **not verified in this implementation**. Tests use dummy secrets, isolated PostgreSQL and interception at urllib's external HTTP boundary. They prove local software behavior only, with no live-readiness, actual charge, market-completeness, language-quality or marketer-usefulness claim.

Raw primary documentation copies are retained under `/tmp/smi-ticket-24-primary-{0,1,2,3}.txt` and `/tmp/smi-ticket-24-{async,tiktok,progress,snapshot,dataset}.txt`; source fingerprints are appended below for audit.

- `primary-0`: 42351 bytes, SHA-256 `3a560ba5eb36cf94821773cde9f1ef180d3b96011209ad6627d142e2ec7c3436`.

- `primary-1`: 14794 bytes, SHA-256 `be95071846817358f6ef018314162c7bc96048275045a9d1910c4cfb5b15214e`.

- `primary-2`: 14001 bytes, SHA-256 `05a5cb2760daa068159aeaae47b5756733356ecb8cdbf61115be24a8424e022d`.

- `primary-3`: 4769 bytes, SHA-256 `b1b69f9eb41d243cf4fdd06e4ebb529a5ae58a5aade034bc84329273470b6ae0`.

- `async`: 18219 bytes, SHA-256 `5e79f2288126b2d20787ccb9935b6c21b9102ccfd11cf565489999899079968a`.

- `tiktok`: 22750 bytes, SHA-256 `7d00a64639388d1f026e4fef01ba1750c008e721d9618d26d0f474dab474c5df`.

- `progress`: 5054 bytes, SHA-256 `605bd7e3cc551363be9034a0d2378baa8e3b9af9b448dc7103df1f0e0d0947a1`.

- `snapshot`: 52254 bytes, SHA-256 `2d54b626e29974864db5e6f809b989526f89926a0ad4ce90abfe9accc3ec81c3`.

- `dataset`: 7372 bytes, SHA-256 `dd96dae72c61670d614bd39eeee97a55f6bba7d0bf1779bba4e3ede7e8f05457`.
