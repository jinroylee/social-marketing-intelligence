# Round-1 critical review of the Task 4 implementation-spec sequence

Reviewed package: `.scratch/product-design-2026-11/task4/`, which contains `implementation-sequence.md`, all 30 specs, `gap-analysis.md`, `architecture-target.md`, `traceability.md` headers and the `plan.json` dependency edges. I also reviewed `wayfinder/issues/000` and `001`, `task4-brief.md`, `task1-recovery/decisions.md`, `ui-review-status.md`, `task3/r2/design-spec.md`, `FR.md` and `docs/functional-requirements.md`.

Method: I checked the material claims against `src/`, `tests/`, `docs/` and git history. I ran `verify_plan.py`, which passes. That result is structural only and none of the findings below rely on it. I did not run the test suite, open a browser, call a provider or audit every traceability row. File references are repository-relative unless they start with `specs/`, which means `.scratch/product-design-2026-11/task4/specs/`.

## 1. Verdict

**Validity.** At the level of named interfaces, the package is mostly accurate. The cited methods exist with the stated names: `CampaignStore.start/revise_brief/interpret_criteria/prepare_current_comparison/recommend/recommend_ranked/save_shortlist`, `CampaignRecommendations.regenerate`, `AcquisitionTasks`, `UsageAccounting.configure_*/allowance/reconcile_usage/recover_meter`, `RecentPolling.activate/deactivate/read/run_due`, `KnowledgeGraph.search/read` and `CompletionInbox`. The authority invariants match ADRs 0002/0003/0004/0017/0018 and the code. However, the gap analysis misses three code-level facts. Each one decides whether the pilot works on real data:

1. Governed retrieval only scans the newest 100 publications and returns at most 100 members, or at most 20 for chat. Chat retrieval never uses the question text.
2. Automated task publications carry no caption interpretations. As a result, brand and product criteria are "unknown" for every automatically discovered account.
3. The installed live X route collects 10 posts per window and has no known metric-measurement time. Matched-age engagement (S13) and meaningful volume or shift detection are not achievable as specified.

There is also no operator path to configure a live model or live X today. S01 under-scopes a recurring clock-aging problem. Several specs are multi-owner bundles. The UI specs' central acceptance depends on browsers that implementing agents may not use, and no client test strategy replaces them.

**Optimality.** The ordering inverts the risk. The highest-uncertainty items are live source/model/email feasibility and real marketer use. They sit at depth 8–9 of a 9-deep chain (S19, S20), behind every build spec. The premises of S13, S16 and S17 would therefore be tested only after those specs are built, and real data would reach the product only at the end. About 15 `plan.json` edges are either presentation conveniences or point the wrong way. Removing or softening them shortens the pilot chain from 9 to about 5 and lets graph, chat and monitoring methods proceed in parallel.

The set lacks five specs: a frontend foundation and verification spec, a pilot configuration spec, an automated-interpretation spec, a pilot-scale retrieval spec, and early live probes. Meanwhile it carries hosted-grade machinery for a single loopback user. The later lanes (S21–S30) are fenced sensibly, but the S21→S20 edge pushes chat usefulness, the user's most explicit UI request, behind the whole pilot.

## 2. Findings, most severe first

### R1-F01 — Governed retrieval cannot reach a real automated KB, and chat retrieval ignores the question

- **Severity:** critical. **Confidence:** high.
- **Affected:** S03, S07, S21 (and the consumers S06, S18), plus `gap-analysis.md`.
- **Evidence:**
  - `src/smi_knowledge/queries/store.py:24-33`: `QueryScope` defaults to `text=''` and `limit=100`, with a maximum of 100. Line 25 documents this: "empty filters admit bounded published support". Line 129 sets `publication_limit = 100`, and line 163 scans newest first.
  - Chat: `src/smi_assistant/store.py:60` defaults to `QueryScope(limit=20, max_age_seconds=2592000)` and never derives anything from the question. The model then selects IDs from those ≤20 newest members (`src/smi_assistant/answers.py:43-73`). Today's form makes up for this with an "optional literal filter" field (see the knowledge-questions section of `src/smi_review/AGENTS.md`). The approved r2 composer has no such field (`task3/r2/design-spec.md:60`).
  - Campaigns: `src/smi_campaigns/store.py:362` uses `QueryScope(platforms=brief.platforms, max_age_seconds=...)`. The candidate pool is therefore the newest ≤100 permitted members drawn from the newest ≤100 publications.
  - `specs/07-conversations.md:26-30` never says how a turn's retrieval scope is derived. S03 says "Reuse campaign schemas". S21 is "later-core-depth" and depends on S20 in `plan.json`.
