# Round-2 critical review of the Task 4 implementation-spec sequence

Reviewer scope: `.scratch/product-design-2026-11/task4/` (sequence, S01–S40, gap analysis, target architecture, plan.json) and the wayfinder issues W00–W02, checked against `src/` and `tests/`. I ran only read-only commands and `verify_plan.py --frontier`, which passes. I drafted these findings before opening `spec-review/round-1/`. Each finding states how it relates to round 1.

Line references are repository-relative. Size-weighted path estimates use illustrative weights (S = 0.5, M = 1, L = 3 weeks). They are used to compare orderings, not as schedule promises.

## 1. Verdict

**Validity.** Most of the gap register holds up against the code. I re-verified:

- `smi-review main` builds `ReviewApp` without a model route (`src/smi_review/server.py:131`).
- The 100-publication scan and 100-member caps (`src/smi_knowledge/queries/store.py:33,129,163-169`; `src/smi_knowledge/graph/store.py:34`).
- The chat limit of 20 with only a separate literal text field (`src/smi_assistant/store.py:60`; `src/smi_review/app.py:617`).
- Worker publication without interpretation IDs (`src/smi_tasks/worker.py:343`).
- The existing attempt phase history (`src/smi_tasks/schema.sql:59`).
- The tick and run entry points the runtime would compose (`src/smi_tasks/schedules/__init__.py:181`; `src/smi_monitoring/polling/store.py:99`; `src/smi_tasks/worker.py:180`).
- The test baseline: 652 test functions, `--maxfail=1`, and about 217 hard-coded September/October dates.

Owner names, public operations and the authority invariants are accurate, and most build specs could be claimed by one owner with checkable acceptance.

The package still has two critical validity defects that would leave a headline deliverable broken with every spec done:

- **No live monitoring alert can ever fire.** Every live X window is saved as `partial`, and both installed monitoring methods refuse partial windows. No spec changes that rule (R2-F01).
- **The "early" live probes have no executable operator path.** No CLI or form configures cost routes or activates X polling before S24 and S17 (R2-F02).

S16 also re-specifies fields the code already persists, in a way that would discard recorded data (R2-F07). The W02 and S29 records contradict their own dependency graph (R2-F08, R2-F10). Several UI integrations belong to no spec (R2-F09).

**Optimality.** The set of specs is broadly right, and the round-1 reordering improved risk order and parallel width. The current order still has three problems:

- **The release path is longer than it needs to be.** It runs through an artificial UI edge (S08→S20) into the acquisition backend chain S20→S25→S26 (R2-F03). An L-sized client-foundation bundle (S03) sits in front of every UI spec (R2-F04).
- **The highest-uncertainty items reach people late.**
  - Live monitoring meaning (R2-F01, R2-F06) has no decision point after the probe.
  - Real-data usefulness of lexical retrieval and extractive answers is checked only after the full C1 and chat UIs are built (R2-F05).
  - The agent-unverifiable graph and chart reach a human only at S23 (R2-F05).
- **S06 hides decisions that drive usefulness.** It does not choose the index or the ranking rule (R2-F11).

The proposed changes in section 3 cut the illustrative release path from about 12 to about 9.5 weeks. They bring a real-data output check to about 4.5 weeks instead of about 8.5, and they add one widened decision plus one post-probe decision on monitoring. Nothing below calls for a rewrite or a new technology.

**Round-1 fidelity.** The coordinator applied validation section 4a/4b faithfully: edges, sizes and depths match `plan.json`. The revision itself introduced or kept these defects:

- the S20 UI edge on the backend chain (from the R1-F14 resolution),
- S16's duplicate fields (from the validator's S16 text),
- the W02 default-versus-blocker contradiction,
- the S13→S07 edge,
- the S03 bundle.

R1-F06's premise that only windows with more than 10 posts are incomplete was wrong. All live windows are partial (R2-F01).

## 2. Findings, most severe first

### R2-F01 — The installed volume and controversy methods can never assess a live X window, and no spec changes that

