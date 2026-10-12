# Pilot acceptance and first implementation boundary

Status: agreed acceptance and build boundary, resolved through the builder's live answers.
Prepared: 2026-10-12.
Decision ticket: [Set pilot acceptance criteria and the first implementation boundary](issues/07-set-acceptance-and-build-boundary.md).

This is a build handoff for a local development pilot, not evidence that the pilot already passes its acceptance checks. The [minimum domain contract](minimum-domain-contract.md) and [accepted marketer workflow](issues/05-prototype-marketer-output.md) govern the behavior. Live-source readiness, deployment, and actual sales measurement remain separate efforts.

## What the pilot must make usable

The marketer can independently save a scoped investigation of the fixed caption/post sample and start a campaign from a brief, review automated account comparisons, confirm a versioned shortlist, and record a descriptive measurement plan. Shared evidence connects the features; neither feature requires the other to have run.

The pilot answers questions such as "What Hero Cushion claims and commerce references appear in these selected captions?" and "Which observed accounts are worth investigating for this brief, with what supporting posts and unknowns?" It does not turn this sample into a representative market trend, a complete account history, verified Japanese audience coverage, or a sales-performance ranking.

## Accepted human decisions

| Decision | Accepted choice | Review status |
| --- | --- | --- |
| Japanese review responsibility | Translation-assisted review only. Show the original permitted text, attributable translation and uncertainty; consequential original-language judgments remain provisional. | Confirmed by the builder. No Japanese-original reviewer is established. |
| Useful-result gate | Evaluate one monitoring investigation and one campaign on the same fixed sample against the marketer's manual approach. Require no uncorrected material unsupported claim or translation error detected in the chosen review process, at least one useful source-backed observation, and one keep/exclude/defer candidate decision the marketer would reuse. Record task times without a speed target or sales-improvement claim. | Confirmed after explanation. Original Japanese nuance remains provisional. |
| Initial workload and spend | Plan for one local marketer, the 19-post sample, about 10 monitoring summaries and 10 comparison preparations per month, zero new paid-source calls, and roughly USD 10 per 30 days of LLM use. Estimate costs by purpose rather than enforce workload/spend limits in code. | Confirmed with the builder's explicit correction: estimates, not programmatic caps. |

The checks below separate structural/evidence correctness, language quality, and marketer usefulness. Passing one does not establish the others. The accepted translation-assisted path permits exploratory technical/workflow evaluation, not validated Japanese-original accuracy. Absence of a detected translation error cannot establish absence of a real one.

## Fixed evidence and reset-safe loading

Use [the portable snapshot](../../examples/curated/jp-kbeauty-tiktok-2026-10-05/observations.json) as the default development input, not the live manifests. Its dataset ID is `jp-kbeauty-tiktok-public-video-sample-2026-10-05`; it contains 19 posts from 17 native accounts. The three completed source-run references define the original sample. Earlier partial runs, later captures, and synthetic fixtures are not extra members.

The sample has six Hero Cushion posts, one other APRILSKIN cushion post, and selected competing cushions. Publication dates range from 2023-08-09 through 2026-10-02; capture was on 2026-10-05. Profiles, follower counts, complete recent histories, audience geography, fees, availability, video/transcript evidence, and commercial outcomes are absent. The `curation` labels are development annotations to inspect, not verified semantic ground truth.

The current ingestion implementation has no offline importer for this snapshot. Its UUIDs point to the original database, and its JSON is not retained TikTok HTML. The first implementation must therefore:

