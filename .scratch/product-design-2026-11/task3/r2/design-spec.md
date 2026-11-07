# Product UI design specification, r2

Revision r2 is a review proposal, not an approved design or an implementation plan. The [interactive prototype](prototype.html) uses visibly labeled fixture data and in-memory state. [Task 1 recovery decisions](../../task1-recovery/decisions.md) establish the confirmed brief; [Task 2](../../task2/codebase-analysis.md) establishes current owner boundaries. The actual human must review this exact artifact before Task 4 starts.

Open [prototype.html](prototype.html) directly from disk. The artifact has no dependencies, network calls, browser storage, source requests, email delivery, or paid actions. The earlier r1 server URL does not identify r2. Browser access was declined and has not been retried. See [changes.md](changes.md) for the focused review requests.

## Product and intended experience

The primary user is a beauty marketer planning a Korean or Japanese market campaign while building reusable market knowledge. The starting page is a populated campaign because the confirmed review priority is brief to automatically saved shortlist. Monitoring, assistant questions and graph investigation remain independently accessible. Campaign creation is an internal planning action, never external activation.

A usable result answers four questions without opening a technical log: what is recommended, why, what is unknown, and what changed? A contextual inspector supplies original support, dates, observed/derived/human basis and limitations. Long manifests and operational identifiers sit behind disclosure controls. The global fixture notice applies to every destination and dialog. Target success examples are design examples, not assertions of installed capability.

## Information architecture and alternatives

The recommended A layout has persistent left navigation, a central task area and a right evidence inspector. Primary destinations are Campaigns, Knowledge assistant, Market monitoring and Knowledge graph. Operations destinations are Pipeline & lineage, Scheduled discovery, Spending and Inbox. Measurement & learning remains visible and is linked from the campaign. The header carries workspace context, EN/KO switch and inbox access.

```text
[Fixture notice]
[Brand                       Workspace  Language  Inbox]
[Destinations] [Current decision and actions] [Evidence]
              [Version / scope / coverage]    [Dates]
              [Result or working area]        [Unknowns]
```

Variant B, Campaign desk, places navigation horizontally and evidence below a full-width work area. It gives account comparison more width and reduces vertical destinations, but requires scrolling to cross-check evidence. Variant C, Research notebook, places the inspector before the decision in reading order and visual layout, with a narrower reading column and a prominent current question. It suits source review but increases the distance between account rows and actions. These are real structural alternatives on the same route, not palette variations. Use `?variant=A`, `B` or `C`, or the floating prototype switcher. The switcher is review chrome and must never enter production.

Campaign-first A is recommended because it keeps the decision and its evidence visible together while preserving independent investigation. A universal chat-first interface would conceal saved versions and monitoring baselines. A graph-first home would make routine brief entry and ranking harder. Both remain intentional destinations rather than replacing the full workspace.

## Visual and language system

| Token | Value | Use |
| --- | --- | --- |
| Signal | `#E6002A` | Primary action, selection focus, graph account/content fill |
| Petal | `#F4ABAF` | Active navigation, relationship accents, quiet selected regions |
| Graphite | `#3E3A39` | Body text, graph background, prototype chrome |
| White | `#FFFFFF` | Workspace, primary-button text, graph labels |

Text uses the system CJK-capable stack with Apple SD Gothic Neo, Hiragino Sans and Noto Sans CJK fallbacks. No font download is required. Page title is 32px, section title 22px, body 15px with line-height 1.55, secondary text 13px. Labels use sentence case. Most prose stays below 80 characters per line; wide evidence tables scroll within their container.

Status always has text. Solid, dashed and dotted graph lines distinguish observed, derived and human relationships. Circle, rectangle and diamond distinguish account, post and catalog entity. Petal carries graphite text; white text is reserved for sufficiently contrasting red or graphite. Focus is visible with a 3px red outline and offset. Reduced-motion preferences are respected; there is no idle animation.

