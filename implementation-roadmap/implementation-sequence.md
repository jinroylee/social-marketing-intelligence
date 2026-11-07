# Proposed implementation sequence for the approved product

Status: revised plan for review. These are proposed implementation contracts for an approved product/UI, not implemented features or accepted successor ADRs. Both review rounds' findings, validations and applied changes are in [the design history](../.scratch/product-design-2026-11/history/spec-review/).

Start with [S01 Restore a complete, time-stable verification baseline](specs/01-stable-verification-clock.md). It is the only dependency-free spec. Every direct dependency precedes its consumer, every edge records its reason in the spec's "Direct spec blockers" line, and each spec is independently claimable once its direct blockers and configuration prerequisites pass. None is implemented by this planning package.

The first delivery is the approved campaign-first, single-workspace local pilot: automated work, EN/KO chat with question-scoped retrieval, a current-highlighted monitoring stream, a fully interactive graph, independent spending controls, inbox and email. Live feasibility is probed early in S05 once the operator commands S03 exist, and recorded finally in four independently claimable readiness rows (S31–S34). Human evidence comes early at S08 (real discovered data on pre-UI paths) and S25 (browser check of graph, chart, campaign and chat), before the release record S35. Code or fixture completion does not complete any validation spec.

The r2 UI approval is already satisfied by [the actual user response](../.scratch/product-design-2026-11/ui-review-status.md#actual-r2-approval). Current ADRs, including 0017, 0018 and 0023, remain in force for the pilot. Open decisions: [Set the richer research and synthesis boundary](decisions/001-richer-agent-boundary.md) (W01) blocks S39; [Decide live X window comparability and receipt-time semantics](decisions/002-x-metric-measurement-time.md) (W02) blocks no spec. The map is [the wayfinder product map](decisions/000-product-map.md).

Use [gap analysis](gap-analysis.md) for installed foundations, [target architecture](architecture-target.md) for proposed ownership/contracts, and [traceability](traceability.md) for all 99 upstream IDs plus three r2 IDs. Publish a spec as a local execution issue under the repository tracker when starting implementation, with a real assignee, direct blockers and acceptance evidence.

## Ordered specifications

Depth is the longest dependency chain ending at the spec, counting the spec itself. Size: S = up to a few days, M = about one week, L = multi-week. Validation rows need actual people, access and authorization in addition to their build blockers.

| Order | Specification | Lane | Size | Mode | Milestone | Depth | Direct blockers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | [Restore a complete, time-stable verification baseline](specs/01-stable-verification-clock.md) | pilot-build | M | single-pass | M0 | 1 | None |
| S02 | [Compose the local pilot from one validated configuration](specs/02-pilot-configuration.md) | pilot-build | M | single-pass | M0 | 2 | S01 |
| S03 | [Give the operator recorded commands for cost controls and bounded X polling](specs/03-operator-commands.md) | pilot-build | S | single-pass | M0 | 3 | S02 |
| S04 | [Establish the bilingual client foundation, shell and client verification](specs/04-client-foundation.md) | pilot-build | M | wayfinder | M0 | 2 | S01 |
| S05 | [Probe bounded live model, discovery, X and email-provider feasibility early](specs/05-live-feasibility-probes.md) | live-validation | M | single-pass | M0 | 4 | S03 |
| S06 | [Publish catalog-scoped caption interpretations from automated tasks](specs/06-automated-interpretation.md) | pilot-build | M | single-pass | M0 | 2 | S01 |
| S07 | [Select question-, brief- and graph-scoped governed support at pilot scale](specs/07-pilot-scale-retrieval.md) | pilot-build | L | wayfinder | M0 | 2 | S01 |
| S08 | [Check shortlist and answer usefulness with a marketer on real discovered data](specs/08-early-marketer-checkpoint.md) | human-validation | S | single-pass | M0 | 5 | S05, S06, S07 |
| S09 | [Run bounded local work continuously with restart, health and lifecycle maintenance](specs/09-local-runtime.md) | pilot-build | L | wayfinder | M1 | 3 | S02 |
| S10 | [Open saved campaigns and inspect governed evidence in the shared inspector](specs/10-workspace-and-evidence.md) | pilot-build | M | single-pass | M1 | 3 | S04 |
| S11 | [Describe usable source routes and bounded selection policy](specs/11-source-capabilities.md) | pilot-build | M | wayfinder | M1 | 3 | S02 |
| S12 | [Complete brief to saved recommendation and explicit regeneration](specs/12-campaign-decisions.md) | pilot-build | L | wayfinder | M1 | 4 | S10, S07, S06, S02 |
| S13 | [Read asynchronous progress and exact pipeline lineage](specs/13-task-events-lineage.md) | pilot-build | S | single-pass | M1 | 4 | S10 |
| S14 | [Review exact enrichment scope and expose governed agent operations](specs/14-exact-approval-tools.md) | pilot-build | M | single-pass | M1 | 5 | S13, S10 |
| S15 | [Save conventional chat threads with question-scoped extractive turns](specs/15-conversations.md) | pilot-build | L | wayfinder | M1 | 4 | S10, S07, S02 |
| S16 | [Configure scheduled discovery and see route and runtime health](specs/16-discovery-operations-screen.md) | pilot-build | S | single-pass | M1 | 4 | S10, S11, S09 |
| S17 | [Page governed graph branches with stable identities and policy frontiers](specs/17-graph-reads.md) | pilot-build | M | wayfinder | M2 | 3 | S07 |
| S18 | [Explore the production graph with camera, pins and incremental branches](specs/18-interactive-graph.md) | pilot-build | L | wayfinder | M2 | 4 | S17, S10 |
| S19 | [Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility](specs/19-monitoring-depth-and-timing.md) | pilot-build | M | single-pass | M3 | 2 | S01 |
| S20 | [Operate independent topics, activation and alert history](specs/20-monitoring-workspace.md) | pilot-build | M | single-pass | M3 | 4 | S10, S19 |
| S21 | [Plot current and selected monitoring windows without fabricated data](specs/21-monitoring-history.md) | pilot-build | M | single-pass | M3 | 5 | S20, S19 |
| S22 | [Investigate alerts with existing KB context and promote selected evidence](specs/22-alert-investigation-promotion.md) | pilot-build | S | single-pass | M3 | 5 | S20 |
| S23 | [Detect supported engagement changes with comparable measurement ages](specs/23-engagement-anomalies.md) | pilot-build | M | wayfinder | M3 | 4 | S19, S11 |
| S24 | [Detect provisional semantic shifts with a comparable baseline](specs/24-semantic-shift.md) | pilot-build | L | wayfinder | M3 | 3 | S19 |
| S25 | [Check graph, chart, campaign and chat interaction in a real browser](specs/25-interaction-checkpoint.md) | human-validation | S | single-pass | M3 | 6 | S18, S21, S12, S15 |
| S26 | [Inspect and operate independent spending controls](specs/26-spending-operations.md) | pilot-build | M | single-pass | M4 | 4 | S04, S03 |
| S27 | [Plan finite field-capability acquisition steps and stop honestly](specs/27-progressive-acquisition.md) | pilot-build | L | wayfinder | M4 | 4 | S11 |
| S28 | [Task-integrate one named supplementary detail route](specs/28-supplementary-detail-route.md) | pilot-build | M | single-pass | M4 | 5 | S27 |
| S29 | [Deliver durable task and alert notifications through inbox and email](specs/29-inbox-email.md) | pilot-build | L | wayfinder | M4 | 4 | S09, S02, S10 |
| S30 | [Preserve measurement planning and prepare attributable KR/JP quality packets](specs/30-plans-and-quality.md) | pilot-build | M | single-pass | M4 | 5 | S12 |
| S31 | [Record live discovery, model and recurring-work readiness](specs/31-provider-readiness.md) | live-validation | S | single-pass | M5 | 5 | S05, S09, S26 |
| S32 | [Record live X monitoring and alert-method readiness](specs/32-monitoring-readiness.md) | live-validation | S | single-pass | M5 | 5 | S05, S09, S19, S23, S24, S26 |
| S33 | [Record supplementary detail-route readiness](specs/33-detail-route-readiness.md) | live-validation | S | single-pass | M5 | 6 | S05, S28, S26 |
| S34 | [Record email send readiness](specs/34-email-readiness.md) | live-validation | S | single-pass | M5 | 5 | S05, S29 |
| S35 | [Record pilot release acceptance on live data](specs/35-human-pilot-acceptance.md) | human-validation | M | single-pass | M5 | 7 | S14, S08, S22, S25, S30, S31, S32, S33, S34 |
| S36 | [Improve multilingual retrieval with pinned, rebuildable support](specs/36-evaluated-retrieval.md) | later-core-depth | L | wayfinder | Later | 6 | S07, S30 |
| S37 | [Prepare a bounded research and synthesis candidate for decision review](specs/37-agent-candidate.md) | later-candidate | L | wayfinder | Later | 6 | S14, S15 |
| S38 | [Obtain actual adjudication for the richer-agent successor](specs/38-agent-human-evidence.md) | human-validation-later | M | single-pass | Later | 7 | S37 |
| S39 | [Enable only the accepted grounded research and synthesis contract](specs/39-enable-richer-agent.md) | decision-blocked | L | wayfinder | Later | 8 | S38; decision W01 |
| S40 | [Move the proven pilot to authenticated workspace tenancy](specs/40-hosted-actors-tenancy.md) | later-proposal | L | wayfinder | Later | 8 | S35 |
| S41 | [Reconcile retained copies and rebuildable projections with operational recovery](specs/41-projection-governance.md) | later-proposal | L | wayfinder | Later | 9 | S36, S40 |
| S42 | [Add evidenced multimodal and richer ontology concepts](specs/42-multimodal-ontology.md) | later-proposal | L | wayfinder | Later | 10 | S36, S41 |
| S43 | [Compare objective-specific creator factors and feasible portfolios](specs/43-objective-portfolios.md) | later-proposal | L | wayfinder | Later | 11 | S36, S42 |
| S44 | [Measure actual outcomes and rule-based attribution](specs/44-outcomes-attribution.md) | later-proposal | L | wayfinder | Later | 10 | S30, S40, S41 |
| S45 | [Estimate incremental effect only under an accepted causal design](specs/45-causal-measurement.md) | later-proposal | L | wayfinder | Later | 11 | S44 |

## Execution modes

Each spec is classified for execution. **Single-pass** (24): one owner or a thin layer over installed operations, with its design pinned by the spec and size S or M, so one agent can claim and finish it; human- and operator-run validation specs are single-pass procedures. **Wayfinder** (21): large or foundational, with several open internal decisions that shape other specs; chart those decisions as a wayfinder map with child issues and slice the work before implementation. Each spec's header names its reason and, for wayfinder specs, the decisions to chart.

- Single-pass build: S01, S02, S03, S06, S10, S13, S14, S16, S19, S20, S21, S22, S26, S28, S30
- Single-pass human/operator procedures: S05, S08, S25, S31, S32, S33, S34, S35, S38
- Wayfinder, pilot: S04, S07, S09, S11, S12, S15, S17, S18, S23, S24, S27, S29
- Wayfinder, later: S36, S37, S39, S40, S41, S42, S43, S44, S45

## Milestones

- **M0** (S01, S02, S03, S04, S05, S06, S07, S08). Baseline, configuration, operator commands, client foundation, live probes, automated interpretation and pilot-scale retrieval, ending at the early real-data marketer check S08 on pre-UI paths (legacy forms and CLI). The probes S05 run once the operator commands exist and the user grants bounded live authorization (U1).
- **M1** (S09, S10, S11, S12, S13, S14, S15, S16). Runtime with lifecycle maintenance, workspace and inspector, source capabilities, brief-to-shortlist, task progress, exact approval, chat, and the D1 schedule plus runtime-health screen.
- **M2** (S17, S18). Graph reads and the interactive graph, whose first deliverable is a time-boxed layout-library spike.
- **M3** (S19, S20, S21, S22, S23, S24, S25). Live-window comparability, topics and alerts, the current-highlighted chart, investigation and promotion, engagement and semantic-shift methods, ending at the browser checkpoint S25 for graph, chart, campaign and chat.
- **M4** (S26, S27, S28, S29, S30). Spending controls, the acquisition plan model and one named supplementary route, inbox plus single-recipient SMTP email, and planning with KR/JP quality packets.
- **M5** (S31, S32, S33, S34, S35). Four independently claimable readiness rows (S31–S34) and the live-data release record S35.
- **Later** (S36, S37, S38, S39, S40, S41, S42, S43, S44, S45). Evaluated retrieval, the richer-agent candidate, adjudication and decision-blocked enablement, hosted tenancy, projection governance, multimodal ontology, portfolios, outcomes/attribution and causal measurement. These preserve full FR and proposal coverage without blocking the local pilot.

## Critical paths (computed from plan.json)

- First live evidence: S01 → S02 → S03 → S05 (depth 4).
- Early real-data marketer check: S01 → S02 → S03 → S05 → S08 (depth 5).
- Deepest pilot build spec: S01 → S04 → S10 → S13 → S14 (depth 5).
- Browser interaction checkpoint: S01 → S04 → S10 → S20 → S21 → S25 (depth 6).
- Pilot release record: S01 → S04 → S10 → S20 → S21 → S25 → S35 (depth 7).
- Size-weighted, early real-data marketer check: S01 → S07 → S08 (about 4.5 illustrative weeks).
- Size-weighted, pilot release record: S01 → S07 → S17 → S18 → S25 → S35 (about 9.5 illustrative weeks).
- Headline journeys complete at depth S12 4, S15 4, S18 4, S21 5 (campaign, chat, graph, chart).

Depth chains are precedence, not duration; the size-weighted chains use illustrative weights only to compare orderings. Provider access and actual reviewer availability can dominate elapsed time, which is why the bounded live authorization (U1) is requested at plan start.

## Safe parallel execution

Pilot specs grouped by dependency depth; every spec in one group can run in parallel once the earlier groups it depends on are done:

- Depth 1: S01
- Depth 2: S02, S04, S06, S07, S19
- Depth 3: S03, S09, S10, S11, S17, S24
- Depth 4: S05, S12, S13, S15, S16, S18, S20, S23, S26, S27, S29
- Depth 5: S08, S14, S21, S22, S28, S30, S31, S32, S34
- Depth 6: S25, S33
- Depth 7: S35

Coordinate shared smi_review catalogs and adapters through one integration owner, with distinct feature modules per spec. Do not have workers write one shared spec, schema migration or browser state object concurrently. Integration with a spec that has not landed is a conditional check, never a hidden blocker; each conditional check is mirrored in its partner spec, and when both exist the spec that lands second makes the check pass unconditionally.

## User decisions with recommended defaults

None of these blocks the start of the pilot build or any pilot spec; W01 blocks only S39. Each has a default the plan proceeds on until the user answers. Ask U1, W02, U3, U5 and U7 at plan start.

| ID | Decision | Default if unanswered | Affects |
| --- | --- | --- | --- |
| U1 | Grant bounded live authorization and credentials early: model; Bright Data keyword, including a bounded discovery corpus for the early marketer check (up to 10 keywords, a few hundred posts); X recent for one topic over a bounded number of windows; the email mailbox's semantics. Per-capability call counts and one spending ceiling. | Request at plan start with the smallest useful caps. If not granted, the probes and the early marketer check stay blocked, the build continues on fixtures and premise-dependent specs stay provisional. | S05, S08, S31, S32, S33, S34 |
| W02 | Ask at plan start. For live X: (a) may the recorded receipt time bound capture and metric measurement time from above; (b) may an unsaturated single page count as a complete sample of the provider's recent-search results for the literal query; (c) may a saturated window support only lower-bound crossing claims? This amends ADR 0019, ADR 0023 and docs/monitoring.md through new method versions. | Accept all three as a narrowly scoped amendment, with market coverage still unknown and installed v1 unchanged. If rejected, live windows stay not assessable, there are no live alerts and no live engagement, and monitoring readiness records blocked_by_decision. Blocks no spec. | S19, S23, S24, S32 |
| U3 | Pilot X monitoring depth, revisited after the probe's X row: (a) counts endpoint as the volume series; (b) bounded multi-page collection; (c) shorter cadence within configured cost; (d) accept a saturated lower-bound display. (a) and (b) need an ADR 0023 successor and more recurring paid authority. | (c)+(d). The probe's X row records the saturation rate and a recommendation, and the coordinator re-asks. Choosing (a) or (b) adds one M spec before monitoring readiness. | S05, S19, S21, S32 |
| U4 | Which supplementary detail route, and is tiktok-web source use permitted? | Bright Data profile/post detail fields; tiktok-web stays unavailable. | S28, S33 |
| U5 | Permit scoped headless-browser tests against the loopback app, either (i) in CI only with no agent browsing, or (ii) also by agents? | Keep declining. Stated cost: graph and chart interaction stay human-verified only, at the browser checkpoint and release record, with Node state tests in between. | S04, S18, S21, S25 |
| U6 | W01 initial direction: agent-drafted scope for human approval, and validated fluent synthesis. | Proceed with the disabled candidate under the recommended 'yes' branches as non-binding working assumptions; enabling stays decision-blocked. | S37, S39 |
| U7 | Pilot email goes to one configured recipient through SMTP submission from an operator-supplied mailbox account; multi-recipient preferences come later. | Yes, with SMTP submission. If the operator has only an HTTP email API account, inbox-email uses it behind the same delivery-identity model. | S05, S29, S34, S40 |

Engineering choices recorded inside specs, not user decisions: graph library versus hand-built layout (S18, first deliverable), configuration file format (S02), retrieval index mechanism and ranking rule (S07), event table versus derived phases (S13), interpretation before publication (S06), live-page method versioning (S19) and notification Message-ID derivation (S29). External prerequisites, not decisions: a named marketer and a KR/JP reader for S08, S25 and S35; an operator mailbox account (U7); live accounts under U1.

## Prerequisites and honest blocked states

S01 requires real PostgreSQL and the locked development environment, and first inventories the whole suite without --maxfail; no green baseline is claimed before that run. Retention, thresholds, models, provider accounts, rate versions, currencies and ceilings are validated operator configuration in S02, not fabricated product constants; cadence stays a topic-revision setting. Cost configuration and X activation are recorded operator commands (S03); keyword schedules use the legacy /schedules form until S16, and topic forms arrive in S20.

Specs whose premises depend on probe results (S19 live-page premises, S23, S28 fields, S29 transport) record those premises as provisional until the matching S05 row passes. Contingency: if U3 is answered (a) or (b), add one M spec "Extend live X monitoring depth" after S19 and S03 that blocks S32. S15 requires a finite configured retention policy for user text and drafts. S29 requires validated recipient/sender/link policy before transport activation. Agent browser access remains declined (U5); human browser checks run at the checkpoints. Failure of one live capability blocks claims for that capability only.

S36–S39 deepen retrieval and richer research; S39 stays blocked until W01 is resolved and the accepted method/error policy is concrete. S40–S45 keep the broader proposal with explicit prerequisites. No graph database, multiple agents, microservices, queue vendor, vector store or analytics stack is preselected by the UI's appearance.

## Verify this plan

From the repository root, run:

```bash
python implementation-roadmap/source/build_plan.py
python implementation-roadmap/source/write_sequence.py
python implementation-roadmap/source/verify_plan.py --frontier
uv run --locked python tools/check.py --static
```

[`source/plan_source.json`](source/plan_source.json) is the single editable source; `source/build_plan.py` renders the specs, `plan.json` and traceability from it. [Verification output](verification/verification-results.txt) records structural checks only. A passing planning verifier cannot prove semantic completeness, provider readiness or human acceptance. The implementation checks in each spec remain required.
