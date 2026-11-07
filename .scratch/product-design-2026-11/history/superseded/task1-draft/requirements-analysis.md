# Product requirements analysis and design brief

Analysis date: 2026-11-03. Status: factual analysis complete; human decisions and shared-understanding confirmation pending. This report does not authorize UI or backend implementation.

## The product supports decisions over shared evidence

The intended product helps brand and agency marketers observe accessible markets, investigate signals, compare creators, plan campaigns, measure outcomes, and reuse learning. Beauty in South Korea and Japan is the first proving domain. One multilingual domain model serves both markets, with localized labels and market-specific policies. The operational core connects campaign recommendations, a knowledge assistant, and independent X monitoring over shared evidence. Graph exploration and pipeline lineage make the basis of those decisions inspectable. [POPOSAL.md §1–2, L5–29](../../../../../POPOSAL.md), [roadmap L3–11](../../../../../docs/roadmap.md).

This is internal decision support. It does not contact or contract creators, publish content, buy media, or activate/change connected marketing systems. A saved shortlist is neither creator participation nor human endorsement. A campaign is a marketer-created planning context, and a monitoring alert cannot automatically initiate one. [POPOSAL.md L5/L19/L37](../../../../../POPOSAL.md), [glossary L34–50](../../../../../GLOSSARY.md).

The proposal's measurement ambitions remain in scope as future direction. Current measurement plans describe intent and assumptions; decision notes are human feedback. Actual outcome ingestion, rule-based attribution, randomized lift, quasi-experiments, and calibrated marketing-mix models need their own data, permissions, methods, and evaluation. Attribution and incrementality are different claims. [POPOSAL.md L35](../../../../../POPOSAL.md), [planning L9–27](../../../../../docs/planning.md), [roadmap L36](../../../../../docs/roadmap.md).

## The current application is a bounded local implementation

The installed software is a modular Python/PostgreSQL application with a standard-library loopback browser server, CLI, and permitted local evidence files. Compose starts PostgreSQL only. Submitting a task acknowledges durable work. An explicit invocation of `OfflineTaskWorker.run_one` executes/resumes one task, and `RecentPolling.run_due` is a separate bounded monitoring worker. There is no continuously deployed queue consumer, cron, scheduler, or hosted authentication. These facts constrain how an honest present-day design describes availability; they do not constrain the accepted product destination to a local app. [architecture L3–23](../../../../../docs/architecture.md), [worker L180–207](../../../../../src/smi_tasks/worker.py), [Task 2 investigation](../../../task2/codebase-analysis.md).

Installed model/source transports do not establish current credentials, account access, source-use rights, defensible live cost bounds, or acceptance of returned data. Simulated software verification, live route acceptance, translation-assisted review, Japanese-original adjudication, and marketer usefulness are separate evidence. The roadmap records all live/human readiness as pending or unverified and a known aging-fixture test limitation. This investigation conducted no source/model calls, behavioral tests, database migrations, or actual quality review. [roadmap L13–24](../../../../../docs/roadmap.md), [development L18–26](../../../../../docs/development.md), [evaluation L40–55](../../../../../docs/evaluation.md).

## The main user workflows

### A marketer creates and revisits a campaign recommendation

1. Create a brief with brand/product scope, objective, target market, platforms, and selection needs. Natural-language interpretation is visible and versioned, preserves human requirements, and is explicitly selected before assessment.
2. Search current permitted published knowledge. A stable platform account with one permitted ingested supporting observation can qualify even when its profile is incomplete. A bare handle or URL can seed discovery but cannot appear as a supported ranked candidate.
3. Filter/assess using the selected criteria. Show evidence, reasons, unknowns, freshness, and method. Constrained model order is relative fit under the supplied evidence, not verified audience, fee, availability, sales effectiveness, or source truth.
4. Save the supported ordered recommendation automatically as an attributed generated shortlist. Human approval is not a prerequisite. Optional human select/reorder/reason edits create an attributable successor with separately recorded confirmation if performed.
5. Assess quantity/relevance/freshness coverage. Save even a thin/empty supported result before automatic bounded discovery admission. If admission is refused, retain the result and show the actual reason.
6. After usable KB publication, notify and offer explicit regeneration. Only that explicit action assesses current context and saves a successor. Existing membership, order, brief, method, and support remain historical.