The EN/KO switch changes navigation, actions, explanations, validation, state controls, variant names and main accessibility labels. Draft text and semantic select values remain in memory on switch, as do page, tab, selected graph entity, traversal settings and revision. Source captions stay in their original language. Target market, UI language, evidence language, product origin and audience geography are distinct. Japanese source text uses natural wrapping and no forced letter spacing. A Japanese UI or automatic source translation is not claimed. Long Korean and Japanese labels must be visually reviewed at narrow widths before implementation.

## Campaigns

The campaign header identifies the internal planning context and exact brief version. New campaign opens a name form, then a brief with brand/product scope, objective, target market, platforms and at least one selection criterion. The sample supports one active fixture campaign at a time; creating a new fixture resets its current shortlist history. A production campaign index and per-campaign route must retain all campaign contexts.

Brief & criteria shows original natural-language needs, typed requirement/preference/exclusion meaning, missing-information policy and the selected executable interpretation. A model suggestion is additive and attributed. Users explicitly select the interpretation, preserving human constraints. Saving a brief appends a version; existing shortlist versions keep their original brief and criteria. Empty required fields produce guidance and preserve input.

Saved shortlist presents ordered account candidates with their platform/native identity, supported fit, capture freshness and explicit unknowns. An incomplete profile remains eligible when stable platform identity and one permitted ingested supporting observation exist. Display names and handles are labels, not identity keys. Fees, availability, audience location and performance stay unknown without evidence.

Generating or regenerating a recommendation automatically saves it before the coverage discovery disposition. The UI needs no approval to save an automated shortlist. The visible badge identifies automated authorship, and optional human curation creates a separately attributed successor. Curation retains selected membership and a human reason, including an empty set. It does not imply creator consent or factual verification.

The coverage summary separates quantity, relevance and freshness. Insufficient coverage leaves the saved result usable within its limits and shows a separately configured campaign-discovery task. That origin uses its own configured authority, without borrowing assistant approval or asking for a new approval on every automatic campaign task. Source capability, hard bounds and spending admission still apply.

Regenerate from current knowledge reviews the current brief and current permitted knowledge, then appends an automatically saved successor. It does not silently overwrite an old result, promise better ranking or authorize external retrieval. Version history opens pinned member lists, brief/criteria, method, support and author. New publication alone does not change the selected result. Current source policy can withhold historical source content.

## Knowledge assistant and research

The assistant is a conventional chat view. A thread rail offers New conversation and saved fixture threads. The center contains distinct user and assistant turns in a scrollable log. A bottom composer accepts multiline text. Send or Enter appends a user turn and a scripted assistant follow-up. Shift+Enter inserts a newline; IME composition does not send. Empty input adds no turn. Sending clears only that thread's draft. Each thread retains its turns, draft, and scroll position across EN/KO and destination changes. Reload clears fixture state.

Sources, original-language extracts, dates, actual-input membership, claim details, and research status appear in secondary disclosures. The initial answer remains an extractive published finding. Follow-up messages explicitly identify themselves as scripted fixtures. Arbitrary input does not invoke a conversational model or imply a validated answer to that arbitrary question. The current installed backend still selects exact published findings for one bounded question. It has no installed multi-turn conversational synthesis.

The assistant supports existing published knowledge without enrichment approval. Missing recent coverage is distinct from empty support, ambiguous scope, configuration failure, invalid model output, and current-policy withdrawal. A model failure alone never establishes a research gap. A dependent answer becomes unavailable if its full input loses permission, while safe historical identity can remain. Source publication, capture, and KB-publication dates retain separate meanings. UI language changes neither original text nor evidence meaning.

Research status sits between the message log and composer. Its disclosure contains intent selection, exact proposal review, a task link after submission, and target research steps. The target claim inspector and richer grounded synthesis remain roadmap work under ADR 0017 and ADR 0018. Claim validation must check each factual claim against actual inputs; citation membership alone is insufficient. Invalid claims or invalid full support withhold the claim or answer.

### Production conversation contract

