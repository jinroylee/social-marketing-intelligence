# Ticket 34: official X recent-search primary contract

Verified **2026-10-28**, read-only public documentation only. No credential lookup, source request, model/paid operation, live receipt or permission approval occurred. Original fetched Markdown and `sources.json` remain in the persistent worker's git-excluded `verification/ticket-34/primary/`.

## Current primary contract and installed choice

The [endpoint reference/OpenAPI](https://docs.x.com/x-api/posts/search-recent-posts.md) specifies `GET https://api.x.com/2/tweets/search/recent`, Bearer authorization, required `query`, `max_results` 10–100, explicit `start_time` within seven days, `end_time`, `sort_order` and `post.fields`; `next_token`/`pagination_token` are alternative continuation inputs. The reference's query schema allows 4096 characters, while the [rate reference](https://docs.x.com/x-api/fundamentals/rate-limits.md) states 512 for ordinary recent search and 450 app requests per 15 minutes. The installed PostgreSQL schema additionally coordinates a two-second minimum source-request interval across workspaces; other installations/schemas/databases or external shared-app traffic remain outside that quota guarantee. The implementation uses a strictly smaller 200-character literal phrase plus a 2048-byte encoded-URL cap, one page of ten, `sort_order=recency`, no continuation/expansion, and `post.fields=created_at,public_metrics`.

The [recent-search quickstart](https://docs.x.com/x-api/posts/search/quickstart/recent-search.md) still shows `tweet.fields`, unlike the current endpoint/OpenAPI's `post.fields`. Current primary schema is selected; actual provider acceptance is unverified. No compatibility fallback or extra call is authorized. Numeric post IDs retain native identity, `created_at` stays publication time, and neither current schema nor quickstart supplies an original capture/metric-measurement timestamp. Those remain unknown; actual request/response retrieval identity/time is separate. Current `PostPublicMetrics` names `repost_count`, `reply_count`, `like_count`, `quote_count`, `bookmark_count` and `impression_count`. The bounded existing recent metric vocabulary maps the first three only. Legacy `retweet_count` is not substituted, and `impression_count` is not relabeled `view_count`; unsupported views stay unknown. Incomplete fields stay missing.

[Query guidance](https://docs.x.com/x-api/posts/search/integrate/build-a-query.md) describes phrase/operator syntax. The installed route allows only literal alphanumeric/space/underscore/hyphen text wrapped in quotes, with local literal/time eligibility. [Pagination guidance](https://docs.x.com/x-api/posts/search/integrate/paginate.md) describes `meta.next_token`; its presence means more uncollected data, and no token is persisted or followed. All pages remain partial samples with unknown market coverage.

[Current pricing](https://docs.x.com/x-api/getting-started/pricing.md) lists resource-based reads and presently USD 0.005 per Post read. It describes a UTC-day deduplication mechanism as soft, not certain, and allows possible negative credit balance. The implementation installs **no commercial rate**. Exact account terms/rates/currency/period/ceiling must be configured. Each request reserves ten declared post units and retains its liability; returned rows or daily repeat identity do not settle the bill. Explicit provider-basis final reconciliation remains required, with billing lag and zero-overshoot unknown.

[Developer Policy](https://docs.x.com/developer-terms/policy.md) governs permitted use, content integrity/display, redistribution, privacy and prompt current-state/deletion handling. It includes relevant removal/update obligations within 24 hours of applicable notice and restrictions on measuring platform performance. It does not establish this product's source-use/display/storage clearance. No current-display refresh or automatic compliance feed is installed. Local policy and withdrawal propagation support enforcement but do not prove complete provider compliance.

## Unmet external prerequisites

Approved app/access and credential; explicit live-operation authorization; clearance of intended analysis, retention, display and selected-KB-copy use; an applicable current-state/update/deletion compliance procedure or provider-approved alternative; account-specific rate/commercial bounds and configured shared allowance; independently authorized bounded live verification of current endpoint/parameter/response behavior. **No readiness receipt exists.** Tests use fake external HTTPS and real PostgreSQL. They do not establish actual charges, service health, complete market coverage, original-language accuracy or marketer usefulness.

## Exact fetched source identities

| Primary Markdown | Bytes | SHA-256 |
| --- | ---: | --- |
| [1](https://docs.x.com/x-api/posts/search-recent-posts.md) | 94599 | `e571ade10bad81f413d8eebdb3d40eb830ccd62e0f625d84f5178994ea6a1a99` |
| [2](https://docs.x.com/x-api/posts/search/quickstart/recent-search.md) | 6437 | `106dea73e1a90ef8c08e55eb90c480b03946ecee1963653b50d4578de7a14ca9` |
| [3](https://docs.x.com/x-api/fundamentals/rate-limits.md) | 14277 | `7ed4cdea57b5c83205ff098c62e899e5bd53eb073ce37e2cddf51e844c1d0aaf` |
| [4](https://docs.x.com/x-api/getting-started/pricing.md) | 11495 | `4b5bbde372d273e2001e5ea122bec018e30a7c6b9f45a28ec12fa13771618c58` |
| [5](https://docs.x.com/developer-terms/policy.md) | 29747 | `1287c6f859d19daaeb2a9b2e83c9306ebf147a3e945a06b69945b9f845e3fc7e` |
| [6](https://docs.x.com/x-api/posts/search/integrate/build-a-query.md) | 8436 | `6b78864969548b0870d1b681c629fdf7b796f5405476610b69702de7c0fd60be` |
| [7](https://docs.x.com/x-api/posts/search/integrate/paginate.md) | 8794 | `b6c71381127b1bc2f4bc779d07902daa863c8c5d3e447e9bcd19d5575391874d` |