- **Consequence:** Scheduled discovery admits up to 50 posts per day, so the campaign candidate pool will cover roughly the last two days of posts. Older eligible creators fall out of every comparison. This is reported honestly as `result_limit_reached`, but the result is still not useful. Each chat turn answers from the newest ≤20 facts whatever was asked, so most real questions return `missing_information`. The two headline journeys, campaign-first and familiar chat, would not work on real data. The plan schedules the fix after human acceptance.
- **Proposed change:** Add a pilot spec, N3 "Question- and brief-driven governed retrieval at pilot scale", which must finish before S03 and S07 are accepted. It should cover three things:
  - Bounded selection of candidates and support beyond the newest 100 publications, for example a permitted account/support index or keyset pagination with explicit, reported scan bounds.
  - A per-turn retrieval scope derived from the question. This can be deterministic literal or trigram terms and/or model-proposed terms. The terms are validated, pinned in the turn record and never broaden authority.
  - Acceptance on a KB with at least 1,000 publications.

  Keep embeddings and semantic evaluation in S21, but drop S21's edge to S20.

### R1-F02 — Automated discovery publishes no caption interpretations

- **Severity:** critical. **Confidence:** high.
- **Affected:** S05, S16, S03, S08/S09 and `gap-analysis.md`. No spec covers this.
- **Evidence:**
  - `src/smi_tasks/worker.py:343` calls `publications.publish(support, ...)` without `interpretation_ids`. The parameter exists at `src/smi_knowledge/publications/store.py:41-42`.
  - `KnowledgeStore.prepare` runs only from the manual CLI (`prepare-knowledge` in `src/smi_ingestion/cli.py`) and from frozen-dataset comparison composition (`src/smi_review/app.py:648`, `:715`).
  - Queries flag such members as `caption_interpretations_not_published` (`src/smi_knowledge/queries/store.py:120-121`).
  - Campaign `brand_mention` and `product_mention` criteria are judged only from published interpretations (`src/smi_campaigns/comparison.py:81-88`, which sets `state = "unknown"`).
- **Consequence:** Everything that "real automated discovery" adds to the KB has unknown brand and product fit and no mention edges in the graph. Shortlists over discovered creators cannot express the brief's main criteria, and the graph shows accounts and posts with no Brand/Product relationships. No spec, gap row or acceptance check catches this, because every acceptance check uses fixtures.
- **Proposed change:** Add N2 "Automated catalog-scoped interpretation in the task pipeline". After publication, the worker or a runtime-registered step prepares interpretations against the workspace's registered catalogs and publishes them as a successor publication. That step has:
  - an idempotent identity,
  - a method/policy version,
  - a separate "interpretation pending/failed" state that never blocks member publication.

  Add an S03 acceptance check: a shortlist over task-discovered support shows real mention judgments. Put N2 in the first milestone with S05.

### R1-F03 — Live feasibility is validated last, so the risk order is inverted

- **Severity:** critical. **Confidence:** high.
- **Affected:** S19, the design premises of S12, S13, S14, S16 and S17, and the sequence milestones.
- **Evidence:**
  - In `plan.json`, S19 depends on S13, S14, S16, S17 and S18. Computed from `plan.json`, the longest chain is S01→S02→S04→S05→S10→S11→S13→S19→S20: S19 sits at depth 8 and S20 at depth 9.
  - Gated live software already exists for each capability: Bright Data keyword discovery (`src/smi_ingestion/cli.py:145-150`, `:211-214`), official recent X (`src/smi_monitoring/polling/route.py:74-92`) and metered Responses calls (`src/smi_assistant/answers.py`). Probing them needs credentials and authorization, not new code.
  - Build specs nevertheless embed premises that only live evidence can settle:
    - S13 needs metric capability tied to measurement age (`specs/13-engagement-anomalies.md:9`, `:26`).
    - S16 needs "at least one verified supplementary route" (`specs/16-progressive-acquisition.md:28`).
    - S17's retry design depends on the provider's acceptance and idempotency semantics.
