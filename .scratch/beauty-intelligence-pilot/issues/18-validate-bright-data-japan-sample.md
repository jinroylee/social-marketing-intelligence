# Implement a bounded Bright Data TikTok adapter

Label: wayfinder:task
Type: task
Mode: AFK
Status: resolved
Assignee: Codex / Bright Data agent
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 17

## Question

Implement the first Bright Data profile-by-URL and posts-by-profile adapter for known TikTok creators, using the existing collector/mapper seam. The builder chose this provider as the primary technical source for the unpublished prototype. The separate API credential may be absent for now: document a blank environment-variable placeholder and make missing credentials fail clearly before a network request. Never use or print the TikTok sandbox client key/secret for Bright Data.

Use the [technical validation protocol](../research/17-source-validation-protocol.md) and [endpoint mechanics](../research/17-sandbox-and-provider-ops.md). Bound references, requested post count, requests, time, bytes, retries and monetary exposure; do not retry paid calls blindly. Model provider errors, partial rows and missing fields explicitly. Keep account/post IDs separate from mutable handles and tag every observation with provider, capture time, data version and source policy. Add synthetic-response tests for mapping, limits, idempotence and absent credentials. Actual Japan field coverage, refresh consistency and charges remain for [Validate a Bright Data Japan profile and post sample](21-validate-bright-data-live-sample.md).

## Answer

Implemented the bounded [Bright Data collector/mapper](../../../src/smi_ingestion/adapters/bright_data.py), registered it with the ingestion runner, and added the [one-profile, ten-post example](../../../examples/live/brightdata-tiktok-manifest.json). `BRIGHTDATA_API_TOKEN=` is blank in both `.env.example` and the local `.env`; a missing token yields `missing_brightdata_api_token` with zero provider requests. The TikTok sandbox credentials are never used for this adapter.

The collector accepts at most three direct profile references and ten requested posts each, with at most six paid scrape POSTs, bounded progress/snapshot GETs, fixed time and response-byte caps, and no automatic retry of a paid POST. HTTP 202 stores a snapshot checkpoint; a later resume can poll progress and retrieve the result without reissuing the scrape. Outcome, dataset/phase, row/error counts, capture time, format version and fixed local-prototype policy are recorded. The mapper keeps stable numeric IDs separate from handles, rejects mismatched ownership, accepts only returned matching TikTok post permalinks, and leaves absent fields explicit. [Adapter tests](../../../tests/test_bright_data.py) cover bounds, missing credentials, partial/error rows, snapshot resume, mapping and replay. The full suite passes (65 tests); a local blank-token CLI check made zero provider requests.

This resolves adapter implementation only. Actual Japanese creator coverage, field shape, refresh consistency and billed cost are unverified because no Bright Data token was supplied. Those checks remain in [Validate a Bright Data Japan profile and post sample](21-validate-bright-data-live-sample.md). Before a paid live call, set a provider-side free-tier or spend limit.