- **Severity:** critical. **Confidence:** high (code facts and an existing test).
- **Affected specs:** S16, S17, S18, S21, S22, S27, S29, S30; decision W02.
- **Evidence:**
  - The live X route hard-codes `'declared_coverage': 'partial'` and maps every record with `'captured_at': None, 'metric_measured_at': None` (`src/smi_monitoring/polling/route.py:150,156`).
  - The recent owner sets `collection_status` from `declared_coverage`. It also marks a window incomplete whenever any selected record lacks `captured_at` (`src/smi_monitoring/recent/store.py:261-264`).
  - `tests/test_live_recent.py:162` asserts that a live window is `partial`.
  - The volume method returns `not_assessable` with `collection_incomplete` for any non-complete window (`src/smi_monitoring/alerts/store.py:54-55`). The semantic method's `eligible` adds the same no-call limitation (`src/smi_monitoring/semantic/method.py:58-59`).
  - `docs/monitoring.md:86` documents that partial collection or unknown capture times give `not_assessable` and no alert.
  - No spec touches this rule:
    - S16 adds only a `collection_saturated` label and `metrics_retrieved_at` (`task4/specs/16-monitoring-depth-and-timing.md:31,53`).
    - S17-A01 "detect[s] a bounded volume/controversy sample" on fixtures (`17-monitoring-workspace.md:55`).
    - W02 asks only about metric time for engagement and claims to block S21 alone (`wayfinder/issues/002-x-metric-measurement-time.md:10`).
- **Consequence if unchanged:**
  - With S01–S29 complete, live topics yield windows but every volume and controversy assessment is `not_assessable`. There are no live alerts, no live alert inbox or email (S27), and no method points on the live chart (S18). S22's baseline shift fails the same eligibility check.
  - Every build acceptance still passes on fixtures, which declare `complete`. The failure surfaces only at S29 or S30.
  - The user's confirmed "real automated … monitoring" goal is not met.
- **Proposed change:**
  - **Widen W02** into one decision on live X window semantics:
    - (a) Can the response receipt time (already recorded, see R2-F07) serve as an upper bound for both capture time and metric measurement time?
    - (b) Can a single page without `next_token` count as complete for the query within the provider's recent index?
    - (c) What is a saturated window: lower-bound only and not comparable, or does it trigger the U3 or counts-endpoint options in R2-F06?
  - Ask it at plan start. It is an evidence-semantics question with a cheap answer and no build cost.
  - **Make S16 own the resulting change** to coverage derivation and the method eligibility inputs, with a W02 decision blocker on that live part only.
  - **Add live-shaped fixture acceptance** to S16, S17, S18 and S22: a receipt shaped like `route.py`'s output, with `partial` and missing capture time, must yield the decided outcome. That prevents fixture-only passes.
- **Round-1 relation:** New. R1-F06 saw incompleteness only for saturated windows.

### R2-F02 — The live probes (S04) and the simulated-model start-up check (S02-A02) have no executable operator path

- **Severity:** critical. **Confidence:** high.
- **Affected specs:** S02, S04, S13, S24, S29.
- **Evidence:**
  - **Every live route refuses without an operator-configured cost route:**
    - X polling waits with `live_x_cost_configuration_required` (`src/smi_monitoring/polling/store.py:150-152`).
    - Live keyword discovery raises `live_discovery_cost_configuration_required` (`src/smi_ingestion/adapters/tiktok_keyword/__init__.py:81`).
    - Profile supplementation stops with `shared_cost_configuration_required` (`src/smi_tasks/supplementation/__init__.py:126-129`).
    - The model route opens a metered operation on `route.scope_id`. It requires a `metered`/`weighted_token` scope with a matching rate version (`src/smi_campaigns/responses/__init__.py:140-146`). Even a simulated model in S02-A02 needs a configured scope.
  - **No shipped path configures those controls.** Only tests call `UsageAccounting.configure_scope/configure_route/configure_ceiling` (`src/smi_costs/store.py:33,51,85`). `smi-ingest` has no cost subcommands (`src/smi_ingestion/cli.py` parser list), and `ReviewApp` exposes no configuration route.
  - **No shipped path activates X polling.** No CLI or HTTP route calls `RecentPolling.activate` or `run_due`; the app only reads polling state (`src/smi_review/app.py:220`). Activation creates a recurring authority (`src/smi_monitoring/polling/store.py:48-60`).
  - **S04 forbids exactly what it needs.** It says "Probes activate no recurring topic or schedule" (`04-live-feasibility-probes.md:46`), yet it must measure `next_token` frequency and metric timing across windows (`:28`, S04-A02).
  - **The configuration path arrives late.** Cost configuration belongs to S24 (`24-spending-operations.md:27,31`), at depth 4 behind S03 and S08. Activation forms belong to S17, also at depth 4. S04 depends only on S02.
- **Consequence if unchanged:**
  - S04 cannot produce any live row, so S13 ("requires passed … rows"), S29 and S30 stall.
  - Workers will improvise by seeding the cost ledger from the configuration file, or will run ad-hoc Python. Either collides with S24's versioned operator-command model ("Never rewrite historical rates") and with ADR 0023's recorded-activation rule.
