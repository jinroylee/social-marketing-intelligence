# Requirements analysis and Task 3 brief

Analysis date: 2026-11-03. This is a product explanation and design handoff, not an implementation or a new durable contract. The [matrix](requirements-matrix.md) retains the original analysis IDs. The [decision record](decisions.md) separates actual human agreement from recommendations.

## Confirmed outcome

The user confirmed a campaign-first UI covering every FR, including a Neo4j-style graph, with an English/Korean switch and the colors `#E6002A`, `#F4ABAF`, `#3E3A39`, and `#FFFFFF`. Implementation completes a single-workspace local pilot first, including automated acquisition, monitoring, background task processing, the in-product inbox, and email notifications. Richer agent research and grounded synthesis belong in the target roadmap. Human review of the actual UI is required before Task 4 starts. This agreement comes from the coordinator's [recovery brief, lines 9–17](../history/task1-recovery-brief.md), supported by the [run record](../history/run-state.md).

Task 1 creates no UI or production feature. Shared-understanding confirmation authorizes the design handoff. It establishes neither actual UI approval nor provider access, external spending, email sending, language accuracy, or marketer usefulness.

## Product purpose and boundaries

Brand and agency marketers need shared evidence to observe markets, investigate signals, compare creators, plan campaigns, measure outcomes, and reuse learning. Beauty in South Korea and Japan is the first proving domain. One multilingual model serves both markets. A campaign-first journey organizes the first review, while monitoring and knowledge work remain independent of campaigns. See [POPOSAL.md, sections 1–2, lines 5–29](../../../POPOSAL.md) and PROP-01–PROP-07.

The product supports internal human decisions. It does not contact creators, publish content, buy media, contract creators, activate external campaigns, or change connected marketing systems. Plans and decision notes are installed. Actual outcome ingestion, attribution and causal measurement are future work with separate data and evaluation prerequisites. Attribution does not establish incremental effect. See [proposal lines 33–37](../../../POPOSAL.md), [planning](../../../docs/planning.md), and PROP-12–PROP-14.

Four evidence states must remain separate throughout the design:

| State | Meaning in this analysis | Consequence |
| --- | --- | --- |
| Installed bounded software | Current documented owner behavior, corroborated by source investigation | It can constrain interfaces. This analysis did not run it |
| Accepted target | FR, proposal direction, or an actual recorded user decision | It must receive a design/spec path even when implementation is absent |
| Live readiness | Real access, permitted use, commercial configuration, authorized bounded receipts and operational acceptance | Installed transports and simulated tests do not establish it |
| Human acceptance | An attributable person reviews the exact artifact or output for a stated purpose | Requirements confirmation, UI approval, language review and usefulness review are different events |

The installed runtime is a modular Python application with PostgreSQL, local evidence files, a standard-library browser server, CLI operations and explicit bounded workers. Compose starts PostgreSQL alone. Task submission and schedule ticks do not start a continuous consumer. Current notifications are local. Automated continuous operation and email are therefore real work in the confirmed local-pilot sequence. See [architecture lines 21–23 and 89–97](../../../docs/architecture.md), [roadmap lines 7–22](../../../docs/roadmap.md), and the [Task 2 investigation](../task2/codebase-analysis.md).

## Main user workflows

### Create and revisit a campaign recommendation

A marketer creates a brief with brand/product scope, objective, target market, platforms and creator-selection criteria. Natural-language interpretation is visible, versioned, additive to human constraints and explicitly selected before assessment. Requirements, preferences, exclusions and unknown handling must remain legible.

The system searches current permitted published knowledge. Stable platform identity plus one permitted ingested supporting observation admits an incomplete account. A reference-only URL or handle can seed discovery but cannot become a ranked candidate. Missing audience, fee, availability, history or profile fields remain unknown. A rank expresses supported fit under the selected criteria, not verified source truth or sales effectiveness.

The recommendation is saved automatically with actual producer, method, order, reasons, gaps and pinned support. Human review is optional. The installed deterministic method preserves encounter order and explicitly remains unranked; the bounded model method supplies constrained relative ranking. The UI must label the actual method rather than present both as the same score.

