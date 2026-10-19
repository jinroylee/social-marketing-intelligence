# Source integrations and readiness

This document describes implemented acquisition capabilities and the evidence still needed for the [operational requirements](functional-requirements.md). Source/provider availability and pricing must be verified when an integration is enabled; adapter code or a past successful request does not guarantee current access, cost or coverage.

## Implemented routes

| Route | Supported input and result | Important boundary |
| --- | --- | --- |
| Offline snapshot | Import the frozen sample with exact observation/derivation membership and preserved capture times | Reproducible downstream development; no live discovery or fresh source measurement |
| TikTok public web | Collect explicitly supplied references and interpret available source fields in `web:public` | Challenges and partial coverage are explicit; selected post success does not establish complete profiles/history |
| TikTok oEmbed | Resolve supplied video/profile references as bounded availability/operational observations | Not a retained creator-history or engagement feed; no canonical post/account facts are inferred from the embed response |
| Bright Data TikTok | Collect a supplied creator profile and requested posts in `tiktok:public`, with bounded provider-snapshot polling/resume | Supplied-profile collection, not arbitrary keyword/creator discovery or an application job queue |
| X | None | Collector, topic polling, recent-observation path and anomaly methods remain implementation work |

See [local source commands](../README.md#explicit-live-source-operations), [adapter code](../src/smi_ingestion/adapters/registry.py) and [evidence contracts](evidence-sets.md). Examples under `examples/live/` are explicit network operations; the default snapshot workflow is offline. Load credentials from local configuration without printing or committing them. Existing credentials do not themselves authorize additional source calls or prove source-use clearance.

## Retained Bright Data verification evidence

The [redacted API/ingestion receipt](../.scratch/brightdata-source-readiness/api-retry-2026-10-12T092701Z.json) records a successful bounded profile-and-posts check: two synchronous HTTP 200 responses produced one account and ten posts; offline mapper replay resolved their identities/author links. It is an operational verification record, not a current service-health check or a completed discovery benchmark.

The mapper supports current and legacy provider identity fields and rejects conflicting author IDs. Keep native IDs separate from mutable handles and retain source namespaces; do not merge Bright Data and public-web accounts or metrics without supported equivalence/comparability rules. The receipt does not establish complete latest-post history, repeat freshness, broader creator coverage, actual credit consumption or monetary charges. Those gaps remain relevant to progressive acquisition and spending control.

## Operational work still required

- Implement real query discovery, distinct from the existing supplied-reference collectors. Verify each route's request/schema contract against current primary documentation and bounded actual responses before calling it ready.
- Measure successful and failed requests, returned records, timestamps, missingness, repeat behavior and usable KB updates. Provider HTTP success alone is not complete or relevant evidence.
- Record actual billable units/charges where derivable, with applicable rates/currency and period, and implement configured ceilings. Keep unknown-cost portions forecast-only; per-request bounds are not monetary enforcement.
- Define route selection, retry/resume, freshness and expected-information-value stopping using measured behavior. No automatic provider fallback or marginal-value orchestration exists today.
- Connect acquisition through durable task authorization, ingestion and KB publication. The assistant cannot use new raw fetch results before publication; X anomaly investigation cannot launch external searches.
- Preserve policy, provenance, coverage and source-specific metric semantics through normal KB and lightweight monitoring/alert paths. Source permissions and technical access are separate configuration/validation concerns.

Do not restore a full-profile/history prerequisite for recommendations: a stable account identity and one permitted ingested supporting observation satisfy the accepted minimum admission rule. Additional evidence improves assessment and may trigger enrichment without invalidating every incomplete account.