- **Proposed change:**
  - **Add S02b**, "Operator command surface for cost controls and bounded polling" (size S, depends on S02). It contains:
    - CLI commands over the existing `configure_scope/configure_route/configure_ceiling`, with request IDs and receipts that S24 later reuses;
    - `RecentPolling` activate, deactivate and run-due commands.
  - **Redefine the S04 X row** as an explicitly bounded activation (N windows, then a recorded deactivation). Replace the "no recurring topic" invariant with "no unbounded or unrecorded activation".
  - **Re-point dependencies.** S04 depends on S02b. S24 keeps the S1 UI, reconciliation and meter recovery.
- **Round-1 relation:** New. Neither round-1 document mentions cost-route configuration or an activation path.

### R2-F03 — The round-1 fix put a UI edge on the acquisition backend chain, and that chain is the release critical path

- **Severity:** major. **Confidence:** high.
- **Affected specs:** S20, S21, S25, S26, S29, S30.
- **Evidence:**
  - **S20 bundles three different concerns:**
    - a typed capability registry,
    - a deterministic recency, engagement and trend selection policy (FR-P02/P03),
    - the D1 configuration screen.
  - Because of the screen, S20 depends on S08 (`20-source-capabilities.md:8`).
  - **The downstream edges need only the backend half.** S25 depends on S20 only for "declared route/field capability and selection policy" (`25-progressive-acquisition.md:8`). S21 depends on S20 only for "metric capability per route" (`21-engagement-anomalies.md:8`). The single X route's metric fields are fixed in `src/smi_monitoring/polling/route.py:87,145-151`.
  - **The sequence's own critical paths go through this edge.** "Deepest pilot build spec: S01 → S03 → S08 → S20 → S25 → S26" and "Pilot release record: … → S29 → S30" (`implementation-sequence.md:72,77`). Size-weighted, that is about 12 weeks; splitting S20 gives about 10.
- **Consequence if unchanged:** The supplementary-detail chain waits for the client foundation and campaign workspace it does not use. Release slips by roughly the duration of S03 plus S08.
- **Proposed change:**
  - **Split S20.** S20a is the registry plus selection policy and public readiness read (M, depends on S02). S20b is the D1 screen (S, depends on S08 and S20a), which also hosts runtime health (R2-F09).
  - **Re-point S25** to S20a.
  - **Drop S21→S20.** Read the X metric capability from the polling route description, or from S20a only as a conditional check.
- **Round-1 relation:** Introduced by the R1-F14 resolution ("S20 owns the D1 configuration UI").

### R2-F04 — S03 is a multi-week bundle in front of every UI spec and front-loads its consumers' logic

- **Severity:** major. **Confidence:** high.
- **Affected specs:** S03, S08, S12, S15, S18, plus every UI spec through S08's fan-out of 9 dependents.
- **Evidence:**
  - **S03 (L) carries consumer-specific work:**
    - the graph layout and library decision,
    - graph branch/generation reducers,
    - chart-series reducers,
    - composer/draft/IME reducers (`03-client-foundation.md:28`).
  - **Its acceptance duplicates the consumers' acceptance.** S03-A02 (stale-generation discard and overlapping-branch collapse) repeats S15-A01/A02 (`15-interactive-graph.md:52,56`). S03-A03 (IME, Shift+Enter, empty input) repeats S12-A04 (`12-conversations.md:65`).
  - **Several S08 edges justify themselves with S03 content.** S24 and S27 cite "renders in the shell" (`24-spending-operations.md:8`, `27-inbox-email.md:8`). The shell is S03, not S08.
- **Consequence if unchanged:** No feature UI can start until about weeks 4–5 of the illustrative schedule. Reducer design for graph, chart and chat is fixed before those specs' owners have studied their data contracts (S14, the history read, conversations), so rework is likely.
- **Proposed change:**
  - **Narrow S03 to M:** API client/envelope, `/api/v1` adapter framework, i18n mechanism and completeness check, shell, navigation, theme, EN/KO switch, the freshness utility, and the `node --test` harness.
  - **Move consumer logic to its consumers.** The graph reducer and library decision go to S15, as a time-boxed first spike (see R2-F05). The chart-series reducer goes to S18. The composer reducer goes to S12.
  - **Re-point S24 and S27** to S03. Make inspector links from the inbox a conditional check.
- **Round-1 relation:** Refines R1-F04 and R1-F10. Round 1 asked for a foundation; it did not ask for consumer reducers inside it.