1. Validate the dataset ID, schema, content digest, 19 record memberships, string native IDs, author references, source URLs, timestamps, metric types, and curation/source distinction before publishing a usable evidence set. Malformed records produce an inspectable error; an incomplete load cannot claim the complete sample.
2. Materialize imported snapshot observations through the acquisition/canonical boundary using an explicit local development policy. Preserve the original source observation/run IDs as origin references, and bind them to actual locally created observation/assertion IDs. Fresh local UUIDs must not be presented as the original web fetch.
3. Preserve the original capture and publication times, external namespaces, source adapter/provider lineage, and snapshot format/importer version. The time of importing is a separate system-recording time, never a new source capture.
4. Keep dataset membership stable using dataset ID and digest. Repeat import is idempotent; changed bytes under the same identifier are rejected or require an explicit new dataset version. An import into an empty database reproduces the same 19 selected posts and 17 accounts, despite different local UUIDs.
5. Expose the dataset manifest, member origin-to-local bindings, coverage, policy state, and digest through a public evidence-set reader. Decision modules do not resolve foreign UUIDs themselves or query adapter-specific tables.

Default import, inspection, retrieval, saved-view reopening, and deterministic tests make no platform/provider/model network request. Optional model preparation is explicit and credential-gated. A new live fetch is a separate operation and cannot silently replace the frozen baseline.

## Local architecture and review surface

Keep one Python application and the existing PostgreSQL instance. Responsibility seams remain acquisition/canonical evidence, shared knowledge, monitoring, and campaign decisions; they are modules, not separately deployed services. New business records belong to decision/knowledge-owned tables rather than expanding account/content ingestion entities into campaigns.

The evidence interface must provide a policy-filtered enumerated snapshot with stable account/content references, assertion/metric IDs, source locators, original permitted caption text, exact time semantics, missingness, and conflicts. The current `CanonicalReader.entity()`/`metrics()` APIs expose current fields and metric history but do not supply this complete frozen-set/as-of contract or workspace/actor context. Extend that boundary explicitly rather than letting a comparison read whichever database facts happen to be current.

Use PostgreSQL/ordinary Python keyword and relationship retrieval over the 19 records first. Add a small typed semantic vocabulary for brand/product mentions, product specificity, language evidence, and caption topics. A language model may prepare bounded semantic assertions and explanations behind this interface. It must return structured claims and cited assertion/span references; deterministic validation verifies references, types, and calculations. Automated reference validation does not by itself prove semantic support.

One local browser review surface is sufficient, with the existing HTML prototype as a layout/reference asset. The implementation needs two independently reachable areas: investigations and campaigns. A localhost server connects real persistence to forms and evidence panels; choosing its small framework is a reversible implementation detail. No frontend framework, hosted account system, queue, graph store, embeddings, or autonomous multi-agent runtime is needed to pass the pilot.

The surface shows original permitted captions beside source URLs, publication/capture times, translations when used, evidence-supported versus provisional judgments, coverage, and unknowns. A named local human actor confirms decisions; automation can write drafts only. Bind the application to localhost for the local pilot. A builder can run a guided marketer session on the same machine or share a permitted, explicitly frozen review export. The exporter rechecks source display/retention policy, carries dataset/version context, and cannot pretend to support edits in the database. Remote access and multi-user hosting need their own access/deployment design.

## Required monitoring behavior

- A human saves product/topic scope, intended market context, platforms, language constraints, and requested date window. Intended Japan context is not an observed audience location.
- Retrieval uses publication time for requested post windows and reports actual returned membership and capture age. A window containing no sample posts yields "no matching observations in this dataset", not "no market activity".
- An insight revision summarizes caption-supported findings, names the observed population, retains supporting assertion/span references, and identifies unknowns and review status. Counts of retrieved posts are deterministic and explicitly sample-scoped.
- Saving or refreshing an insight creates no campaign, comparison run, or selected account. Growth/change alerts are excluded without comparable repeated observations, a sampling frame, and a defined baseline.
- Reopening a saved investigation reproduces its permitted answer revision and evidence membership. Corrections or withdrawn support are visible rather than silently rewriting the old finding.

## Required campaign behavior

