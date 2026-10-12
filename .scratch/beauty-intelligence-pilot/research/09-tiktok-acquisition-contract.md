# First automated TikTok acquisition: verified contract and gaps

**Checked 2026-09-29.** Native marketplace access to Instagram and TikTok is assumed, as instructed. Initial acquisition is TikTok-only; the domain must remain extensible to other platforms. This is desk research, with no credentials, account setup, subscriptions, live social-data collection or implementation.

**Current scope clarification (2026-09-29):** known-creator retrieval/refresh still precedes discovery, but the builder cannot use TikTok for Business and has prioritized modular ingestion design. The Business API experiment below is background, not the next action; its [live-check task](../issues/10-validate-tiktok-api-access.md) was closed without execution. See the [current milestone brief](../first-acquisition-milestone.md). A usable live route will be selected separately; regular developer API access remains unverified.

**Result:** first-party sources expose concrete TCM creator-discovery/profile/video requests and a fully inspectable SDK contract for hashtag trends. However, the current **TikTok One creator API contract is not yet implementation-ready**: the public Postman examples still use TCM paths, while the current portal describes TTO operations without rendering their complete schemas. Do not silently prepend `/tto/`, assume the old methods still work, or substitute hashtag trends for the required creator discovery.

## 1. Creator acquisition: exact evidence from TikTok's Postman collection

These are **published TCM examples**, not verified current TTO endpoints. The collection supplies request examples, not a complete required/optional schema or a live grant. Host is `https://business-api.tiktok.com`; `Access-Token` is the illustrated authentication header.

