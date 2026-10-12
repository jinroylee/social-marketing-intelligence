# Build the modular acquisition foundation for known TikTok creators

Status: direction and architecture accepted; local synthetic ingestion and limited oEmbed URL integration implemented on 2026-09-29; comparison-grade acquisition pending

Decision owner: [Define the modular source-to-canonical acquisition pipeline](issues/04-select-pilot-evidence-scope.md).
Architecture: [Modular source-to-canonical acquisition pipeline](source-to-canonical-design.md).

## Accepted direction

Automate evidence fetching and refresh for known creators before automated discovery. Begin locally with TikTok, while keeping the system applicable to other platforms, markets, and products. Both discovery and creator comparison remain required by the integrated pilot.

The campaign context is APRILSKIN Hero Cushion sales in Japan. The builder selected the [official Japan Hero Cushion + refill listing](https://aprilskin.jp/products/papkr18024) and all four Pink Edition shades (19, 21, 22, 23) on 2026-09-29. Shade-specific evidence requires an explicit shade reference; a generic Hero Cushion mention is product-level only. Japanese-language relevance can support an exploratory shortlist; audience geography remains unknown without evidence. Product/market context is campaign configuration, not source-adapter logic.

The builder clarified on 2026-09-29 that TikTok for Business is unavailable to them. Marketer users may have TikTok One/business accounts but must not need to configure developer APIs. Regular TikTok developer API access is only a possibility. The builder chose official TikTok oEmbed as the first narrow live integration for supplied URLs and retained the requirement to compare arbitrary known creators who have not authorized the app. The [live-source ticket](issues/11-select-live-source-and-evidence-scope.md) records that regular developer endpoints do not meet this unconsented requirement and that direct website scraping is not selected under TikTok's currently served Japanese-language terms. A comparison-grade licensed route remains to be validated.

## First technical result

One local command automatically processes bounded inputs through a collector, retained raw observations, a source-specific mapper, and shared canonical persistence. A report exposes acquired and applied records, unresolved identities, missing values, freshness, partial coverage, and failures. Replaying permitted retained data works without contacting its original source.

The proposed interfaces were proven using two different synthetic source formats before adding a live connector. Test fixtures demonstrate orchestration, mapping, identity, and replay behavior; they do not deliver a real creator shortlist. The first live integration is limited URL resolution through oEmbed. Automatic comparison-grade evidence retrieval and refresh for supplied creators remains a separate later milestone.

The [approved architecture design](source-to-canonical-design.md) owns the contracts, module responsibilities, failure behavior, and acceptance criteria. [The implementation task](issues/12-implement-local-ingestion-slice.md) tracks the build under wayfinder. Start with one Python application, local relational storage, local payload files, and on-demand runs. No model call or cloud deployment is needed for the first technical slice.

## Supplied source reference

`https://www.tiktok.com/@maronayannyan/video/7632620458235530504`

This is a video URL, containing the handle hint `maronayannyan` and video identifier string `7632620458235530504`. An initial best-effort page lookup on 2026-09-29 returned a restricted-URL fetch failure; no page contents were obtained through that route. Do not infer metrics, stable author identity, or audience geography from the URL alone.

Later on 2026-09-29, TikTok's documented oEmbed endpoint resolved this exact URL with HTTP 200 and returned video attribution and a title referring to Hero Cushion with `#PR`. See [the live-source selection ticket](issues/11-select-live-source-and-evidence-scope.md) for the bounded observation. The result verifies basic URL metadata availability only; it does not establish author identity independently, creator post history, engagement, audience, sales evidence, or canonical ingestion.

## Subsequent live-source work

The [bounded oEmbed reference adapter](issues/16-implement-live-oembed-reference-adapter.md) now uses the existing pipeline seam without persisting TikTok-returned content under unverified commercial analytics rights. Its actual fields and limits are stated in the [source decision](issues/11-select-live-source-and-evidence-scope.md). This local integration validates supplied URLs and transient attribution, not a full creator profile, post history, or performance comparison.

Then [validate a comparison-grade source](issues/17-validate-comparison-grade-tiktok-source.md) for known creators without app authorization. Establish its authorization, actual fields, costs, coverage, refresh limits, and processing/retention conditions with a minimal authorized sample before adding that provider's collector and mapper. The builder owns integration, and marketer-side developer configuration is not part of the workflow. Earlier suggestions of 10 creators and 5 posts per creator remain illustrative, not approved quotas or demonstrated provider capabilities.

The local ingestion application runs the two synthetic fixtures and the bounded official oEmbed adapter. A fresh-schema CLI validation resolved the supplied video and profile in two HTTP requests; it wrote two non-retained operational observations and **zero** canonical entities, fields, or metrics. No authenticated TikTok API request, account signup, paid subscription, or comparison-grade evidence ingestion has been performed. The earlier Business API validation task was closed as out of scope, without a successful access check.
