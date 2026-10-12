# Investigate TikTok acquisition API operations and contract gaps

Label: wayfinder:research
Type: research
Mode: AFK
Status: resolved
Assignee: pilot-builder (via Codex TikTok API research)
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: none

## Question

Given the builder's TikTok-first direction and assumed TikTok One access, which documented official API calls and authorization steps can support a small automated local flow for finding new creator candidates and collecting available profile/post evidence for known and discovered candidates?

Narrow the previous route inventory to an implementation contract: official TikTok One/business discovery API operations, required identifiers, authentication/scopes and grants, pagination/filter semantics, fields/content types, quotas/pricing when documented, and a first read-only connection test. Consult official SDK/source repositories if public documentation pages are incomplete. Clearly mark anything that cannot be verified; do not invent endpoint paths, parameter names, response fields, region guarantees, or data-export permissions. Distinguish marketplace UI access from app approval and actual API access without asking the user to reconfirm the assumed UI access.

Recommend the smallest meaningful automated acquisition experiment and the boundary between source-specific API details and reusable domain/evidence records. The total eventual operating budget remains around USD 100/month; initial execution is local with very low expense. No account setup, paid service, social-data collection, or production implementation is part of this investigation. Existing constraints about Japanese-language relevance, unknown audience geography, sales objectives, and platform-policy permissions remain.

Write findings to `../research/09-tiktok-acquisition-contract.md`. Resolve the documented contract investigation separately from live-access validation and the user's final acquisition-scope decision.

## Answer

Resolved on 2026-09-29 as a documentation investigation. TikTok's official Postman collection publishes creator discovery, public creator profile, and creator video-insight operations under TCM-labelled paths. The current business API catalogue names corresponding TTO capabilities, but a current runnable contract, scope grants, pagination, response fields, quotas, and pricing could not be established from the accessible public material. The official SDK provides inspectable hashtag-discovery operations, which do not substitute for creator discovery.

The [TikTok acquisition findings](../research/09-tiktok-acquisition-contract.md) contain exact primary-source request evidence, the pinned SDK reference, current-versus-older documentation discrepancies, and a minimal read-only experiment. The parent session checked the creator-request examples through indexed official Postman pages after direct page loads timed out. The conclusion is a specific contract/access gap, not a completed runnable integration or evidence that TikTok access is unavailable.

The next prerequisite is [Validate TikTok API access with a minimal read-only evidence sample](10-validate-tiktok-api-access.md), using the current approved app documentation and actual grant. No API request with project credentials, collection, purchase, or code implementation occurred. The user is separately choosing whether first-milestone automation fetches evidence for supplied creators or includes discovery immediately; both remain pilot requirements.

### Subsequent scope clarification — 2026-09-29

The preceding prerequisite recommendation is superseded. The builder cannot use TikTok for Business and prioritized modular source-to-canonical design; that live-check task is closed without execution. Known-creator retrieval first is already accepted. These research findings remain background, while [Select the first live source and evidence scope](11-select-live-source-and-evidence-scope.md) will evaluate a usable route after the modular contract is settled.