- The marketer creates a campaign with brand/product scope, objective, target market, platform scope, and at least one selection criterion. Dates, budget/currency, audience geography, fees, and availability may remain explicit unknowns. No signal or investigation link is mandatory.
- Known accounts can be supplied by exact references and marked `marketer_known`; retrieval finds additional candidates only within the fixed dataset and marks their campaign-relative origin. An absent account may be represented as an unverified requested candidate with no evidence, never an invented successful discovery.
- Preparation creates a comparison draft tied to the exact brief revision, evidence membership, method/version, and preparation time. Candidate subjects are platform accounts; Creator grouping is optional and needs corroboration or a recorded human identity decision.
- Each criterion has a support-aware state: satisfied, not satisfied on evidence, or unknown. Reasons cite permitted posts/assertions; requested account history, Japanese audience share, fee feasibility, or conversion effectiveness cannot be inferred from this sample. No universal creator score or performance ranking is required.
- The human may edit criteria, candidate selection and reasons, save a draft, and confirm an exploratory shortlist after acknowledging unknowns. Confirmation requires a supporting relevance reason for each selected account and an attributable human actor. Unverified human beliefs are labeled as human inputs, not silently promoted to source evidence.
- Confirmation pins the brief, comparison, selected account set, reasons/support, unknowns, reviewer and time. Saving is transactional, retry-safe, and version checked; retrying the same request does not create duplicate confirmed revisions. A conflicting edit fails visibly.
- New brief fields, refreshed evidence, changed selected accounts, or corrected judgments produce a successor comparison/shortlist revision. Old confirmed membership and original reviewer remain inspectable, subject to current support-policy checks.
- A short measurement-plan revision and later human decision note attach to the campaign/relevant shortlist. No action contacts creators or activates a campaign externally.

## Must-pass correctness and failure checks

Every check below is mandatory for a working local pilot. These are implementation acceptance cases, not tests already passed by the ingestion foundation. Use the real snapshot for happy paths and explicitly synthetic mutated fixtures for failure cases; never mix those fixtures into marketer results.

| Case | Required result |
| --- | --- |
| Empty database, then offline import | Exactly the frozen 19 post memberships and 17 native account identities are usable; origin-to-local lineage resolves; source times are unchanged; no network is needed. |
| Repeat import, changed digest, broken foreign reference | Repeat is idempotent; changed content has an explicit version/error; broken member/author/support references prevent a falsely complete evidence set. |
| Unrelated current rows or old partial runs exist | Frozen outputs contain only selected dataset members. Extra rows do not alter post counts, candidate reasons, or confirmed history. |
| Large native IDs, handle rename/reuse, namespaces | IDs remain exact strings; handle reuse does not merge accounts; identical handles across namespaces require a recorded association. Optional Creator corrections do not change historical selected accounts. |
| Monitoring is used alone | Saved investigation and insight are usable; campaign/comparison/shortlist counts remain unchanged. |
| Campaign begins without monitoring | The five required brief elements enable draft comparison. A missing required element fails with a field-specific validation error. No signal is generated to make the path appear complete. |
| Requested publication window excludes every sample post | Empty scoped result and actual coverage, rather than market absence or fabricated candidates. |
| Caption/topic claim or inclusion reason | Every source-backed claim resolves to permitted source/assertion and original caption span. Derived interpretation and human input are visibly labeled. Uncited/fabricated support is rejected or withheld. |
| Japanese text, product naming and unknown geography | A Japanese caption supports language relevance only; a generic cushion mention does not prove Hero Cushion/version/shade; product claims are attributed to the author. Audience country, fees and sales remain unknown. |
| `#PR`, Qoo10 reference and caption-only evidence | Literal markers are visible; paid contract/conversion claims and claims about unseen video technique are withheld. |
| Zero, missing, removed, unavailable and conflict | Genuine zero stays zero. Missing is not a negative result. Explicit removal suppresses the affected current value; conflict remains inspectable. A failed/challenged profile does not establish no posts. |
| Point counts and repeated observations | Display definition/unit/time/precision; repeated snapshots are not extra posts; selected post counts do not become creator averages or sales predictions. |
| Human draft and automation confirmation attempt | Draft remains unconfirmed until a permitted human confirms. Automation cannot forge a human actor or set confirmation state. |
| Save, reload, process restart and retry | Draft/confirmed record is in PostgreSQL and reopens with exact versions, membership and reasons. Retry does not duplicate a confirmed revision. Browser memory is not the save boundary. |
| Brief edit, evidence refresh or competing save | New work creates a successor revision; stale expected-version saves visibly conflict; old confirmation is not overwritten. |
| Expiry, revocation, or `can_display=false` after saving | Current summaries, evidence panels, reopened snapshots and exports hide affected source content and dependent explanations. Permitted decision metadata remains with unavailable-support/review markers. Hidden content cannot leak through copied reasons or caches. |
| `can_process=false` or actor outside the local workspace | Evidence is excluded from model payloads/new computations; unauthorized reads/writes fail. Display permission alone does not authorize processing. |
| Model unavailable, malformed answer, timeout or token limit | No fabricated success, automatic shortlist confirmation or unlimited retry. Keep the existing draft intact, show incomplete preparation and remaining unknowns; deterministic evidence inspection stays usable. |
| Untrusted caption asks the agent to change rules or reveal credentials | Caption is data. Preparation does not execute instructions, access secrets/tools, weaken criteria or bypass confirmation. |
| Missing model key/API configuration | Show model preparation as unavailable without fabricating output; deterministic evidence inspection and saving/reading an existing draft still work. Unknown pricing is reported as an estimate gap, not a programmatic spending block. |
| Descriptive sales measurement plan | Proposed definitions/source/matching/window and absent outcome access are visible. No attributed revenue, lift, ROAS or conversion figure is generated from views/likes/comments/shares. |
| Alternate market/category fixture | A non-Japan/non-beauty brief and product can use the same objects/actions; beauty attributes and Japanese-language rules are optional extensions. This checks extension structure, not global data coverage. |