### R2-F05 — Real-data usefulness and agent-unverifiable interaction reach people only after the L-sized builds they should steer

- **Severity:** major. **Confidence:** high on the structure; medium on how often the early check would change direction.
- **Affected specs:** S06, S09, S12, S13, S15, S18, S23, S31; user decision U5.
- **Evidence:**
  - **S13 is not early.** Its direct blockers are S04, S07, S09 and S12 (`13-early-marketer-checkpoint.md:8`). Transitively it waits for S03 (L), S06 (L), S07 (L), S09 (L) and S12 (L). Illustratively it lands about 8.5 weeks into a 12-week path, the same time as S23.
  - **A real-data output check is already possible without the new UI.** The legacy server-rendered UI runs brief → interpretation → current comparison → (ranked) recommendation → shortlist, and question → answer (`src/smi_review/app.py:612-619,670-720`). `smi-ingest run-live-discovery-task` exists (`src/smi_ingestion/cli.py`). Each UI spec retires these forms only after parity, so they remain usable early.
  - **Retrieval quality is checked only on fixtures before S13.** S06 acceptance is fixture-only (`06-pilot-scale-retrieval.md:54-70`). Literal containment over captions is the installed matcher (`src/smi_knowledge/queries/store.py:84-109`). Cross-language questions (an EN question over KO/JA captions) depend on catalog aliases alone. S31 is "Later" with no trigger that pulls it forward.
  - **The graph and chart have no rendered verification before S23.** S15 (L) and S18 (M) are client-heavy and agents cannot see them while U5 stays declined.
- **Consequence if unchanged:** The two highest-uncertainty questions are answered after the expensive UI is built:
  - Are shortlists and extractive answers useful on discovered KR/JP data with lexical retrieval?
  - Does the graph feel genuinely interactive?

  A negative answer at S13 or S23 means rework in S06, S09, S12 or S15 late in the plan.
- **Proposed change:**
  - **Add S13a, "Real-data output check"** (S, human-validation; depends on S04, S05 and S06). A marketer and a KR/JP reader grade about 10 briefs' shortlists and about 10 questions' supporting findings, with recorded denominators, through the legacy forms and CLI. Pre-declare the outcomes:
    - Retrieval fails → revise S06 ranking or pull a subset of S31 forward before S12 starts.
    - Mention judgments fail → revise S05 catalog rules.
  - **Re-point S13:** depend on S13a, S09 and S12, and drop S13→S07. The checkpoint judges output usefulness; automation is proven by S07-A01 and S29.
  - **Run the S15 graph-library spike early,** with a 30-minute human look.
  - **Re-ask U5 narrowly:** headless tests against loopback in CI only, with no agent browsing. State the cost of declining: S15 and S18 stay unverified until S23.
- **Round-1 relation:** Extends R1-F08. The intent there was early, real-data H1; placing it after the full UI defeats that intent.

### R2-F06 — Monitoring depth and engagement meaning have no decision point after the probe, and the measurement route S21 needs is missing

- **Severity:** major. **Confidence:** medium. Volume saturation depends on topic traffic; the age effect follows from the code.
- **Affected specs:** S04, S16, S18, S21, S29; decision U3.
- **Evidence:**
  - **Volume is capped at one 10-post page per window.** `MAX_RECORDS = 10` with one recency-sorted page (`src/smi_monitoring/polling/route.py:21,87`). The volume value per window can therefore never exceed 10 (ADR 0023).
  - **The posts are minutes old when measured.** A window is collected once it ends at least 30 seconds in the past, and the next is due one cadence later (`polling/route.py:85`; `polling/store.py:233`). The collected posts are the ≤10 newest in each window, so their `public_metrics` are taken minutes after posting.
  - **S21 names a route no spec builds.** It warns that "Additional measurement acquisition needs a separately activated bounded route/operation" (`21-engagement-anomalies.md:27,31`).
  - **The post-probe revisit has no owner.** U3's default is "No at pilot start … revisit with X probe data" (`implementation-sequence.md`, user-decision table). No spec or decision owns that revisit.
  - **The counts-endpoint probe result has no consumer.** S04 probes counts-endpoint availability (`04-live-feasibility-probes.md:28`), and no spec uses the result.
- **Consequence if unchanged:**
  - The approved time-series chart may plot a series pinned at "10, saturated" for any active topic.
  - Even with W02 accepted, live engagement compares near-zero counts on minutes-old posts. The output is honest but not useful.
  - S21 (M) and its S29 row become effort spent to prove a method unassessable.