A future conversation owner/read adapter must provide workspace and conversation IDs, thread titles, ordered immutable turn IDs, human actor and original input, parent/context turn IDs, and per-thread drafts. Bounded turn history needs a stable cursor and head version. A new message supplies a request identity and expected thread head. Retry returns the original turn/result; a changed prompt is a new operation. Concurrent edits preserve the draft and ask the human to resolve the new head.

Each assistant turn pins question scope, the explicit context actually supplied, query and full input manifest, selected findings, claim/method/model versions, relevant dates, gaps, and policy dependencies. Context summaries must retain provenance and uncertainty. User text and quoted source instructions supply no authority. Prior turns cannot silently broaden scope or convert an unsupported human statement into evidence. Every read reopens current permitted support. Historical turns retain their original support rather than adopting a newer publication.

Separate turn states include accepted, preparing existing-KB answer, partial, complete, invalid, interrupted, and unavailable. Streaming, if later selected, must withhold unvalidated factual content and never display retrieved-but-unpublished evidence as an answer. Background research status belongs to the task/proposal owner rather than generated message text. Navigation or cancellation of an answer does not cancel or reissue a paid task. Local draft persistence and retention need an explicit policy before implementation; this fixture persists nothing beyond memory.

A conversational yes, an approval-like user phrase, and a model message cannot authorize paid work. Approval requires the separate attributable action against an exact saved proposal revision/digest and scope. Publication enables a later explicit question; neither publication nor a new message rewrites prior turns. Multi-turn retrieval, synthesis, claim validation, and storage/read adapters require future specifications and acceptance, not an assumption that the current one-question backend already supports them.

Review enrichment proposal opens an immutable saved proposal revision with purpose/intent, subject, exact query, platform/route scope, source time window, request/record/byte bounds, spending basis and uncertainty. An unchecked approval box leaves the primary approval action disabled. A deliberate checked approval authorizes only that exact revision. Revise scope edits subject/query/record bound, saves a successor and clears approval. A changed route, configured limits or material scope also requires a fresh server-approved digest; a client checkbox cannot authorize them.

After approval, the target adapter records approval then submits once, exposing any approved-but-unsubmitted gap with a safe retry using the original request identity. The fixture combines those acknowledgments for the visible queued state. The async path is queued → running → retrieved but not usable → published/partial/no-update/failure, with waiting states for safe recovery. Inbox completion links back to a new question. The original answer does not change and cannot answer from unpublished retrieval.

## Independent market monitoring

Topics have their own question/query, source scope, cadence, collection interval, record/request bounds, retention, significance method, source policy and activation. They are not registered discovery keywords or campaigns. Saving a topic revision is separate from authorizing recurring collection. Pause prevents future due work but does not undo a dispatched call. Local worker health and last successful tick distinguish operation from an unattended promise.

### Stream and selected-window contract

An inline SVG chart precedes the selected-window summary and latest alerts. The method selector chooses posts, matched-age median likes, coded-negative percentage, or controversy input count. The history control shows the last six or four collection windows. Both controls have stable semantic values across EN/KO. The horizontal axis uses elapsed UTC time, with dates stated below it. The vertical axis uses metric-specific units and ticks. A labelled red latest point and dashed red window outline distinguish the current/latest window from pink selected-window shading. Selecting an older point changes its summary and evidence without relabelling the older window as current.

The six fixture windows span November 2 at 20:00 through November 3 at 03:00 UTC. The 22:00 collection is missing, 23:00 was not scheduled, and 00:00 has a real observed post count of zero. Lines break at missing values and nonadjacent collection intervals. Absent engagement or semantic inputs remain unassessable, including in the zero-post window. Neither interpolation nor zero filling is allowed. The plot represents bounded irregular query samples, not a continuous census or an estimate of all market activity.

SVG point controls expose time, metric, value, and selection. Enter or Space selects a point. A disclosure contains the equivalent window-value table with ordinary selection buttons. This supports keyboard and list access without requiring the visual chart. Each selected summary links to its own window evidence modal. Latest alert investigation and retained evidence remain explicitly tied to 02:00–03:00 UTC. Historical windows have snapshot summaries and no invented comparison result.