- **Consequence:** Teams could build matched-age engagement, a multi-route planner and email retry handling for weeks, then learn at S19 that X metric timing, Bright Data fields or costs, or the email provider do not support the design. Every UI would also be tuned against fixtures until the end.
- **Proposed change:** Split S19 into early per-capability probes:
  - L1: model.
  - L2: Bright Data keyword discovery (fields, capture times, cost basis).
  - L3: X recent (posts per window, `next_token` frequency, metric fields and timing).
  - L4: email transport.

  Each probe depends only on N1 (see R1-F05) and on human authorization or credentials. Schedule them in the first milestone, running alongside the build. Their findings feed the scopes of S12, S13, S16 and S17. Keep a final S19 readiness record in which each capability row depends only on that capability's own build spec, not on S18. Request the bounded live authorization from the human at plan start, because it is the long-pole external dependency.

### R1-F04 — No frontend foundation or client verification strategy, and UI acceptance needs browsers agents cannot use

- **Severity:** critical. **Confidence:** high.
- **Affected:** S02, S07, S09 and S11 (and every UI-bearing spec), plus S20.
- **Evidence:**
  - The current UI is server-rendered forms with one 56-line script (`src/smi_review/static/review.js`). There is no `package.json`, and `tools/check.py` runs no JS checks.
  - Agent browser access remains declined (`task4-brief.md`, "Actual approval").
  - S09's central acceptance can only run in a browser: "In an actual browser, drag/pin, expand two overlapping branches…" (`specs/09-interactive-graph.md:53`), and "These browser checks require future permission" (S09-A04). S11 is the same (`specs/11-monitoring-history.md:66`), as are S07's IME and composer checks.
  - S02 says only "Start with bundled browser JS and CSS; no framework rewrite is required" (`specs/02-workspace-and-evidence.md:30`).
  - No spec chooses a graph-layout approach (S09 just says "deterministic relationship/compact layouts"), chart rendering, an i18n mechanism, client module structure or a client test harness.
  - Node is available, and r2 already used Node source-state checks (`task3/r2/verify-prototype.cjs:1`).
- **Consequence:** The most visible pilot deliverables are the interactive graph, the chat composer and the highlighted chart. Agents will mark them build-complete without ever running their core behavior: discarding stale pages, keeping shared members when a branch collapses, not sending during IME composition. Defects will surface only in the single S20 human session. Parallel UI workers on S03, S07, S09 and S11 will each invent their own client patterns.
- **Proposed change:** Add F0 "Frontend foundation and verification" as the first UI spec, split out of S02. It should:
  - Choose between hand-written ES modules and a vendored, pinned library for graph layout and charting, and record the trade-off. A hand-built incremental force or relationship layout with pinning is multi-week work on its own.
  - Define the API client and response envelope, the i18n catalog mechanism (catalogs grow with each spec) and the router/state conventions.
  - Put client state in Node-testable modules run by `tools/check.py` through `node --test`: the graph branch/generation reducer and stale-page discard, the chart series builder for missing/zero/latest/selected, and composer/draft/IME state.
  - Require a short human browser checklist at the completion of each UI spec, not only in S20.

  Separately, ask the user whether scoped headless-browser tests against the loopback app are acceptable. This is a genuine user decision, and it is currently declined.

### R1-F05 — No pilot composition or configuration spec, and no operator path to a live model or live X

- **Severity:** major. **Confidence:** high.
- **Affected:** S05, S12, S17 and S19. No spec covers this.
- **Evidence:**
  - `smi-review`'s `main` builds `ReviewApp` without `model_route`, `model_transport` or `model_credential` (`src/smi_review/server.py:131`; compare `src/smi_review/app.py:110-113`). The shipped server therefore cannot run answers, ranked recommendations or criteria interpretation against any model.
  - `ResponsesRoute(` and `LiveXConfig(` are constructed only in tests (`tests/test_assistant.py`, `tests/test_live_recent.py`, `tests/test_semantic_alerts.py`, `tests/test_criteria_interpretation.py`). `RecentPolling` defaults to a disabled `LiveXConfig()` (`src/smi_monitoring/polling/store.py:33`).
  - The Bright Data token environment-variable names disagree: `BRIGHT_DATA_API_TOKEN` (`src/smi_ingestion/cli.py:214`) versus `BRIGHTDATA_API_TOKEN` (`src/smi_ingestion/adapters/bright_data.py:171`).
  - S05 lists configuration only as a prerequisite (`specs/05-local-runtime.md:9`). Secrets are specified only for hosted operation (S26).