Coverage assesses quantity, relevance and freshness. A thin or empty result is saved before bounded discovery admission. Admission failure cannot discard the saved result. Usable KB updates trigger a notification and an offer to regenerate. Only the explicit regeneration action creates a successor. Human curation creates a separately attributable successor. Neither action rewrites historical membership, methods or support.

Trace: FR-A01–FR-A07, OFR-A01–OFR-A02. Evidence: [operational A, lines 23–29](../../../docs/functional-requirements.md), [campaign contract](../../../docs/campaigns.md), [ADR 0003](../../../docs/adr/0003-automatic-shortlist-persistence.md), [ADR 0008](../../../docs/adr/0008-generated-criteria-preserve-human-constraints.md), [ADR 0009](../../../docs/adr/0009-constrained-supported-ranking.md), and [ADR 0010](../../../docs/adr/0010-save-before-coverage-discovery-admission.md).

### Ask a knowledge question and approve scoped enrichment

A free-form question reads existing permitted KB knowledge without enrichment approval. The answer presents support, dates, uncertainty and coverage. The installed answer selects exact published findings through one tool-free model request. It does not perform semantic retrieval, arbitrary factual synthesis or autonomous research.

A real missing, stale, incomplete, ambiguous or unavailable-support gap can motivate enrichment. Model, configuration or accounting failure alone is not a knowledge gap. The installed journey requires human intent, subjects, one query and a bounded publication window, then saves an exact proposal revision. The user reviews its purpose, scope, route and limits before approving. Approval belongs to that revision, workspace and actor, and authorizes at most one logical task. Approved on-demand scope may exceed scheduled keywords. Material expansion needs a new approval.

The task returns acknowledgment and asynchronous status. Collection, normalization, publication and completion are distinct. Newly fetched or ingested-but-unpublished material cannot support an answer. A later explicit question uses new usable publications while the original answer remains pinned.

Richer agent research and synthesis are accepted roadmap scope. Their evidence and validation contracts are unresolved implementation design, not a silent repeal of the current exact-finding and human-scope decisions. See [ADR 0017](../../../docs/adr/0017-exact-supported-answers.md) and [ADR 0018](../../../docs/adr/0018-explicit-assistant-gap-scope.md).

Trace: FR-B01–FR-B09, OFR-B01–OFR-B02, UD-04. Evidence: [operational B, lines 35–40 and 94](../../../docs/functional-requirements.md), [knowledge lines 137–151](../../../docs/knowledge.md), and [tasks lines 213–225](../../../docs/tasks.md).

### Monitor X independently and investigate with existing knowledge

An operator configures monitoring topics independently of scheduled KB keywords. Recurring collection has explicit scope, cadence, bounds, retention and activation. Recent observations can support detection before full KB publication of every post.

Users inspect concise quantitative and semantic alerts with evidence, actual windows, baseline where applicable, method, coverage and uncertainty. The installed quantitative method compares configured comparable sampled-volume windows. Its thresholds are sample rules, not proof of population change or statistical significance. The installed semantic method marks provisional product-quality positions and possible controversy. It has no baseline and establishes neither verified sentiment nor emergence over time. Engagement spikes, sentiment shifts and broader semantic methods remain core FR gaps requiring specifications.

An investigation uses original recent evidence and pinned existing-KB context only. It cannot search externally, expand topic scope or create a campaign. Empty context stays empty. Selected useful observations can be explicitly promoted through normal ingestion/publication, retaining original identity, unknown dates, source policy, withdrawal and retention dependencies. Alert history can survive as safe metadata when its evidence becomes unavailable.

Trace: FR-C01–FR-C07, OFR-C01. Evidence: [operational C, lines 44–51](../../../docs/functional-requirements.md), [monitoring](../../../docs/monitoring.md), and [ADRs 0004](../../../docs/adr/0004-lightweight-monitoring-evidence.md), [0019](../../../docs/adr/0019-source-free-quantitative-alert-history.md), [0020](../../../docs/adr/0020-bounded-semantic-positions-full-input-policy.md), [0021](../../../docs/adr/0021-pinned-local-alert-context.md), [0022](../../../docs/adr/0022-promoted-source-lifecycle-inheritance.md) and [0023](../../../docs/adr/0023-bounded-recent-x-poll-authority.md).