Latest volume, engagement, semantic shift, and controversy chart values are respectively 24, 36, 35%, and 4. The chart and selected summary read the same window model. Volume counts distinct eligible posts. Engagement uses a separate matched-age support set with 24 measured posts, native X likes at six hours. Semantic coding has 7 of 20 inputs and controversy has 4 of 12. These support sets and denominators cannot be pooled. Semantic positions stay provisional.

Baseline insufficiency withholds the comparison signal while retaining permitted recent snapshot values. Failed method validation withholds the generated signal. For semantic and controversy methods it also removes derived chart points; permitted original evidence remains inspectable. Missing baseline never means no activity. A zero post window means zero eligible posts in that bounded collection only. Production history needs bounded window reads with exact intervals, collection/missing status, support IDs, metric definition/age, denominators, method version, baseline comparability, and current-policy availability. It must not invent data for unloaded pages or connect across unobserved intervals.

The method selector offers four full target cases: volume ratio, matched-age engagement, semantic/sentiment shift and emerging controversy. The selected alert shows recent and baseline windows, sample denominators, metric definition, method/version, significance policy, source coverage and uncertainty. Fixture numbers illustrate a design and are not product thresholds.

- Volume compares 24 versus 8 distinct eligible posts under the same query/route/window and shows the sample ratio.
- Engagement compares median native `like_count` 36 versus 12 for 24 posts per sample, measured at six hours after publication. Different metrics or capture ages cannot be silently pooled.
- Semantic shift compares 7/20 versus 2/20 negative-coded inputs with the same scope, coding method and language mix. It shows +25 percentage points and provisional position labels. It does not measure population sentiment.
- Controversy inspects four of twelve actual inputs discussing cracking. Packaging versus product-finish ambiguity remains visible. Without a semantic baseline, there is no change-over-time claim.

Comparison support switches between a comparable-baseline success, insufficient baseline and failed method validation. Missing comparison yields a snapshot, not a spike or shift. Method failure withholds the generated signal while permitted raw support remains inspectable. Stale/restricted/unavailable support and partial sampling have distinct states. A concise inbox alert leads to full method and evidence details and relevant alert history.

Investigate with existing knowledge saves context using the original alert evidence and selected existing KB support, with dates and sample limits kept distinct. It makes no external source call, creates no campaign and does not imply causation. Similarity between a recent phrase and historical support is context only.

Evidence timeline retains publication, capture, metric-measurement and import times separately. Recent observations may alert without complete KB modeling. Explicit selected promotion reviews exact observation membership, then uses normal ingestion/publication while inheriting source permissions, native withdrawal and the original retention deadline. It cannot manufacture Creator/product associations or renew evidence age. Expired/withdrawn evidence becomes a source-free historical reference. Snapshot investigations save fixed-sample findings without claiming growth or baseline change.

## Graph explorer

The graph follows Neo4j-style node selection, bounded relationship expansion and a side inspector. It is a projection over governed knowledge, not a commitment to Neo4j or a new canonical store. Native accounts and content remain distinct from Creator identities. Catalog brand/product nodes are contextual references grounded in permitted mentions. No unsupported Creator equivalence, collaboration, audience or commercial-outcome edge appears in the normal fixture.

The prototype implements entity text search, kind filter, relationship-basis filter, one-to-three-hop traversal, node/edge selection, zoom/reset and an equivalent entity/relationship button list. Selecting an entity updates the inspector and roots exploration. Selecting a relationship exposes its endpoints, observed/derived/human basis, support, dates, method, provisional review status and limits. Traverse from a relationship moves to its endpoint. A root whose evidence is withdrawn produces an unavailable inspector and no leaked label/excerpt/dependent relationship.

The target filter drawer also needs direction, exact predicate, platform, namespace, capture range, exact observation IDs, node/relationship/work limits and truncation coverage. These controls map to existing `GraphScope` and `GraphTraversal` fields. They are specified rather than all reproduced in the compact prototype. Filtered nodes cannot bridge a path; exact observation filtering cannot borrow labels from unselected support. Empty search does not establish market absence. Each bounded projection states sample and truncation, separately from total market coverage.

