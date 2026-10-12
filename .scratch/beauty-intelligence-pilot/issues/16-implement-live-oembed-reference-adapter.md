# Implement the first live TikTok oEmbed reference adapter

Label: wayfinder:task
Type: task
Mode: AFK
Status: resolved
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 11

## Question

Implement the approved first narrow live integration: automatically resolve a bounded list of supplied TikTok video/profile URLs through TikTok's [documented oEmbed endpoint](https://developers.tiktok.com/docs/en/embed-videos), using the existing collector/mapper seam and local CLI. This is URL attribution and availability, not comparison-grade creator evidence. Keep the Japan APRILSKIN product context out of the adapter.

Start with a self-imposed maximum of 10 supplied URLs and 10 HTTP attempts total per run, including at most one retry for a transient failure. Enforce finite response size/time, explicit 429/404/private/removed/invalid handling, and source/capture provenance. Support on-demand runs and a documented weekly refresh procedure during the local pilot. The profile URL may yield an author handle but no stable platform-account ID; do not merge creators by handle. The video ID parsed from an input URL remains a hint unless the returned oEmbed data corroborates it. Do not extract counts or posts from rendered embed markup or ordinary TikTok HTML.

TikTok documents URL-to-embed conversion but has not granted this project commercial analytics archiving. Default to transient response processing: retain the builder-supplied URL, request time, outcome, source context, and non-content operational hash/status as permitted, but no raw response, title, author metadata, thumbnail, embed HTML, or derived creator assertions in the durable canonical dataset until use rights are established. A live embed may be presented with TikTok attribution where allowed. Make the retention/processing policy explicit; do not silently mark returned content retainable. If the existing runner cannot safely separate transient resolution from durable source facts, extend that seam minimally before a live canonical write.

## Completion evidence

Tests with recorded *synthetic* oEmbed-shaped fixtures for URL validation, bounded calls, successful video/profile responses, non-200 outcomes, identity uncertainty, idempotent refresh, and no accidental TikTok-content persistence. Run a tiny read-only live check against the supplied video and derived profile URL through the new adapter, recording only the permitted operational evidence and clear missing fields. Demonstrate no paid service or developer credentials are needed for this first connector. Do not claim creator-comparison or production use readiness.

## Answer

Implemented the approved local live URL check on 2026-09-29. The [TikTok oEmbed collector and mapper](../../../src/smi_ingestion/adapters/tiktok_oembed.py) use the existing [adapter registry](../../../src/smi_ingestion/adapters/registry.py) and [runner](../../../src/smi_ingestion/runner.py). The collector accepts only direct HTTPS TikTok video/profile URLs, removes tracking parameters, limits a run to ten references and ten actual source attempts, enforces an 8-second/64-KiB response bound, and gives transient failures at most one retry. A 429 stops without retry; unavailable/private and source failures remain distinct in the report. The mapper validates the response and possible video-ID corroboration, but emits no creator entities, fields, or metrics. The fixed non-retaining policy stores only canonicalized input references, timestamps, status, attempt counts, and operational hashes; returned title, author, thumbnail, embed markup, and raw JSON stay transient.

The [live example manifest](../../../examples/live/tiktok-oembed-manifest.json) and [README](../../../README.md) give the local command and weekly refresh procedure. A fresh PostgreSQL schema was migrated and the actual CLI resolved the supplied video and profile with **HTTP 200 on both**, two source attempts, two operational observations, and two generic unresolved-account markers. Direct database inspection found **zero** canonical entities, external identities, field assertions, or metrics; both payload paths were null and the evidence directory was empty. The disposable schema and directory were removed after verification. No developer account, API credential, paid service, or LLM was used.

`uv run pytest -q` passed **36 tests**, including synthetic oEmbed-shaped response tests for URL validation, response size, 404, 429, retry/request-budget accounting, a fixed ten-attempt cap even if CLI limits are raised, mismatched video IDs, repeated refresh, and no returned-content persistence. The first live connector is a URL/availability check only. It does not retain source titles or perform post enumeration, engagement comparison, audience analysis, discovery, or sales measurement. Broader storage and [comparison-grade source access](17-validate-comparison-grade-tiktok-source.md) still require their own source-rights and actual-data validation.