### Explore supported relationships and inspect pipeline lineage

The graph answers which supported entities and relationships are present in a bounded permitted selection. Search, filters, selection, traversal, relationship direction, details and exact evidence all belong in the Neo4j-style experience. The installed projection includes native accounts/content, supported Brand/Product mentions, observed authorship and human catalog association. A Creator is distinct from an account. Matching handles, mentions or visual adjacency establish no identity equivalence, endorsement or causation. Observed, derived and human relationships need distinct inspectable bases.

The installed graph supports bounded cycle-safe 1–3-hop traversal. Its search pins support, while labels and transient traversal remain current governed exploration. It is not an immutable historical campaign graph. Empty and truncated selections, source narrowing and unavailable entities are first-class states. There is no requirement for a graph database. See [knowledge lines 157–173](../../../docs/knowledge.md), [local review lines 287–295](../../../docs/local-review.md) and the [graph owner](../../../src/smi_knowledge/graph/AGENTS.md). Trace: FR-G01–FR-G02 and OFR-G01.

Lineage answers how authorized work produced evidence, transformations, usable knowledge and attributed resource use. It links task origin/scope/approval, attempts, execution/recovery, runs, observations, derivations, prepared support, committed publication and cost. Queue acceptance is distinct from collection, ingestion, publication and terminal completion. A partial subset may publish. A publication may commit while completion is pending. Historical completion counts remain separate from current support availability.

The installed lineage projection reads one task through independent owner frontiers. It is read-only and not an atomic global pipeline snapshot. It exposes sanitized metadata and truncation, without provider handles, paths, secrets or unrestricted response/error text. Unknown cost is not zero, and amounts across currencies, periods or measurement bases cannot be indiscriminately totaled. See [tasks lines 227–239](../../../docs/tasks.md), [local review lines 297–303](../../../docs/local-review.md) and the [lineage owner](../../../src/smi_tasks/lineage/AGENTS.md). Trace: FR-L01–FR-L02 and OFR-L01.

### Configure acquisition, control cost and preserve learning

At most ten scheduled keywords share an initial configurable allowance of fifty unique eligible new posts per workspace/accounting day. Fifty is a total allowance, not a per-keyword quantity, guaranteed yield, provider request count, cost estimate or throughput promise. Refreshes and duplicate identities consume no new-post admission. Stable accounting-day identity survives configuration edits and restarts.

Automatic campaign discovery, configured scheduled discovery and exactly approved assistant tasks use the shared acquisition pipeline under different authority. General recency/engagement/trend prioritization, multi-route progressive acquisition, cross-route avoidance and value-based stopping remain targets beyond the installed bounded paths. The installed optional nickname fill is not a general enrichment planner.

Metered admission considers actual derived usage plus outstanding commitments before further chargeable calls. Unmeterable scope stays explicitly forecast-only. Approval, acquisition bounds, source quotas, spending ceilings and information-value stopping are separate controls. Meter failure is a visible control failure. Final cost reconciliation neither recovers a lost response nor permits another paid dispatch. Exact local retry identities cannot establish provider-side exactly-once execution.

Measurement plans preserve intended outcomes, access gaps, matching and attribution assumptions. Decision notes preserve attributable human learning. The UI cannot invent conversions, revenue, verified audience or causal lift from these records.

