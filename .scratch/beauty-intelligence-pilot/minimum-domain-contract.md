# Minimum domain contract for the beauty intelligence pilot

Status: agreed minimum domain contract, resolved through the builder's live answers.
Prepared: 2026-10-12.
Decision ticket: [Define the minimum domain contract that extends beyond Japan and beauty](issues/06-define-minimum-domain-contract.md).

This contract defines the smallest shared vocabulary and behavioral contract for independent market monitoring and marketer-initiated campaign planning. It records decisions and their evidence-preserving consequences; it does not change production code, the database schema, source access, or the accepted workflow. Live-source readiness remains outside this local-development milestone.

## Accepted foundation

The [validated decision-brief workflow](issues/05-prototype-marketer-output.md) already establishes that:

- Monitoring informs the marketer and shared knowledge independently. A signal neither creates a campaign nor starts creator selection.
- A marketer starts campaign planning with a campaign brief. Monitoring evidence is optional context.
- Automation prepares candidates, evidence, comparisons, and draft reasons. The marketer reviews and confirms the selected set.
- Saving means a campaign-linked, versioned decision record with subject references, reasons, evidence and relevant times, unknowns, and reviewer context. Separate decision-owned storage in the existing PostgreSQL database is the accepted implementation direction.
- Japanese-language relevance can support an exploratory shortlist while audience geography remains unknown. It does not establish a Japan audience or sales potential.
- TikTok comes first; source access and live comparison-grade validation remain separate from the domain contract.
- The builder's live answer during this decision session confirms account-first candidates, with corroborated or explicitly human-corrected Creator associations optional.
- The builder also confirms exploratory comparison with the five minimum brief elements below and explicit unknown dates, budget, audience geography and creator fees.
- The builder confirms snapshot investigations and summaries as the first independent monitoring scope, reserving change/growth claims for evidence that actually supports them.

Product choices and their current human-review status:

1. **Confirmed — account-first selection:** select concrete platform accounts initially; a separate Creator identity is optional and needs corroboration or a recorded human identity decision before accounts are grouped.
2. **Confirmed — minimum brief and exploratory comparison:** require brand/product scope, objective, target market, platform scope, and at least one marketer-supplied selection need. Dates, budget, fees, intended audience detail, and availability can remain explicit unknowns during exploratory planning.
3. **Confirmed — first monitoring boundary:** saved product/topic investigations and evidence summaries over the fixed sample, reserving change/growth alerts for comparable repeated observations with a stated sampling frame and baseline.

The rest of this document spells out technical consequences of the accepted evidence and versioned-decision boundaries. Measurable usefulness, Japanese review responsibilities, score/extraction methods, and implementation acceptance are the downstream acceptance decision rather than additional claims settled here.

## Domain responsibilities

| Boundary | Owns | Receives and returns |
| --- | --- | --- |
| Acquisition and canonical evidence | Source references, observations, account/content identities, source fields, metric observations, provenance, coverage and source policy | Collectors return source-shaped observations; deterministic mappers return evidence-backed canonical candidates. No campaign or creator suitability inference belongs here. |
| Shared knowledge | Brand/product references, topic labels, evidence-backed semantic assertions, optional Creator/account identity decisions, permission-filtered knowledge views | Reads canonical evidence through a public interface; records derived or human assertions with their dependencies. Does not rewrite source observations. |
| Market monitoring | Investigation scopes and saved insight revisions | Searches shared evidence and returns scoped summaries or eligible signals. Has no implicit campaign-creation action. |
| Campaign decisions | Campaign briefs, comparison drafts, shortlist revisions, measurement plans and human decision notes | Uses shared evidence to explain candidates against a brief. Confirmation requires a human actor. |

Applications and agents use these boundaries, rather than reaching into an adapter or directly changing ingestion tables. These are responsibility seams, not a decision to create four services. One local application and PostgreSQL instance suffice for the contract.

## Minimum objects and supporting records