The inspector keeps conflicting assertions accessible rather than choosing identity from matching handles. Source-publication, source-capture, source-as-of, ingestion, derivation and KB-publication times have distinct meanings. Current process/display/retention rights and derivation health are checked on every navigation and reopen. An unavailable selection preserves only permitted source-free identity metadata. Later publications do not substitute into a pinned support selection.

### Production interaction contract

The mockup retains its simple fixed layout, selection, depth/filter controls, zoom buttons, and list. The following are concrete requirements for the actual UI, not implemented graph-engine behavior in r2.

| Interaction | Production behavior | Invariant |
| --- | --- | --- |
| Pan, zoom, and fit | Drag empty canvas to pan. Wheel/pinch zoom anchors at the pointer. Zoom buttons and Fit visible graph animate smoothly, respecting reduced motion. Fit includes visible nodes without changing the selected entity | Camera state changes no evidence scope or task authority |
| Drag and pin | Drag a node to position it. Pin/unpin is explicit in the node inspector and keyboard menu. Pinned nodes keep positions across expansion and relayout | Node identity and selection never depend on screen coordinates |
| Layout controls | Offer deterministic relationship and compact layouts, relayout, and reset positions. Retain pinned coordinates and camera unless the user chooses Fit | Layout controls rearrange the existing projection and make no read/acquisition claim |
| Expand and collapse | Expand selected node on demand. Choose incoming, outgoing, or both directions, relationship type/basis, entity types, and one-to-three-hop depth. Collapse a branch without removing nodes still reached by another visible branch | Traversal never crosses filtered-out support; depth and work limits stay explicit |
| Stable selection and inspector | Node or edge selection opens endpoints, native identity, basis, support, dates, method, conflicts, uncertainty, and current availability. Keep selection when the camera or layout changes | A hidden or withdrawn selection becomes unavailable. No automatic replacement entity |
| Keyboard and list | Use arrow navigation among visible nodes and edges, Enter to inspect, explicit expand/collapse and pin controls, plus labelled pan/zoom/fit buttons. Search and a paginated entity/relationship list expose the same selection and inspector | Evidence access and branch control do not require dragging, color, or a pointer. Announce loading, added counts, truncation, and unavailable selection |

### Incremental governed graph reads

Maintain selection, camera/layout positions, and branch membership as separate client state. Use stable source/native node and relationship IDs, never display labels or coordinate keys. Retain a selected ID across relayout and language changes. Collapsing its branch keeps a source-free selection placeholder with a path back to the list. A source-policy loss clears forbidden labels, snippets, aggregates, and dependent edges immediately on the governed response. Pins and cached layouts cannot restore them.

Each expansion request carries the current search/support selection, root ID, exact filters/direction/depth, observation scope, node/edge/work bounds, cursor, and request generation. The response identifies its query generation and policy frontier, exact support scope, returned members, continuation cursor, per-branch counts, truncation/reason, and unavailable members. Pagination is bound to that scope and frontier; a changed filter or expired cursor restarts the bounded read. No unbounded recursive fan-out or silent fetch-all is allowed.

Cancel superseded requests where possible and ignore late responses whose generation, root/branch request, filters, or support scope no longer match. Merge pages by stable IDs while preserving positions, pins, and selection. Avoid duplicate branches, edges, and in-flight expansions. A loading or failed branch retains prior governed members, with a retry of the same read. Policy-invalid prior members are withheld rather than kept as an offline cache. Partial results must expose truncation and a deliberate Load more or narrower-filter action; no cursor exhaustion establishes complete market coverage.

Expansion is a governed knowledge read through `KnowledgeGraph`, `GraphScope`, and `GraphTraversal`, with a future bounded read adapter where needed. It never acquires external sources, promotes observations, establishes Creator/account equivalence, endorsement, or causation. Retain PostgreSQL canonical authority. No graph database or new graph engine is selected merely for visual appearance. Actual camera, drag, expansion, accessibility, policy-race, cursor, and cancellation behavior require implementation acceptance after UI approval.