Trace: FR-P01–FR-P09, FR-S01–FR-S03, OFR-P01, OFR-S01–OFR-S04, PROP-12–PROP-14. Evidence: [FR lines 43–49](../../../FR.md), [operational pipeline/spending lines 55–76](../../../docs/functional-requirements.md), [costs](../../../docs/costs.md), [planning](../../../docs/planning.md), and [ADRs 0011](../../../docs/adr/0011-stable-schedule-accounting-day.md), [0012](../../../docs/adr/0012-atomic-scheduled-post-admission.md), [0013](../../../docs/adr/0013-capture-based-discovery-avoidance.md), [0014](../../../docs/adr/0014-live-discovery-response-and-billing-identity.md), [0015](../../../docs/adr/0015-recorded-live-schedule-authority.md) and [0016](../../../docs/adr/0016-explicit-bounded-profile-supplementation.md).

## Authority and evidence rules for every journey

| Actor or operation | Authority | Required visible distinction |
| --- | --- | --- |
| Trusted local human | Briefs, criteria selection, questions, exact assistant approval, optional curation, regeneration, plans and notes | The human action is attributable. Local actor configuration is not hosted authentication |
| Supported automated analysis | Criteria/ranking/answer preparation and automatic shortlist persistence | Generated output cannot create roles, weaken human constraints, approve research or manufacture review |
| Campaign or scheduled acquisition | Server-configured authority tied to actual coverage or an occurrence | A prompt or form cannot claim another origin to bypass assistant approval |
| Worker or polling execution | One admitted bounded task or interval | Ownership grants no new scope, source rights or uncertain paid retry |
| Graph, lineage or evidence read | Governed inspection | A read cannot acquire, retry, publish, create campaigns or approve work |
| Quality review | Actual person reviews exact attributable examples | Design approval, prepared packets and synthetic reviews cannot establish language accuracy or usefulness |

Evidence: [interface lines 7–36](../../../docs/implementation-spec.md), [architecture lines 89–107 and 141–153](../../../docs/architecture.md), and [evaluation lines 57–85](../../../docs/evaluation.md).

The [glossary](../../../GLOSSARY.md) distinguishes source reference, observation, assertion, interpretation, publication, answer, task and decision. Preserve native identity separately from mutable handles and corroborated Creator identity. Target market, interface language, post language, product origin and audience geography are different concepts. Unknown is distinct from zero. Source publication, capture, source-as-of, ingestion, KB publication, analysis and human review dates cannot substitute for one another.

Consequential results pin actual inputs, methods and support. Later evidence supports new work, not rewritten history. Current process, display and retention rights still govern each use. Loss of an unselected model input can invalidate the whole derived finding. A bilingual label or email must not create an unrestricted source copy. See [ADR 0002](../../../docs/adr/0002-pinned-support-current-policy.md) and [architecture lines 147–153](../../../docs/architecture.md).

## Findings that determine the handoff

| Finding | Evidence and implication |
| --- | --- |
| Local-first does not mean manual operation | UD-02/UD-05 and architecture L21/L93. The pilot roadmap needs actual worker scheduling, monitoring operation and email delivery, including failure/recovery, rather than relying on manual commands |
| Full FR UI is broader than installed methods | FR-C02/FR-C03 and operational L45/L51. Core engagement and semantic-shift gaps require explicit design/spec coverage. Keep them distinct from optional proposal extensions |
| Richer agent work changes the validation problem | ADR 0017/0018 and UD-04. Citation IDs alone do not validate arbitrary prose or executable scope. Future synthesis and proposed research plans need explicit evidence and approval contracts |
| Graph and lineage serve different decisions | FR-G01–FR-L02. Cross-link supported entities and their production history while preserving separate navigation, authority and coverage semantics |
| The proposal's ontology exceeds current identities | PROP-19–PROP-22 and architecture L68. Do not display Creator, Collaboration, audience or commercial outcomes as observed installed facts without their future evidence contracts |
| Email extends the source-copy boundary | UD-05, ADR 0002/0019/0020 and the notification owner. Prefer source-free status and governed links in the future delivery design. A delivered email cannot be retroactively redacted like the application |
| Bilingual UI is not language validation | UD-03, PROP-16 and evaluation L85. A working EN/KO switch must preserve IDs, state and source meaning. It does not establish Korean/Japanese model quality or Japanese-original adjudication |
| Technology examples do not require a rewrite | PROP-29–PROP-35 and interface L25. Sequence public operations and operational contracts first. FastAPI, queues, embeddings and specialized stores need a concrete reason |
| Human agreement has distinct gates | Recovery L15/L17 and roadmap L18. Shared understanding is confirmed. Actual UI review is pending. Language/usefulness and live-provider acceptance remain separate later evidence |