- **Proposed change:**
  - **Add decision W03, "pilot X monitoring depth".** Its prerequisite is S04's X row. Options:
    - (a) the counts endpoint as the volume series (an ADR 0023 amendment: a new operation),
    - (b) bounded multi-page collection (U3),
    - (c) shorter cadence within quota,
    - (d) accept a saturated "≥10" display.

    Resolve it before S18 acceptance.
  - **Decide engagement explicitly.** Either add a spec "Bounded X re-measurement lookup at a configured post age" (M; depends on S16 and S07; needs an ADR 0023 successor), or declare live engagement unassessable for the pilot and remove S21 from S29's live rows.
- **Round-1 relation:** Partly re-raises R1-F06. Its counts-endpoint and re-measurement options were dropped in validation, not explicitly rejected; validation only moved multi-page collection to U3. The age-at-measurement argument and the missing post-probe owner are new.

### R2-F07 — S16 re-specifies behavior that is already installed and would discard recorded evidence

- **Severity:** major. **Confidence:** high.
- **Affected specs:** S16, S21; decision W02.
- **Evidence:**
  - **Receipt time is already recorded.** The poller sets `acquisition['retrieved_at']` after the response returns (`src/smi_monitoring/polling/store.py:212`). It enforces a 20-second save deadline against it and saves it on the window and attempt (`:230-232`).
  - **The receipt already carries the other proposed fields:** `pagination_remaining`, `retrieved_at` and `elapsed_seconds` (`polling/route.py:128,155-156`).
  - **Both windows and observations already persist the acquisition JSON,** next to `published_at` (`src/smi_monitoring/recent/store.py:271-272,287-288`).
  - **Cadence is already per-topic and revision-pinned.** Cadence, window, record and retention settings are validated per topic revision (`recent/store.py:102-104`). Window ends align to cadence (`:194`). A topic revision change forces reactivation (`polling/store.py:157`).
  - **S16 nonetheless asks for redundant or conflicting work:**
    - to "add the saturation and `metrics_retrieved_at` fields with explicit legacy-unrecorded values" (`16-monitoring-depth-and-timing.md:37`),
    - S16-A04, "Legacy windows report `metrics_retrieved_at` as unrecorded" (`:67`),
    - "Cadence is read from S02 and pinned per activation" (`:31`),
    - S16-A02, which tests installed alignment (`:59`).
- **Consequence if unchanged:**
  - Duplicate columns get added.
  - Real receipt times on existing live windows are labelled unrecorded, which discards evidence.
  - A revision-pinned topic setting moves into global configuration, which conflicts with ADR 0023's model that an activation pins a topic revision.
  - W02's question also overstates the semantic leap: the measurement already lies within the recorded request interval.
- **Proposed change:** Rewrite S16 as size S:
  - project `pagination_remaining` into a typed `collection_saturated` limitation on window, volume and semantic reads;
  - expose `acquisition.retrieved_at`, with its elapsed bound, as `metrics_retrieved_at`;
  - backfill live windows from the stored JSON, and mark only offline windows as unrecorded;
  - have S02 supply only allowed cadence bounds and cost caps;
  - keep A02 as a regression test only;
  - carry the R2-F01 coverage-derivation change.
- **Round-1 relation:** Introduced by the validator's S16 text (`validation.md:130,492-500`), which assumed receipt time was not recorded.

### R2-F08 — W02 is both a default-proceeding user decision and a hard blocker, so the pilot release record is gated on an unanswered human decision

- **Severity:** major. **Confidence:** high.
- **Affected specs:** S21, S29, S30; issue W02.
- **Evidence:**
  - **The two records disagree.** The sequence says of its decisions table, "None of these blocks the start of the pilot build. Each has a default the plan proceeds on" (`implementation-sequence.md:99`), and W02 is in that table (`:104`). Yet S21 lists W02 as a direct decision blocker (`21-engagement-anomalies.md:9`), and `verify_plan.py --frontier` prints "DIRECT DECISION-BLOCKED: S21 (W02)".
  - **The block propagates to the release record.** S29 depends on S21 and S30 on S29, so the claim "No other pilot build spec is blocked by this decision" (`wayfinder/issues/002-x-metric-measurement-time.md:10`) is false transitively.
  - **S21's build does not need the decision.** Without W02, S21 reports `measurement_time_unknown` (`21-engagement-anomalies.md:27`).
