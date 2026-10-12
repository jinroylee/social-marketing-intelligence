# Validate a Bright Data Japan profile and post sample

Label: wayfinder:task
Type: task
Mode: HITL
Status: resolved
Disposition: out-of-scope
Assignee: Codex / brightdata_scope
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 18

## Question

When the builder supplies a Bright Data API key through the local environment, run the smallest bounded live sample through [Implement a bounded Bright Data TikTok adapter](18-validate-bright-data-japan-sample.md). The TikTok sandbox app credentials cannot authenticate this provider. Configure the free tier or an explicit hard spend cap before calls; stop if a paid commitment is required without authorization.

Start with the supplied `@maronayannyan` profile and up to ten recent posts. Record actual profile/post schema, IDs, ownership of the supplied video, publication and capture times, counts, missing/partial/error rows, request/record usage and charges. Repeat after a known interval, then test two additional marketer-selected Japanese beauty creators for coverage. Compare against the [technical validation protocol](../research/17-source-validation-protocol.md) and record what the source can and cannot establish. Do not label a synthetic test or API documentation as live comparison-grade evidence.

## Answer

Deferred without successful execution following the builder's choice to continue ontology and agent development on the fixed local dataset and revisit actual sources later. The scope closure was recorded during the 2026-10-12 parallel Wayfinder pass. Bright Data remains blocked by the reported `Customer is not active` response; creator profile/recent-post coverage, repeatability, usage, and charges are unvalidated. The fixed 19-post sample is development evidence only and does not satisfy this ticket.

This task belongs to a later source-readiness effort rather than the current fixed-sample build-ready specification. Resume that effort with the activation, quota, bounded capture, repeatability, and additional-creator checklist recorded below. No new provider call was made for this scope closure.

## Progress — 2026-09-30

The builder supplied `BRIGHTDATA_API_TOKEN` in the local `.env`; its value was not printed or retained. A read-only progress request for a nonexistent snapshot returned 404 rather than an authentication error. Two bounded profile scrapes for the supplied `@maronayannyan` URL returned HTTP 400 before any posts request: run `e38e67d3-7ace-4d58-ab08-4d6162f7ce53` at 05:04 UTC used the API-reference `{"input":[...]}` body; run `31cbe4c3-27f4-4d03-b0b3-2ea7c0c9d1e5` at 05:05 UTC used the TikTok endpoint guide's top-level array. Each run used one request, stored an operational observation, and produced no canonical Bright Data account or post. The provider's error text was not retained, and whether either failed request consumed free credits is unknown. No further paid scrape requests should be made until the builder supplies the dashboard error and confirms remaining free credits and a zero-spend setting. The [profile API reference](https://docs.brightdata.com/api-reference/scrapers/social-media-apis/tiktok-profiles-collect-by-url) and [TikTok endpoint guide](https://docs.brightdata.com/products/scrapers/tiktok/send-first-request) currently show different request body shapes.

The separate direct-web run `d56b3bd7-76c6-463b-9949-936786dc119d` seeded the persistent local database with the supplied video's post ID, caption, publication time, URL and four public engagement counts; the profile request was challenged and yielded no recent-post list. This is a useful real-data fixture for downstream code, not the ten-post comparison-grade Bright Data sample requested here.

The builder clarified that only the Bright Data account and API key were created, so an [account setup guide](../brightdata-setup-guide.md) and [interactive checklist](../brightdata-setup-wizard.sh) now cover the key, free-balance check, dataset IDs, and a single optional diagnostic request that prints the provider error without exposing the key. No further live scrape was sent during this documentation step. The ticket remains open until the free balance and exact HTTP 400 error are known, then a successful profile-plus-post sample is captured.

The builder subsequently reported that a direct `/datasets/v3/scrape` request with the TikTok comments dataset returned `Customer is not active`. This is a likely account-status block; the exact provider conditions are not documented. The setup guide now directs the builder to check account verification/onboarding and contact Bright Data support if needed, then defer all further scrape requests until the account is active. The comments dataset differs from the profile and posts-by-profile datasets required by this ticket.

## Progress — 2026-10-12 source deferral review

The builder explicitly deferred actual source work on 2026-10-05 so ontology and agent development could proceed against a fixed local sample. The [curated Japanese K-beauty TikTok sample](../../../examples/curated/jp-kbeauty-tiktok-2026-10-05/README.md) contains 19 observed public video pages from 17 accounts and is available offline. It does not provide creator profiles, about ten recent posts per creator, repeat captures, audience geography, or sales outcomes, and it does not validate Bright Data. This review made no provider request, did not inspect secret values, and did not change the established source acceptance threshold.

The adapter implementation, example manifest, setup guide, and validation protocol already exist. The remaining work requires an active provider account, confirmed free quota with zero paid exposure, and two additional marketer-selected creators. Consequently there is no further agent-doable live-validation step under the current source pause. Being unblocked by another ticket does not remove these external prerequisites. The downstream [source fallback and evidence reconciliation decision](20-decide-tiktok-source-fallback-policy.md) still lacks the measured live sample it requires; a fixed post sample must not be substituted for it.

### Eventual resumption checklist

1. The builder reopens source-readiness work, confirms the provider account is active, and checks current free credits and a zero-spend setting in the dashboard. Keep `BRIGHTDATA_API_TOKEN` in the environment; do not paste its value into tickets or manifests. Follow the existing [account setup guide](../brightdata-setup-guide.md) if access remains blocked.
2. Run the existing one-profile, up-to-ten-post [bounded manifest](../../../examples/live/brightdata-tiktok-manifest.json) for `@maronayannyan`. If the earlier HTTP 400 remains unexplained, use at most the guide's single diagnostic request after the account and quota checks. Record a redacted error and stop if access remains blocked; do not vary endpoints or retry paid POSTs blindly. Resume any accepted pending snapshot instead of triggering it again.
3. Capture actual profile/post schema, source account/post IDs, ownership of the supplied video, publication and capture times, public counts, partial/missing/error rows, window/completeness, latency, request/result counts, and credits charged. Preserve raw observation/provenance and do not interpret a HTTP success or provider listing as complete evidence.
4. Repeat after a recorded interval, then sample two additional public Japanese beauty creators selected by the marketer. Assess the accepted weekly refresh workload and total operating cost against the [technical validation protocol](../research/17-source-validation-protocol.md).
5. Revisit the provider/direct-web fallback decision only with actual results from both routes. Publication/source-use review remains a separate later condition. Neither a successful technical sample nor this fixed development dataset establishes audience or sales evidence.

## Comments

### Authorized API retry — 2026-10-12, 09:27 UTC

After completing API setup, the builder explicitly requested another attempt. A [fresh one-creator source-readiness check](../../brightdata-source-readiness/api-retry-2026-10-12.md) returned HTTP 200 for the supplied profile and ten posts. A mapper correction for the returned `id`/`profile_id` fields and offline replay produced one canonical account, ten posts, ten author links and 53 metrics, with zero unresolved candidates or quarantines. Only two scrape requests were made; the replay made no additional provider request. One share count remains missing.

The previous account-availability block no longer reproduces. This historical scope closure remains unchanged: repeat captures, additional creators, actual quota/charges and measured fallback behavior have not been completed by the retry, and the original planning map is still resolved.