Provenance/reference coverage must be 100% for displayed source-backed claims and chosen-account reasons. Material unsupported claims, policy leaks, false human confirmations and silently mutated historical decisions are correctness failures. A fully cited but mistranslated claim still fails its language review.

## Japanese-language review and extraction evaluation

The builder confirmed translation-assisted review only. Prepare a small annotation/evaluation packet from the 19 original captions. Each item records the post reference, exact original span, translation, proposed brand/product specificity, literal PR/commerce markers, attributed claim/topic, and ambiguity. Translation-assisted annotations are provisional references, not validated Japanese-original gold labels. Cover target and competing products, multiple products in one caption, generic product references, shorthand/hashtags, and unsupported inferences such as Japan audience or sales. Add separately labeled challenge examples for negation, comparison and uncertainty if the real captions do not exercise them.

Use a named rubric and method/prompt version. Reviewers mark each evaluated item as supported, unsupported, ambiguous, or not assessable and record materiality. An observed positive promotional claim is represented as an author statement, not a verified efficacy conclusion. No model self-confidence score counts as evaluation evidence.

- **Accepted translation-assisted review:** show original spans and attributable translation alongside the interpretation; record translator/model version and unresolved nuance. The marketer validates workflow and business usefulness and records material errors they can detect. Consequential original-language judgments remain provisional. Independent original-language validation remains a later language-readiness gate, rather than pretending two model translations establish it.
- **Technical review:** deterministic identities, source counts, save behavior, explicit text markers and provenance can be tested now. Unsupported inferences and known material translation defects must be corrected or withheld. Semantic summaries/relevance carry provisional review status even if no translation problem is detected.
- **Later original-language review:** if a qualified reviewer becomes available, that reviewer can adjudicate consequential extraction/relevance/translation claims against originals. Report raw correct/incorrect/ambiguous counts and the exact reviewed set; correct material errors before labeling those outputs reviewed. No broader Japanese accuracy percentage follows from 19 captions. Recruiting such a reviewer is not a prerequisite for building this accepted exploratory pilot.