No newly discovered contradiction blocks Task 3. The accepted target is broader than the installed software. All new implementation details below are recommendations until reviewed in their own specification or design decision.

## Task 3 design brief

Produce an actual human-reviewable UI design/prototype for the confirmed brief within Task 3's authorized ownership. Task 1 supplies requirements and constraints, not a screen layout or feature implementation. Use the [matrix](requirements-matrix.md), [decision tree](decisions.md) and [Task 2 codebase report](../task2/codebase-analysis.md) together.

The first complete review journey is campaign creation through automatically saved recommendation, insufficient-coverage discovery, completion and explicit regeneration. Retain the assistant, independent X monitoring, graph, pipeline lineage, acquisition configuration, spending visibility, inbox/email notification design, measurement plans and human notes. Full FR scope cannot be reduced to the campaign journey. Distinguish the installed baseline, target preview and proposal future concepts wherever capability state matters.

Demonstrate a working English/Korean switch across navigation, controls, validation, statuses, empty/error states and explanations. Keep entered values, request/revision identities and selected graph/task context stable when switching. Preserve original source text and attribution. Translation features or Japanese-language UI were not requested. Use the four confirmed colors with readable text, keyboard focus and status cues that do not rely only on color. These interaction details are design recommendations implementing UD-03/UD-07, not additional user answers.

Every major view, action and material state needs a matrix ID. For each action, document the human goal, entry point, displayed evidence, actual actor/authority, public owner operation or missing adapter, immutable record/result, idempotent retry, version conflict, and observable completion. Existing form routes are not an assumed independent JSON API. Thin adapters must preserve the server-owned contracts in [implementation-spec.md](../../../docs/implementation-spec.md).

The design review must demonstrate these cases:

| Review case | Trace and completion evidence |
| --- | --- |
| Campaign, thin/empty result, optional curation and regeneration | FR-A01–FR-A07. Show original constraints, actual ranking method, automatic-save attribution, support, unknowns, discovery admission/refusal, unchanged old revision and explicit successor |
| Knowledge answer and exact enrichment approval | FR-B01–FR-B09. Show supported versus missing/blocked states, exact proposal scope, approval, acknowledgment, asynchronous task phases, usable publication and a later explicit question |
| Quantitative and semantic monitoring | FR-C01–FR-C07. Show comparable versus inadequate baseline, provisional semantics, core target-method gaps, KB-only context, unavailable support and selective promotion |
| Neo4j-style relationship exploration | FR-G01–FR-G02. Demonstrate search, filters, select/traverse, direction/basis, entity/edge details, exact evidence, bounded/truncated result and unavailable node |
| Pipeline and cost lineage | FR-L01–FR-L02, FR-S01–FR-S03. Trace authority to run/observation/transformation/publication/cost, including partial work, pending completion, unknown billing and current support loss |
| Acquisition and automated operation | FR-P01–FR-P09, OFR-P01, UD-02. Separate scheduled keywords/topics/on-demand scope, shared daily allowance, route capability, actual activity, blocked readiness and recoverable versus uncertain work |
| Inbox and email | FR-A07/FR-B09/FR-C05, UD-05. Design completion/alert content, source-free delivery, current governed links, channel configuration/status and delivery failure without changing task outcome |
| Bilingual state and preserved learning | UD-03/UD-07, OFR-X01. Switch language during a journey. Keep plans proposed, notes human-supplied and original evidence unchanged |

Across these cases include permission denial, withdrawal/expiry, stale captures, unknown dates, truncation, unavailable configuration, pending approval, waiting/partial/no-update/failure, meter refusal/failure, outstanding commitments, uncertain paid responses and stale edits. Distinguish a repeated exact request from a deliberate new operation. Mock or illustrative data must be labeled and cannot imply a live provider receipt or completed human quality review.