| Term | Minimum meaning and fields | Boundary and constraints |
| --- | --- | --- |
| Brand | Stable internal reference and preferred name; localized names or aliases when known | Distinct from an owner/operator such as APR. An owner relation can be an assertion without creating a full Company domain now. |
| Product | Stable internal reference, brand reference and product-family name; version, listing or variant specificity when supported | Hero Cushion is the family; a generic caption does not prove the Pink Edition, a generation or a shade. Brief scope and observed mention specificity can differ. |
| Platform account | Stable canonical reference plus corroborated external identities; handles/display names are assertions | This is the confirmed initial selection subject. An account may represent a person, group, brand or organization; account existence alone does not prove a Creator identity. |
| Content | Stable canonical reference, source-supported author-account relation, URL, caption and publication time when available | The sample contains caption observations and counts, not watched video, transcript, media or audience. An uncertain author relation remains unresolved. |
| Creator | Optional business identity for a person, group or organization producing content | One Creator can have multiple accounts; one account can change operators or involve several Creators. Association has evidence, role and known validity interval. No automatic person matching by handle or display name. |
| Monitoring investigation | Saved query scope: brand/product/topic, intended market context, platforms, language constraints, requested time window, author and revision | Market context describes the question; it does not prove that the retrieved population lives in that market. It can exist without a campaign. |
| Market insight | Saved answer revision with findings, evidence set, method/version, actual coverage and times, limitations and review status | A summary can be supported by selected posts. A claim of change requires a comparable baseline and method; one capture does not supply them. |
| Campaign | Stable planning record created by a human, with owner and current brief revision | Creation starts internal planning, not an external marketing activation. A campaign can be planned without a signal or insight reference. |
| Campaign brief revision | Immutable version of product/brand scope, objective, target market, platform scope and selection needs; optional context and unknown fields | **Confirmed:** five required elements above; optional dates, budget with currency, audience criteria, exclusions, formats, language and source insight links. Editing creates a new revision. |
| Comparison draft | One automated or human-prepared comparison run tied to one exact brief revision and evidence set | Contains candidate accounts, per-criterion supported judgments, unknowns, method/version and preparation time. It proposes; it is not a confirmed selection. |
| Shortlist revision | Exact selected account set and associated reasons, pinned brief/comparison references, support references and times, unknowns, human reviewer and confirmation time | A confirmed revision is a historical internal decision. Editing or refreshing produces a successor revision rather than mutating the old decision. |
| Measurement plan revision | Descriptive plan tied to a campaign and relevant shortlist revision: objective, proposed measures, definitions/windows, intended outcome source, matching assumptions and gaps | The sales objective does not create sales data. Unknown data access or absent baseline remain visible. Actual attribution, experimentation and outcome ingestion are later work. |
| Decision note | Human feedback, assumptions, later observations or learning attached to a campaign/shortlist revision, with author and time | Preserves learning without requiring an Outcome or Collaboration object before actual campaign records exist. |

Source observation, assertion, metric observation, identity decision and actor context are supporting records described below. Topic is initially a controlled or human-defined label on investigation/extraction scope; Audience segment, Collaboration, Social event and contracted Creator engagement do not need independent core objects until a real workflow requires their own identity and lifecycle.

## Relationships and identity

Required relationships are `Content authored_under PlatformAccount`, `Product marketed_under Brand`, `Campaign described_by BriefRevision`, `ComparisonDraft evaluates Accounts for BriefRevision`, `ShortlistRevision selects Accounts for Campaign`, and `MeasurementPlanRevision plans_measurement_for Campaign` with its relevant shortlist version. Findings and reasons refer to evidence through assertions. Optional context links can connect briefs or comparisons to insights; their absence is valid.

**Confirmed account-first subject, with evidence-preserving identity rules:**

- Source keys are strings with platform, identifier namespace, resource kind and native identifier. Large TikTok IDs are never numeric floating-point values. Supplied handles and URLs remain unverified references until corroborated.
- A handle rename updates an alias assertion without changing account identity. Reuse of an old handle by another native account creates no equivalence.
- Evidence from two namespaces is separate until a recorded mapping demonstrates compatible native-ID semantics. Cross-source metric names likewise need a declared comparability mapping; account equivalence does not make counts comparable automatically.
- Accounts may be grouped under a Creator only through a supported association or a human decision labeled as such. Human input is attributable but does not become independently verified source evidence.
- An identity decision records the input references, proposed association/equivalence, supporting assertions, actor/method, creation time, applicable interval if known, and what it supersedes. Prefer reversible associations to destructive merges of source entities.
- Correcting an account-to-Creator association preserves account and content evidence. It marks affected current comparisons for regeneration and saved decisions for review. A past shortlist continues to identify the exact accounts selected at that time; correction history explains why its prior identity interpretation changed.
- No automatic deduplication by language, similar names, shared handles, brand affinity or a guessed nationality.

## Evidence assertions and times

An assertion says something about an identified subject; it is not an unqualified property. The assertion envelope is:

| Part | Required semantics |
| --- | --- |
| Subject and predicate | Stable subject reference; a named, versioned property or relationship definition with expected value type. Use a small typed vocabulary needed by the brief, not an unrestricted ontology of everything. |
| Value and knowledge state | Observed value, explicit absence/removal, unsupported/unknown or conflicting candidates as applicable. Keep state separate from zero, false or an empty string. |
| Basis | `source_observed`, `derived`, or `human_supplied`. A language/script rule and product curation label are derived/human labels, not facts returned by the platform. |
| Support | Observation and assertion IDs, source locator or permitted text span, and direct source reference. Every derived reason retains its input dependencies. Human input retains actor/time and any evidence cited. |
| Method | Mapper, rule, extraction, prompt/model or human-review version relevant to the result. A free-form explanation cannot replace a method reference for calculated results. |
| Times | Source publication/event time when known; source-as-of time if supplied; capture time; system recording time; derivation/review time; applicable interval/window where meaningful. Their absence is explicit. |
| Uncertainty and conflict | Meaningful reason or confidence category with definition; alternative assertions when material. Do not treat a model confidence number as calibrated probability without evaluation. |
| Coverage and policy | Evidence-set membership, requested versus actual scope, synthetic status and processing/display/retention policy dependencies. |

Keep observational state independent from interpretation status. A caption can be observed while its product match is unresolved; a marketer may confirm a shortlist while its audience geography is unknown.

The minimal semantic vocabulary initially needs product/brand mentions with specificity, language/script evidence, content topic/aspect, and account-to-Creator association if used. Each derived mention must quote or locate its supporting caption span and retain its original text. A caption claiming durability supports “the creator states durability”; it does not establish tested product efficacy. A literal `#PR` marker supports the presence of that marker, not a paid contract. A Qoo10 mention supports a commerce reference, not a conversion.

Times must retain timezone and resolution. Compare content published during a requested window by publication time, while showing when its counts were captured. Capture order does not prove the chronological order of unknown source-as-of values. Refreshing old posts creates additional observations, not replacement history or new publication events.

## Missingness, metrics and coverage

- Preserve `not_returned`, `unavailable`, explicit `removed`, and genuine observed zero. Current-reader aggregate `unknown` needs inspectable reasons for the missing support; it must not silently mean zero.
- A bot challenge, HTTP error, private/removed resource and empty returned list are separate acquisition outcomes. A failed fetch is not evidence that a creator has no posts.
- A metric carries definition/version, source-native name, unit, subject, value, exact/approximate precision, raw display if retained, measured/source-as-of time and capture time. Never sum repeated snapshots as separate posts.
- Use common metric labels in the UI only with a declared definition mapping; retain each source observation and any conflict. A high count for one hand-selected post is insufficient to infer average creator performance or sales potential.
- A comparison records both requested evidence and actual evidence, including missing history, unavailable profile fields, missing audience/fee/outcome data, source selection, sampling dates and synthetic status.
- The fixed development sample is pinned by dataset ID, its three completed run IDs and member observation IDs. The earlier partial runs are not extra baseline sample posts. All inputs to a result identify their actual membership; current database contents are not silently substituted for the frozen evidence set.
- A result says “within these selected observations” rather than “the Japan market” when the evidence lacks a representative frame. The 2026-10-05 capture does not make posts from 2023–2026 a recent-post history.
- **Confirmed exploratory boundary:** comparison and a saved exploratory shortlist are allowed with known gaps. Each selected candidate still needs a supported relevance reason, acknowledged unknowns and explicit labels for required criteria whose results remain unknown. Unknown requirements do not become satisfied. Later campaign readiness or paid selection can require stricter evidence in a separate workflow.

## Campaign brief, comparison and save behavior

The five confirmed minimum brief elements give the automation an actual question. Selection needs are visible criteria such as Japanese-language cushion content; if an LLM proposes criteria from prose, the marketer can inspect and edit them. Criteria distinguish requirements from preferences and record how unknowns should be treated. An objective such as sales does not authorize substituting engagement counts for conversion evidence.

Each comparison uses one immutable brief revision and one enumerated evidence set. A candidate row references its account, possible Creator association, candidate origin (`marketer_known`, `retrieved`, or both), per-criterion evidence and judgment, unknowns and proposed reason. Domain identity does not globally label an account “discovered”; discovery is contextual to a campaign or working set. Automated rankings or scores require an explicit method later; the contract does not choose a ranking formula.

A human can save an unconfirmed working selection as a draft. Confirming a shortlist records the actor, time, selected subjects, reason for each inclusion, supporting assertion IDs, acknowledged unknowns and brief/comparison versions. Confirmation validates the internal selection; it does not verify every source claim, establish creator consent, or mean a campaign has been executed.

Saving a confirmed shortlist is transactional and retry-safe. A revision has a stable identifier and expected prior version; simultaneous incompatible edits must produce a conflict that can be reviewed, rather than silently overwriting another selection. A refresh creates a new comparison against the chosen brief. It cannot silently replace the evidence or membership of a confirmed shortlist.