Trace: FR-A01–FR-A07, OFR-A01–OFR-A02 in [the matrix](requirements-matrix.md). Accepted trade-offs are [ADR 0003](../../../../../docs/adr/0003-automatic-shortlist-persistence.md), [ADR 0008](../../../../../docs/adr/0008-generated-criteria-preserve-human-constraints.md), [ADR 0009](../../../../../docs/adr/0009-constrained-supported-ranking.md), and [ADR 0010](../../../../../docs/adr/0010-save-before-coverage-discovery-admission.md).

### A marketer asks a knowledge question and approves bounded research

1. Ask in free-form language. Existing permitted KB reads require no acquisition approval.
2. Inspect the answer's actual evidence, dates, provenance, coverage, and uncertainty. The installed answer selects exact published findings from a bounded support sample. It does not produce arbitrary factual synthesis or run an autonomous tool loop.
3. For a real missing/stale/incomplete/ambiguous/unavailable-support gap, review an enrichment proposal. The installed journey asks the human to supply intent, exact subjects, one query, and a bounded publication window. A model/configuration/accounting failure alone is not a knowledge gap.
4. Approve one exact immutable proposal revision in the correct workspace under the actual human actor. Approval authorizes at most one logical task, not broader future work. Approved scope may exceed the scheduled keyword list.
5. Receive task acknowledgment and asynchronous status. Collection, normalization, publication, and terminal completion are distinct. Fetch success with publication failure is not a successful KB update.
6. Inspect the completion outcome/publication and explicitly ask a later question to use the updated knowledge. The original answer does not silently change.

Trace: FR-B01–FR-B09 and OFR-B01–OFR-B02. [ADR 0017](../../../../../docs/adr/0017-exact-supported-answers.md) deliberately trades fluent synthesis for exact finding selection; [ADR 0018](../../../../../docs/adr/0018-explicit-assistant-gap-scope.md) makes executable research scope independently reviewable. A richer future research agent needs an explicit successor design rather than looser prompts.

### A marketer monitors and investigates without starting a campaign

Configured X monitoring topics have independent scope, cadence, collection bounds, retention, and activation authority. They may overlap scheduled KB keywords, but are not the same subscriptions. Recent monitoring observations can support timely alerts without full KB publication of every post. [operational C L44–49](../../../../../docs/functional-requirements.md), [glossary L118–140](../../../../../GLOSSARY.md).

The user inspects concise alerts with the observation window, comparable baseline where applicable, method, support, uncertainty, and current evidence availability. The installed quantitative method compares configured comparable sampled-volume windows. The installed semantic method marks provisional product-quality concern/counterposition/unresolved spans and may produce a possible controversy signal. It has no baseline and cannot establish sentiment shift, verified sentiment, a shared disputed proposition, or emergence over time. Engagement anomalies, general semantic shift, richer methods, and live continuous operation remain future/readiness work. [operational C L45/L51](../../../../../docs/functional-requirements.md), [ADR 0020](../../../../../docs/adr/0020-bounded-semantic-positions-full-input-policy.md).

Investigation juxtaposes original recent support with a pinned existing-KB context query. It performs no additional external search and creates no campaign. Selected useful observations can be deliberately promoted through normal ingestion/publication. The promoted source retains its original identity, unknowns, permission, withdrawal, and deadline dependencies. An alert's historical existence does not grant continuing access to expired text. Trace: FR-C01–FR-C07, OFR-C01; [ADRs 0004](../../../../../docs/adr/0004-lightweight-monitoring-evidence.md), [0021](../../../../../docs/adr/0021-pinned-local-alert-context.md), [0022](../../../../../docs/adr/0022-promoted-source-lifecycle-inheritance.md), and [0023](../../../../../docs/adr/0023-bounded-recent-x-poll-authority.md).

