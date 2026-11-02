# System interface and acceptance contract

The [functional requirements](functional-requirements.md) are the accepted product behavior. This document preserves the shared public-operation semantics and acceptance scenarios; exact installed types, limits, errors and schemas belong to the owning [feature contracts](README.md#implemented-contracts). The [roadmap](roadmap.md) identifies remaining readiness and future design. A required scenario is an acceptance obligation, not by itself evidence of a live or human-quality pass.

## Public operations and authorization

Thin browser, CLI, internal endpoint or future MCP-compatible wrappers delegate to the same owning operations. Trusted server composition resolves workspace/actor authority; source text, generated output and submitted actor/origin fields remain data. A second protocol must preserve these authorization, source-policy and spending boundaries.

| Operation | Required context/input | Observable result and invariant |
| --- | --- | --- |
| Query current knowledge | Trusted workspace/actor, purpose, subject/search scope, relevant time/freshness constraints | Permitted knowledge with exact support references, relevant times, method/publication versions, coverage, and explicit missing states; no pending raw fetch output |
| Propose enrichment | Workspace/actor context, purpose, subject/search scope, requested refresh/expansion | Immutable identifiable proposal revision that can be reviewed; no acquisition submission |
| Approve and submit assistant enrichment | Actual human approval of an exact proposal revision/scope, workspace/actor, request identity | Durable task acknowledgment tied to that approval; changed scope, wrong workspace, or unsupported origin is rejected before work is dispatched |
| Submit configured acquisition | Server-established schedule or campaign context, bounded scope, request identity | Durable task with recorded configuration/coverage basis; an assistant cannot select this authority by changing an input field |
| Execute/resume task | Trusted worker authority and an admitted durable task | Bounded progress through existing ingestion and publication, with recoverable attempts and accurate coverage; logical effects remain retry-safe |
| Inspect task and updates | Trusted workspace/actor and task identity | Sanitized phase/outcome, attempts, failures, coverage, publication links, and attributable usage; acknowledgment is distinguishable from completion |
| Recommend and save | Exact campaign brief, executable criteria/ranking/coverage profile versions, request identity and revision concurrency context | Ordered supported KB candidates and an automatically saved attributed shortlist revision; incomplete coverage is explicit |
| Regenerate recommendation | Explicit user action and current campaign revision context | A newly assessed, automatically saved successor; discovery completion alone cannot invoke it |
| Inspect alert or graph/lineage | Trusted workspace/actor, purpose, selected records/filters | Governed views of permitted records and unavailable-support markers; no unrestricted source or secret exposure |

Submission request identities are scoped to the operation and workspace. An identical retry returns the original logical result; reuse with a materially different payload is rejected. Human-edited revision heads retain expected-version conflict behavior. Approval binds to one proposal revision and its resulting task; a retry must not turn one approval into multiple distinct tasks.

## Shared invariants

- Preserve the modular Python/PostgreSQL foundation, collector/mapper interfaces, bounded runner and owner-specific SQL. Cross-owner composition uses public ports. No broker, graph database, microservice or framework migration is required by this contract.
- Canonical evidence belongs to ingestion; business references/interpretations/publications belong to knowledge; campaign and monitoring decisions retain their own owners. Platform/native namespaces, source-specific metric definitions and relevant times remain explicit. Handles alone cannot establish Creator or cross-source equivalence.
- Frozen membership and consequential actual input manifests are immutable. New evidence, captures or methods support explicit successor work; current source permission, expiry and derivation health still govern reads, model dispatch and dependent writes.
- Separate collection, ingestion and publication. Task acknowledgment performs no collection. Persist exact authority, scope/limits, original actors, attempts/runs, phase/coverage and publications; retry identities and ownership fencing preserve committed effects. Partial success exposes both usable support and its failed remainder. Unknown remote outcomes retain their uncertainty rather than authorizing blind paid reissue.
- Campaigns remain marketer-initiated. Visible executable interpretations preserve requirements, exclusions and unknown policies. Candidate admission needs stable platform identity plus permitted published ingested support, allowing incomplete profiles. Reference-only seeds remain discovery gaps. Record deterministic versus model methods truthfully.
- Save recommendations automatically with actual producer, exact order/support/reasons/gaps and head checks; human confirmation/curation remains separate. Save the supported result before automatic coverage discovery admission. Completion offers explicit regeneration; it cannot rewrite history.
- Answers use existing permitted published knowledge. Exact assistant proposal approval grants one task and no broader scope or spending exemption. Approved on-demand work can exceed registered keywords; materially broader work requires a new approval. Later queries alone can use new publications.
- Scheduled keywords and monitoring topics have separate authority. At most ten keywords share an initial configurable fifty-new-post daily allowance. Stable day/timezone/identity and atomic canonical admission preserve usage across restarts, overlap and edits; refreshes remain distinct from new posts. Recency/engagement/trend prioritization and general progressive route selection remain explicit target policy rather than claims about the installed source-order fixture method.
- Recent X detection may precede full KB publication. Comparable windows/baselines govern numerical change; semantic methods expose actual inputs and provisional limits. Alert context uses only existing KB knowledge. Investigation cannot expand external research or create campaigns. Selected promotion preserves original policy, provenance and lifecycle.
- Coordinate metered admission across workers/tools using actual derived use plus bounded commitments. Preserve actuals, forecasts and unknowns separately; meter failure remains a control failure. Final reconciliation is idempotent and names liabilities; it grants neither response recovery nor another dispatch. Strict pre-call limits require defensible bounds/provider caps; delayed/unbounded charges retain visible overshoot limits.
- Source-dependent copies in every result follow exact dependencies and retention/withdrawal. Preserve safe metadata where permitted. Graphs are governed read projections; lineage distinguishes source response from publication. Existing measurement plans/notes stay proposed/human input rather than fabricated outcomes.
- Preserve loopback Host/Origin/CSRF checks, bounded escaped forms and server-owned actors. Hosted identity is separate future work. Never surface credentials or unrestricted provider payloads through operational views, errors or retries.

## Verification boundaries

Use the highest public operation that exposes a behavior, real isolated PostgreSQL schemas and temporary evidence directories. Restart tests reconstruct owners or use separate processes. Concurrency tests use competing connections/operations. Replace external provider/model/notification transport and controlled clock/fault boundaries with deterministic doubles; retain real task, ingestion, publication, budget and policy handling. Public campaign/monitoring and local HTTP journeys test their own responsibilities without a universal catch-all service. Test observable outcomes rather than private helpers, incidental SQL layout or a queue library.

Run [the shared checks](development.md) for each behavior change. Live route acceptance and actual language/usefulness review require separately attributed evidence, independently of simulated software tests. Missing configuration is a visible unavailable capability; values are not invented to imply readiness.

## Acceptance scenarios

| ID | Scenario | Required observation |
| --- | --- | --- |
| T01 | Submit approved offline enrichment, execute it, restart, and query | Same durable task and actual producer/approval remain visible; declared published support is queryable and completion links to it |
| T02 | Submit missing approval, changed proposal scope, foreign workspace, or forged schedule/campaign origin | Submission is rejected; no collector/model acquisition work is dispatched |
| T03 | Retry the same submission, publication, and completion delivery concurrently | One logical task/publication/event per request; changed payload under that identity conflicts; transport retries do not invent a second update |
| T04 | Interrupt after raw evidence persistence, canonical commit, publication commit, or completion commit | Resume uses committed work, preserves exact support, and does not repeat chargeable work or duplicate effects |
| T05 | Fetch succeeds but mapping, permission validation, interpretation, or publication fails | Accurate failed/partial phase is visible; unpublished records cannot support KB answers and no usable-update success is asserted |
| T06 | Search yields no usable new records or only unchanged published support | Coverage and no-update outcome are explicit; no fictitious publication benefit or market-absence claim is returned |
| T07 | Competing workers claim/resume the same task | Shared coordination prevents duplicate logical execution and preserves completed effects after a worker loses acknowledgment |
| T08 | Withdraw or supersede support during preparation and after publication | Consequential stale writes fail or exclude invalid support consistently; current readers redact/flag dependencies without substituting new evidence into history |
| T09 | Query after a later publication while reopening an older result | New queries can see the update; the old result retains exact membership, methods, times, order, and authorship under current policy |
| T10 | Rank an incomplete supported account alongside a handle-only seed | Supported account remains eligible subject to criterion unknown policy; un-ingested seed is not ranked; all gaps are visible |
| T11 | Interpret structured/natural-language criteria and assess a constrained candidate set | Recorded criteria/profile versions determine filtering/order; rationale references permitted assessed support; missing information is not invented |
| T12 | Model returns malformed, unsupported, scope-expanding, or authority-forging content | Output cannot approve acquisition, override controls, introduce unsupported candidates, or masquerade as a valid completed assessment |
| T13 | Generate, automatically save, retry, and optionally curate a shortlist | Automation can persist without human approval, exact rank and support reopen, retries return the original result, and curation creates an attributed successor |
| T14 | No candidate qualifies or campaign coverage is insufficient | Explicitly empty/thin supported result is saved, coverage reasons are shown, and bounded discovery is queued or its admission failure is visible |
| T15 | Campaign discovery publishes new knowledge | Notification offers regeneration; the old shortlist is unchanged until explicit regeneration saves a successor |
| T16 | Ask a supported and an unsupported assistant question | Supported claims cite current permitted KB support; unsupported information stays explicit; existing reads require no enrichment approval |
| T17 | Approve expansion outside scheduled keywords, then request broader work | Exact approved scope is accepted independently of keyword subscriptions; material expansion cannot reuse that approval |
| T18 | Repeat/overlap scheduled queries across keywords and workers at a day boundary | At most ten registered scheduled keywords; initial fifty-new-post allowance is shared across the configured day; duplicate posts consume no extra new-post admission; restart does not reset usage |
| T19 | Source route lacks discovery capability, returns partial coverage, or has pending/ambiguous paid work | Capability/coverage limitation is reported; supplied-reference success is not called query discovery; paid scrape is not blindly repeated |
| T20 | Refresh known evidence or run a new mapper while prior queries are recorded | Unnecessary unchanged work is avoided while legitimate new observations, separate namespaces, metric semantics, and older pins survive |
| T21 | Concurrent metered work approaches a configured ceiling | Actual spend plus bounded commitments is coordinated before calls; refused/paused work makes no additional chargeable call |
| T22 | Billing arrives late, an attempt is retried, or an expected meter fails | Commitments and actuals reconcile once; uncertainty and lag remain visible; meter failure does not silently permit unlimited work |
| T23 | Cost is unmeterable or strict charge bounds are unavailable | Forecast assumptions and enforcement limits are shown; unknown is not zero and no unsupported zero-overshoot claim is made |
| T24 | X collection has comparable baseline, missing baseline, and changed sampling coverage | Justified quantitative changes expose their context; inadequate/incomparable baselines cannot produce unsupported spike claims |
| T25 | Recent X evidence contains an attributable semantic anomaly | Versioned semantic assessment and relevant recent evidence support the alert; existing KB context is labeled separately |
| T26 | Detect/investigate without full KB publication and attempt external search/campaign creation | Alert can use permitted recent evidence, while investigation authority rejects additional external acquisition and campaign creation |
| T27 | Promote selected monitoring evidence, retry, then expire/withdraw original support | Promotion is traceable and retry-safe; both monitoring/alert and KB dependents honor the applicable policy lifecycle |
| T28 | Traverse graph and pipeline across visible and denied support | Permitted entities/relationships and task-to-publication links are navigable; denied text and secrets do not leak through details, errors, or notifications |
| T29 | Upgrade an existing local database and reopen pilot records/forms | Existing evidence IDs, historical human decisions, snapshot investigations, proposed plans/notes, and form-origin/CSRF protections retain their meaning |
| T30 | Evaluate relevance, translations, and usefulness | Attributable reviewed examples record membership, methods, denominators, and corrections; automated test success cannot manufacture human evaluation |

## Configuration and product boundary

Only the ten-keyword maximum and initial configurable fifty-new-post daily total are fixed numerically by the product requirements. Model/source contracts, ranking/coverage/freshness policies, anomaly windows/thresholds, retention and cost scope/rate/ceiling/period settings need explicit configuration and validation. Installed bounds are specified by each owner; they are not universal throughput promises.

The broader [proposal](../POPOSAL.md) retains multilingual intelligence, supported Creator associations, portfolio planning, outcome ingestion, attribution and causal measurement as the product destination. Their acceptance requires the relevant data, permission, assumptions and evaluation. Creator outreach, publishing, media buying and external campaign activation remain outside the product boundary. Human review is required to establish quality evidence, not before every automatic shortlist save.
