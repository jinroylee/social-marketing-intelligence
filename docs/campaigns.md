# Campaign decision contract

[`smi_campaigns`](../src/smi_campaigns/__init__.py) currently owns internal campaigns, immutable briefs, visible simulated model criteria interpretations, rule-based comparison drafts and human shortlist revisions. The public interface consists of `CampaignStore`, `Brief`, `Criterion` and `Selection`. The sections below describe this implemented contract. The [target requirements](functional-requirements.md#a--campaign-based-recommendations-and-shortlists) additionally permit automatically saved ranked shortlists without human review or approval; that interface is not implemented yet.

## Implemented briefs and actors

`CampaignStore.start(brief, actor, request_id=...)` creates a human-authored campaign and its first brief. A brief requires brand/product scope, objective, target market, platform scope and at least one criterion. The catalog binds human-configured Brand/Product references; product IDs must belong to the stated brand. A brand-level brief can leave `product_ids` empty.

Criteria carry a stable ID, visible label, typed kind, expected value, inclusion/exclusion operator, requirement flag and unknown handling. `unknown_handling="acknowledge"` permits an exploratory decision with an explicit gap. `"defer"` blocks confirmation for an unknown required criterion. Optional campaign dates, budget, currency and audience details remain human context or explicit unknowns. Publication filters use a separate timezone-aware window.

`Brief.original_input` optionally retains the marketer's exact prose alongside those structured choices. Prose is human context, not an interpreted assessment or source evidence. Callers submit stable criterion IDs again when editing the same need; adding/removing needs changes the successor's criteria without changing historical IDs. The browser preserves IDs while editing rows or adding/removing neighboring rows.

Every newly saved brief atomically records `campaign_briefs.executable_profile`, an immutable structured snapshot pinned by `brief_id` and `brief_version`. `read_campaign` returns it alongside the original brief document, author and time; `read_comparison` exposes the snapshot from its exact pinned brief. Requirements/preferences, exclusions and explicit unknown policies retain the existing caption-judgment and human-confirmation effects described below. Changed prose or structured choices participate in request conflict checks and create attributable successors through `revise_brief`. The application cannot supply or overwrite execution-version metadata.

The installed profile versions describe these bounded capabilities:

| Profile | Recorded version | Installed behavior |
| --- | --- | --- |
| Criteria | `structured-caption-criteria-v1` | Human structured choices, with `human_structured_input` basis; literal caption method `campaign-caption-comparison-v1` |
| Ranking | `unranked-caption-comparison-v1` | Explicitly `unranked`: marketer-known accounts followed by dataset encounter order; no fit score or ranked assessment |
| Coverage | `fixed-selected-observations-v1` | `descriptive_only` for fixed selected observations; sufficiency assessment is `not_implemented` |

The profile records baseline unknown audience geography, fees, availability, sales effectiveness and recent-post history. A structured audience/fee/availability/sales need remains a need, even if its label sounds factual; it cannot supply source support. Migration leaves pre-profile revisions with `executable_profile=null`. Reads never reconstruct their historical method versions; a new brief revision records the installed profile. Briefs without separate prose retain their structured fields as the original input and preserve their existing request identity.

Known accounts use exact platform/namespace/native string IDs. Handles are not identity keys. In the legacy frozen-dataset path, unsupported references can remain requested candidates with no observed evidence. In the current-KB path they remain discovery gaps only.

`revise_brief(..., expected_version=..., request_id=...)` appends a successor rather than changing an earlier question. A stale expected version raises `brief_version_conflict`. Starting and revising require a trusted human actor in the configured workspace. Automation can read and prepare a comparison for an existing human-initiated campaign, but cannot save a human selection or confirmation.

`require_current_brief(campaign_id, brief_id, actor, expected_version=..., connection=...)` validates an exact current workspace brief and holds its campaign share lock until the caller's transaction commits. Dependent task admission joins this transaction, so a concurrent brief revision cannot change the authorized campaign question between validation and acknowledgment. Historical or foreign brief/version combinations fail with `brief_version_conflict`; task retries reopen their original acknowledgment before this new-admission check.

The local actor context is supplied by the trusted application boundary. It is not hosted authentication; a future browser server must construct actor kind/identity itself rather than accept those fields from submitted JSON.

## Comparison preparation

```mermaid
flowchart LR
    Human[Marketer] --> Brief[Exact brief revision]
    Brief --> Compare[Rule-based comparison]
    Evidence[Frozen evidence process view] --> Compare
    Knowledge[Exact knowledge run] --> Compare
    Compare --> Draft[(Pinned comparison draft)]
    Draft --> Review[Human review and unknown acknowledgement]
    Review --> Save[Transactional version-checked save]
    Save --> Shortlist[(Draft or confirmed shortlist revision)]
```

`prepare_comparison(campaign_id, brief_id, knowledge_run_id, actor, request_id=...)` pins the current brief, exact knowledge run, dataset ID/digest, enumerated actual observation membership, method/version, preparation actor and time. The catalog must match the brief. Old brief comparisons remain readable but cannot confirm a new decision after the campaign question changes.

The method is explicitly `rule_based`, version `campaign-caption-comparison-v1`. Candidates come from marketer-known exact references and accounts observed within the supplied dataset/platform/publication scope. Origin is `marketer_known`, `retrieved` or `both`, relative to that campaign. A requested account without evidence is not presented as successfully discovered. A publication window with no records yields no retrieved candidates, not an assertion of no market activity.

Each criterion has one of three states:

| State | Meaning |
| --- | --- |
| `satisfied` | A current, unambiguous interpretation supports the requested literal inclusion criterion in the selected captions |
| `not_satisfied_on_evidence` | A requested literal exclusion is contradicted by an observed matching mention/marker |
| `unknown` | The bounded evidence/method does not establish the criterion; absence of a match is not automatically a negative claim |

Supported kinds are Brand/Product/topic mentions, kana script evidence and literal PR/Qoo10 markers. Exact meaning follows the [knowledge method](knowledge.md): a family mention does not establish a variant, kana does not prove caption language or audience geography, and a PR marker does not establish a paid contract. Semantic review remains provisional. Other typed needs—caption language, audience, fees, availability, sales, history or custom criteria—remain unknown under this method.

Every candidate shows baseline unknown audience geography, fees, availability, sales effectiveness and complete recent-post history, plus unmet unknown criteria. The method does not calculate a global creator score, creator-average performance or sales prediction. Evidence panels return exact interpretation/source assertion IDs, original spans, source references and publication/capture times through policy-aware readers.

Preparation checks process/retention permission and current derivations before committing source-dependent copies. It locks source support and rejects a withdrawal/correction race with `comparison_support_changed`. New work uses a new request ID and can pin a newly prepared knowledge run; repeating an identical request returns the original draft.

## Current-KB comparison

`prepare_current_comparison(campaign_id, brief_id, actor, request_id=..., interpretation_id=None, include_synthetic=False, max_age_seconds=None)` prepares an additional comparison over current committed knowledge. It uses the exact current human brief, optionally the explicitly selected successful immutable model criteria interpretation for that same brief, and the existing deterministic caption criteria. It performs no acquisition, model dispatch, ranking or automatic shortlist save. Legacy `prepare_comparison` and its frozen-dataset behavior remain supported.

The campaign owner calls public `KnowledgeQueries.search` and `account_support`; it never queries knowledge or ingestion tables. Retrieval examines at most the 100 newest committed publications and pins at most 100 distinct support bundles. Platform scope is enforced in retrieval and account selection; the brief's inclusive publication window applies to observed source publication dates. A configured window excludes observations whose publication date is unknown. Brand/product needs are evaluated through the recorded criteria, not inferred from language or geography. The result contains at most 100 stable platform/namespace/kind/native account identities, ordered by publication/member/account encounter order, explicitly **unranked**. Candidate and retrieval bounds are reported independently.

One current, process/retention-permitted ingested observation supporting an account identity suffices. Account subjects on assertions (including missing profile fields) or metrics, and observed post-author account assertions establish identity. Mutable handles and URLs do not. Full profiles, captions, interpretations, fees and history are not prerequisites. Caption claims must belong to the candidate's account/author subject and exact catalog. Unsupported or out-of-scope marketer references are recorded as `coverage.discovery_seeds`, never supported candidates. Missing attributes remain explicit gaps, including unknown contracts; kana, language and PR markers do not establish audience, contracts or sales.

Each candidate retains its exact actual support manifest and source capture/as-of/ingestion dates. The linked `knowledge_query` exposes publication, observation, derivation, assertion, metric and interpretation IDs, method/catalog/publication versions, original retrieval coverage and current health. Freshness uses source capture time; an omitted threshold is `not_assessed`, and ingestion/publication do not renew it. Candidate explanations preserve the selected freshness assessment. Original human/generated profiles stay exact; `execution_profile` separately records this run's actual `current-kb-caption-comparison-v1` method, brief/profile versions, unranked ordering and bounded coverage.

Required observed exclusions produce `excluded_on_required_evidence`; required unknowns with `defer` produce `deferred_unknown_requirements`. Otherwise the displayed assessment is `eligible_with_explicit_gaps`, retaining each criterion's acknowledge/defer policy and requirement/preference status. These states do not imply human acknowledgment or ranking. Zero candidates records `no_eligible_supported_accounts_in_campaign_scope`, preserves discovery gaps and saves a readable empty comparison, without asserting an empty market.

Preparation holds the campaign head, workspace publication frontier, source policy and exact derivation locks through the draft/result commit. A concurrent publication or withdrawal serializes before selection or after that commit. Identical retries return the original draft before checking a newer brief or KB; changed retries conflict. Reopening never refreshes membership, order, explanations, brief/profile or support. Current display/process permissions and supersession still govern visibility, and retention withdrawal permanently purges copied bodies and dependent human reasons. An explicit new request can reconsider currently permitted support.

## Shortlist persistence

`save_shortlist(comparison_id, selections, actor, confirmed=..., expected_version=..., request_id=...)` saves an unconfirmed human draft or appends a confirmed revision. The initial expected shortlist version is zero. Subsequent saves must name the current head; stale competing edits raise `shortlist_version_conflict`.

For each confirmed account:

- It must be a candidate of this exact comparison.
- A nonempty human reason must cite at least one current positive relevance interpretation from that candidate's judgments. Invented or cross-candidate support is rejected.
- All recorded unknowns must be acknowledged; submitted acknowledgements can reference only those declared unknowns. A required contradicted exclusion or required unknown set to `defer` prevents confirmation.
- Its support must still be processable and displayable. The comparison's brief must still be current.

A human reason is labeled `human_supplied`; confirmation records an internal selection rather than independently validating every sentence of that reason or its supporting semantic interpretation. An empty selected set can record deliberate deferral. Automation cannot set confirmation state through this action.

Saving locks the campaign head, validates expected versions and commits the revision, selected membership, exact brief/comparison links, supporting interpretation IDs, acknowledged unknowns, human actor and timestamp together. Identical request retries return the original revision even if the head subsequently advanced. Reusing an ID with a different payload or actor raises a request conflict. Request IDs are scoped to the relevant action/campaign; campaign-start IDs are workspace-scoped.

Edits, new evidence or changed judgments produce successor brief/comparison/shortlist records. Old selected membership and reviewer attribution remain inspectable. `read_campaign`, `read_comparison` and `read_shortlist` reopen database-backed records across process restarts.

## Source-policy overlays and cleanup

Comparison candidates retain explicit observation, source assertion and interpretation dependencies. Copied candidate bodies and human reasons inherit that support's policy. A current read checks purpose-specific permission, derivation health and surviving knowledge interpretations.

Denied support hides the candidate body, reason, evidence excerpts and dependent explanations, returning unavailable metadata. Superseded derivations require review. A retention withdrawal, expiry or revocation purges the stored candidate body and associated saved reasons. Account references, membership, actors, times and permitted audit/support IDs remain. Retrying the same request never rebuilds a purged explanation.

Redaction is conservative at candidate scope: if any cited observation is withdrawn, the copied candidate explanation and its saved reasons are withheld rather than guessing which sentences can survive. An explicit successor comparison can reconsider still-permitted evidence with its own provenance. Reconciliation runs synchronously on comparison/shortlist reads and saves. It does not claim a background deletion service or complete cleanup of operator-managed files.

## Local operator workflow

After migrating and preparing the frozen sample's knowledge:

```bash
uv run smi-ingest migrate
uv run smi-ingest start-campaign examples/campaigns/hero-cushion-brief.json --request-id campaign-1
uv run smi-ingest prepare-comparison CAMPAIGN_ID BRIEF_ID KNOWLEDGE_RUN_ID --request-id comparison-1
uv run smi-ingest inspect-comparison COMPARISON_ID
uv run smi-ingest save-shortlist COMPARISON_ID selections.json --expected-version 0 --request-id selection-draft
uv run smi-ingest save-shortlist COMPARISON_ID selections.json --confirm --expected-version 1 --request-id selection-confirmed
uv run smi-ingest inspect-shortlist SHORTLIST_ID
```

IDs come from preceding command results. `selections.json` is a list of `candidate_id`, `reason`, `support_ids` and `acknowledged_unknowns` taken from human review of that comparison. Empty selections are `[]`. Submitted selection JSON cannot supply actor or confirmation fields. The console commands run as the named trusted local human operator; `--actor` records attribution.

The [local browser surface](local-review.md) implements this workflow over the same public actions. `list_campaigns` returns heads/human brief context; `read_campaign` includes comparison/shortlist history metadata and saved original-input interpretation outcomes. [Monitoring](monitoring.md) operates independently. [Campaign planning](planning.md) adds proposed plans and human notes, using public `shortlist_support` for content-free dependencies. No action contacts creators, activates campaigns or calculates outcomes.

## Accepted future recommendation workflow

Extend the installed current-KB deterministic comparison and structured/simulated natural-language profiles with live model operation and LLM assessment. The current unranked/descriptive version labels do not claim that assessment or sufficiency checks are implemented. Eligibility requires stable account identity and at least one permitted ingested supporting observation; full profiles/history are not required. Other missing/stale attributes remain visible. The current-KB path already treats unsupported references as discovery inputs; legacy frozen comparisons retain their earlier compatibility behavior.

The agent can save the ordered recommendation as a shortlist without a human save, review, confirmation or approval step. Record actual authorship, ranking/model/method versions, source support, exact brief, rationale and gaps. Optional human curation/review is separately attributed; an automated save cannot claim human confirmation. This deliberately extends the current store's human-only authority, as recorded in [ADR 0003](adr/0003-automatic-shortlist-persistence.md).

Coverage assessment evaluates quantity, relevance and freshness against an explicit profile. Insufficiency automatically requests bounded discovery through the shared task service. The returned/saved recommendation still uses only the current KB. After ingestion/publication, notify and offer regeneration; an explicit regeneration creates a successor and never silently changes saved membership, order or explanations. Current policy still governs the availability of pinned source-dependent text.

Automatic persistence is internal decision support, not external campaign activation or permission to acquire additional assistant-requested evidence. Assistant enrichment approval and hybrid spending checks remain separate contracts.

## Bounded natural-language interpretation

`CampaignStore(..., model_route=ResponsesRoute(...), model_transport=..., model_credential=...)` composes one explicitly configured OpenAI Responses route. `ResponsesHTTPTransport(enabled=False)` is a concrete fixed-endpoint HTTPS adapter, disabled by default. Trusted server composition must opt in with `enabled=True`, provider execution mode and explicit credential/configuration. There is no environment-key lookup, default model/rate, implicit retry or paid preflight. CLI/server startup without composition visibly reports the route unavailable. **All verification in this change uses simulated external connections**: no live receipt, account readiness or language/marketer-quality result is established.

Provider mode supports the explicitly selected snapshot `gpt-5.4-mini-2026-03-17`, not an inferred model alias. Contract `openai-gpt-5.4-mini-2026-03-17:2026-10-20` pins the [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini), verified 2026-10-20: 400,000 context, 272,000 maximum input and 128,000 maximum generated output tokens. The route must declare the full 272,000 input bound and a finite configured output cap (this journey caps it at 10,000). `truncation=disabled` prevents silently dropping constraints. This is a conservative model-input admission bound, **not** a character-derived exact token estimate. Unsupported model/contract/bounds or missing model/credential/rate classification/enablement block before transport. No commercial rates are installed: the operator explicitly supplies rate version, scope unit rate and input/cached/output weights. Cache-write input uses the uncached-input weight rather than inventing a separate price class.

The single request uses strict structured text (`text.format`), `service_tier=default`, `store=false`, `background=false`, no tools and no streaming. The concrete adapter fixes host `api.openai.com` and path `/v1/responses`, uses verified TLS, refuses non-200 responses without following redirects, closes on every outcome and enforces finite request/response byte caps plus connection/socket/deadline timeouts. No secondary retrieval, polling or hidden request occurs. Timeouts/lost acknowledgments remain uncertain consumption; client limits do not establish provider cancellation or a final-billing deadline.

`interpret_criteria(campaign_id, brief_id, human_actor, expected_version=..., request_id=...)` reads original prose from an existing human-initiated brief and commits one attempt before I/O. Identical body/actor retries reopen that outcome across restart and later brief revisions without another dispatch; changed reuse conflicts. New requests require the exact current workspace brief/version. Interrupted `in_progress` attempts remain visibly in flight or uncertain. New identities are explicit new work, not recovery permission for an earlier possible charge.

Successful profiles retain requirements/preferences, inclusion/exclusion, acknowledge/defer unknown policies, method `campaign-criteria-responses-v1`, schema `campaign-generated-criteria-v1`, original brief/prose linkage and exact profile revision. Generated IDs are namespaced under the interpretation identity. The profile **appends** independently validated generated criteria to unchanged human structured constraints. Human input and `model_generated` basis remain visible. Generated values are campaign needs, never source facts, task authority or approval; they cannot replace platforms, market, product scope, candidates or external-action limits. Unsupported/extra fields, authority-forging objects and malformed criteria are invalid. Existing caption-method limitations remain unchanged.

`read_interpretation` and campaign history expose input, requester, model automation, configuration, outcome, validated profile, usage and cost-operation link. The browser displays the saved interpretation before offering separate explicit selection in `prepare_comparison(..., interpretation_id=...)`. Selection requires success for that exact campaign/brief. Comparison drafts pin the immutable profile; current-brief checks protect commit/confirmation. A successor racing transport makes the result `stale`, with no executable profile. Historical comparisons remain unchanged. Assessment stays rule-based and unranked; LLM assessment is separate work.

Durable outcomes include success, invalid/refused/incomplete, blocked, meter failure, transport uncertainty, stale and interrupted in-progress. Only matching-model `completed` or `incomplete` response envelopes with valid final usage can settle; provider mode also requires the returned standard service tier. Queued/in-progress/unknown statuses, unsupported terminal statuses, model/tier mismatch and missing/invalid usage retain the reservation and fail the expected meter. No partial count releases a full bound. Valid final usage settles even malformed/refused/incomplete/stale interpretations. Raw responses, refusal strings and provider exceptions are not retained. Explicit final operator reconciliation and separate meter-health recovery remain with [the cost owner](costs.md#responses-token-measurement-and-provider-provenance).

A simulated execution mode remains available for local fixtures with `synthetic-transport-input-bound-v1`. Its input bound is a declared fake-service contract, not proof for commercial dispatch. The transport execution mode must match the route and immutable cost-scope basis; a real HTTP adapter cannot run under synthetic classification. `interpretation_capability` inspects configuration/enablement without I/O, credentials or admission. All test keys/rates are unmistakably synthetic even when testing the provider-shaped accounting path.