For the local-pilot implementation roadmap, recommend an operational unit that advances due schedules, executes admitted tasks, runs monitoring and delivers notifications through public owner interfaces. It must retain existing scope/attempt identities, fencing, finite bounds, readiness gates and uncertain-response handling. The particular scheduler/transport/process arrangement remains an engineering choice. Current code does not justify a wholesale rewrite.

Email needs a delivery contract for configured recipients, event identity, status, retry, failure and source-policy handling. Recommended content is a concise source-free outcome with a governed link. In a local pilot, a local application link requires access to the review machine/runtime. Do not invent a public URL, remote exposure, provider, price, delivery guarantee or authorization to send. Persistent delivery and any new copied content require an explicit future owner and documentation decision.

The richer-agent roadmap must specify allowed read/proposal tools, bounded research plans, full input provenance, claim validation, uncertainty, human approval of exact external scope, spending admission, asynchronous publication and follow-up questions. Include prompt/source-text handling, changed-scope rejection, partial evidence, validation failure and interrupted paid calls. A model cannot self-approve, become another task origin or make monitoring investigation acquire externally. ADR successor proposals need actual review before replacing current answer or gap-scope semantics.

Keep broader proposal extensions visible as distinct roadmap work: multimodal listening, stronger creator/audience/performance evidence, portfolio scenarios, ontology extensions, lifecycle-safe projections, actual outcomes/attribution/causal methods, hosted identity/tenancy and specialized technology only when justified. Core FR methods cannot be relabeled optional merely because they are also mentioned in the proposal.

Task 3 completion requires a reviewable artifact plus traceability and limitations. The coordinator must present its exact revision for actual human review before Task 4's implementation specs begin. Do not infer approval from a timer, task completion, model review or the earlier shared-understanding reply.

## Verification and limits

This recovery read the full proposal, both FR sources, glossary, root/domain/documentation/issue guidance, all 23 existing ADRs, architecture, roadmap, interface contract, relevant campaign/knowledge/task/monitoring/cost/planning/review documentation, graph/lineage/notification owner rules, prior matrix and Task 2 report. The matrix preserves stable IDs and original source line references. Local structural checks verify source-unit coverage, ID uniqueness and report links.

Structural verification passed on the three reports. It checked 99 unique matrix IDs, comprising 39 FR rows, 16 operational additions, 35 proposal rows and 9 confirmed-choice rows. All 27 numbered or bulleted source units in `FR.md` map to their original lines and expected IDs. All 37 operational requirement units checked have source references. All 94 local links resolve, including heading targets, and Markdown fences are balanced. Proposal goal coverage was reviewed against the complete source; the automated ID check does not establish semantic completeness or implementation correctness.

To reproduce the matrix row counts from the repository root, run:

```bash
python - <<'PY'
from collections import Counter
from pathlib import Path
import re
text = Path('.scratch/product-design-2026-11/task1-recovery/requirements-matrix.md').read_text()
ids = re.findall(r'^\| ((?:FR|OFR|PROP|UD)-[A-Z0-9]+) \|', text, re.M)
assert len(ids) == len(set(ids))
print(dict(Counter(value.split('-')[0] for value in ids)))
PY
```

No behavior changed, so this recovery did not rerun the shared suite or live operations. The coordinator's [existing verification record, recovery lines 35–37](../history/task1-recovery-brief.md), reports Ruff and documentation/ERD/symlink checks passing, then pytest stopping with 1 failed and 51 passed at the documented aging-fixture assertion in `tests/test_assistant_enrichment.py:261`. See [development lines 18–26](../../../docs/development.md). This is an inherited baseline limitation, not a passing suite or a fix performed here.

Only `.scratch/product-design-2026-11/task1-recovery/` is written. The fenced original task1 reports, production files, accepted glossary/ADRs, existing `.agents/`, `.claude/`, `skills-lock.json` and unrelated work remain outside this recovery's writes. No commit, push, spend, external message, delegation or email was performed.