- **Consequence if unchanged:** A worker following the claimability rule cannot start S21. If the user never answers, S29 and S30 never become claimable, or the coordinator overrides the plan informally.
- **Proposed change:**
  - Remove W02 as an S21 build blocker. Bind live-X metric time behind a configuration choice that defaults to unassessable.
  - Make the widened W02 (R2-F01) a decision blocker only of S16's live coverage derivation and of the relevant S29 rows.
  - Correct the W02 issue text.
- **Round-1 relation:** Introduced by the revision (validation decision table 4e).

### R2-F09 — Cross-spec UI integration is left to "conditional checks" that no spec is obliged to complete

- **Severity:** major. **Confidence:** high on the gaps; medium on the impact.
- **Affected specs:** S07, S10, S12, S16, S17, S18, S21, S22, S25, S26.
- **Evidence:**
  - **The runtime-health screen has no owner.** S07 says "Operations screens show last tick, per-component health, next due" (`07-local-runtime.md:42`), but it has no S03/S08 dependency, no UI obligations and no UI acceptance. No other spec builds the health screen that r2 requires ("health, last success and recovery", `task3/r2/design-spec.md:156`).
  - **Plan-step rendering has no owner.** S25 says "Pipeline renders broad/detail choices…" (`25-progressive-acquisition.md:43`) without an S10 dependency or UI acceptance; S26 is the same.
  - **Method display is conditional on both sides.** S22's "M1 shows provisional codes…" and its chart and alert integration are conditional (`22-semantic-shift.md:40`). S17 only says it will "register S21/S22 methods when available".
  - **S16 tests a read that does not exist yet.** S16-A01 asserts saturation on "dependent volume and chart reads" (`16-monitoring-depth-and-timing.md:53`), but the chart (S18) is not a dependency and S18's acceptance never mentions saturation.
- **Consequence if unchanged:** When a producer lands before its renderer, nobody has unconditional acceptance for the integration. The gaps first show up in human review at S30.
- **Proposed change:**
  - Adopt the rule "the spec that lands second owns the integration as an unconditional acceptance check", and write it into each affected spec.
  - Give S18 a method-series registration contract, tested with a stub method, so S21 and S22 plug in without UI work.
  - Put runtime and route health into S20b (R2-F03).
  - Give S10 an unconditional "renders plan steps" check, gated on S25's read model, and make S25 provide that read model.
- **Round-1 relation:** New. R1-F14 assigned the D1 screen, but not these surfaces.

### R2-F10 — S29 is one aggregate spec that contradicts its own per-row independence and makes release wait on the least essential route

- **Severity:** major. **Confidence:** high.
- **Affected specs:** S29, S30, S26.
- **Evidence:**
  - **The spec contradicts its own blockers.** S29 has seven direct blockers (`29-provider-readiness.md:8`), yet claims "Each row can be completed when its own capability spec is done; no row waits on unrelated build work" (`:28`).
  - **The sequence's claim rule makes that impossible.** A spec is claimable only "once its direct blockers … pass" (`implementation-sequence.md`, opening paragraph).
  - **S30 waits on all of S29,** including the supplementary detail route (S26) and the decision-blocked S21.
- **Consequence if unchanged:**
  - Readiness evidence for capabilities finished early (the model, keyword discovery, recurring runtime) is not recorded until the slowest capability lands.
  - The pilot release record waits on the deepest acquisition chain.
- **Proposed change:**
  - **Split S29 into separately claimable rows,** each size S:
    - model and keyword discovery (S04, S07),
    - recurring X (S04, S07, S16),
    - email (S27),
    - billing (S24),
    - detail route (S26),
    - methods (S21, S22).
  - **Make S30 depend on the rows its journeys use.** State that a recorded blocked row is a valid S30 input.
- **Round-1 relation:** New in this form. Validation kept S29 as one spec.

### R2-F11 — S06 leaves open the two choices that decide chat and campaign usefulness

- **Severity:** major. **Confidence:** medium.
- **Affected specs:** S06, S09, S12, S14, S31.
- **Evidence:**
  - **The index mechanism is not chosen.** S06 specifies "governed text and normalized-term index" and "CJK n-grams" (`06-pilot-scale-retrieval.md`, Scope). It does not choose among an own term table, `pg_trgm` and `tsvector`. PostgreSQL 16 (`compose.yaml`) has no Korean or Japanese text-search parser.
  - **The ranking rule among matches is not chosen.** When hundreds of publications match, the spec does not say which 20 members reach the model (`src/smi_assistant/store.py:60-61`). The installed search is newest-first containment (`queries/store.py:163-169,84-109`).
  - **Acceptance does not test relevance.** It checks recall of one old brand, scan-bound reporting and latency on fixtures (S06-A01..A05).
  - **The sequence lists only "deterministic per-turn retrieval" as the recorded engineering choice** (`implementation-sequence.md`, after the user-decision table).
