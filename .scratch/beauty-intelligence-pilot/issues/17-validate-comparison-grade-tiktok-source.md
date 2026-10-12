# Validate a comparison-grade TikTok source for unconsented creators

Label: wayfinder:grilling
Type: grilling
Mode: HITL
Status: resolved
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 16

## Question

After the narrow oEmbed adapter, which accessible and permitted source can automatically retrieve and refresh useful profile/post evidence for arbitrary known TikTok creators in Japan who have not authorized this app? This is the accepted marketer-workflow requirement; consented Display API reads or oEmbed URL attribution alone do not satisfy it. Keep automated discovery as a later step.

Use [regular developer access research](../research/13-regular-tiktok-developer-access.md), [affordable-route research](../research/14-affordable-tiktok-source-routes.md), and [Japan terms/endpoint research](../research/15-japan-public-tiktok-routes.md) as starting evidence. Check any provider's source authority and the project's allowed processing, retention, deletion, display, and model use; an advertised scraper price is not a rights grant. Verify actual Japan coverage, identifiers, fields, time windows, missingness, rate limits, refresh cost and failures with a minimal authorized sample before selecting a connector. Fit the eventual USD 100 monthly *total* envelope or explicitly narrow the pilot. Do not ask marketer users to configure developer APIs, bypass platform controls, create a paid account, or contact a provider without the builder's authorization where needed.

## Answer

Resolved as a **technical route choice with a negative live-readiness result** on 2026-09-30. The builder chose Bright Data as the primary automated source for known, unconsenting public TikTok creators and a separately implemented direct web/browser collector as a fallback. This is an unpublished personal prototype; the builder explicitly deferred source/use-rights and consent review as a prerequisite for *technical* experimentation. The decision does not establish a right to publish or retain a commercial creator intelligence product. The two routes must remain separate adapters with distinct provenance and operational outcomes. The existing oEmbed route continues to resolve supplied URLs only.

The builder's comparison-grade threshold is a profile and about ten recent posts per creator, with post dates, captions/URLs and public engagement counts, refreshed weekly. Neither selected route has passed this threshold yet. The local `.env` has `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` and sandbox mode configured; it has no Bright Data key or creator OAuth access token. TikTok's [sandbox](https://developers.tiktok.com/docs/en/add-a-sandbox) is limited to added target users, and [Display API post reads](https://developers.tiktok.com/docs/en/tiktok-api-v2-video-list) require a creator-authorized user token, so these credentials cannot retrieve arbitrary unconsenting creators. They remain useful for a separate consenting-account integration. No secret value was printed or copied to this ticket.

One read-only plain-HTTP request to the supplied `@maronayannyan` profile on 2026-09-30 returned HTTP 200, `text/html`, and only 1,462 bytes; it contained a challenge marker but neither the `SIGI_STATE` nor `__UNIVERSAL_DATA_FOR_REHYDRATION__` profile-data marker. No page content was retained. This is evidence that a simple successful status code is insufficient, not evidence that browser scraping will succeed. No Bright Data request or paid service was used. The provider documents [profile and posts-by-profile APIs](https://docs.brightdata.com/products/scrapers/tiktok/introduction), but Japan field coverage, exact identifier semantics, ten-post completeness, refresh stability and charges remain unverified. The [technical validation protocol](../research/17-source-validation-protocol.md) records the sample and measurement gate.

The next takeable work is [Implement a bounded Bright Data TikTok adapter](18-validate-bright-data-japan-sample.md) and [Prototype bounded direct TikTok web collection and challenge handling](19-prototype-direct-tiktok-web-collection.md). [Validate a Bright Data Japan profile and post sample](21-validate-bright-data-live-sample.md) waits for the provider credential, and [Decide TikTok source fallback and evidence reconciliation](20-decide-tiktok-source-fallback-policy.md) follows those source experiments. Until they pass, the pilot must label comparison-grade coverage as unverified and must not turn challenge pages or provider claims into canonical creator facts. Publication/use-rights remain an explicit open condition for the future product, even though the builder does not want it to block the local technical prototype.

## Evidence reviewed

- [Current provider and official-route check](../research/17-comparison-source-current.md): no source has both the necessary documented rights and a successful Japan profile/post sample; Bright Data is a low-cost technical candidate, while Apify's community Actor has weaker source and support evidence.
- [Technical validation protocol](../research/17-source-validation-protocol.md): prepared for the chosen prototype routes; no provider contact, account, payment, or vendor API call has occurred.
- [Sandbox and Bright Data API mechanics](../research/17-sandbox-and-provider-ops.md): app sandbox keys cannot substitute for a creator OAuth token or a separate Bright Data API key.

## Comments

- 2026-09-30, builder: Minimum comparison-grade live evidence is a profile and about ten recent posts per creator, including post dates, captions/URLs, and public engagement counts, refreshed weekly. Audience geography and sales impact remain separate unknowns.
- 2026-09-30, review pending: Current public evidence validates no rights-cleared source that meets this threshold. Awaiting the builder's choice between pursuing written provider terms and a capped sample while retaining automatic refresh as a requirement, or narrowing the initial pilot to marketer-supplied evidence. No comparison-grade connector was selected.
- 2026-09-30, builder: Use Bright Data and direct web scraping for the personal prototype; prioritize robust challenge handling and fallback behavior. Defer rights/consent questions as a technical-prototype gate. The follow-up source experiments retain the original comparison-grade evidence threshold.
