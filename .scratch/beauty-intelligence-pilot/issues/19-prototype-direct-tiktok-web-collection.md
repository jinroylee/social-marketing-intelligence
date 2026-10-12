# Prototype bounded direct TikTok web collection and challenge handling

Label: wayfinder:task
Type: task
Mode: AFK
Status: resolved
Assignee: Codex / direct-web agent
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 17

## Question

Test a direct public-page route as a separate fallback source for known TikTok profile and post references. The builder wants browser/web scraping and robust handling of bot challenges. A first plain HTTP fetch of the supplied profile returned HTTP 200 but only a challenge page, so status code alone cannot prove extraction.

Build a bounded local prototype using the existing collector/mapper seam: explicit URL validation, finite request/time/byte/retry budgets, challenge versus private/removed versus partial-result outcomes, per-source provenance, and no silent empty-profile result. Explore whether a normal browser-rendered public page exposes stable profile/post facts; measure what is actually returned for the supplied creator and video. Do not infer account identity from a mutable handle, copy engagement values across unrelated posts, or claim Japan audience from language/proxy locale. Compare actual post IDs, dates, captions/URLs, and counts with the builder's ten-post weekly threshold. Record setup and operating cost, failures and variability. Keep direct-web extraction isolated from the Bright Data adapter so one can be changed or disabled independently. Do not present an anti-bot challenge as successful evidence.

## Answer

Implemented a separate [direct public-page collector/mapper](../../../src/smi_ingestion/adapters/tiktok_web.py) and [example manifest](../../../examples/live/tiktok-web-manifest.json). It accepts direct HTTPS TikTok references only, caps each run at ten references/HTTP attempts, caps each response at 1 MiB and eight seconds, retries a transient failure at most once within the cap, and leaves raw HTML transient. It records challenge, partial, unavailable/private, rate-limit and source-error outcomes independently from Bright Data. A profile is marked resolved only when embedded page data contains ten distinct posts with matching author ID, valid date, caption, corroborated video/photo permalink and the four core public counts; missing saves are allowed. [Adapter tests](../../../tests/test_tiktok_web.py) cover these boundaries and the runner's challenge stop. The full suite passes (65 tests).

In a local check of the builder's supplied reference, the video page yielded one post's public facts and was mapped into one canonical post. The supplied profile did not expose any recent-post list: direct fetches varied between a recognizable HTTP-200 challenge page and an incomplete page with zero posts. A standard headless-browser profile attempt also timed out after 20 seconds. Thus this route has not met the ten-post weekly comparison threshold. No bypass or automatic Bright Data fallback is claimed; the measured failures inform [Decide TikTok source fallback and evidence reconciliation](20-decide-tiktok-source-fallback-policy.md). Local collection itself has no provider API charge, while browser/proxy operating cost and success rate remain unmeasured.