### A user inspects the knowledge graph

Search/filter a permitted bounded KB sample, select an entity, traverse filtered relationships, and open the exact support. The installed graph projects account/content subjects, supported Brand/Product mentions, observed authorship, and human catalog association. It does not infer a cross-platform Creator. A derived mention and a human-configured catalog association must remain distinguishable from observed facts. [knowledge L157–173](../../../../../docs/knowledge.md), [graph owner instructions](../../../../../src/smi_knowledge/graph/AGENTS.md).

The original support selection is pinned, but navigation and labels are current governed projections over that support. The graph is not an immutable historical campaign decision. Search, hops, nodes, relationships, and work are bounded and truncation is explicit. Denied/expired support must not reappear in labels, tooltips, counts, or details. The visual interaction can draw inspiration from Obsidian/Neo4j without requiring their storage systems. Trace: FR-G01–FR-G02 and OFR-G01. The [source implementation L252–330](../../../../../src/smi_knowledge/graph/store.py) corroborates pinned searches and public purpose-aware reads.

### An operator inspects pipeline lineage and resource use

Start from a task or linked completion/publication. Inspect its true authority, exact scope, attempts, worker/recovery history, source observations, transformations, prepared support, committed publication receipt, coverage, failures, and attributed costs. Queue acceptance, retrieval, ingestion, publication, and completion are distinct outcomes. Current visibility of support is independent of the historical completion count. [tasks L227–239](../../../../../docs/tasks.md), [lineage implementation L29–97](../../../../../src/smi_tasks/lineage/__init__.py).

The installed view is a read-only composition of independently committed owner frontiers, not an atomic global snapshot or a retry console. It executes no collection/model work and exposes sanitized operational metadata, not secrets, unrestricted payloads, or arbitrary provider errors. Cost absence remains unknown, and currencies/periods/bases cannot be indiscriminately summed. Trace: FR-L01–FR-L02, OFR-L01, FR-S01–FR-S03, and OFR-S01–OFR-S04.

### An operator configures acquisition while a marketer learns

At most ten registered scheduled keywords share the initial configurable fifty unique eligible new posts per accounting day, total across the workspace keywords. Refreshes and duplicate identities consume no new-post admission. It is an allowance, not guaranteed throughput, a target to fill, fifty per keyword, or a provider-cost claim. On-demand campaign and exactly approved assistant work share the ingestion pipeline without being restricted to those ten keywords. Recency/engagement/trend prioritization and general progressive value-based acquisition remain broader targets. [FR L43–49](../../../../../FR.md), [operational pipeline L55–61](../../../../../docs/functional-requirements.md).

Progressive acquisition must choose supported routes under capability, permission, freshness, scope, information value, and independent resource/spending bounds. The installed exact optional nickname fill is not a general enrichment planner. Metered work uses measured derived spend plus outstanding commitments before further calls; unmeterable scope remains explicitly forecast-only. A failed meter is a control failure, and reconciliation neither recovers a missing response nor grants another dispatch. [ADR 0016](../../../../../docs/adr/0016-explicit-bounded-profile-supplementation.md), [costs](../../../../../docs/costs.md).

Measurement plans and notes preserve proposed outcomes, source/access gaps, matching/attribution assumptions, and attributable human learning. Their presentation must not suggest observed conversions/revenue/lift. Trace: FR-P01–FR-P09, OFR-P01, PROP-12–PROP-14, and [planning](../../../../../docs/planning.md).

## Authority is a domain contract

These are current and accepted authority distinctions. Hosted role names and delegation between real people remain a future design decision.