- **Consequence if unchanged:** The choice that most affects whether chat feels useful is made ad hoc by the S06 implementer and checked only by humans at S13. With the current order, that check comes after S12 is built.
- **Proposed change:**
  - Require S06 to record the index and ranking choice, with a short benchmark on the 1,000-post fixture.
  - Add an acceptance item with a small real KR/JP question set drawn from S04 data (precision@k recorded, no threshold claimed).
  - Feed the result into S13a (R2-F05).
- **Round-1 relation:** Extends R1-F01; does not contradict its accepted resolution (deterministic scope, no model-proposed terms).

### R2-F12 — The email transport is undecided, and S27's no-resend rule biases a notification channel toward missed alerts

- **Severity:** minor. **Confidence:** medium.
- **Affected specs:** S04, S27.
- **Evidence:**
  - **No transport is named.** S04 probes "the email provider's semantics" (`04-live-feasibility-probes.md:28`), and S27 relies on "provider idempotency only after verified support" (`27-inbox-email.md`, Failure and recovery). Neither names SMTP or an HTTP provider API, and neither appears in the user-decision or engineering-choice lists. That choice determines whether idempotency or acceptance semantics exist at all.
  - **Ambiguous acceptance blocks resending.** S27 treats ambiguous acceptance as uncertain and allows no resend without an operator decision. For a single-recipient, source-free notification email, a duplicate is harmless and a missed alert is the real failure.
- **Consequence if unchanged:** The S04 email row cannot be executed as written. S27 may build operator-reconciliation machinery for a channel where at-least-once delivery with a stable message identifier is the better default.
- **Proposed change:**
  - Record the transport choice in S27 (or as U8); recommend SMTP through an operator-supplied account for the local pilot.
  - Default notification email to at-least-once delivery, with the logical delivery key in a stable message ID or header. Keep the delivery-identity model.
- **Round-1 relation:** New. Round 1 called the delivery-identity model sound, and I do not contest that model.

### R2-F13 — S01 is a start gate for every lane, though its rationale is a merge condition

- **Severity:** minor. **Confidence:** medium.
- **Affected specs:** S01, S02, S03, S05, S06, S22.
- **Evidence:**
  - **Every outgoing edge is justified by "suites must be green"** or "need a trustworthy full-suite result" (e.g. `02-pilot-configuration.md:8`, `05-automated-interpretation.md:8`, `22-semantic-shift.md:8`). Green suites are needed to merge, not to start.
  - **The brief asked for something narrower.** It requested a "narrow fixture-maintenance/readiness prerequisite" (`task4-brief.md`, Existing baseline). S01 is M and converts about 217 dates across 47 files.
- **Consequence if unchanged:** Five parallel M0 lanes idle for S01's duration.
- **Proposed change:** Make S01 a merge gate rather than a start gate:
  - S01a (S): inventory, shared clock helper and the failing class;
  - per-module conversions continue in parallel;
  - M0 specs may start immediately and must merge onto a green S01a baseline.
- **Round-1 relation:** New angle on R1-F09. It does not dispute the inventory scope validation accepted.

### R2-F14 — The continuous runtime omits payload-expiry maintenance

- **Severity:** minor. **Confidence:** medium.
- **Affected specs:** S07, S36.
- **Evidence:**
  - **Payload deletion is not automatic.** Read paths reconcile policy (`src/smi_ingestion/support/reader.py:76,173`), but evidence payload deletion on expiry runs only through `smi-ingest expire` (`src/smi_ingestion/evidence.py:282-291`; `cli.py:333`).
  - **The architecture says so explicitly:** "no universal background deletion guarantee" (`docs/architecture.md:151`).
  - **Live sources carry deletion obligations.** X's policy includes deletion obligations (`docs/source-integrations.md:72`).
  - **S07 composes only** schedules, polling, the worker and delivery (`07-local-runtime.md`, Owners).
- **Consequence if unchanged:** A continuously running live pilot keeps expired payload files on disk until someone runs the CLI.
- **Proposed change:** Add a bounded lifecycle-maintenance component to S07 that runs evidence expiry, orphan reconciliation and inbox reconciliation. Leave hosted-scale governance in S36.
- **Round-1 relation:** New.

I deliberately did not re-raise the items validation explicitly rejected in R1-F11: the freshness timer, cursor workspace/requester binding, and S24 command receipts. Its reasons, cheapness once centralized and correctness of stale-page rejection, hold.