| Required capability | Published operation | Verified inputs | Still unresolved |
| --- | --- | --- | --- |
| Discover creators | `POST /open_api/v1.3/tcm/creator/discover/` | JSON example: `tcm_account_id`, `country_code: "US"`, `fast_growing: true`; `Content-Type: application/json`. | Current TTO equivalent and migration status; complete filter schema; whether country means creator/audience/account market; Japanese-language or keyword filtering; pagination, response fields, grants. [Official request](https://www.postman.com/tiktok/tiktok-api-for-business/request/zsxb705/tcm-creator-discover). |
| Read known/discovered creator profile | `GET` request template ending `/open_api/v1.3/tcm/creator/public/` | Query `handle_name`, `tcm_account_id`; token header. | Current TTO method/path, exact profile fields, unavailable-account behavior, identifier returned for deduplication. [Official request](https://www.postman.com/tiktok/tiktok-api-for-business/request/roa0au7/tcm-creator-public-insights). |
| Read creator post evidence | `GET` request template ending `/open_api/v1.3/tcm/creator/public/video/list/` | Query `handle_name`, `tcm_account_id`; token header. | Current TTO equivalent, video fields/metrics, captions, dates, links, pagination, lookback, media types and limits. The operation title establishes a video-insights route, not access to binaries, transcripts or comments. [Official request](https://www.postman.com/tiktok/tiktok-api-for-business/request/bsyn9bl/tcm-creator-public-video-insights). |

**Source inconsistency:** the latter two examples include `/open_api/` in the request template while the generated base URL may already contain it; the video cURL shows a duplicated `/open_api/open_api/`. These examples are useful evidence of operation shape, but must not be copied as production URLs. No current TTO wire path is asserted here.

The [current official API catalog](https://business-api.tiktok.com/gateway/docs/index?identify_key=c0138ffadd90a955c1f0670a56fe348d1d40680b3c89461e09f78ed26785164b&language=ENGLISH) names the necessary TTO operations: **Get authorized TTO Creator Marketplace accounts**, **Get TTO Public Account Insights**, **Get TTO Public Media Insights**, **Discover TTO creators**, and separately authorized insights. It also lists account authorization/authentication and TTO rate-limit guides. This verifies their existence; their request/response bodies did not render in the bounded investigation.

## 2. Official SDK: executable contract exists for hashtag context

Inspected TikTok's SDK repository at commit **`f809c396520df2d7b201a9ccc5378d822b728ed3`**. The Python API-file inventory contains no TTO/TCM creator API module; therefore it cannot close the creator contract above. Its `CreativeManagementApi` does contain:

| SDK method | HTTP request and parameters | Meaning |
| --- | --- | --- |
| `discovery_trending_list(discovery_type, advertiser_id, access_token, **kwargs)` | `GET https://business-api.tiktok.com/open_api/v1.3/discovery/trending_list/`. Required query: `discovery_type`, `advertiser_id`; optional `country_code`, `category_name`, `date_range`. Token goes in `Access-Token` header. | Popular hashtags, not an arbitrary creator or post keyword search. |
| `discovery_detail(hashtag_id, discovery_type, country_code, date_range, advertiser_id, access_token, **kwargs)` | `GET https://business-api.tiktok.com/open_api/v1.3/discovery/detail/`. All arguments except token become query parameters; token is the same header. | Details of a returned hashtag. |

[Generated method and HTTP source](https://github.com/tiktok/tiktok-business-api-sdk/blob/f809c396520df2d7b201a9ccc5378d822b728ed3/python_sdk/business_api_client/api/creative_management_api.py), [host configuration](https://github.com/tiktok/tiktok-business-api-sdk/blob/f809c396520df2d7b201a9ccc5378d822b728ed3/python_sdk/business_api_client/configuration.py).

The [trending specification](https://github.com/tiktok/tiktok-business-api-sdk/blob/f809c396520df2d7b201a9ccc5378d822b728ed3/yml_files/discovery_trending_list.yml) includes `HASHTAG`, categories such as `BEAUTY` and `BEAUTY_AND_PERSONAL_CARE`, default country `US`, default period `7DAY`, and period keys `1DAY`, `7DAY`, `30DAY`, `120DAY`. Its generated response type leaves `data` generic; internal response mappings name `list`, `filter_info`, `hashtag_id`, `hashtag_name`, `posts`, `views`, `rank_change`. No cursor/page input is exposed by the inspected method. Japan support and the precise enum wire interpretation should be checked in the [linked current reference](https://business-api.tiktok.com/portal/docs?id=1825119032526849), not inferred from accepting a string. The YAML labels `Access-Token` as a query parameter, whereas executable SDK code uses a header; this discrepancy is another reason to verify the live contract.

This can be an optional API connectivity/context experiment if the app has its permissions. It **does not satisfy creator acquisition** and should not become an extra mandatory integration.

## 3. Authorization, scope and cost contract

The [official SDK prerequisites](https://github.com/tiktok/tiktok-business-api-sdk#prerequisites) are Business account → developer registration → developer app → authorization → authentication. Assumed native UI access covers only the first product context; it does not prove app permissions. For the intended creator route, the future connection work must establish:

- Which approved TTO read scopes cover account enumeration, public account/media insights and creator discovery, and how the selected marketplace account authorizes the app.
- The actual marketplace account identifier returned by the current account-enumeration operation. Do not substitute a handle, advertiser ID or Business Center ID for it. Discovery SDK's `advertiser_id` is a different input from Postman's `tcm_account_id`.
- Current TTO methods, paths, required fields, pagination and response schema, including the identity join between discovered candidates and the public profile/video calls.
- Endpoint quotas, subscription/usage fees, regional coverage and applicable retention/export/analytical-use terms. None was verified for the current TTO API. The free native search price in [research 08](08-instagram-tiktok-discovery.md) is **not an API price quote**; no claim that API operation fits USD 100/month follows yet.

Numeric scope IDs found in third-party sources were deliberately not adopted. Reuse restrictions documented in research 08 remain route-specific; approval for local storage or model processing must not be inferred from a successful request.

## 4. Smallest meaningful automation experiment

**Proposed full acquisition experiment for later authorized execution:** one local, read-only TTO run, after confirming current schemas and grants. The user has selected known-creator evidence first and automated discovery next. Steps 1–2 cover the initial evidence-fetching milestone; steps 3–4 remain the later discovery check. Both capabilities remain in pilot scope. No campaign, invite, posting or ad operation is needed.

1. Enumerate accessible TTO marketplace accounts using the current documented operation; select the intended account. Save a redacted access result and API version, never credentials.
2. Fetch the public profile and first video-results page for **one known handle**. Record which actual fields support a source-linked comparison; preserve missing/unavailable fields explicitly.
3. Make **one creator-discovery request** using verified Japan/language/category filters that the account actually supports. Do not hard-code unverified `JP` or Japanese filter syntax. Preserve submitted filters and result ordering.
4. Fetch profile and first video-results page for **one newly discovered creator**, joining using the documented identity. Deduplicate against the known seed. If discovery returns no usable candidate, retain that as the outcome rather than filling it with a fabricated result.

This is at most six logical reads: account enumeration, discovery, and profile/video reads for two creators. Exact HTTP count may differ with the current contract. Initial local request ceiling is six, with no automatic pagination or retries; that is an experiment control, **not a platform quota**. Success means both discovery and known-candidate acquisition demonstrably work and yield inspectable evidence. A permission error diagnoses API access; an empty valid query diagnoses the chosen query/coverage. Native browsing remains available but must not be presented as successful API discovery.

If current TTO operation schemas remain inaccessible, the next concrete deliverable is a connection worksheet capturing them from the developer portal and verifying the grant—not another broad platform survey. No credentials are needed in this research artifact.

## 5. Source adapter versus reusable evidence

Keep TikTok auth, TTO IDs, endpoints, filter translation, pagination, field mapping and errors inside the acquisition adapter. Reusable records should carry platform + source account/content identity, source URL when supplied, acquisition time, source metric name/value/window, discovery provenance, evidence origin, missingness and any reuse/retention metadata. Preserve handles as mutable labels; do not merge cross-platform people solely by matching handles.

Campaign criteria remain independent: APRILSKIN Hero Cushion, Japanese-language relevance and sales objective. Language is an observed relevance signal; audience geography stays unknown unless an actual permitted source supplies it. Engagement is not sales. No model should manufacture a comparable field absent from the API. These boundaries support a later Instagram adapter without forcing identical platform metrics.

**Outcome:** exact first-party request evidence and an explicit six-read experiment are documented. Current TTO migration/schema, permission grant and live feasibility remain unresolved; this is not a completed runnable integration contract.