Record precision/recall or item accuracy only with explicit reference-label provenance, denominators and treatment of ambiguity/unknowns; translation-assisted agreement must not be called Japanese-original accuracy. Do not invent a numeric pass threshold before a validated reference set exists. For generalization testing, reserve an untouched evaluation subset before tuning and report its size. If all 19 captions are used during development, call later checking a reviewed development-set check. A Japanese-capable reviewer may identify a future broader threshold after the first error profile is visible; that future calibration does not block building the technical workflow.

## Marketer usefulness evaluation

The builder accepted the following usefulness and evidence checks after reviewing their explanation. Use the same frozen corpus so data breadth is not confused with product assistance. The marketer first records a manual answer and account keep/exclude/defer choices using their existing intuition/monitoring approach over these supplied observations. Then they use the pilot for the two tasks, with order and any prior exposure recorded. This is a small usability/evidence review, not a controlled causal experiment.

1. Save one product/topic investigation with at least one concrete caption-supported finding and its limits. Ask which finding, if any, adds useful understanding and why.
2. Start an APRILSKIN Hero Cushion sales-in-Japan TikTok campaign with a marketer-defined criterion, compare known/retrieved accounts, confirm an exploratory shortlist or deliberately defer candidates, and reopen the saved decision. Ask which keep/exclude/defer decision and explanation they would reuse and why.

Record task time, manually inspected posts, missing evidence, corrections, helpful observations, and reviewer acceptance. Usefulness pass: at least one observation the marketer finds useful and one reusable evidence-based candidate decision, with no uncorrected material unsupported claim or translation error detected in the chosen review process. Unknown Japanese-original nuance remains provisional; this gate does not prove every translation correct. A material error is one that changes the interpretation of an insight, an inclusion/exclusion/defer decision, or the decision's stated evidence/limits. If no candidate has enough support, an honest defer decision can be useful; saving unsupported selections to manufacture a pass is unacceptable. Time is recorded without an initial speed target. Sales improvement cannot be measured with this dataset.

Technical correctness, translation-assisted review, and this usefulness gate receive separate pass/fail/pending results. Japanese-original semantic accuracy remains unvalidated even if the marketer likes the workflow.

## Initial cost/workload envelope

The builder accepted the small starting envelope with an explicit correction: workload and spending are estimates, not limits enforced by the application. Plan for one local marketer, 19 fixed posts, about 10 monitoring summary preparations plus 10 comparison preparations per month, and roughly USD 10 per 30 days of LLM use. Deterministic retrieval, save/reopen, manual edits, and cached valid results do not require another model call. Local Python/PostgreSQL replaces recurring cloud subscriptions; no new paid data call is needed. The earlier [budget research](research/03-operating-budget.md) is a planning hypothesis, not current-rate verification or approval to purchase anything.

Maintain a planning forecast by purpose, including preparation calls, translation and development evaluation. An initial allocation of the roughly USD 10 estimate can be described as USD 3 monitoring, USD 4 comparison and USD 3 translation/evaluation; these are adjustable forecast amounts, not entitlements or caps. For each purpose estimate input/output volumes, rate version, expected retries/cache effects and total cost. If rates or volumes are unknown, report the estimate as incomplete. Actual usage/cost may be recorded to improve the forecast, including out-of-application developer calls when known.

Do not reject work, reserve budget, impose a workload/spend limiter, or automatically stop on a forecast/spend threshold. Visible API/context errors and ordinary bounded retry behavior prevent a broken operation from pretending to succeed; they are technical failure handling, not a budget enforcement policy. Existing acquisition run/request/record bounds remain separate established behavior and are not changed by this planning decision. No autonomous indefinite model loop or media-processing workload is needed for the selected pilot.

Initial unit-cost evidence should report model/method version, input/output/cache units, latency, retries and observed or estimated spend for this workload. Provider/model choice is not necessary to settle the module boundaries; it must be selected using current primary documentation and the scoped Japanese evaluation before paid integration is called ready. Model configuration and missing credentials remain normal integration prerequisites, not budget approval gates.