## Pipeline, operations and delivery

Pipeline & lineage starts with the task's exact origin and immutable scope, then shows execution ownership, attempt/run, collection, mapping, publication and terminal completion. Queued work does not display completed retrieval or publication. Historical completion and current permitted usability have separate summaries. A source request may finish while transformation/publication fails. Partial publication retains both its usable subset and the failed remainder.

Progressive acquisition displays broad discovery followed by selected detail only for decision-relevant gaps. The plan lists permitted API/oEmbed/web choices, field-specific support, freshness, expected value, route capability and stop reason. No automatic fallback may widen approved scope. New request/record/byte/spending bounds remain independent. The current installed methods are narrower; the prototype's plan is the target reading experience, not provider execution.

Avoidance decisions identify exact prior query/context and usable capture support. Reuse preserves original capture age. A refresh of a known post is distinct from a newly admitted post. Method changes, invalid/quarantined records, missing capture time, unresolved response or rights changes prevent unjustified reuse. Idempotent processing must not erase failed/partial history or falsely claim complete cross-route deduplication.

Recovery uses the same task, original authority, attempt and prepared membership. Safe local replay may resume committed work. An ambiguous external response blocks blind paid reissue; outstanding cost is not zero. Sanitary error codes and actionable recovery summaries are visible, while secrets, opaque provider operation handles and raw arbitrary responses are not exposed.

Scheduled discovery shows at most ten registered keywords and the initially configurable shared fifty-new-post allowance per workspace accounting day. It distinguishes unique new posts, known refreshes, duplicates, excluded/unassessable input, requests and actual source usage. It shows fewer-record outcomes without promising fill, per-keyword yield, throughput or complete coverage. Each occurrence pins its original day/configuration/authority. On-demand campaign and approved assistant work can exceed registered keyword membership but retain their own bounds.

The target local pilot includes automatic due-work advancement and workers, health, last success and recovery. Installed ticks/worker invocations are explicit and no daemon is established by this design. Provider access, policy, operator activation and monetary authority remain separate from code installation. Hosted identity/tenant administration remains later work.

Inbox has durable task-completion and alert events with read/unread attention. Acknowledging or retrying delivery never runs acquisition again. Historical outcome, currently permitted publication, inbox attention and email transport status are separate. Email belongs in the first pilot delivery alongside the inbox.

The proposed email payload contains outcome/status plus a governed application link, with no source excerpts or copied generated answer. Configured recipient authority, sender, provider, credentials, immutable event-to-delivery identity, retry policy, final failure and retention need a reviewed transport contract. Retrying the same delivery reuses its identity. Transport success does not establish receipt/read or KB usability. A local link requires access to the review machine/runtime. This task sends no email and configures no provider.

## Spending

The spending view selects service/provider, currency and start-inclusive/end-exclusive accounting period. Synthetic measured amounts are visibly distinct from commercial charges. Actuals, outstanding commitments and forecast-only ranges are three different quantities. Missing coverage is Unknown, never zero. Cross-currency or cross-period totals are not invented.

For a bounded metered scope, allowance subtracts measured actual plus all outstanding commitments from its exact ceiling. A forecast-only scope has no enforced monetary ceiling claim. Operator rates and synthetic unit weights do not become commercial prices. Each operation exposes actor/method, task/attempt where applicable, measurement evidence/time, unit/rate version, reconciliation and current control health.

New chargeable dispatch is blocked by exhausted allowance, unknown/unbounded pre-call liability, paused control or expected-meter failure as appropriate to the configured contract. Human task approval does not override any of these. Strict commercial limits require defensible charge bounds or provider caps; delayed billing and unknown portions remain visible. No approximate all-in target becomes a workload guarantee.

Meter recovery and final liability reconciliation are separate, attributable operator operations. Restored meter health does not settle a failed measurement; final cost does not recover a missing response or authorize another call. The prototype opens a recovery explanation and keeps live operator actions disabled. Current accounting configuration/reconciliation operations have no installed browser forms; a future adapter needs a separate operator authority contract.