Historical explanation combines pinned references and a permitted decision snapshot. Copy only the excerpts or generated material permitted for retention; pointers alone are sufficient when content cannot be copied. Policy checks still apply when reopening history. “Versioned” does not mean source-derived text can remain displayable after withdrawal.

## Internal actions and permissions

| Action | Actor and precondition | Result and failure behavior |
| --- | --- | --- |
| Save investigation / generate insight | Authorized human or configured monitoring job; readable evidence and explicit scope | Saves a scoped investigation or insight revision. Missing baseline prevents an unsupported change claim; it does not prevent a descriptive summary. Creates no campaign. |
| Start campaign / revise brief | Human marketer; required brief fields and owner context | Creates campaign/brief revision or a new brief revision. The caller sees validation errors for missing required fields. |
| Prepare comparison | Human-requested automation or background continuation of an explicitly initiated campaign; exact brief revision and processable evidence | Writes a draft with actual coverage, failures and unknowns. It cannot confirm a shortlist. |
| Save draft / confirm shortlist | Human marketer with decision-write permission; exact brief/comparison version and reasoned selected set | Stores a working draft or a new confirmed revision with audit context. Fails visibly on changed version or invalid references. |
| Record measurement plan / decision note | Authorized human; campaign and relevant revision reference | Writes an attributable revision or note. Unsupported measurements remain proposed, not observed outcomes. |
| Record/correct identity association | Authorized human or a designated evidence-supported rule; explicit subjects and rationale | Appends a reversible identity decision. Flags affected interpretations for review rather than changing past selected account references. |
| Withdraw evidence | Operator/policy event; identified evidence and dependency context | Hides unavailable support, removes retained copies as required, invalidates current dependent extracts, and preserves only permitted tombstones/audit metadata. |

Actor context minimally identifies workspace, actor and human/automation kind. The technical default for this local pilot is one workspace with attributable builder and marketer identities; no multi-tenant administration interface or approval hierarchy is needed. Human confirmation permission is separate from an automation actor's draft-write permission, reflecting the accepted human-selection boundary. Every read must intersect the actor's workspace access with the source's process/display policy; using the same PostgreSQL database is not authorization.

No internal action contacts creators, publishes, purchases media or activates an external campaign. That boundary is already fixed by the proposal.

## Correction, removal and historical decisions

Source page availability and source-use withdrawal are different:

- A failed fetch or disappeared page records an availability observation; it does not by itself revoke permitted historical evidence. A current view must show old capture times and unavailable refresh coverage. A source explicitly removing a field can supersede that source's earlier current value without making other observations disappear.
- Expiry or revocation excludes affected evidence from replay, current knowledge views and new comparisons. If another valid observation supports the same claim, the view can use it with its own provenance; otherwise the claim becomes unavailable.
- Dependent model extracts, search projections, cached explanations and copied source excerpts must participate. A saved shortlist may retain its permitted selected-account references, actor, time and decision version, but a hidden source value must not be reconstructed from its saved reason or copied excerpt. Redact dependent text as needed, retain an unavailable-support marker and require review.
- A historical decision remains the record of what was decided, with a visible current support-health overlay. New valid evidence can lead to a successor shortlist; it does not rewrite the old membership or reviewer.
- Correcting a caption/product extraction supersedes the assertion with method/actor context. It preserves explainable correction history where permitted and invalidates derived judgments that relied on the previous interpretation.

The contract does not equate local policy flags with verified publication clearance. Nor does it require the builder to reopen the already deferred source-access decision to review this model. Full dependency propagation is future implementation work, not a capability established by the ingestion slice.

## Extension rules and scenario tests

Core values separate campaign target market, observed text language, product/brand origin, source region and measured audience geography. None establishes another. Use standard market/language identifiers with localized display labels, but do not encode Japan or Korean beauty into source identities, brief workflows or metric definitions.

Product category extensions hold category-specific attributes and mention specificity. Beauty can add shade, finish, ingredient or skin concern when actual evidence needs them. A different category can supply its own typed vocabulary without replacing Brand, Product, Account, Content, Brief or Shortlist. Policies specific to a market are contextual/versioned facts rather than inferred from caption language.