Eventual active operation keeps the user's approximately USD 100/month all-in target. Hosting, backups, storage, source subscriptions/charges, models, tax/currency and reserve belong in that total. The local pilot does not prove that unknown live-source prices or a larger workload fit it. Hosting and sources need a separately measured workload/cost decision.

## Descriptive sales measurement plan

The pilot records intent and missing prerequisites rather than pretending to have outcomes. A minimum plan names the sales objective, proposed outcome definition, intended source/owner, product/listing/currency, period/baseline, account-to-campaign and order matching approach, attribution assumptions, and known gaps. Actual access to order/traffic/creator records is unknown until supplied.

Possible later measures include tagged-link traffic, creator-specific code use, matched orders/revenue, and returns-adjusted revenue if actual commerce records permit them. These are proposals. The attribution rule/window, baseline and reporting period must be chosen and versioned before calculation; the prototype's illustrative seven-day last-click rule is not a decision adopted by this ticket. Missing identifiers, unmatched orders, overlap between creator touches and data access remain explicit. Attributed outcomes would still not establish incremental sales lift. Causal experiments, attribution computation, campaign execution and outcome ingestion remain outside the first local pilot.

## First implementation slice and handoff

Build the campaign path first because it serves the accepted initial marketer decision. Its end-to-end acceptance is:

> From an empty local PostgreSQL database, import the frozen snapshot without source calls; create a human-authored five-element brief; automatically prepare a bounded, source-linked account comparison; let the human confirm a justified exploratory shortlist with unknowns; restart and reopen the exact saved revision in a local browser.

This first slice includes the importer/evidence-set read seam, minimal Brand/Product references and typed caption assertions needed for the criterion, brief/comparison/shortlist persistence, actor separation, provenance/uncertainty panels, save/version tests and explicit failure handling. A deterministic provider/stub supports offline tests; a paid model is optional until configured/evaluated. The slice must call deterministic preparation a rule-based draft when no model is used, rather than imply a running LLM/agent. Cost forecasting supports review; no budget/workload limiter is part of the slice.

Next, add independent saved investigations over the same evidence interface and measurement-plan/decision-note revisions, then perform the two-task marketer review. That completes the local pilot acceptance boundary. The ordering does not make monitoring dependent on campaign creation.

This decision is resolved and implementation tickets can now be created in a separate build effort. Extraction rules, small Python types, migration layout, template framework and fixtures are concrete implementation choices, not unresolved destination-level fog. The reviewed error profile can drive later extraction improvements. Repeat captures, global coverage validation, richer retrieval, profile histories, audience/fee data, live fallback/cost policy, hosted access, and commercial outcome learning remain later milestones.

## Inherited policy gaps and honest readiness

The builder has deferred source/use-rights review for the unpublished local technical prototype. That permits continuing this local planning boundary; it is not publication or commercial-source clearance and does not require a new vendor-credentials approval round here.

Current policy-aware canonical reads/replay hide denied, expired or revoked source evidence, and raw evidence revocation removes retained payload files. Current canonical assertion values remain physically stored; there is no actor-aware frozen-set API or dependency propagation to semantic extracts, copied reasons, caches, indexes or shortlist history. Those gaps must be covered for the new pilot paths before declaring the corresponding correctness checks passed. No blanket compliance or complete deletion capability is inferred from the existing ingestion tests.

For the local pilot, policy dependency tracking, refusal to process denied inputs, and current-display redaction must work across every store/projection the pilot actually introduces. Cleanup of retained source-derived copies follows the configured policy and is tested where used. Future hosted/public operation needs reviewed source clearance, separate human identities/access control, network exposure protection, secret handling, backup retention/deletion behavior and a measured all-in budget. Those are readiness conditions for that later stage, not reasons to reopen deferred live-source work now.

The builder's Japanese review path, usefulness gate and estimated spend/workload decision are recorded. The route to this local-development pilot is clear. Building the system, conducting the evaluation and passing these checks are subsequent work; this resolved planning ticket does not claim those outcomes already occurred.
