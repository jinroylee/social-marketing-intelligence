# Define the modular source-to-canonical acquisition pipeline

Label: wayfinder:grilling
Type: grilling
Mode: HITL
Status: resolved
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 01, 02, 03, 08, 09

## Question

What interfaces, evidence contracts, and verification criteria let interchangeable data sources feed a trustworthy canonical dataset without putting provider details into the shared model?

Define the first local implementation slice from a source reference through acquisition, retained raw observations, normalization, and canonical writes. Keep collection and source-schema mapping replaceable. Cover identity, provenance, missing values, replay, partial failures, and bounded runs. Demonstrate the proposed seams with two different input formats, without claiming that test data establishes live source access.

The builder's 2026-09-29 clarification supersedes the earlier API prerequisite: TikTok for Business is unavailable to the builder, regular TikTok developer API access is only a possibility, and marketer users must not need to configure developer APIs. Marketers may have TikTok One/business accounts; that is distinct from the builder's integration access. Detailed provider selection and live access validation can follow this architecture decision.

TikTok remains the first platform; future platforms and multiple providers for one platform must fit the same design. Automatic evidence fetching/refresh for known creators precedes automated discovery, with both still required for the pilot. Source-specific lookback, field availability, refresh cadence, fees, grants, and actual coverage remain unverified until a live route is selected. Preserve unknowns rather than infer audience geography, prices, or sales from public activity.

The current proposal is linked from the comments below. Historical comments preserve the discussion; this question and the latest scope clarification govern the current work.

## Comments

### First acquisition round — 2026-09-29

All blocking decisions/investigations are resolved, and this ticket is claimed before discussing route selection. Available account access remains unknown: the earlier question about whether the marketer can arrange brand-account access was not answered by the request to resume.

Two inputs are now required:

1. Whether the marketer can access or arrange access to Instagram Creator Marketplace through Meta Business Suite and TikTok One, and whether relevant account/app permissions can be obtained if a programmatic route is selected. Ordinary brand-account login, marketplace eligibility, and API approval are separate facts.
2. Whether the first pilot may use human-assisted discovery in native platform tools with local evidence comparison, or whether in-app programmatic discovery on both platforms is required from the start.

Recommendation, not an accepted decision: begin with human-assisted discovery and a small local comparison sample if account access and permitted evidence transfer support it, while investigating API automation. Preserve newly discovered and previously known candidates on both platforms. An initial sample of three new and two known candidates per platform is illustrative only. No provider choice, collection volume, refresh schedule, model-processing allowance, development budget, or product variant has been approved by these notes.

### Builder's direction — TikTok first with automation

- Assume access to both marketplaces for planning; stop treating that assumption as a question needing reconfirmation.
- Start with TikTok to build the acquisition flow. Maintain multi-platform applicability, while deferring the Instagram connector.
- Include some automation from the beginning. The exact minimum automated capability is not yet specified; manual initiation of an automated collection run is distinct from copying each candidate or post by hand.
- The preceding manually assisted, two-platform recommendation is superseded by this direction.
- Investigate the concrete official TikTok API contract before naming implementation endpoints or promising which discovery/collection steps the app can automate.

### Proposed first automated acquisition run

The proposal below is a concrete option for the human to assess, not a resolved acquisition contract or implemented collector.

1. Start one local run for the APRILSKIN Hero Cushion Japan campaign. A person initiates the run; the supported collection steps execute automatically. A scheduler is not required for this first flow.
2. Use supplied native creator identifiers and, where the selected API supports it, campaign-related search criteria to collect both known and newly discovered candidates. Preserve how each candidate was found. Unsupported filters must not be presented as applied.
3. Fetch the selected API's permitted profile/post evidence with explicit request, page, record, and time-window bounds. Record missing fields rather than manufacturing audience geography, sales performance, creator fees, or content not returned by the route.
4. Store attributable source observations and normalize them into source-independent concepts already named in the proposal: creator/account, content, and metric observations. Keep TikTok endpoint details inside its acquisition adapter. Source observation payload retention and any media/model processing must follow the actual grant.
5. Rerun safely: match source-native identifiers, avoid duplicate canonical accounts/posts, preserve observation times and meaningful metric history, and report partial runs or source errors. Cross-platform identity merging is not inferred from similar handles.
6. Produce an acquisition summary and a reviewable evidence sample before adding ranking or narrative generation. LLM calls are not inherently required to retrieve records; source/API costs remain to be checked in the actual route.