| Scenario | Expected behavior under the contract |
| --- | --- |
| APRILSKIN Hero Cushion campaign for Japan | Brief names the selected product/listing scope, sales objective and TikTok. A caption containing ヒーロークッション supports a family-level mention; shade remains unknown unless stated. Japanese text can support content relevance while audience country, creator fee and sales remain unknown. |
| German-market launch of a US camping stove | Same brief/comparison/shortlist objects; product extension uses stove model/fuel type rather than cushion shades. A German caption does not prove a Germany audience, account nationality or the product's origin. |
| Monitoring sees several new cushion posts | Save a summary over those observations. Without a comparable baseline/selection method, do not assert market mention growth or automatically start a campaign. A marketer may later cite the summary in a brief. |
| Campaign begins without any insight | Required brief can directly trigger automated draft preparation after the human action. No signal reference is mandatory. |
| TikTok handle changes or is reused | Corroborated native account ID anchors identity; new aliases do not merge a different account. Old shortlist references continue to identify the selected account. |
| Web and Bright Data return the same handle | Separate namespaces remain separate until evidence supports an explicit account equivalence. Raw source metric definitions remain distinct even after equivalence. |
| A creator runs two accounts, or an agency takes over an account | Account-to-Creator associations carry role and known validity. A correction flags current interpretations; historical account selections remain inspectable. |
| A requested post has zero shares and unknown fee | Zero shares is an observed metric; fee remains unknown. Missing fee neither becomes zero nor makes a constrained budget feasible. |
| Human saves a draft, then changes the product or target market | New brief revision means the previous comparison is tied to the old question. Generate/review a new draft before confirming a new shortlist revision. |
| Old post counts refresh after confirmation | Additional metrics and a new comparison are allowed; the confirmed record remains pinned. Counts do not silently change the historical justification. |
| Supporting caption is corrected or its permission is revoked | Mark/redact the affected claim and dependent explanations. Keep permissible decision metadata and review marker; do not expose the hidden content from a saved snapshot. |
| A profile returns a challenge while ten hand-picked URLs work | Coverage stays selected post observations with profile/history unknown. Successful URL retrieval cannot become a complete recent-creator history. |

## Existing implementation cross-check

This contract was checked against local code and tests, without reading credentials or making source calls:

- [Canonical schema](../../src/smi_ingestion/schema.sql) currently permits only `account` and `content` entities. External identities include platform, namespace, kind, native ID and synthetic status. No Creator, Brand, Product, monitoring, campaign or shortlist tables exist.
- [Ingestion contracts](../../src/smi_ingestion/contracts.py) and [canonical reads](../../src/smi_ingestion/canonical.py) retain provenance, active derivation/version, source field states and separate metric observations. Reads exclude synthetic evidence by default and hide expiry/revocation by policy. They do not expose workspace/actor context or an as-of decision-snapshot API.
- [Direct web mapping](../../src/smi_ingestion/adapters/tiktok_web.py) uses `web:public`; [Bright Data mapping](../../src/smi_ingestion/adapters/bright_data.py) uses `tiktok:public`. Their metric definitions also differ. No cross-namespace association/correction mechanism is implemented. Content-to-author is currently an assertion value containing an external account key rather than a typed relationship object.
- [Evidence store](../../src/smi_ingestion/evidence.py) removes retained raw files on revocation and blocks replay/current display. `can_retain` currently governs raw payload retention; canonical assertion values are still physically stored. There are no model extracts or decision snapshots to invalidate yet. Full source-derived-copy cleanup cannot be claimed from this code.
- [Pipeline tests](../../tests/test_pipeline.py) cover separate provenance, replay, missing values versus zero, conflicts, metric history, explicit removal, expiry and revocation. They do not establish reversible identity correction, confirmed shortlist revisions or actor authorization.
- [Fixed sample](../../examples/curated/jp-kbeauty-tiktok-2026-10-05/README.md) has 19 posts from 17 accounts, six Hero Cushion posts, one other APRILSKIN cushion post and selected competing products. It lacks profile/follower data, complete recent posts, audience geography, fees, video content and sales. Curation labels are not normalized semantic assertions in the current database.
- The portable JSON retains source observation/run references from the original database. No offline snapshot importer or reset-safe observation-ID remapping is implemented. A future offline slice must bind those references explicitly; loading the JSON is not automatically a canonical replay of nonretained HTML.

## Handoff boundary

The domain decision is settled through the builder's three live answers. The glossary records domain terms only. The next acceptance decision should choose the first vertical slice, concrete Japanese-language evaluation and human review responsibility, useful-result thresholds, cost workload and known evidence limitations. Implementation can then introduce decision-owned types/storage and semantic extraction behind the evidence seam.

This contract deliberately does not choose a universal ontology, graph database, multilingual model, ranking formula, audience estimator, causal-sales method, paid source, refresh scheduler or multi-tenant product. Those choices require evidence or decisions beyond this minimum contract.
