# Technical validation protocol for prototype TikTok sources

**Status:** Local prototype protocol after the builder chose Bright Data plus direct web collection on 2026-09-30. No provider contacted, account created, or paid test run. [Current source research](17-comparison-source-current.md) distinguishes vendor claims from validated access. The builder defers a source/use-rights decision during this unpublished technical prototype; revisit it before publishing or treating retained data as production evidence.

## Intended use to disclose to a provider

A solo developer is building an internal tool for a Japan-market beauty brand. A marketer supplies public TikTok creator profile URLs; the tool automatically retrieves each creator's profile and roughly ten recent public posts weekly for comparison. It records post dates, captions/URLs, and public view/like/comment/share counts with retrieval times and source provenance. Marketers view selected facts and links in a shortlist. The tool may derive aggregate comparisons and later send relevant text to a contracted LLM for analysis, without training a model on the source data. Initially, the target workload is ten creators × up to ten posts × four weekly refreshes, about 440 profile/post observations per month if each returned profile or post is one observation. Audience country and sales are not inferred from post language or public counts.

## Source and use questions to preserve for publication review

1. What is the source of the TikTok profile/post data, and what rights or other basis permit your automated acquisition for this commercial Japan use case? Does any platform agreement or restriction apply to us as your customer?
2. Do your agreement and the source conditions permit our internal creator comparison, marketer-facing display of captions/metrics/links, weekly historical snapshots, derived aggregates, and sharing limited caption text with a contracted LLM? If LLM use is allowed, are no-training terms or other restrictions required?
3. What retention period, deletion-on-removal or takedown obligations, source-attribution rules, and restrictions on derived records apply to us? Can you point to the controlling written terms?
4. Can an individual developer open and use the account? Which product/API and contract tier apply; what are the actual free allowance, billing unit, account minimum, hard spend cap, rate limits, and use limits for the proposed workload?
5. For public Japanese creator URLs, which profile and post fields are supported, how many recent posts can be returned, and how are private/deleted posts, missing metrics, partial results, and changed handles represented? Are platform account IDs available apart from mutable handles?

## Minimal technical samples

Use the builder-supplied `@maronayannyan` profile and video first, then two additional public Japanese beauty creators selected by the marketer to assess coverage. With a separate Bright Data key, request a profile and up to ten recent posts per creator, then repeat after a known interval. Set an account-level hard spend cap before requests and use the free allowance if available. Record response schemas, source IDs, post ownership, field presence and missingness, newest-post ordering/window, retrieval and publication times, latency, errors, actual request/result counts, and credits charged.

Test the direct web route separately against the same references. The first bounded plain-HTTP fetch on 2026-09-30 returned HTTP 200 but only a 1,462-byte challenge page with no recognizable profile-data markers. A browser-based experiment must report challenge/empty/partial states separately from genuine unavailable content, cap retries and bytes, and measure runtime. Do not classify a successful HTTP status as extracted creator evidence. Compare any parsed values against the provider sample and the supplied video ID before canonical mapping.

A route passes the technical gate only if actual returned data supports the builder's chosen comparison threshold for the requested public creators and the refresh remains reproducible within the total USD 100/month operating envelope. A source's technical success does not establish its publication/use terms.

The currently working TikTok oEmbed adapter is a separate URL-resolution route; it does not pass this evidence gate.