Suggested first sample for evaluation: at most 10 creator candidates with at most 5 relevant posts per candidate where available and permitted. These are proposed pilot bounds, not verified API limits, completeness claims, accepted collection quotas, or permission to spend. Exact discovery support, returned fields, refresh cadence, final workload limits, and a live API connection test remain unresolved.

The next concrete prerequisite is [Validate TikTok API access with a minimal read-only evidence sample](10-validate-tiktok-api-access.md). When this proposal was written, the builder was asked whether the first milestone should automate retrieval/refresh for supplied creator identifiers first, with discovery next, or automate discovery and retrieval together. The accepted answer is recorded below; both capabilities remain required by the pilot.

### Accepted milestone order — 2026-09-29

The builder answered "Recommended" to the choice of **automatic evidence fetching and refresh for known creators first, followed by automated discovery**. That implementation order is settled and must not be asked again. Both discovery and comparison remain pilot requirements.

The [first acquisition milestone brief](../first-acquisition-milestone.md) makes the selected direction concrete and separates it from still-proposed collection bounds and verification details. This ticket remains open because a current API contract, actual returned evidence, limits, and the final acquisition scope depend on the minimal live check. Its claim is released while that prerequisite is active; the dependency prevents another session from treating it as ready.

### Scope clarification — modular pipeline first — 2026-09-29

The builder explicitly prioritized an abstract, modular pipeline from raw sources (including APIs or web collection) to canonical data, with deeper acquisition research allowed later. The Business API access task is removed as a dependency and closed as out of scope for this planning step; no live validation was completed. This ticket is reclaimed to design the source-independent interfaces.

Supplied example: `https://www.tiktok.com/@maronayannyan/video/7632620458235530504`. This is a video reference containing the handle `maronayannyan` and video identifier string `7632620458235530504`. These are parsed user input, not verified account identity, retrieved content, or metric observations. Preserve the identifier as text.

The integrated pilot destination is retained. This change narrows the immediate decision to ingestion architecture, without declaring that useful live evidence or the whole pilot is feasible yet.

### Proposed architecture — 2026-09-29

[Modular source-to-canonical acquisition pipeline](../source-to-canonical-design.md) compares three approaches and recommends separate collection and normalization interfaces around retained raw observations, followed by a shared canonical writer. It defines provenance, identity namespaces, missingness, replay, corrections, partial runs, and bounded acquisition. A local two-format fixture slice would verify the seams before selecting a live provider.

The [revised acquisition milestone](../first-acquisition-milestone.md) links that design and preserves the accepted known-creators-first order. This is a proposal, not a human-approved detailed contract or an implemented pipeline. The ticket remains claimed pending the builder's review; source-specific acquisition feasibility remains separate.

## Answer

Resolved on 2026-09-29 through the builder's response, "I like your recommendation," to the proposed modular pipeline and local fixture-first implementation slice.

Adopt the [source-to-canonical design](../source-to-canonical-design.md): separate collector and mapper interfaces around retained raw observations, followed by shared canonical validation and persistence. Platform and provider remain separate; compatible identity namespaces determine entity matching, while each source retains its own provenance. Replay, history, corrections, missingness, bounded runs, and partial failures belong to the shared pipeline contract.

The first implementation slice uses one local Python application, PostgreSQL, raw payload files, and two synthetic source formats (JSON and saved HTML). Prove ingestion and replay before adding a live provider. Fixture success will not be presented as TikTok access or real campaign evidence. The builder owns future developer integrations; marketers are not responsible for API configuration.

The builder subsequently deleted the separate implementation plan and requested execution under [Implement the local source-to-canonical ingestion slice](12-implement-local-ingestion-slice.md). This does not change the settled architecture decision. [Select the first live source and evidence scope](11-select-live-source-and-evidence-scope.md) retains the deferred provider-specific questions; the broader integrated pilot specification remains open.