- **Consequence:** The runtime (S05) and the live probes or S19 have no supported way to receive credentials, model routes or authority opt-ins. Each worker will invent its own flags. The name mismatch will produce "credentials required" failures that look like provider problems.
- **Proposed change:** Add N1 "Pilot composition and validated configuration". It provides:
  - one versioned local configuration (a file, with secrets in environment variables only) consumed by the review server, the runtime and the CLIs,
  - explicit simulated/provider classification for the model, X, Bright Data and email routes,
  - authority opt-ins and thresholds,
  - a source-free readiness read that S12 later extends,
  - a single Bright Data token variable name.

  Place N1 right after S01, and make S05, L1–L4 and S17 depend on it.

### R1-F06 — Monitoring depth and metric timing are undecided choices hidden inside S10, S13 and S14

- **Severity:** major. **Confidence:** high on the facts, medium on the impact (it depends on topic volume).
- **Affected:** S10, S11, S13, S14 and S19.
- **Evidence:**
  - The live X route collects one page with `MAX_RECORDS = 10` (`src/smi_monitoring/polling/route.py:21`, `:87`).
  - Per `docs/monitoring.md:166-168`, `next_token` marks "additional uncollected pages, not authority to fetch them", and "original capture/metric measurement times remain unknown".
  - Incomplete collection adds `collection_incomplete` (`src/smi_monitoring/alerts/store.py:54-55`).
  - S13 needs a reference measurement age and tolerance (`specs/13-engagement-anomalies.md:28`), but only says not to assume six-hour follow-ups (`:26`).
- **Consequence:** Any topic with more than 10 posts per window produces only incomplete live windows. Volume comparison is then limited, the S11 chart plots a capped count, and S14's coded-share shift runs on ≤10 posts. With installed data, S13 has no measurement time to match ages on. The pilot's "real monitoring" goal would not be met even with every spec done.
- **Proposed change:** Add N4 "Bounded monitoring collection depth and metric timing", or make it an explicit first slice of S10. Use probe L3 to decide between three options: bounded multi-page collection with a per-window page cap, X's recent-counts endpoint for volume, or shorter cadence. Separately decide whether the local receipt time of a successful response is an acceptable metric-measurement time, or whether a bounded re-measurement lookup is required. That is an evidence-semantics decision and may need an ADR. Make S13 depend on N4 and S12, and drop its dependency on S11.

### R1-F07 — Artificial and inverted edges stretch the critical path

- **Severity:** major. **Confidence:** high overall, medium for individual judgement calls.
- **Affected:** the `plan.json` edges and `implementation-sequence.md:58`.

| Edge(s) | Why it is not a real blocker | Evidence |
| --- | --- | --- |
| S13→S11, S14→S11 | Inverted. The methods produce results and the chart consumes them. | S11 renders engagement and shift as "unavailable until S13/S14 return real method results" (`specs/11-monitoring-history.md:26`) |
| S10→S05 | M1/M2 compose installed owners. The runtime only adds the "last tick" field. | `specs/10-monitoring-workspace.md:32` |
| S18→S17, S18→S07, S18→S10 | P1 composes `CampaignPlanning` only. Packets for chat and monitoring are extra members, not blockers. | `specs/18-plans-and-quality.md:31` |
| S19→{S13, S14, S16, S17, S18} | Live validation of installed routes needs no new build. Each capability row depends only on its own spec (R1-F03). | `plan.json` |
| S20→S19 (and S20 on everything) | Browser and language review per journey can use labelled synthetic data. Only the final usefulness row needs live data. | "synthetic review remains explicitly synthetic", `specs/20-human-pilot-acceptance.md:39` |
| S06→S03 | Exists only for a `campaign.recommend` tool. It puts chat behind campaigns. | `specs/06-exact-approval-tools.md:30` |
| S07→S06 | Chat needs the A1 research-status disclosure. Thread, turn and draft persistence do not. | `specs/07-conversations.md:26-30` |
| S16→S15, S16→S05 | Cost admission is already enforced in the worker, and S15 is operator UI. `run_one` executes plans without the runtime. | `src/smi_tasks/AGENTS.md` (admission and settlement on `TaskExecution.transaction`) |
| S17→S10, S17→S15 | Alert notifications already exist in the owners and are shown in `/inbox`. Spending applies only "if chargeable". | `src/smi_review/AGENTS.md` (inbox composition); `specs/17-inbox-email.md:44` |
| S12→S04, S15→S04 | The capability registry and the cost forms do not read the task event feed. | `specs/12-source-capabilities.md:27`; `specs/15-spending-operations.md:30` |
| S21→S20, S22→S21 | Retrieval evaluation and the disabled candidate need neither pilot acceptance nor semantic retrieval. These edges push W01 evidence past the pilot. | `plan.json` |
| S08→S02 | Graph paging is backend-only. S09 needs both S08 and the UI shell. | `specs/08-graph-reads.md:29` |