| Actor or context | Permitted responsibility | Boundary the UI must preserve |
| --- | --- | --- |
| Trusted local human marketer | Brief, explicit criteria selection, knowledge questions, exact assistant proposal approval, optional curation/confirmation, regeneration, plan/note writes | A local actor label is not hosted authentication. Approval belongs to one exact scope, not all future agent activity |
| Trusted automation/model preparation | Supported interpretation/ranking/answer/semantic assessment and automatic shortlist persistence | Generated text grants no role, changes no human constraints, and cannot approve acquisition or impersonate human review |
| Server-configured campaign acquisition | Bounded discovery from actual saved campaign coverage | The assistant cannot claim campaign origin. Admission/refusal is visible and never discards the saved result |
| Operator-configured schedule/monitoring | Bounded scheduled KB queries or separately activated X topics | Keyword/topic edits do not silently broaden existing recurring paid authority. Runtime access, source policy, and cost controls are separate gates |
| Worker execution owner | Resume one admitted bounded task/interval under fencing | Temporary ownership grants no new scope, source permission, paid retry, or provider-side exactly-once guarantee |
| Graph/lineage reader | Governed inspect/search/traverse/read | Opening evidence or operational records cannot submit, publish, retry, acquire, or infer identity |
| Actual quality reviewer | Record attributable labels, translations, methods, usefulness, errors, corrections | A prepared packet, synthetic actor, or user approval of a design is not actual semantic/usefulness review |

Evidence: [interface L5–36](../../../../../docs/implementation-spec.md), [architecture L74–109/L139–153](../../../../../docs/architecture.md), [planning L5–27](../../../../../docs/planning.md), and [evaluation L40–85](../../../../../docs/evaluation.md).

## Evidence, time, and uncertainty must remain legible

The domain distinguishes source references, source observations, assertion/metric support, provisional interpretations, publications, consequential decisions, tasks, and human review. A pointer is not retrieved support; an observation is not independent truth; a publication is not a newly captured source; a saved result is not a human endorsement. Platform account identity is separate from mutable handles and corroborated Creator identity. [glossary L43–50/L91–116/L151–164](../../../../../GLOSSARY.md).

Keep native post publication time, source capture time, source-as-of time, local ingestion time, KB publication time, assessment time, and human review time separate. Unknown dates stay unknown. Re-import/publication does not refresh capture age. New publications affect new queries; exact historical input membership remains pinned. Current process/display/retention rights still govern every use, and source withdrawal can withhold the whole derived finding even when its selected citation survives. Safe lineage may remain after text is purged. [ADR 0002](../../../../../docs/adr/0002-pinned-support-current-policy.md), [architecture L147–153](../../../../../docs/architecture.md), [knowledge L149/L163–171](../../../../../docs/knowledge.md).

## Findings for the next design

| Finding | Evidence | Design consequence |
| --- | --- | --- |
| The proposal is broader than creator discovery | POPOSAL L15–19/L33–35; PROP-01/04/08–14 | Keep market, campaign, knowledge, and learning contexts visible without forcing every investigation into a campaign |
| Human review of product quality differs from runtime approval | operational L26/L37/L88; ADR 0003; evaluation L40–55 | Do not gate automatic saving behind review. Do gate each assistant task. Do not label either action as a passed quality evaluation |
| Fluent answers and general agent orchestration are not installed | ADR 0017/0018; K L137–151; PROP-05 | Show exact bounded current behavior honestly and specify richer synthesis/research as new future contracts |
| Current monitoring is sampled and method-limited | operational L45/L51; ADR 0020/0023 | Include missing baseline, partial page, unknown dates, provisional semantics, and unavailable support as designed states |
| Graph and lineage answer different questions | K L157–173; T L227–239 | Graph explains supported entity relationships. Lineage explains how work produced usable knowledge/costs. Cross-link them without merging their authority |
| Current source identity is narrower than the illustrative ontology | A L68; POPOSAL L43–58; PROP-19/20 | Do not populate Creator, Collaboration, audience, contracts, or outcome objects as installed evidence |
| A task can publish partially or be complete while current support is unavailable | T L27–50/L118–136; ADR 0002 | Separate historical outcome from current usability and provide understandable next actions without blind paid retry |
| Money, quotas, approval, and expected value are independent controls | operational L65–76; PROP-28 | Show each control's actual status. Forecast-only is no monetary ceiling, unknown is no zero, and an approval is no spending exemption |
| Production technologies are target options | POPOSAL L88–99; R L43; PROP-29–34 | Build roadmap around required contracts and measured need, not presumed FastAPI/queue/vector/graph prerequisites |
| No human quality gate has passed | R L18; E L40–55 | A reviewed UI specification will establish design agreement only. Actual language/relevance/usefulness validation remains a separately attributed gate |