## Measurement, learning and proposal extensions

Measurement plan records objective, intended outcome/source/owner, periods/baseline, matching and attribution assumptions, known gaps and exact brief/shortlist. It remains proposed, with unverified outcome access and no measured revenue, conversions or lift. Human decision notes retain author/time, shortlist and supporting dependencies. They are human statements, not source observations. Policy/retention applies to source-dependent copied note text.

Future descriptive outcomes and rule-based attribution require authorized actual data, matching definitions and quality checks. Incremental lift needs an experiment or justified causal model with explicit assumptions; engagement is never a proxy for measured sales. Portfolio scenarios need costs, overlap, constraints and their own feasibility evidence. Multimodal listening, richer Creator/Collaboration/Audience/Social Event objects, beauty aspects and ontology correction are separately traced proposal work, not fixture facts.

Quality review packet preview identifies exact member sets, original-language/translation method, reviewed denominator and pending named human review. A technically valid response and a localized interface do not establish Korean/Japanese quality or marketer usefulness. No fixture action records the actual approval required for Task 4.

## State behavior

The floating state selector is review-only. It changes a full current view to Empty, Loading, Error, Partial, Stale, Restricted, Unavailable, Budget or Meter failure. It never changes the product's permission authority. Normal remains the default. Method-specific monitoring states are also selectable in the monitoring view.

| State | User presentation and recovery | Required boundary |
| --- | --- | --- |
| Empty | Clear absent sample, adjust scope or create proposal | No market-absence claim or automatic external request |
| Loading | Saved selection loading, no new work submitted | Stable selection and in-progress request identity |
| Error | Read failed; retry same saved selection | No duplicate command or paid reissue |
| Partial | Usable subset plus coverage/gaps | Do not hide failed remainder or inflate denominator |
| Stale | Original capture age and selected freshness policy | Existing history remains; refresh is explicit |
| Restricted | Role-based action unavailable with operator guidance | Server authority; no client role field grants access |
| Unavailable | Current policy withholds content, preserve permitted history | No copied text, aggregate leakage or replacement support |
| Budget | New paid work paused with exact scope/allowance | Approval and monetary admission remain independent |
| Meter failure | Expected measurement failed, pause and show recovery path | No silent forecast downgrade or zero-cost assumption |
| Version conflict | Preserve edits, show current revision, explicit rebase/review | No last-write-wins or automatic new approval |
| Unknown external response | Waiting, outstanding liability, inspect recovery | No timeout-driven paid retry |
| No baseline / invalid method | Snapshot or withheld generated signal | No spike/shift or inferred research authority |

Version-conflict and source/configuration-specific errors are specified here and in traceability; the global prototype selector does not reproduce every validation code. Bounded prototype forms cover campaign required fields, keyword count, scope bounds and explicit checkbox approval.

## Read models, commands and adapter contract

These are owner operations and proposed presentation models, not claims of installed JSON endpoints. The existing UI is Python forms in one trusted local process. A production client must use owner adapters preserving authority, expected versions, request identity and source policy. Protocol choice is deliberately open.