The stated "main dependency chain" (`implementation-sequence.md:58`, S01→S02→S03→S06→S07→S18→S19→S20, 8 deep) is not the longest path in `plan.json`. The longest path is S01→S02→S04→S05→S10→S11→S13→S19→S20, 9 deep.

- **Consequence:** A serial chain 9 deep, with S19 and S20 waiting on everything. With these edges removed, S20's build prerequisites are about 5 deep (computed from `plan.json`), and chat, graph and monitoring methods can start in parallel from the first milestone.
- **Proposed change:** Remove or soften the edges above as shown in section 3. Where integration matters, write it as a conditional acceptance item ("when S0x exists, also verify…") rather than a blocker. Regenerate the narrative critical path from `plan.json`.

### R1-F08 — Human feedback comes all at once at the end (S20)

- **Severity:** major. **Confidence:** high.
- **Affected:** S20, S18 and the milestone structure.
- **Evidence:** S20 blocks on S09, S11, S13, S14, S18 and S19 and covers every journey (`plan.json`; `specs/20-human-pilot-acceptance.md`, scope). The only human input so far is approval of a fixture prototype. `ui-review-status.md` says it "approves the product design and planning input, not … a fabricated record of completed browser tests".
- **Consequence:** The marketer first uses working software after about 18 specs. A single session on real data would reveal usefulness defects such as R1-F01 and R1-F02, but that session comes only after they are expensive to fix. KO catalogs and KR/JP judgment review pile up into one large packet.
- **Proposed change:** Replace the single gate with milestone checkpoints:
  - H1: brief→shortlist on real discovered data, after S03, S05, N2, N3 and L2.
  - H2: chat on the real KB, after S07 and L1.
  - H3: graph interaction, after S09.
  - H4: monitoring stream and alerts, after S11, S13, S14 and L3.

  Keep S20 as the final release record that collects these checkpoints and the live journeys.

### R1-F09 — S01 treats a recurring clock problem as a single test

- **Severity:** major. **Confidence:** medium-high.
- **Affected:** S01 and every spec whose completion evidence includes the shared check.
- **Evidence:**
  - S01's scope is "Change only the fresh-evidence scenario's clock" (`specs/01-stable-verification-clock.md:25`).
  - `tests/` contains 192 hard-coded September/October 2026 timestamps across 30 files (grep for `datetime(2026, 9|10` and `2026-09|10-DD`).
  - The same class of failure has been fixed in other files before: commit `ecc011f` (`test_costs.py`, `test_cost_reconciliation.py`, "keep … fixtures current") and commit `a70341a` (`test_live_recent.py`, "within current retention").
  - The live X route rejects windows older than seven days (`src/smi_monitoring/polling/route.py:84`).
  - `docs/development.md:18-26` documents only the remaining instance.
- **Consequence:** A multi-week build will push more fixtures past 30-day freshness, retention or seven-day windows. The shared check will then fail on unchanged code, and parallel agents will fix these ad hoc or misattribute regressions, which is exactly what S01 is meant to prevent.
- **Proposed change:** Rescope S01 to audit wall-clock dependence reached by tests with fixed dates, both database `now()` and Python `datetime.now`. Introduce one controlled-clock or relative-date helper. Add the acceptance check "the suite passes with the clock shifted +90 and +365 days", or an equivalent date-shift harness. Leave the product freshness policy untouched. S01 remains small (days of work) and remains first.

### R1-F10 — Spec sizes are uneven, and S02 is an overloaded bundle that contradicts itself