No material contradiction requires reversing an accepted ADR to satisfy the core FR. Apparent gaps mostly reflect a broader accepted target versus bounded installed behavior. The dangerous failure would be silently treating a target example as current capability or using a UI redesign to erase an existing authority/evidence boundary.

## Task 3 design brief

Task 3 should produce a requirements-grounded, human-reviewable product experience and staged implementation specification, not feature code. The coordinator confirms that the original user requires full FR UI coverage and sequential specifications. The six decision questions and confirmation state live in [decisions.md](decisions.md). Pending answers must remain pending in the brief.

Design all A/B/C journeys, graph exploration, pipeline lineage, acquisition configuration, spending visibility, completion/alert inbox, and preserved plans/notes. Link every screen, action, and material state to the matrix IDs. Keep future proposal extensions separately labeled so the full product destination remains visible without pretending it is installed.

For each workflow, specify the human goal, entry point, important decisions, data shown, action authority, public owner operation or missing adapter contract, immutable record created, retry/version behavior, and evidence of completion. Existing server-rendered forms are not an assumed remote JSON API. New wrappers must preserve the same domain operations and server-owned authority. [interface L7–21](../../../../../docs/implementation-spec.md), [Task 2 investigation](../../../task2/codebase-analysis.md).

The review must cover these parallel states:

- A supported happy path with a real visible evidence chain and exact producer/method attribution.
- Empty/thin results, explicit unknowns, stale captures, bounded/truncated retrieval, and unsupported criteria.
- Missing route/configuration/access, unverified live readiness, or unavailable model operation.
- Pending approval, exact approved scope, queued work, waiting/partial/failure/no-update/usable publication, and completion pending after publication.
- Stale edits/revision conflict and identical retry versus changed-payload conflict.
- Meter refusal/failure, outstanding commitments, forecast-only/unknown cost, and uncertain paid response without blind reissue.
- Permission denial, withdrawal/expiry, unavailable historical support, and safe retained provenance.

The design review should let a human explain why an account was recommended, what a knowledge answer actually supports, precisely what an enrichment approval authorizes, whether an alert establishes change, and whether completed work produced currently usable knowledge. Graph review should demonstrate an evidence-backed relationship and an unavailable/truncated traversal. Lineage review should trace a task to publication and cost while showing a partial or uncertain phase. This is a proposed review checklist, not a record of a completed review.

After the user chooses the first review priority, operating model, language, research scope, and notification channel, order the specifications into verifiable stages. Preserve all FR coverage and explicitly state dependencies for hosted identity, agent tools, continuous operations, additional methods, source acceptance, and future measurement. User approval of shared understanding must precede dependent design work.

## Investigation scope and limits

Read sources include the root instructions, domain/documentation/issue rules, the full proposal, both FR documents, glossary, architecture, roadmap, relevant owner contracts and ADRs, local UI routes, review procedures, and the graph/lineage/worker code cited above. The matrix captures every core capability and wider proposal goal. The [Task 2 report](../../../task2/codebase-analysis.md) supplies an independent broader codebase inventory.

Only `.scratch/product-design-2026-11/task1/` is owned by this task. No accepted glossary/ADR, production file, unrelated work, untracked skill directory, or lockfile was changed. Human answers, shared-understanding confirmation, and any resulting precise documentation recommendations are recorded separately in [decisions.md](decisions.md).
