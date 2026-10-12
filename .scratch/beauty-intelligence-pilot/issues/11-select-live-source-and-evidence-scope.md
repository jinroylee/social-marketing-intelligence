# Select the first live source and evidence scope

Label: wayfinder:grilling
Type: grilling
Mode: HITL
Status: resolved
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 04, 13, 14, 15

## Question

After the modular ingestion contract is settled, which accessible route can supply useful real TikTok evidence for known creators, and what field set, coverage, refresh workload, and cost will the pilot commit to?

The builder cannot use TikTok for Business. Regular developer API access is only a possibility, and marketer users must not configure developer APIs. Evaluate usable API, licensed, customer-provided, or permitted web routes against actual access and evidence needs; no route is preselected. Create focused research or access tasks only once needed for this decision. This ticket does not block designing the source-independent pipeline or its local fixture slice.

Before claiming live readiness, establish supported operations and identifiers, actual obtainable fields, source/processing/retention conditions, time window, per-run limits, refresh cadence, and total cost within the eventual USD 100 monthly envelope. Separate provider documentation, granted access, and a successful minimal sample. Record unknown audience geography, commercial outcomes, and coverage explicitly. Select the Hero Cushion version/listing and shade scope for the real campaign sample.

Known-creator retrieval/refresh comes first, automated discovery next. Preserve that accepted order; do not reopen it or infer that a successful known-creator sample establishes discovery capability. Markers of synthetic evidence and live validation remain separate throughout the workflow.

## Context

This ticket carries the source-specific questions deferred from [Define the modular source-to-canonical acquisition pipeline](04-select-pilot-evidence-scope.md) following the builder's 2026-09-29 clarification. The earlier Business API validation task was closed without execution. The [milestone brief](../first-acquisition-milestone.md) records the current order and supplied video reference.

## Evidence reviewed

- [Regular developer access](13-research-regular-tiktok-developer-access.md), [affordable automated routes](14-research-affordable-tiktok-source-routes.md), and [Japan-facing endpoint and website terms](15-research-japan-public-tiktok-routes.md) were checked separately against primary sources. Documentation is not a substitute for granted access or a successful sample.
- APRILSKIN's [Japan storefront lists Hero Cushion + refill](https://aprilskin.jp/products/papkr18024) with Pink Edition shades 19, 21, 22, and 23. The builder selected this listing and all four shades for the pilot sample.
- On 2026-09-29 around 07:52 UTC, a read-only call to TikTok's documented [video oEmbed endpoint](https://developers.tiktok.com/docs/en/embed-videos) for the supplied URL returned HTTP 200 and JSON type `video`. It attributed the post to `@maronayannyan` (display name `まろん`) and returned a title referring to Hero Cushion with `#PR`, plus thumbnail and embed markup. A second call using that account's profile URL returned HTTP 200 and type `rich`, with author attribution and embed markup but no JSON engagement counts or post list. These are **live URL-resolution samples**, not a canonical ingestion run or proof of independent author identity, sustained access, product sales, audience geography, or engagement performance. No raw response was retained.

## Routes considered

| Route | What is established | What remains before it can be the creator-comparison source |
| --- | --- | --- |
| TikTok oEmbed | One supplied video URL was resolved live; it provides attribution and title suitable for a bounded relevance check. | No structured engagement, account post history, audience, or sales fields; it cannot meet the known-creator refresh milestone alone. |
| Regular Display API | Documented profile/video refresh for a creator who grants OAuth, including post counts and optional profile statistics. | App/scope grant, creator consent, a response sample, and TikTok's approval of this commercial analysis and persistent creator records. It cannot read arbitrary unconsented creators. |
| Low-cost scraper provider | Bright Data publishes a free monthly allowance and URL-based profile/post collection. | TikTok source authorization, client processing/retention rights, actual Japan sample/fields/charges, and a recurring refresh test. A vendor listing alone is not clearance. |

The detailed findings are in [regular developer access](../research/13-regular-tiktok-developer-access.md), [affordable source routes](../research/14-affordable-tiktok-source-routes.md), and [Japan public routes](../research/15-japan-public-tiktok-routes.md).

## Answer

Resolved as a **narrow first-source decision** on 2026-09-29 with the builder's answers to Q1–Q3. The first live integration will use TikTok's documented **oEmbed** operation for supplied public video and profile URLs. The two read-only HTTP 200 probes above establish basic technical access for the supplied reference; they do not establish a retained canonical sample, recurring availability, or commercial analytics permission. The goal still requires automatic comparison of known creators who have **not** authorized the app. oEmbed is the first small integration, not a replacement for that requirement or for later automated discovery.

| Boundary | First oEmbed integration |
| --- | --- |
| Supported operation and identifiers | Resolve a marketer-supplied video/profile URL. Keep the original URL and any parsed video ID/handle as intake hints; require returned evidence before treating a video ID as corroborated. An oEmbed author URL is a mutable alias, not a stable account identity or proof that two accounts are the same creator. |
| Available evidence | For a video, the documented response may return title, author name/URL, thumbnail URL, and embed markup; for a profile, author name/URL and embed markup. The observed sample returned those classes of data. Use the embed for attributed viewing; the official JSON supplies no machine-readable follower counts, post list, post engagement, audience geography, or sales. Generic Hero Cushion mentions are product-level; the shade is unknown unless explicitly named. |
| Coverage and time | Only requested public URLs that resolve at the time of each call. Record acquisition time separately from any source publication time, which oEmbed does not provide. A failed lookup or later removal is an availability observation, not proof that a creator never posted. No historical completeness, Japan audience coverage, or future URL stability is promised. |
| Run and refresh workload | Start locally with at most 10 supplied URLs and 10 total HTTP attempts per run including any single transient retry; one bounded response per URL, on demand and approximately weekly during the first pilot month. At 10 URLs and four weekly runs, the successful no-retry path is about 40 calls/month. TikTok publishes no oEmbed bulk quota here; stop/back off on throttling instead of bypassing it. |
| Processing, retention, and cost | TikTok documents programmatic URL-to-embed conversion and attributed display. It does not establish a grant to archive returned creator metadata for commercial analysis. The first connector therefore keeps raw JSON, title, author metadata, thumbnails and embed HTML transient; durable records are limited to builder-supplied references and operational retrieval provenance unless use rights are clarified. No developer credentials, paid account, cloud server, or LLM are needed for this local slice; no oEmbed charge was incurred by the two probes, but no continuing fee/rate guarantee is published. The eventual USD 100/month all-in target still depends on a comparison-grade source and measured workload. |

Other official TikTok developer reads were considered: Display and Content Posting require the creator's OAuth token; Research Tools exclude this commercial user; Commercial Content API does not cover the needed Japan creator corpus. The currently served [Japanese-language Other Regions terms](https://www.tiktok.com/legal/page/row/terms-of-service/ja) prohibit automated website collection, so direct profile-page or rendered-embed scraping is **not selected**. Its posted revision date is February 2020; if web collection is revisited, verify the account's applicable terms and obtain a permitted basis. Bright Data and similar vendors remain technical candidates only: their published prices do not establish TikTok source authority or this project's retention/derivation rights.

Next work is [the bounded oEmbed adapter](16-implement-live-oembed-reference-adapter.md), followed by [access validation for comparison-grade unconsented creator data](17-validate-comparison-grade-tiktok-source.md). Neither ticket may label oEmbed URL attribution as a creator-performance feed. No service was purchased, no developer grant was obtained, and no live TikTok response was written to the canonical dataset in this decision session.