- **Severity:** major. **Confidence:** medium.
- **Affected:** S01, S02, S05, S10, S14, S15, S16 and S20.
- **Evidence:**
  - S02 combines the app shell, navigation, campaign index and detail, theme, shared inspector, status controls, "complete EN/KO catalogs" (`specs/02-workspace-and-evidence.md:26`), the versioned `/api/v1` adapter framework (`:30`) and the cross-cutting `display_valid_until` revalidation contract (`:40`). Catalogs cannot be complete before the S03–S18 screens exist.
  - At the small end, S01 is hours of work, and S15 is mostly forms over existing `UsageAccounting` operations (`src/smi_costs/store.py:33-335`).
  - At the large end, S14 (a new LLM coding method, an independent validator, baselines and KR/JP evaluation preparation) and S16 (a plan/step engine, a new route, cross-route avoidance and migration of legacy plan methods) are each multi-week. S05 composes four owners plus packaging. S10 bundles all of M1 and M2.
  - Every spec uses the same roughly 70-line template with about four acceptance checks, whatever its size.
- **Consequence:** Progress tracking is misleading. S02 becomes a long pole blocking every UI spec, and the large specs will be split ad hoc mid-flight.
- **Proposed change:** Make these splits:
  - S02 into F0 (R1-F04), S02a (shell, navigation, theme, EN/KO switch with catalogs growing per spec) and S02b (shared inspector and evidence reads).
  - S16 into S16a (the plan/step model over the existing nickname route) and S16b (one named additional route; see R1-F13).
  - S14 into the method/validator and the evaluation-packet preparation.
  - S10 into M1 (topics, activation, alerts) and M2 (investigation and promotion).

  Add an S/M/L size to each spec in `plan.json`.

### R1-F11 — A single-user local pilot carries hosted-grade cross-cutting machinery

- **Severity:** major. **Confidence:** medium.
- **Affected:** S02, S04, S07, S08, S09, S11, S15 and S17.
- **Evidence:**
  - The same client freshness contract (revalidate on focus, navigation and a timer; fail closed at `display_valid_until`; never restore from a stale response) is a separate required acceptance check in S02-A05, S07-A05, S09-A05 and S11-A05. The server already rechecks current policy on every read (`src/smi_review/AGENTS.md`: "Recheck display policy through public readers when rendering").
  - S08 requires server-authenticated cursors bound to workspace and requester for one local user (`specs/08-graph-reads.md:29`).
  - S04 adds `task_progress_events` (`specs/04-task-events-lineage.md:36`), although `acquisition_attempts.phases` already records bounded phase history (`src/smi_tasks/schema.sql:59`) and tasks expose status and coverage.
  - S17 builds recipient preferences, multi-channel logical keys and attributable reissue for what is, in the pilot, a single recipient (`specs/17-inbox-email.md:30`).
  - S15 adds operator command-receipt and configuration-revision metadata.
- **Consequence:** Every UI spec carries a timer-driven revalidation framework, and backend specs carry tenancy-grade binding. That is weeks of work that a loopback, single-user pilot never exercises, and it delays the features the user asked for.
- **Proposed change:**
  - Implement the freshness behavior once in F0 as a shared client utility with one acceptance test, and have UI specs reference it instead of accepting it again. For the pilot, the server-side recheck plus revalidation on focus and navigation is enough. Move the timer deadline to S25 (hosted).
  - Use signed cursors only where cursor reuse is a real risk.
  - Derive S04's progress view from existing attempt phases first, and add an events table only if per-phase timestamps are actually missing.
  - Scope S17 to one configured recipient and channel, keeping its delivery-identity model, which is sound. Defer multi-recipient preferences to S25.

### R1-F12 — Chat usefulness and the richer-agent path come last, and W01 direction is not sought early

- **Severity:** major. **Confidence:** medium.
- **Affected:** S07, S21, S22, S23, S24 and W01.
- **Evidence:**
  - The user's r1 feedback asked for a "typical, regular chatbot ui" (`ui-review-status.md`, "Actual r1 review feedback").
  - S07 keeps "labelled extractive selections" (`specs/07-conversations.md:26`).
  - The richer chain is S21(→S18, S20)→S22(→S06, S07, S16, S21)→S23→S24 (`plan.json`).
  - W01 notes that "Actual direction can constrain candidate work" (`wayfinder/issues/001-richer-agent-boundary.md`), yet S22 has no W01 edge. The question was asked once and deferred (`msg_dc61fda11b05`).