## 3. Proposed revised ordering and dependency set

Only changed rows are shown. All other specs keep their current dependencies.

| ID | Change | Direct deps | Size |
| --- | --- | --- | --- |
| S01 | Becomes a merge gate (S01a scope); M0 specs may start in parallel | — | S (+ parallel conversions) |
| S02b | **New:** operator CLI for cost scope/route/ceiling with receipts; X activate/deactivate/run-due; bounded probe activation | S02 | S |
| S03 | Narrowed foundation; reducers and graph library move to S12/S15/S18 | S01 | M |
| S04 | X row is a bounded activation with recorded deactivation | S02b | M |
| W02′ | **Widened decision**, asked at plan start: receipt-time bounds for capture and metric time; completeness of an unsaturated page; saturated-window semantics | — (informs S16) | decision |
| S16 | Rewritten: project the existing `retrieved_at`/`pagination_remaining`; implement the W02′ coverage derivation; live-shaped fixture acceptance | S02; decision W02′ (live part only) | S |
| S13a | **New:** real-data output check on legacy forms/CLI, with pre-declared outcomes | S04, S05, S06 | S |
| S13 | Drop S07; consume S13a results | S13a, S09, S12 | S |
| S15 | Owns the graph library choice as an early spike, plus the branch reducer | S14, S08 | L |
| S18 | Owns the chart reducer and a method-series registration contract; live acceptance after W03 | S17 | M |
| W03 | **New decision** after the probe: monitoring depth (counts endpoint, multi-page, cadence or accepted saturation) | prerequisite: S04 X row | decision |
| S20a | Capability registry, selection policy, readiness read | S02 | M |
| S20b | D1 screen plus runtime/route health | S08, S20a, S07 | S |
| S21 | No S20 edge; no W02 build blocker; live row conditional on W03/re-measurement | S16 | M |
| S24, S27 | Re-pointed from S08 to S03 (S27 keeps S07, S02) | S03 (+ existing) | unchanged |
| S25 | Re-pointed to the backend registry | S20a | L |
| S29-x | S29 split into claimable rows: model and keyword (S04, S07); recurring X (S04, S07, S16); email (S27); billing (S24); detail route (S26); methods (S21, S22) | per row | S each |
| S30 | Depends on the rows its journeys use; blocked rows are valid inputs | S11, S13, S19, S23, S28, S29 rows | M |
| optional | X re-measurement lookup spec, only if W03 or the user chooses live engagement | S16, S07 | M |

Illustrative effect, using the size weights in the reviewer note:

- The first live evidence (S04) arrives at about 3.5 weeks instead of 3.0, because the S02b command surface is now an explicit step.
- The first real-data human check (S13a) arrives at about 4.5 weeks; today the first such check is S13 at about 8.5.
- The UI-based S13 arrives at about 7.5 weeks.
- The release record arrives at about 9.5 weeks instead of 12.
- The release critical path becomes S01→S06→S14→S15→S23→S30. It now runs through a headline deliverable (the graph) rather than the supplementary detail route.

## 4. Keep as is

Avoid churning these sound parts:

- **Architecture and boundaries:** the modular Python/PostgreSQL owner boundaries, with no graph database, broker, microservices or new agent framework; the shared command, receipt and read contract; and the authority invariants (exact human approval, save-before-discovery, publication before answer, KB-only investigation, independent spending).
- **S05's design.** Interpretation is support-based, runs before the publication commit inside the fenced worker, and members still publish on interpretation failure.
- **S06's placement and reach.** It sits in M0, covers campaign, chat and graph seeds, and excludes model-proposed retrieval terms under ADR 0017.
- **S10.** Progress is derived from `acquisition_attempts.phases` first.
- **S11's tool boundary.** Approval is human-only, and `campaign.recommend` wraps installed operations.
- **The S14/S15 split,** including generation and cursor binding, and the S17/S19 split.
- **S24's operator receipts and S27's delivery-identity model,** apart from the transport and resend default in R2-F12.
- **The human-checkpoint concept,** with S23 and S30 kept; S13a is an addition, not a replacement.
- **Spec conventions:** "parity-then-retire" for legacy forms, the shared UI obligations stated once, and per-edge rationales.
- **The later lanes S31–S40,** with their explicit prerequisites. W01 stays non-blocking for the pilot.
- **The planning verifier.** Keep it, but extend it to flag a decision issue whose "blocks only" claim is contradicted transitively (R2-F08).