| Model / command family | Needed fields and operations | Current owner and gap |
| --- | --- | --- |
| C1 Campaign workspace | Campaign/brief/criteria heads, exact human original, selected interpretation, candidates, coverage, saved revisions, attribution, current support state | `CampaignStore.start/revise_brief/read_campaign`, `prepare_current_comparison`, `recommend`/`recommend_ranked`, `save_shortlist`; task campaign-coverage composition. Target ranking factors and UI adapter still need specification |
| K1 Knowledge answer | Future conversation/turn/context read contract above; current bounded question/scope, query/actual input IDs, selected findings, dates/coverage/model/method, current usability, gap disposition | `KnowledgeQueries`, `KnowledgeAssistant.ask/read`; richer synthesis/claim validation and research-plan operations are future contracts |
| A1 Exact enrichment | Saved proposal revision/digest, intent/subject/query/time/route/limits, actual proposer, attributable approval, submitted task and retry identity | `AssistantEnrichment` journey and `AcquisitionTasks.save_proposal/read_proposal/approve_proposal/submit_approved`; no prompt-defined authority |
| G1 Governed graph | Future bounded branch/cursor/generation contract above; search ID, exact support manifest, node/edge basis and evidence, selected root, traversal/filters/coverage, current unavailable states | `KnowledgeGraph.search/read`, `GraphScope`, `GraphTraversal`; bounded projection installed. New layout/graph client adapter required |
| M1 Topic/window/alert | Topic revision, activation, cadence/retention/limits, immutable windows/members, metric/method/baseline, notifications, current support | `RecentMonitoring`, `RecentPolling`, quantitative/semantic owners; engagement and semantic-shift methods and automated pilot operation remain target work |
| M2 Investigation/promotion | Exact original alert + selected existing KB support, dates/limits, selected observation IDs and inherited lifecycle | Context `investigate/read`, promotion `promote/read`, snapshot `MonitoringStore`; no additional acquisition in investigate |
| T1 Task/lineage/inbox | Origin/approval/scope, ownership, attempt/run, progress/coverage, prepared support, receipt/publication, terminal event, current usability, delivery | `AcquisitionTasks`, `TaskExecution`, `TaskLineage`, `CompletionInbox`; email and continuous worker service need new adapters/contracts |
| D1 Discovery configuration | Registered keyword identities, immutable revisions/occurrences, accounting day, shared unique-new allowance, independent usage/limits, route health | `ScheduledDiscovery.configure/read/read_occurrence` and due advancement; recency/engagement/trend planner, broad route/value selection and local daemon target |
| S1 Cost control | Exact scope/currency/period/basis, units/rates/evidence, actuals/commitments/forecast, ceiling/allowance, health, reconciliation | `UsageAccounting.list/read/allowance`, trusted configuration/reconciliation/recovery; operator UI and commercial proof remain separate |
| P1 Plans/notes/review | Exact campaign/brief/shortlist, proposed plan/gaps, human notes/dependencies, review packet membership/reviewer/denominator | `CampaignPlanning.save_plan/add_note/read`, review owner; actual outcome/attribution/causal methods future |

Every mutation must derive actor and workspace from trusted context, check server-owned role/policy, parse input at the boundary, require an idempotent request identity, and use an expected version where the owner has a head. A retry reopens the exact original command/result; changed scope conflicts. A read, navigation or language switch never admits acquisition. CSRF/host/origin protections remain required for local forms. A later hosted client also needs real identity/tenant authorization; a fixture actor name is not authentication.

A response envelope needs record identity and revision, original input and author, current command status, immutable outcome, current-policy usability, coverage/unknowns, allowed actions, and a sanitized failure/retry disposition. Source-free metadata can be stable while displayable source values are reopened under current policy. Do not persist unrestricted result snapshots in the browser or email.

## Prototype coverage and verification boundary

The prototype is self-contained and intentionally uses no framework, API or external asset. The design explores target interactions, while the traceability matrix identifies installed, target and proposal contracts. It is not a backend mock service and cannot demonstrate real workers, money, permission checks, publication or delivery.

`node .scratch/product-design-2026-11/task3/r2/verify-prototype.cjs` parses the JavaScript and checks fixture-state transitions with a minimal element stub. It checks approval scope, append-only versions, graph projection/filter/withdrawal, explicit regeneration, waiting, selected promotion gating and bilingual state. It does not render a DOM or automate a browser. [Verification results](verification-results.txt) contain the actual output.

The coordinator reported that browser preview permission was declined and prohibited alternative automation surfaces or origins. No browser automation, rendering screenshots, visual comparison, actual keyboard navigation or responsive rendering was performed. Source hooks are present, but those user-visible checks remain pending. [Review guide](review-guide.md) supplies concrete scenarios; the coordinator must present the exact r2 artifact for actual human review before Task 4. Accessibility and language usefulness are not certified by source checks.