- **Consequence:** The pilot chat looks conversational but answers with extractive selections over unscoped retrieval (R1-F01). The first richer-agent evidence arrives after pilot acceptance, and S22 may be built in a shape that W01 later rejects.
- **Proposed change:**
  - Fix retrieval inside the pilot (R1-F01).
  - Ask both W01 branches again at plan start. This needs no build.
  - Give S22 a soft prerequisite of "W01 initial direction", not final acceptance.
  - Drop S22→S21, S22→S16 and S21→S20, so the disabled candidate can start after S07, S06b and S12.
  - Keep S24 decision-blocked.

### R1-F13 — S16's supplementary route is undecided, and the gap claim about oEmbed/web routes is inaccurate

- **Severity:** major. **Confidence:** high on the facts, medium on the impact.
- **Affected:** S12, S16 and `gap-analysis.md:36`.
- **Evidence:**
  - `default_registry()` registers `tiktok-oembed`, `brightdata-tiktok` and `tiktok-web` (`src/smi_ingestion/adapters/registry.py:29-37`).
  - The oEmbed adapter declares post history, follower, view and engagement counts unavailable (`src/smi_ingestion/adapters/tiktok_oembed.py:26-29`).
  - `tiktok-web` is a "direct public-page experiment" with WAF-challenge detection and post metrics (`src/smi_ingestion/adapters/tiktok_web.py:1-5`, `:31-34`).
  - `gap-analysis.md:36` and S16 (`specs/16-progressive-acquisition.md:28`) describe "unsupported API/oEmbed/web choices" and require "at least one verified supplementary route" without naming it.
- **Consequence:** The plan leaves the S16 owner to make a route, source-use and cost choice on their own. The obvious candidates already exist as supplied-reference adapters. The real work is task integration and source-use review, not a generic planner. There is a risk of building a multi-route planner with only the nickname route behind it.
- **Proposed change:** Name the S16b route and its exact fields. Candidates are Bright Data profile/post fields beyond nickname, or `tiktok-web` post metrics subject to source-use authorization, with oEmbed limited to identity and title. Make the choice an output of probe L2. Correct the gap analysis to say that oEmbed and web adapters exist for supplied references but are not task-integrated.

### R1-F14 — No spec owns retiring the legacy form UI or the D1 schedule configuration UI

- **Severity:** minor. **Confidence:** high.
- **Affected:** S02, S05, S12 and `architecture-target.md`.
- **Evidence:**
  - `architecture-target.md:56` says "Keep existing form routes working while moving their presentation callers". No spec retires the roughly 20 server-rendered view modules (`src/smi_review/*_views.py`, `views.py`), which are English-only.
  - The D1 keyword-schedule configuration screen (ten-keyword limit, activation, day allowance; D1 row of `task3/r2/design-spec.md:214`) is split across S05 ("operations screens"), S12 ("exposes D1") and S16, with no single owner.
- **Consequence:** The pilot will have two UIs to maintain, translate and secure. The schedule configuration may end up with no home in the new UI.
- **Proposed change:** Add a parity-then-remove step to each UI spec, or one cleanup spec after S18. Assign the D1 schedule configuration UI and its acceptance explicitly to S12.

## 3. Proposed revised ordering and dependency set

New and changed items are N1–N4 (new pilot specs), F0 (split from S02), L1–L4 (split from S19) and H1–H4 (split from S20). "Ext" means a human or external prerequisite, not a build dependency.

