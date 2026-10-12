# Check official public TikTok endpoints and Japan web-collection terms

Label: wayfinder:research
Type: research
Mode: AFK
Status: resolved
Assignee: Codex research agent
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: none

## Question

The builder accepted TikTok oEmbed as the first narrow live source, requires eventual comparison of arbitrary unconsented creators, and asked us to consider other TikTok for Developers endpoints or web scraping. Using current primary TikTok sources, check whether any regular non-Business developer endpoint can retrieve arbitrary public creator profiles, posts, or engagement counts without creator OAuth for a commercial Japan marketing use case. Check the current Japan-applicable website terms for automated public-web collection, and whether TikTok's official embed/oEmbed documentation or terms clarify processing, storage, refresh, or commercial use of returned metadata. Distinguish documented permission from technical accessibility. Do not scrape, create an account, buy services, or contact TikTok. Save cited findings to `../research/15-japan-public-tiktok-routes.md`, then resolve this documentation research ticket only.

## Answer

[Cited findings](../research/15-japan-public-tiktok-routes.md) establish that the documented no-consent oEmbed route supports bounded known-URL embedding/attribution, while regular Display and Content Posting data endpoints require creator authorization. Research Tools exclude commercial users, and Commercial Content API coverage is EU content, not the Japan creator-performance corpus. The directly fetched Japanese-language Other Regions terms prohibit automated website scripts and restrict commercial use; the page is dated February 2020, so confirm the builder's account-specific terms before any production web collector. The embed docs do not establish a durable commercial creator database or retention right. This resolves the documentation question only; no comparison-grade source or commercial processing grant was obtained.
