# Define the minimum domain contract that extends beyond Japan and beauty

Label: wayfinder:grilling
Type: grilling
Mode: HITL
Status: resolved
Assignee: Codex / minimum_domain_contract
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 04, 05

## Question

Which stable objects, relationships, evidence assertions, and internal actions are required by the validated pilot workflow, and where do market- and product-specific extensions belong?

Exercise the contract against the Japan pilot and a hypothetical different product category and target market. Distinguish target market, language, product/brand origin, creator identity, and source account without assuming that one proves the others. Decide required provenance, relevant times, missingness, corrections, permissions, and source removal behavior. Refine the proposal's illustrative ontology using real workflow needs, document agreed domain terms in `GLOSSARY.md`, and avoid a universal ontology larger than the pilot requires.

Follow the accepted [decision-brief workflow](05-prototype-marketer-output.md): monitoring and its insights exist independently of campaign planning; a marketer initiates creator selection from a campaign brief. Model their shared evidence without requiring a signal-to-campaign relationship or making a signal an automatic trigger. Define the minimum brief, draft comparison, shortlist revision, and reviewer context needed by the accepted workflow.

## Comments

### Draft contract prepared — 2026-10-12

Prepared a reviewable minimum domain contract draft, now captured as the [agreed minimum domain contract](../minimum-domain-contract.md), against the accepted workflow, glossary, canonical schema, mapper/reader interfaces, pipeline tests and fixed real-world sample. It separates observed accounts from optional Creator identities, monitoring from campaigns, source assertions from derived/human judgments, and historical shortlist decisions from current evidence availability. It stress-tests Japan/K-beauty and a hypothetical German-market camping product without hard-coding either market or category.

Three proposed human decisions are ready: account-first selection with evidence-backed optional Creator grouping; minimum brief fields with explicit optional unknowns; and descriptive monitoring over the fixed sample until comparable repeat captures permit change signals. Automation, human confirmation and separate decision-owned PostgreSQL storage are already accepted and are not reopened. The draft also states the recommended identity-correction, revision, missingness and withdrawal invariants for review.

Important implementation gaps are explicit: source namespaces and metric definitions are not automatically equivalent; current revocation hides reads/removes raw payloads but does not physically remove stored canonical values or propagate through future decision snapshots; current code has no campaign/shortlist persistence, workspace authorization, semantic extraction or reset-safe offline importer. No code, schema, source-policy flags or shared glossary were changed. The ticket remains claimed because a HITL domain decision requires the builder's actual answers rather than the agent adopting its recommendations.

### Builder's live answers — 2026-10-12

The builder selected **Account candidates; verified Creator links optional**: platform accounts are the first selection subjects. Creator grouping requires corroboration or an attributable human identity correction and remains optional.

The builder selected **Allow exploratory comparison with explicit unknowns**: the minimum brief specifies brand/product scope, objective, target market, platform scope and at least one selection need. Dates, budget, audience geography and creator fees can remain unknown during exploratory comparison. Unknown criteria do not count as met and missing budget/fee information does not establish a feasible commercial commitment.

The descriptive-monitoring boundary is still awaiting a live answer. These partial answers do not resolve it by implication. The linked draft distinguishes these two confirmed choices from that remaining question; identity correction, versioning and policy-dependent historical display are technical derivations of the already accepted evidence/decision boundaries rather than extra approval gates.

The builder then selected **Start with snapshot investigations and summaries**. Independent monitoring initially saves scoped investigations and source-linked summaries over the frozen sample. Change or growth claims require comparable repeated observations and a baseline; the current capture supplies neither. All three domain choices are now confirmed.

## Answer

Resolved through the builder's three live answers on 2026-10-12. The [minimum domain contract](../minimum-domain-contract.md) holds the full contract and implementation cross-check; this answer records the settled boundaries.

- **Shared evidence, independent workflows:** monitoring investigations and insights operate without a campaign. A human starts campaign planning from a brief; no signal-to-campaign relationship is required and no signal creates a shortlist automatically.
- **Account-first candidates:** first select concrete Platform accounts. Creator grouping is optional and evidence-backed or human-attributed. Stable source IDs, namespaces and mutable aliases remain separate; cross-source associations and identity corrections are explicit and reversible.
- **Brief and exploratory comparison:** require brand/product scope, objective, target market, platform scope and one selection need. Budget, dates, audience geography, fees and availability can remain unknown. Candidate judgments distinguish supported relevance, unknown required criteria and unmet criteria; exploratory acceptance does not establish commercial feasibility or sales performance.
- **Small stable model:** Brand, Product, Platform account and Content underpin optional Creator identities, independent investigations/insights, human-created Campaigns, brief/comparison/shortlist revisions, measurement plans and decision notes. Typed supporting assertions and metrics retain provenance, times, methods, conflicts and policy dependencies. Topic labels and category-specific attributes extend the core; the illustrative proposal's broader ontology is not all required now.
- **Versioned decisions:** automated comparisons remain drafts. Human confirmation stores selected account references, reasons, exact brief/comparison/evidence versions, unknowns, actor and time. Refreshes or edits create successor revisions; historical selection membership is not silently rewritten.
- **Evidence integrity:** zero is distinct from missingness, failed retrieval from absence, caption language from audience geography, product family mention from exact variant, engagement from sales and a selected sample from market population. Identity correction or withdrawn support flags/redacts dependent explanations and preserves only permissible historical metadata.
- **Local scope:** snapshot monitoring and summaries use the 19-post development sample. Current namespaces/metrics remain source-specific; no complete Creator history, semantic extraction, campaign persistence, authorization or full deletion propagation is claimed from current ingestion code. Future decision-owned tables stay in the existing PostgreSQL instance behind explicit module interfaces.

No production schema or ingestion behavior changed. Verification checked all artifact links and recomputed the fixed sample's 19 posts, 17 accounts, six Hero Cushion observations and three completed runs. Precise language review, extraction/ranking evaluation, workload/cost allowances and measurable usefulness belong to [Set pilot acceptance criteria and the first implementation boundary](07-set-acceptance-and-build-boundary.md).