| Milestone | Spec | Direct build blockers | Ext prerequisite / note |
| --- | --- | --- | --- |
| M0 baseline and de-risk | S01′ suite-wide controlled clock | — | — |
| | N1 pilot composition and configuration | S01′ | — |
| | L1–L4 live probes (model, Bright Data keyword, X recent, email) | N1 | Ext: bounded live authorization and credentials, requested at plan start |
| | W01 initial direction (ask again) | — | Ext: domain owner; no build |
| | F0 frontend foundation and client verification | S01′ | Ext: optional user decision on scoped headless browser tests |
| M1 real-data campaign slice | N2 automated interpretation | S01′ | — |
| | N3 pilot-scale governed retrieval | S01′ | — |
| | S05 runtime (drop S04) | N1 | Registers N2 and delivery when present |
| | S02a shell, navigation, theme, EN/KO | F0 | Catalogs grow per spec |
| | S02b inspector and evidence reads | S02a | Freshness utility from F0 |
| | S03 C1 | S02b, N3 | Acceptance includes N2 mention judgments |
| | H1 checkpoint: brief→shortlist on real data | S03, S05, N2 | Ext: L2 passed, marketer |
| M2 tasks, approval, chat | S04 (slim; existing attempt phases first) | S02a | — |
| | S06a A1 review/approve/submit UI | S02b, S04 | — |
| | S06b agent tool surface (FR-P08) | S04 | Drop S03 |
| | S07 conversations | S02b, N3 | A1 disclosure verified when S06a exists |
| | H2 checkpoint: chat on real KB | S07 | Ext: L1 passed, KR/JP reviewer |
| M3 graph (parallel from M0) | S08 graph pages | S01′ | Drop S02 |
| | S09 graph client | F0, S02b, S08 | — |
| | H3 checkpoint: graph interaction | S09 | Ext: human browser session |
| M4 monitoring | N4 collection depth and metric timing | N1 | Ext: L3 findings |
| | S10a M1 topics/activation/alerts; S10b M2 investigation/promotion | S02b; S10a | Drop S05 |
| | S11 history chart | S10a | Shows engagement/shift when present |
| | S13 engagement | S12, N4 | Drop S10/S11 as blockers |
| | S14a semantic shift method; S14b evaluation packets | N4; S14a | Drop S11 |
| | H4 checkpoint: monitoring | S11, S13, S14a | Ext: L3 passed |
| M5 acquisition, spend, notifications, planning | S12 capabilities and D1 UI | N1, S02b | Drop S04; informed by L2 |
| | S15 spending UI | S02b | Drop S04 |
| | S16a plan/step model; S16b named route | S06a, S12; S16a | Drop S05/S15; S16b informed by L2 |
| | S17 inbox and email (one recipient) | S05, N1 | Drop S10/S15; Ext: L4 |
| | S18 plans and quality packets | S03 | Drop S07/S10/S17 |
| M6 release record | S19′ readiness record | Each row: its own spec plus probe | Not a gate on S18 |
| | S20′ release acceptance | H1–H4, S19′ | Final usefulness on live data |
| Later | S21 semantic retrieval depth | N3, S18 | Drop S20 |
| | S22 disabled candidate | S06b, S07, S12 | Ext: W01 initial direction; drop S16/S21 |
| | S23, S24, S25–S30 | Unchanged | S24 stays decision-blocked |

The longest build chain becomes S01′→F0→S02a→S02b→S03/S07/S09, five build specs deep. Live probes and human checkpoints run alongside it rather than after it.

## 4. Keep as is

- **Authority and evidence invariants, and their acceptance cases.** These are exact human approval per assistant-origin task, no conversational approval, publication before answers, save-first automatic shortlists with separate human curation, explicit successor regeneration, KB-only alert investigation, independent spending admission and no blind paid retry after an unknown response. They are correct against the ADRs and the code, and they are the strongest part of S03, S06, S07, S10, S15 and S16.
- **The lane separation.** Build completion, live readiness and human acceptance stay separate, and fixtures can never complete a validation row. Keep this when S19 and S20 are split.
- **The owner placement.** The plan extends the existing Python/PostgreSQL owners and introduces the proposed `smi_runtime` and `smi_notifications`. It rejects a graph database, a queue vendor, microservices and a new agent framework.
- **The S08/S09 backend/client split and S09's interaction scope.** Pan, zoom, fit, drag, pin, branch membership, generation-based stale-response rejection and keyboard/list equivalence match r2 and the user's "more interactive" request.
- **S11's history semantics.** Missing is distinct from zero, latest from selected, there is no interpolation, and the chart and table come from one object.
- **S17's delivery model.** Email stays source-free, each logical delivery has one identity, and an ambiguous acceptance never triggers a resend.
- **Engagement and semantic shift (FR-C02/C03) as pilot build work** with honest "unavailable" states, not demoted to proposals.
- **The later lanes S21–S30 and their prerequisites.** S24 remains the only decision-blocked spec, and W01 does not block the pilot build.
- **S01 stays first**, with the broader scope from R1-F09.
