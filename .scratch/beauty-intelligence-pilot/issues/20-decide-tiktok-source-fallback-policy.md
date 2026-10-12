# Decide TikTok source fallback and evidence reconciliation

Label: wayfinder:grilling
Type: grilling
Mode: HITL
Status: resolved
Disposition: out-of-scope
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: none

## Question

After the Bright Data sample and direct-web experiment, which measured failures or missing fields should trigger the direct route, and when should collection stop? Decide per-source request and monthly cost caps, retry/backoff, freshness thresholds, source disagreement handling, source-specific confidence and provenance, and what the marketer sees when neither route yields comparison-grade evidence. Keep the working oEmbed URL resolver as a separate reference/availability path and the TikTok sandbox Display API as a separate consenting-account path. Do not merge a creator or post merely because handles, captions, or counts look similar.

Use actual Japan sample results and the builder's accepted minimum of a profile plus roughly ten recent posts with dates, captions/URLs, public engagement counts, and weekly refresh. The outcome is a concrete fallback policy and acceptance boundary for a source-independent canonical dataset; it does not assume that a browser route successfully handles challenges.

## Answer

Deferred without a measured fallback decision during the 2026-10-12 parallel Wayfinder pass. The builder previously chose fixed local evidence for ontology and agent development and postponed actual-source work. This ticket requires successful live-source captures, measured failures, usage, and costs that are not available; its prerequisite [Bright Data sample](21-validate-bright-data-live-sample.md) was scope-closed without successful validation.

Resume this decision in a later source-readiness effort after bounded profile/post captures and repeats establish actual coverage, failures, costs, and disagreement. Its old blocking edges were removed because this task is outside the current map, not because the sample passed. The current pilot still needs source-independent handling of missing, withdrawn, and stale evidence in its domain and acceptance contracts; that behavior does not establish a provider fallback policy or weekly source coverage.
