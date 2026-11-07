VERDICT: YES — the review is worth accepting (fully or with modifications)

# Round-2 validation of the Task 4 spec review

Validated: `spec-review/round-2/review.md`, findings R2-F01 to R2-F14 and the reordering table in its section 3. Package under review: `task4/` (sequence, specs, `plan_source.json`), the wayfinder issues and the round-1 records. Paths are repository-relative. `specs/` means `.scratch/product-design-2026-11/task4/specs/`.

Method:

- I re-read every cited `file:line` myself in `src/`, `tests/`, `docs/`, `docs/adr/`, the specs and `plan_source.json`.
- I recomputed dependency depths and the reviewer's size-weighted paths (S = 0.5, M = 1, L = 3 illustrative weeks) with a throwaway script. I did this for the current plan, for the review's proposal and for the revision in section 4.
- I did not run the test suite, open a browser, use the network or call a provider.

Numbering: sections 1–3 use the current package numbering (S01–S40), as the review does. Section 4 uses the revised numbering (S01–S45) and always names the stable slug. Old numbers there are written `old-Sxx`.

## 1. Verdict

VERDICT: YES — the review is worth accepting (fully or with modifications).

The two critical findings are real and decisive:

- **No live alert can ever fire** (R2-F01). Every live X window is stored `partial` with unknown capture times, and both installed alert methods refuse anything but `complete`. With every spec done, the pilot would still have no live alerts.
- **The early probes have no executable operator path** (R2-F02). No shipped path configures a cost scope or activates X polling, so S04 cannot produce a live row.

The review understates one point. R2-F01 contradicts an accepted ADR, not only a documentation line: ADR 0019 says the volume method "compares only complete … samples". The fix is therefore an ADR amendment the user must accept (a widened W02) plus real build work in S16. It is not "a cheap answer with no build cost".

The ordering findings mostly hold, and I confirmed the numbers:

- Splitting S20 alone moves the illustrative release record from 12 to 10 weeks. With the other accepted changes it lands at 9.5.
- The first real-data human check moves from 8.5 to 4.5 weeks.

I take fewer structural changes than the review proposes:

| Review proposes | I recommend instead |
| --- | --- |
| New S13a | Move the existing S13 early |
| New decision W03 | Widen U3 and give its revisit an owner |
| Optional re-measurement spec | Recorded as a later path only |
| S01 split into a merge gate | S01 unchanged |
| Six readiness rows | Four |
| At-least-once email default | Keep "uncertain plus attributable reissue" |

Net effect: 40 → 45 specs.

| Change | Specs |
| --- | --- |
| New | `operator-commands`; `discovery-operations-screen` (split from S20); `monitoring-readiness`, `detail-route-readiness` and `email-readiness` (split from S29) |
| Rewritten | S16 |
| Rescoped | S03, S04, S06, S07, S13, S15, S18, S20, S21, S23, S27, S29 |
| Re-pointed edges | S04, S16, S17, S18, S22, S24, S30 |

## 2. Per-finding decisions

| Finding | Evidence re-verified | Decision | Change in one line |
| --- | --- | --- | --- |
| R2-F01 live windows never assessable | Yes, every line. Missed ADR 0019 | ACCEPT-MODIFIED | Widen W02 (asked at plan start, blocks no build spec). S16 adds a separately versioned live-page eligibility rule with lower-bound saturation. Live-shaped fixture checks in S16/S17/S18/S21/S22 |
| R2-F02 no operator path for probes | Yes | ACCEPT-MODIFIED | New S-size `operator-commands`: cost scope, route and ceiling plus X activate, deactivate and run-once, with no new receipt model. S04 runs a bounded X activation. S24 reuses the command layer |
| R2-F03 UI edge on the acquisition chain | Yes; 12 → 10 weeks confirmed | ACCEPT-MODIFIED | Split S20 into backend `source-capabilities` (depends on S02) and `discovery-operations-screen` (D1 plus runtime and route health). Keep the S21→registry edge |
| R2-F04 S03 bundle | Yes | ACCEPT-MODIFIED | S03 becomes M. Graph library and branch reducer go to S15, chart reducer to S18, composer reducer to S12. S24 re-pointed to S03. S27 keeps S08 with a corrected rationale |
| R2-F05 real-data usefulness checked late | Yes | ACCEPT-MODIFIED | Move S13 itself early (S04, S05, S06; legacy forms or CLI) instead of adding S13a. S23 absorbs the C1 and chat browser checklists. S15 spike with a non-gating look. U5 re-asked narrowly |
| R2-F06 monitoring depth and engagement | Partly; "not useful" overstated | ACCEPT-MODIFIED | No W03 issue: widen U3 and make S04's X row own the post-probe recommendation. S18 renders saturation as a lower bound. No re-measurement spec. S21 states young-age semantics |
| R2-F07 S16 duplicates installed fields | Yes | ACCEPT-MODIFIED | Rewrite S16 as read projections of the stored receipt: no columns, no backfill, cadence stays per topic revision. Size stays M because S16 absorbs R2-F01 |
| R2-F08 W02 both default and blocker | Yes | ACCEPT | W02 blocks no spec. S21 builds both branches. The monitoring readiness row records the decision state |
| R2-F09 orphaned UI integration | Yes | ACCEPT-MODIFIED | One "second to land owns it" rule, stated once. Health screen moves to the new D1 screen. S18 gets a method-series contract. S17/S18→S16 edges make the saturation display unconditional |
| R2-F10 S29 aggregate | Yes | ACCEPT-MODIFIED | Split S29 into four capability rows, not six. S30 depends on all four, and a recorded blocked row is a valid input |
| R2-F11 S06 index and ranking undecided | Yes | ACCEPT-MODIFIED | S06 records its index and ranking rule with a fixture benchmark and wires the derived scope into the installed paths. Real-data precision goes to S13, not S06 |
| R2-F12 email transport and resend | Transport yes; resend default contradicts round 1 | ACCEPT-MODIFIED (partial) | Default SMTP submission through an operator mailbox (U7). Stable Message-ID from the logical delivery key. Keep "ambiguous = uncertain + attributable reissue" |
| R2-F13 S01 as a start gate | Structure yes; date count overstated | REJECT | Keep S01 as the start gate |
| R2-F14 no payload-expiry maintenance | Yes | ACCEPT-MODIFIED | S07 registers a bounded maintenance component over the existing expire and reconcile operations |
| Section 3 table | Recomputed | ACCEPT-MODIFIED | Use section 4a: 45 specs, release about 9.5 illustrative weeks, first real-data human check about 4.5 |

### R2-F01 — ACCEPT-MODIFIED

Verified:

- `src/smi_monitoring/polling/route.py:150` maps every live record with `captured_at` and `metric_measured_at` set to None, and `:156` hard-codes `declared_coverage: 'partial'`.
- `src/smi_monitoring/recent/store.py:261-264` keeps the declared status and downgrades a complete one whenever a capture time is missing.
- `src/smi_monitoring/alerts/store.py:54-55` and `src/smi_monitoring/semantic/method.py:58-59` refuse any window that is not complete.
- `tests/test_live_recent.py:162` pins `partial`, and `docs/monitoring.md:86,168` documents the behavior.

Fixtures declare `complete`, so every S17 and S18 check passes while live alerts can never fire. The user's "real automated monitoring" goal fails silently until S29 or S30.

The review understates the fix. ADR 0019 (`docs/adr/0019-source-free-quantitative-alert-history.md:7`) says the volume method "compares only complete … samples". `docs/monitoring.md:168` says the live route adds "no new anomaly method or baseline claim". Making live windows assessable is therefore an amendment to an accepted ADR. Under the goal's rule that ADRs stay in force, that is a user decision, and it needs M-sized build work.

Modifications:

1. Widen W02 to "live X window comparability and receipt-time semantics". Ask it at plan start with a recommended default. It blocks no build spec.
2. S16 implements the rule as a separately versioned eligibility rule in the volume and controversy owners. Stored coverage stays as originally recorded, and the installed v1 methods keep refusing partial windows, so no history is rewritten.
3. The rule:
   - An unsaturated page is a complete sample of the provider's recent-search results for the literal query. Market coverage stays unknown.
   - The recorded receipt time is an upper bound for capture time and metric measurement time.
   - A saturated window supports only a lower-bound crossing claim. A non-crossing result on a saturated window, and any saturated baseline, stays `not_assessable` with `collection_saturated`.
4. S16 owns a live-shaped fixture builder. S17, S18, S21 and S22 each add one check that uses it.

### R2-F02 — ACCEPT-MODIFIED

Verified, every live route refuses without operator cost configuration:

- `polling/store.py:150-152` waits with `live_x_cost_configuration_required`.
- `src/smi_ingestion/adapters/tiktok_keyword/__init__.py:80-81` raises `live_discovery_cost_configuration_required`. The worker sets `cost_configured=control is not None` (`src/smi_tasks/worker.py:257`).
- Profile supplementation stops at `src/smi_tasks/supplementation/__init__.py:126-129`.
- `src/smi_campaigns/responses/__init__.py:140-146` requires a metered weighted-token scope with a matching rate version, even for a simulated model.

Verified, nothing ships that configures or activates:

- No `src/` caller of `configure_scope`, `configure_route` or `configure_ceiling` exists.
- No CLI or HTTP route calls `RecentPolling.activate`, `deactivate` or `run_due`. `app.py:126,220` only reads, and `src/smi_review/AGENTS.md:66` confirms "only trusted Python activation".
- Topic configuration and keyword-schedule activation do ship as legacy paths (`--monitoring-operator` with `/monitoring/topics`; `--schedule-operator` with `/schedules`). The gap is exactly cost controls and X polling.

Two further problems:

- S04 says "Probes activate no recurring topic or schedule" (`specs/04-live-feasibility-probes.md:46`), which conflicts with S04-A02 measuring `next_token` frequency across windows.
- S02-A02 cannot pass from the shipped server on a fresh database either. The review mentions this only in passing.

Modifications:

- Add `operator-commands` (size S, depends on S02): thin operator subcommands over the existing owner operations.
- Add no new receipt model. The owner already makes cost scopes and route bindings immutable and conflict-checked (`src/smi_costs/store.py:33-80`). Adapter-safe receipts remain S24's job (its interface: "Add public revision guards/receipts …").
- A command may read scope definitions from a file named on its command line. They are applied only by that explicit, operator-attributed command, never at start-up, so the ledger stays the single source of truth.
- S04 depends on `operator-commands`. Its X row becomes one bounded activation for a configured number of windows, with a recorded deactivation.
- S24 also depends on `operator-commands`, so the browser forms and the CLI share one command layer.

### R2-F03 — ACCEPT-MODIFIED

Verified:

- S20 depends on S08 only for the D1 screen (`specs/20-source-capabilities.md:8`).
- S25's only edge is to the registry and selection policy (`specs/25-progressive-acquisition.md:8`).
- `implementation-sequence.md:72,77` route the deepest build chain and the release chain through S03→S08→S20.

My recomputation puts S30 at 12 illustrative weeks via S20→S25→S26→S29. Splitting S20 alone gives 10.

Accept the split:

- `source-capabilities` keeps its slug and becomes backend only: registry, selection policy and readiness read. It depends on S02.
- The D1 screen becomes `discovery-operations-screen` (size S; depends on S08, the backend and S07). It also hosts runtime and route health (R2-F09).

Modification: keep S21→`source-capabilities`. The registry is the contract that declares each route's metric capability. Once the registry is backend-only, the edge costs nothing (S21 lands at week 4 either way). Hard-coding the X fields in S21 would bypass that contract.

### R2-F04 — ACCEPT-MODIFIED

Verified:

- S03's scope (`specs/03-client-foundation.md:28`) contains the graph library decision and reducers for graph branches, chart series and the composer.
- S03's checks 2 and 3 duplicate S15-A01/A02 and S12's IME, Shift+Enter and empty-input check (`specs/12-conversations.md:41,67`).
- S24 and S27 justify their S08 edge with "renders in the shell", but the shell is S03.

Accept narrowing S03 to M and moving each reducer to its only consumer:

- graph library decision and branch/generation reducer to S15,
- chart-series reducer to S18,
- composer/IME reducer to S12.

This reverses round 1's placement of the library decision in S03. That placement was an engineering choice, not a user decision, and the decision has a single consumer. Re-point S24 to S03 (and to `operator-commands`, see R2-F02).

Modification: keep S27→S08. Inbox items open governed evidence in the shared inspector, and S27 is bounded by S07 (L) anyway, so the edge costs nothing. Only its rationale text is wrong.

Effect: S09 and S12 finish at 7 instead of 8 illustrative weeks. The release path is unchanged.

### R2-F05 — ACCEPT-MODIFIED

Verified:

- S13's direct blockers are S04, S07, S09 and S12 (`specs/13-early-marketer-checkpoint.md:8`). I compute that it lands at 8.5 weeks, the same time as S23.
- The legacy forms already run brief → interpretation → (ranked) recommendation → shortlist and question → answer (`src/smi_review/app.py:612-619,670-720`), and `smi-ingest run-live-discovery-task` exists.

Accept the structure and the intent; the intent is round 1's own goal of an early H1.

Modification: do not add S13a. Move S13 itself early:

- S13 keeps its slug and becomes the real-data output check on whatever UI exists, with legacy forms and CLI expected.
- It depends on S04, S05 and S06, which puts it at about 4.5 weeks.
- The UI-level campaign and chat checks move to S23, which now also depends on S09 and S12. That costs no time, because S15 still determines S23's start at 8 weeks. They also stay in S30.

This keeps two pre-release checkpoints, which round 1 chose deliberately to limit one marketer's load, while delivering the review's early signal. S13 carries pre-declared outcomes:

- retrieval fails → revise S06 ranking, or pull a subset of S31 forward;
- mention judgments fail → revise S05 catalog rules.

Other parts:

- **S15 library spike:** accepted as S15's first deliverable, with an optional, non-gating 30-minute human look. Round 1 rejected per-spec human gates, so it must not gate.
- **U5:** re-asked with a CI-only headless option and its stated cost.

A gap the review missed: the legacy question form passes an explicit `QueryScope(text=…, limit=20)` (`app.py:617`). S06 must wire its derived scope into the installed answer and comparison paths, or the early check would test the old retrieval.

### R2-F06 — ACCEPT-MODIFIED

Verified:

- `MAX_RECORDS = 10` with one recency-sorted page (`route.py:21,87`).
- A window is collected 30 seconds after it ends (`route.py:85`) and the next is due one cadence later (`polling/store.py:233`), so live metrics are minutes old.
- S21 refers to a separately activated measurement route that no spec builds (`specs/21-engagement-anomalies.md`, interface).
- U3's post-probe revisit has no owner, and S04's counts-endpoint result has no consumer.

Accept that the depth question needs an owner and that the chart must be honest about saturation. Reject the new W03 issue and the re-measurement spec: both add process and scope without a demonstrated need.

U3 already is the depth decision:

- Widen it to four options: (a) counts endpoint, (b) bounded multi-page, (c) shorter cadence, (d) accept saturation. Default (c)+(d).
- S04's X row owns the revisit. It records the observed saturation rate across its bounded windows and ends with a depth recommendation, which the coordinator puts to the user.
- If the user chooses (a) or (b), the coordinator adds one M spec, "Extend live X monitoring depth". It depends on S16 and `operator-commands` and blocks `monitoring-readiness`. This is a contingency, not a spec to add now.
- Under any default, S18 renders saturated windows as lower bounds (≥N).

On engagement, the review's "not useful" is overstated:

- `FR.md:30` gives engagement spikes only as an example ("e.g., volume or engagement spikes").
- Matched young-age engagement (receipt time minus publication time, within a cadence-bounded tolerance) is a legitimate early-traction signal if it is labelled as such.
- S21 states that semantics. Six-hour re-measurement stays a later path and is never implied.

### R2-F07 — ACCEPT-MODIFIED

Verified, the fields S16 asks for already exist:

- `polling/store.py:212` sets `retrieved_at` after the response, and `:230` enforces the 20-second save deadline against it.
- The receipt carries `pagination_remaining`, `retrieved_at` and `elapsed_seconds` (`route.py:128,155-156`).
- Windows and observations persist the acquisition JSON (`recent/store.py:271-272,287-288`).

Verified, cadence is already per topic and revision-pinned:

- Cadence, window, record and retention settings are validated per topic revision (`recent/store.py:101-104`).
- Window ends align to cadence (`:194`).
- A revision change forces reactivation (`polling/store.py:145,157`).

S16 as written would do harm:

- "Add … fields with explicit legacy-unrecorded values" duplicates stored fields.
- S16-A04 would label real receipt times "unrecorded".
- "Cadence is read from S02" moves a revision-pinned setting into global configuration, against ADR 0023's activation model.

Accept the rewrite, with two modifications:

- Expose the stored fields as read projections: no column and no backfill write. The review's backfill is unnecessary, because the JSON is already on every live window and observation.
- Keep S16 at M. It also carries the R2-F01 eligibility rule across the recent, alerts and semantic owners, plus the amendment text.

S16 no longer needs S02, because cadence stays a topic setting. It depends on S01 only.

### R2-F08 — ACCEPT

Verified:

- `implementation-sequence.md:99` says no decision blocks the build, and W02 is in that table (`:104`).
- Yet S21 lists W02 as a decision blocker, and `verify_plan.py --frontier` reports it.
- S29→S21 and S30→S29 make the W02 issue's claim "No other pilot build spec is blocked" false transitively.

Accept:

- W02 becomes a decision blocker of no spec.
- S21 builds both branches, selected by the registered method version: `metrics_retrieved_at` as an upper bound if W02 is accepted, `measurement_time_unknown` otherwise.
- `monitoring-readiness` records the decision state. It cannot claim live alert or engagement readiness under an unaccepted amendment, but a recorded `blocked_by_decision` row is a valid S30 input.
- Correct the W02 issue text.

Drop the review's suggestion to make W02′ a decision blocker of only S16's live part. The plan model cannot express it, because decision blockers apply to whole specs, and it would recreate the same contradiction. `verify_plan.py` must accept a decision issue whose `Blocks:` line names no spec.

### R2-F09 — ACCEPT-MODIFIED

Verified:

- S07 promises operations screens (`specs/07-local-runtime.md:42`) with no UI dependency or acceptance.
- S25 promises pipeline rendering (`specs/25-progressive-acquisition.md:43`) with no relation to S10.
- The method display between S22 and S17 is conditional on both sides.
- S16-A01 asserts saturation on chart reads that S18 owns, and S18 is not a dependency.

Accept the rule: when a conditional integration check's partner spec has already landed, the spec that lands second makes the check pass unconditionally.

- State the rule once, in the renderer and the sequence, rather than rewriting it into every spec.
- Mirror each conditional check in its partner spec.
- Runtime and route health go to `discovery-operations-screen`.
- S18 gets a method-series registration contract, tested with a stub method.

Modifications:

- **Saturation display:** add S17→S16 and S18→S16 edges instead of a conditional check. S16 lands at week 2 and S17/S18 at weeks 4–5, so the edges cost nothing and remove the conditionality. Limit S16's own check to window, volume and semantic reads.
- **Plan steps in T1:** use the rule rather than an S25→S10 edge. S25 will almost certainly land after S10.

### R2-F10 — ACCEPT-MODIFIED

Verified: S29 has seven direct blockers (`specs/29-provider-readiness.md:8`) yet says "Each row can be completed when its own capability spec is done" (`:28`). The claim rule requires all direct blockers to pass first.

Accept a split into four capability rows, not six:

| Row | Covers | Depends on |
| --- | --- | --- |
| `provider-readiness` (slug kept) | Keyword discovery, model, recurring work | S04, S07, S24 |
| `monitoring-readiness` | Recurring X plus the volume, controversy, engagement and semantic-shift methods | S04, S07, S16, S21, S22, S24 |
| `detail-route-readiness` | The supplementary detail route | S04, S26, S24 |
| `email-readiness` | Email send | S04, S27 |

Why not the review's six rows:

- Separate "recurring X" and "methods" rows would split one journey (live windows feeding live alerts) across two records.
- A separate "billing" row cannot finish before the charges it reconciles exist. Each row reconciles its own charges through S24 instead.

S30 depends on all four rows. The review's "rows its journeys use" is ambiguous to apply. A recorded blocked row is a valid S30 input.

Gain: discovery, model and runtime readiness lands at about 5.5 weeks instead of about 11; release at 9.5.

### R2-F11 — ACCEPT-MODIFIED

Verified:

- S06's scope names a "governed text and normalized-term index" and CJK n-grams but chooses neither the mechanism nor a ranking rule.
- Chat passes at most 20 members to the model (`src/smi_assistant/store.py:60-61`).
- The installed search is newest-first literal containment (`src/smi_knowledge/queries/store.py:84-109,163-169`).
- `compose.yaml` pins `postgres:16`.

Accept that S06 must record:

- its index mechanism (own term table, `pg_trgm` or `tsvector`), with a small benchmark on the 1,000-post fixture;
- a deterministic, versioned ranking rule among matches. Recommended: exact subject-ID matches first, then derived-term match count, then recency.

Add both to the engineering-choice list.

Modification: measure real KR/JP precision@k in the rescoped S13, which already depends on S04 and S06. A build spec should not need live data for its acceptance. Also add an S06 check that the installed answer and comparison paths use the derived scope (missed issue M3).

### R2-F12 — ACCEPT-MODIFIED (partial)

Verified: neither S04 nor S27 names a transport. S27-A02 keeps an ambiguous accepted response uncertain and allows no duplicate send.

Accepted:

- **Name the transport.** Default: SMTP submission through an operator-supplied mailbox account. Fold it into U7, because it depends on an account the user provides. S04's email row probes exactly that transport.
- **Stable `Message-ID`** derived from the logical delivery key. It is cheap and lets receiving systems collapse an accidental duplicate.

Rejected: the at-least-once default.

- Round 1 explicitly kept "uncertain plus attributable reissue" as the only safe recovery.
- The in-product inbox is the durable channel, so a missed email does not lose the alert.
- SMTP ambiguity (connection lost after DATA, before the 250 reply) is rare.

S27 should instead surface uncertain deliveries prominently in the channel status, with a one-action attributable reissue.

### R2-F13 — REJECT

The structural observation is accurate: every outgoing S01 edge is justified by "suites must be green". The change would still not move the goal:

- S01's first deliverable is the full-suite inventory, which round 1 added because `--maxfail=1` hides the state of about 600 tests. Until it exists, M0 workers cannot tell their regressions from aging failures.
- Converting dates "per module, in parallel" puts several workers into the same test files at once, the conflict pattern the sequence warns against.
- The saving is at most 0.5 illustrative weeks on a 9.5-week path.

The date count is also overstated. I find 173 ISO `2026-09/10-dd` literals in 30 files; round 1 found 207 in 33 with a broader pattern. 47 is the total number of test files, not the number of files with dates.

Keep S01 (M) as the start gate.

### R2-F14 — ACCEPT-MODIFIED

Verified:

- `src/smi_ingestion/evidence.py:282-291` deletes expired payloads only when `expire()` runs, which is reached only through `smi-ingest expire` (`src/smi_ingestion/cli.py:55`).
- `docs/architecture.md:151` disclaims any background deletion guarantee.
- X imposes deletion obligations (`docs/source-integrations.md:72`).
- S07 composes only schedules, polling, the worker and delivery.

Accept with a narrower scope:

- S07 registers one bounded maintenance component that calls the existing public operations (`expire`, `reconcile`, `reconcile-knowledge`) on a configured cadence, with a per-tick bound, and reports it in health.
- No new lifecycle logic. S27 registers inbox reconciliation itself, and hosted-scale governance stays in S36.
- Add PROP-27 to S07.

### Section 3 reordering table — ACCEPT-MODIFIED

Recomputed with the review's weights: the current S30 lands at 12.0 weeks, the review's own table at 9.0 (it states 9.5 because it also shrinks S01 and S16), and section 4a at 9.5.

Differences from the review's table:

- no S13a; S13 moves instead;
- no W03; U3 is widened;
- S01 unchanged;
- S16 stays M and depends on S01, not S02;
- S21 keeps its registry edge;
- S27 keeps S08;
- four readiness rows, not six;
- new edges S17/S18/S22→S16;
- S23 also covers the campaign and chat UI;
- S24 also depends on `operator-commands`.

The release record then has two co-critical chains, both at about 9.5 weeks:

- graph: S01→S06→S14→S15→S23→S30 (old numbering);
- email: S01→S02→S07→S27→email row→S30.

## 3. Material issues the review missed

- **M1. R2-F01 needs an ADR amendment and build work.** ADR 0019 restricts the volume method to complete samples, and `docs/monitoring.md:168` excludes live anomaly claims. The fix is a user-accepted amendment (W02) plus the M-sized S16 change, not a cheap answer. The amendment must be versioned so installed v1 history is unchanged.
- **M2. S02-A02 cannot pass on a fresh database.** The model route requires a metered scope with a matching rate version. Keep S02-A02 with public-operation setup in its test, have `readiness()` name the missing cost scope, and accept the shipped operator sequence in `operator-commands`.
- **M3. The installed question path bypasses the derived scope.** It passes an explicit `QueryScope(text=…, limit=20)` (`app.py:617`). S06 must wire its derived scope into the installed answer and comparison paths, or an early real-data check would exercise the old retrieval.
- **M4. The early check needs a real corpus, not just a probe.** U1 must explicitly cover a bounded keyword-discovery corpus for the early check (up to 10 keywords, a few hundred posts) and the X row's bounded window count. Otherwise the "early" check stalls on authorization.
- **M5. Saturation semantics must be uniform across methods.** A lower bound can support a crossing claim, never a no-change or no-signal result. The review left this open in its question (c).
- **M6. Partial decision blockers cannot be expressed.** The plan model's `decision_blockers` apply to whole specs (`verify_plan.py:80-90`). R2-F08's "decision blocker only of the live part" is resolved by a non-blocking decision plus a recorded readiness state.
- **M7. The UI checklist venues change.** The renderer's shared UI obligation sends checklists to S13, S23 or S30. After S13 moves before the UI exists, the venues become S23 and S30 only.
- **M8. W02 is recorded in two places.** It is in both `plan_source.json` `decisions` and `user_decisions`. Update both, and let `verify_plan.py` accept a decision that blocks no spec.

## 4. Revision suggestion

### 4a. Revised ordered spec list

"kept" means keep the current rationale text for that edge. Every other edge rationale below is new or replaced. All dependencies precede their consumers. Depths and weighted paths are computed in 4d.

| ID | Slug | Title | Lane | Size | Milestone | Direct deps | Edge rationales | Old ID / change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | stable-verification-clock | Restore a complete, time-stable verification baseline | pilot-build | M | M0 | — | — | old-S01, unchanged |
| S02 | pilot-configuration | Compose the local pilot from one validated configuration | pilot-build | M | M0 | S01 | S01 kept | old-S02; readiness names missing cost scopes (4b) |
| S03 | operator-commands | Give the operator recorded commands for cost controls and bounded X polling | pilot-build | S | M0 | S02 | S02: commands act on the owners, routes and trusted operator identity composed from the validated configuration | **new** (R2-F02) |
| S04 | client-foundation | Establish the bilingual client foundation, shell and client verification | pilot-build | M (was L) | M0 | S01 | S01 kept | old-S03, narrowed |
| S05 | live-feasibility-probes | Probe bounded live model, discovery, X and email-provider feasibility early | live-validation | M | M0 | S03 | S03: every live route refuses until a cost scope and route binding exist, and X also needs a recorded activation; these commands are the only shipped path (replaces the S02 edge; S02 remains transitive) | old-S04, rescoped |
| S06 | automated-interpretation | Publish catalog-scoped caption interpretations from automated tasks | pilot-build | M | M0 | S01 | S01 kept | old-S05, unchanged |
| S07 | pilot-scale-retrieval | Select question-, brief- and graph-scoped governed support at pilot scale | pilot-build | L | M0 | S01 | S01 kept | old-S06, rescoped (4b) |
| S08 | early-marketer-checkpoint | Check shortlist and answer usefulness with a marketer on real discovered data | human-validation | S | M0 | S05, S06, S07 | S05: requires passed model and Bright Data keyword rows and the bounded discovery corpus under U1. S06: discovered posts must carry published mention interpretations. S07: shortlists and answers must use pilot-scale, question-scoped retrieval | old-S13, rescoped and moved early |
| S09 | local-runtime | Run bounded local work continuously with restart, health and lifecycle maintenance | pilot-build | L | M1 | S02 | S02 kept | old-S07; maintenance added, health UI moved to S16 |
| S10 | workspace-and-evidence | Open saved campaigns and inspect governed evidence in the shared inspector | pilot-build | M | M1 | S04 | S04 kept | old-S08, unchanged |
| S11 | source-capabilities | Describe usable source routes and bounded selection policy | pilot-build | M | M1 (was M3) | S02 | S02 kept | old-S20, backend half; S08 edge removed |
| S12 | campaign-decisions | Complete brief to saved recommendation and explicit regeneration | pilot-build | L | M1 | S10, S07, S06, S02 | all kept | old-S09, unchanged |
| S13 | task-events-lineage | Read asynchronous progress and exact pipeline lineage | pilot-build | S | M1 | S10 | S10 kept | old-S10, unchanged |
| S14 | exact-approval-tools | Review exact enrichment scope and expose governed agent operations | pilot-build | M | M1 | S13, S10 | both kept | old-S11, unchanged |
| S15 | conversations | Save conventional chat threads with question-scoped extractive turns | pilot-build | L | M1 | S10, S07, S02 | all kept | old-S12; owns the composer reducer |
| S16 | discovery-operations-screen | Configure scheduled discovery and see route and runtime health | pilot-build | S | M1 | S10, S11, S09 | S10: D1 renders in the shell with the shared inspector. S11: route capability, readiness and selection basis come from the registry. S09: last tick, per-component health and next due come from the runtime health read | **new**, D1 half of old-S20 plus old-S07's health UI |
| S17 | graph-reads | Page governed graph branches with stable identities and policy frontiers | pilot-build | M | M2 | S07 | S07 kept | old-S14, unchanged |
| S18 | interactive-graph | Explore the production graph with camera, pins and incremental branches | pilot-build | L | M2 | S17, S10 | S17 kept. S10 replaced: "Selection opens the shared inspector." | old-S15; owns library decision and branch reducer |
| S19 | monitoring-depth-and-timing | Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility | pilot-build | M | M3 | S01 | S01: changes the recent, alerts and semantic owners whose suites must be green; cadence stays a topic-revision setting, so no configuration edge (replaces the S02 edge) | old-S16, **rewritten** |
| S20 | monitoring-workspace | Operate independent topics, activation and alert history | pilot-build | M | M3 | S10, S19 | S10 kept. S19: M1 shows saturation, receipt-time bounds and live-page method outcomes unconditionally | old-S17; edge added |
| S21 | monitoring-history | Plot current and selected monitoring windows without fabricated data | pilot-build | M | M3 | S20, S19 | S20 kept. S19: the chart renders saturated windows as lower bounds from the window projection | old-S18; owns chart reducer and method-series contract |
| S22 | alert-investigation-promotion | Investigate alerts with existing KB context and promote selected evidence | pilot-build | S | M3 | S20 | S20 kept | old-S19, unchanged |
| S23 | engagement-anomalies | Detect supported engagement changes with comparable measurement ages | pilot-build | M | M3 | S19, S11 | S19 replaced: "Consumes the metrics_retrieved_at and saturation projections and the live-page eligibility rule." S11 kept | old-S21; **W02 decision blocker removed** |
| S24 | semantic-shift | Detect provisional semantic shifts with a comparable baseline | pilot-build | L | M3 | S19 | S19: baseline-aware comparison reuses the live-page eligibility rule and saturation limitation rather than a second definition (replaces the S01 edge; S01 remains transitive) | old-S22 |
| S25 | interaction-checkpoint | Check graph, chart, campaign and chat interaction in a real browser | human-validation | S | M3 | S18, S21, S12, S15 | S18, S21 kept. S12: the C1 browser checklist under test. S15: the chat browser checklist (EN/KO, IME, drafts) under test | old-S23, widened |
| S26 | spending-operations | Inspect and operate independent spending controls | pilot-build | M | M4 | S04, S03 | S04: S1 forms render in the shell with governed reads (re-pointed from old-S08). S03: forms reuse the operator command layer for scope, route and ceiling instead of a second path | old-S24 |
| S27 | progressive-acquisition | Plan finite field-capability acquisition steps and stop honestly | pilot-build | L | M4 | S11 | S11 kept | old-S25 |
| S28 | supplementary-detail-route | Task-integrate one named supplementary detail route | pilot-build | M | M4 | S27 | S27 kept | old-S26, unchanged |
| S29 | inbox-email | Deliver durable task and alert notifications through inbox and email | pilot-build | L | M4 | S09, S02, S10 | S09, S02 kept. S10 replaced: "Inbox items open governed task, alert and evidence links in the shared inspector." | old-S27; transport and Message-ID |
| S30 | plans-and-quality | Preserve measurement planning and prepare attributable KR/JP quality packets | pilot-build | M | M4 | S12 | S12 kept | old-S28, unchanged |
| S31 | provider-readiness | Record live discovery, model and recurring-work readiness | live-validation | S (was M) | M5 | S05, S09, S26 | S05: reuses the probe authorizations and record format. S09: recurring keyword discovery needs the runtime. S26: reconciles this capability's actual charges through operator controls | old-S29, split |
| S32 | monitoring-readiness | Record live X monitoring and alert-method readiness | live-validation | S | M5 | S05, S09, S19, S23, S24, S26 | S05: reuses the X row. S09: recurring polling needs the runtime. S19: live windows need saturation and live-page eligibility. S23: the engagement method under test. S24: the semantic-shift method under test. S26: reconciles X and model charges | **new**, from old-S29 |
| S33 | detail-route-readiness | Record supplementary detail-route readiness | live-validation | S | M5 | S05, S28, S26 | S05: reuses the Bright Data row's field findings. S28: the route under test. S26: reconciles its charges | **new**, from old-S29 |
| S34 | email-readiness | Record email send readiness | live-validation | S | M5 | S05, S29 | S05: reuses the email-provider row. S29: the transport, delivery identity and inbox under test | **new**, from old-S29 |
| S35 | human-pilot-acceptance | Record pilot release acceptance on live data | human-validation | M | M5 | S14, S08, S22, S25, S30, S31, S32, S33, S34 | S14, S08, S22, S25, S30 kept. S31–S34: usefulness must be judged on live capabilities; a recorded blocked row is a valid input | old-S30 |
| S36 | evaluated-retrieval | Improve multilingual retrieval with pinned, rebuildable support | later-core-depth | L | Later | S07, S30 | both kept | old-S31 |
| S37 | agent-candidate | Prepare a bounded research and synthesis candidate for decision review | later-candidate | L | Later | S14, S15 | both kept | old-S32 |
| S38 | agent-human-evidence | Obtain actual adjudication for the richer-agent successor | human-validation-later | M | Later | S37 | kept | old-S33 |
| S39 | enable-richer-agent | Enable only the accepted grounded research and synthesis contract | decision-blocked | L | Later | S38; decision W01 | kept | old-S34 |
| S40 | hosted-actors-tenancy | Move the proven pilot to authenticated workspace tenancy | later-proposal | L | Later | S35 | kept | old-S35 |
| S41 | projection-governance | Reconcile retained copies and rebuildable projections with operational recovery | later-proposal | L | Later | S36, S40 | both kept | old-S36 |
| S42 | multimodal-ontology | Add evidenced multimodal and richer ontology concepts | later-proposal | L | Later | S36, S41 | both kept | old-S37 |
| S43 | objective-portfolios | Compare objective-specific creator factors and feasible portfolios | later-proposal | L | Later | S36, S42 | both kept | old-S38 |
| S44 | outcomes-attribution | Measure actual outcomes and rule-based attribution | later-proposal | L | Later | S30, S40, S41 | all kept | old-S39 |
| S45 | causal-measurement | Estimate incremental effect only under an accepted causal design | later-proposal | L | Later | S44 | kept | old-S40 |

Final `order` for `plan_source.json`:

```
stable-verification-clock, pilot-configuration, operator-commands, client-foundation, live-feasibility-probes,
automated-interpretation, pilot-scale-retrieval, early-marketer-checkpoint, local-runtime, workspace-and-evidence,
source-capabilities, campaign-decisions, task-events-lineage, exact-approval-tools, conversations,
discovery-operations-screen, graph-reads, interactive-graph, monitoring-depth-and-timing, monitoring-workspace,
monitoring-history, alert-investigation-promotion, engagement-anomalies, semantic-shift, interaction-checkpoint,
spending-operations, progressive-acquisition, supplementary-detail-route, inbox-email, plans-and-quality,
provider-readiness, monitoring-readiness, detail-route-readiness, email-readiness, human-pilot-acceptance,
evaluated-retrieval, agent-candidate, agent-human-evidence, enable-richer-agent, hosted-actors-tenancy,
projection-governance, multimodal-ontology, objective-portfolios, outcomes-attribution, causal-measurement
```

Decisions in `plan_source.json`:

- W01 is unchanged and blocks S39.
- W02 is retitled "Decide live X window comparability and receipt-time semantics" and blocks no spec (see 4e). Remove `W02` from `engagement-anomalies.decision_blockers`.

### 4b. New, split and materially changed specs

Unless stated otherwise, the shared UI obligations and the completion-evidence text apply as they do today. Set `ui_bearing` as noted.

#### S03 `operator-commands` (new, S, pilot-build, `ui_bearing: false`)

- **Outcome:** an operator can configure spending controls and run bounded live X polling from the shipped tools. Live probes and recurring work then have a recorded, attributable path.
- **Scope:** subcommands on the composed operator CLI from S02:
  - `configure-cost-scope` (a CostScope from an explicitly named file section),
  - `bind-cost-route` (adapter, scope and the owner's required `max_units`),
  - `set-cost-ceiling` (amount, currency, period, pause),
  - `read-allowance`,
  - `activate-x-topic` (topic key, expected topic version, first window end, request ID),
  - `deactivate-x-topic`,
  - `run-x-due --once` (one bounded `RecentPolling.run_due` pass).
- **Non-goals:** browser forms (S20, S26); reconciliation and meter recovery (S26); any daemon or loop (S09); new receipt tables; applying cost settings implicitly at start-up.
- **Owner:** `smi_costs` and `smi_monitoring.polling` keep validation and SQL. The S02 composition module owns argument parsing and the trusted operator identity.
- **Interface and data shape:**
  - Thin adapters with source-free JSON output.
  - Errors are owner reason codes, such as `cost_scope_conflict`, `unsupported_cost_route_contract`, `monitoring_poll_already_active` and `monitoring_topic_version_conflict`.
  - A changed immutable scope requires a new scope ID.
  - Actor and workspace are never taken from arguments.
- **Acceptance:**
  1. On a fresh database, the documented sequence (scope, route binding, ceiling) through the shipped commands makes the simulated model route admissible from the shipped server, and the S02-A02 journeys run. Before the sequence, `readiness()` names the missing cost scope.
  2. Re-running the same scope or route command changes nothing. A changed rate under the same scope ID fails with the owner's conflict reason and writes nothing.
  3. With fake HTTP, activate → `run-x-due --once` N times → deactivate produces N windows and a recorded deactivation. A further run dispatches no request.
  4. Output and logs never contain secrets or provider handles. A forged actor or workspace argument is rejected.
- **Requirements:** FR-C01, FR-S01, OFR-E03, OFR-S03, UD-02.

#### S02 `pilot-configuration` (small change)

- `readiness()` reports a missing cost scope or route binding per route as a named prerequisite.
- S02-A02 configures the simulated scope through the public `UsageAccounting` operation in its test.
- The shipped operator sequence is accepted in S03.

#### S04 `client-foundation` (narrowed L → M)

- **Remove from scope and interface:** the graph layout and library decision, and the "pure reducers for graph branches, chart series and the composer".
- **Keep:** the API client, the `/api/v1` adapter framework, the i18n mechanism and completeness check, shell, navigation, theme, EN/KO switch, the freshness utility and the `node --test` harness.
- **Checks:**
  - Replace check 1 with: "`tools/check.py` runs the Node tests and fails on a broken client-module test."
  - Delete checks 2 and 3; they move to S18 and S15.
  - Keep checks 4 and 5.
  - Add: "The API client parses envelopes, generates request IDs and classifies retry kinds; a sanitized error never renders raw server text."

#### S05 `live-feasibility-probes` (rescoped)

- **Dependency:** S03 instead of S02.
- **Replace the invariant** "Probes activate no recurring topic or schedule" with: "Probes create no unbounded or unrecorded activation. The X row activates one topic through S03 for at most the U1-authorized number of windows and records its deactivation."
- **The X row records:**
  - the saturation rate (share of windows with `next_token`),
  - receipt-minus-publication ages,
  - counts-endpoint availability for the account tier,
  - a U3 depth recommendation and the evidence for W02.
- **The email row** probes the chosen transport (default SMTP submission through the operator mailbox): acceptance-reply semantics and Message-ID handling, with no product send.
- **Replace check 2 (old S04-A02, rendered as S05-A02 after renumbering) with:** "The X row runs one bounded activation for the authorized number of windows, records its deactivation, saturation rate and measurement ages, and ends with a recorded U3 depth recommendation and W02 evidence."
- **Add a fifth check (rendered as S05-A05):** "The email row names its transport and records acceptance-reply semantics, or a blocked reason."

#### S07 `pilot-scale-retrieval` (rescoped)

- **Add to scope:**
  - Record the index mechanism (own term table, `pg_trgm` or `tsvector`) with benchmark results on the 1,000-post fixture.
  - Record a deterministic, versioned ranking rule among matches. Recommended: exact subject-ID matches, then derived-term match count, then recency, with stable tie-breaking.
  - Wire `derive_scope` into the installed question → answer and brief → comparison paths whenever the caller supplies no explicit terms.
- **Add check:** "The recorded index mechanism and ranking rule are documented with fixture benchmark results, and the installed answer and comparison paths (legacy form and CLI) pin the derived scope."

#### S08 `early-marketer-checkpoint` (rescoped and moved; S, human-validation, M0)

- **Outcome:** early, on real discovered data, a marketer and a KR/JP reader judge whether shortlists, mention judgments and extractive answers are useful. S06 (interpretation) and S07 (retrieval) can then change before C1 and chat are built.
- **Scope:**
  - Under U1 caps, the operator runs a bounded live keyword-discovery corpus (up to 10 keywords, a few hundred posts) through the installed live task path with automated interpretation.
  - The reviewers grade about 10 briefs' shortlists and about 10 questions' supporting findings, including EN and KO questions over KR/JP captions.
  - They use whatever UI exists at that build: legacy forms and CLI expected, C1 and chat if they have landed.
  - Record denominators, precision@k for supporting findings (no threshold claimed) and mention-judgment errors.
  - Pre-declared outcomes:
    - retrieval fails → revise S07's ranking rule, or pull a named subset of S36 forward before S15 lands;
    - mention judgments fail → revise S06's catalog rules.
- **Non-goals:** UI review (S25, S35); release gating.
- **Owner:** the actual marketer and KR/JP reader, supported by the campaign, knowledge and assistant maintainers.
- **Interface:** the existing record format (reviewer, language, build and configuration digest, live provenance) plus per-item grades and denominators.
- **Acceptance:**
  1. Named reviewers, build and configuration identity, and live data provenance are recorded.
  2. Each brief and question is graded with its denominator, and failing examples are kept.
  3. Precision@k for supporting findings and mention-judgment error counts are recorded per language.
  4. Each triggered pre-declared outcome is filed against its owning spec's execution issue with the declared action.
- Remove the `{{campaign-decisions}}` and `{{conversations}}` browser-checklist references from this spec; those checklists now run at S25.

#### S09 `local-runtime` (rescoped)

- **Integration:** replace "Operations screens show last tick, per-component health, next due and actual activation" with "`health()` exposes last tick, per-component health, next due and actual activation for S16."
- **Scope:** add one bounded lifecycle-maintenance component. It calls the existing `expire`, `reconcile` and `reconcile-knowledge` operations on a configured cadence with a per-tick bound and reports in `health()`. No new lifecycle logic. Inbox reconciliation is registered by S29.
- **Add check:** "With an expired payload and a withdrawn source, a maintenance tick removes the payload and reconciles dependent copies within its bound, and health reports the run."
- Add PROP-27.

#### S11 `source-capabilities` (backend half of old-S20)

- **Title:** "Describe usable source routes and bounded selection policy". Set `ui_bearing: false`, milestone M1.
- **Scope:** remove "Own the D1 configuration screen…".
- **Integration:** keep the readiness read contract and remove the D1 display sentence.
- **Checks:** move old check 5 (eleventh keyword, daily cap, occurrence authority) to S16. Keep checks 1–4.

#### S16 `discovery-operations-screen` (new, S, `ui_bearing: true`, M1)

- **Outcome:** in one D1 screen, an operator configures up to ten scheduled keywords and the shared daily allowance, activates schedules as recorded commands, and sees route capability, readiness, selection basis and runtime health.
- **Scope:** the r2 D1 screen (ten-keyword limit, recorded activation, day allowance, route health, selection basis) plus runtime health (last tick, per-component health, next due, actual activation). Retire the legacy `/schedules` form after parity.
- **Non-goals:** new scheduling or selection logic; topic activation (S20); spending forms (S26).
- **Owner:** `smi_review`. It reads `ScheduledDiscovery`, `SourceCapabilities` and `LocalRuntime.health` through public ports.
- **Interface:**
  - `/api/v1` reads for schedule settings, occurrences and allowance, per-route capability and readiness, and runtime health.
  - Commands to configure or activate a schedule with an expected version and request ID.
  - Installed, access-unknown, permission-denied, configuration-blocked and activated states stay separate.
- **Acceptance:**
  1. An eleventh scheduled keyword is refused. The daily cap and occurrence authority are shown truthfully, and configuration edits never alter an existing occurrence's scope (moved from old-S20).
  2. Route states display separately from the readiness read, including access-unknown and configuration-blocked.
  3. When the runtime stops, health turns stale within the configured bound. After restart, the new last tick and next due appear.
  4. The legacy `/schedules` routes are removed after their parity tests pass.
- **Requirements:** FR-P01, FR-P02, FR-L01, OFR-E03, PROP-34, UD-03.

#### S18 `interactive-graph` and S15 `conversations` (reducers moved in)

- **S18 scope:** "First deliverable: a time-boxed spike (at most 3 working days) that renders S17 fixture branch pages with the candidate library. Record the engineering decision. Recommended: a vendored, pinned, licence-recorded library such as Cytoscape.js with its SHA-256 in the repository; a hand-built layout only if the spike fails. Offer an optional, non-gating 30-minute human look."
- **S18 interface:** "Owns the graph branch/generation reducer." Its existing reducer checks already cover it.
- **S15 interface:** "Owns the composer/draft/IME reducer with Node tests." Its existing IME check already covers it.

#### S19 `monitoring-depth-and-timing` (rewritten, M, M3, depends on S01)

- **Title:** "Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility".
- **Outcome:** live X windows state their saturation and receipt-time bounds truthfully. Under an accepted W02, they can produce honest live volume and controversy outcomes inside ADR 0023's one-page rule.
- **Scope:**
  1. Project the stored `acquisition.pagination_remaining` as a typed `collection_saturated` limitation on window, volume and semantic reads.
  2. Project the stored `acquisition.retrieved_at` (receipt time) as `metrics_retrieved_at` with its `elapsed_seconds` bound on live windows. Offline and fixture windows report it as unrecorded. No column and no backfill write.
  3. Add a separately versioned live-page eligibility rule to the volume (`alerts/`) and controversy (`semantic/`) owners:
     - an unsaturated live page is a complete sample of the provider's recent-search results for the literal query, with market coverage unknown;
     - receipt time bounds unknown capture and measurement times from above;
     - a saturated window supports only a lower-bound crossing claim;
     - a non-crossing result on a saturated window, and any saturated baseline, is `not_assessable` with `collection_saturated`.
  4. Provide a shared live-shaped fixture builder that reproduces `XRecentRoute.collect`'s receipt: `declared_coverage: partial`, unknown capture time, `pagination_remaining` true or false.
  5. Draft the W02 amendment text for ADR 0019 and ADR 0023 and `docs/monitoring.md`.
- **Non-goals:** pagination or the counts endpoint (U3); global cadence configuration (cadence stays a topic-revision setting); rewriting stored coverage; recomputing existing assessments.
- **Interface and data shape:**
  - Window reads gain `collection_saturated: bool | null` and `metrics_retrieved_at` plus `retrieval_bound_seconds`, where null means unrecorded.
  - The method version is pinned on each assessment. The live-page versions are registered only when W02 is accepted.
  - Installed v1 behavior is unchanged.
- **Authority:** one page per window stays the ADR 0023 rule. A remaining page is a limitation, never a pagination loop.
- **Recovery:** unknown poll responses keep their liability. A legacy window without a receipt stays unrecorded and is never assigned a time.
- **Acceptance:**
  1. A live-shaped unsaturated window and a comparable live-shaped baseline yield `significant_change` or `no_change` under the live-page volume version, and still `not_assessable` (`collection_incomplete`) under installed v1.
  2. A saturated detection window over an unsaturated baseline yields an increase only when its lower bound meets the threshold, labelled as a lower bound. A saturated baseline, or a saturated non-crossing result, is `not_assessable` with `collection_saturated`. The same rule holds for the controversy method's thresholds.
  3. Live windows expose `metrics_retrieved_at` from the stored receipt and offline windows report it as unrecorded. It is never presented as capture time, and no schema column is added.
  4. Regression: cadence alignment, revision pinning and forced reactivation behave exactly as installed.
- **Requirements:** keep FR-C01, FR-C02, FR-P09, OFR-C01, R2-STREAM; add FR-C03.

#### S20 `monitoring-workspace`, S21 `monitoring-history`, S24 `semantic-shift` (new S19 edges)

- **S20:**
  - Replace check 3 with: "A live-shaped window from S19's builder shows its saturation and receipt-time limitation and the live-page method outcome in M1."
  - S23 and S24 method registration follows the integration rule.
- **S21:**
  - Interface: owns the chart-series reducer (moved from S04).
  - Interface: defines a method-series registration contract: `register(method_key, version, read_points(topic, from, to, cursor))`, where each point carries a value or null, unit, denominator, support IDs and comparability.
  - Scope: saturated windows render as lower bounds (≥N) with a distinct marker. Remove the "when {{monitoring-depth-and-timing}} exists" qualifier.
  - Add check: "A stub method registered through the contract appears in the selector and table with its own denominators, with no chart-code change. Live-shaped saturated windows render as lower bounds in both chart and table."
- **S24:**
  - Add check: "A live-shaped window pair is assessed under the live-page eligibility rule, and a saturated baseline is not assessable."
  - Chart, M1 and inbox integration follow the integration rule.

#### S23 `engagement-anomalies`

- **Decision blocker:** remove W02.
- **Scope:**
  - For live X, measurement age = `metrics_retrieved_at − published_at` (an upper bound), comparable within a configured tolerance bounded by cadence and the indexing delay. Label the result young-age engagement.
  - This method version is registered only under an accepted W02. Otherwise live engagement reports `measurement_time_unknown`.
  - Six-hour re-measurement is a later path that needs a separately authorized operation and is not in the pilot.
- **Add check:** "A live-shaped window pair yields a matched-age comparison under the live version and `measurement_time_unknown` under the rejected-decision configuration."

#### S25 `interaction-checkpoint` (widened)

- **Title:** "Check graph, chart, campaign and chat interaction in a real browser".
- **Scope:** also execute the S12 (C1) and S15 (chat) browser checklists in EN and KO. The marketer is preferred for those two journeys; otherwise a named human reviewer.
- **Add check:** "C1 and chat checklists are recorded with per-item pass/fail in EN and KO, with failing examples filed against their owning specs."

#### S26 `spending-operations`

- **Dependencies:** S04 and S03, as in 4a.
- **Interface:** "The configure forms call the S03 command layer. Reconciliation and meter recovery stay here, with the receipts this spec already owns."

#### S27 `progressive-acquisition`

- **Integration:** "Under the integration rule, render plan steps in the S13 T1 pipeline view if S13 has landed (expected), using the `AcquisitionPlan.read` model this spec provides."

#### S29 `inbox-email`

- **Scope:** the transport is SMTP submission through the configured operator mailbox by default (U7). Every email carries a `Message-ID` derived from the logical delivery key. An ambiguous accepted response stays uncertain and appears prominently in the channel status with a one-action attributable reissue, which uses a new Message-ID linked to the original.
- **Add check:** "Each email's Message-ID derives from its logical delivery key; a reissue carries a new linked ID."

#### Readiness rows S31–S34 (split from old-S29)

Each row is size S and live-validation. Each keeps the old-S29 record format, owner and invariants, and links its S05 probe row, stating what changed since the probe.

- **S31 `provider-readiness`**, discovery, model and recurring work:
  1. Actual authorized keyword discovery and model receipts reopen usable permitted publications and answers through public owners.
  2. Recurring keyword discovery runs with finite bounds and refuses on source policy or ceiling, with no fifty-post throughput claim.
  3. Actual provider-basis charges reconcile against exact operations, or remain recorded as unknown.
- **S32 `monitoring-readiness`**, live X polling and alert methods:
  - Outcome: live X polling and each alert method have a signed-off readiness record or an explicit blocked record with its reason. No market completeness or significance claims.
  - Records the states of W02 and U3.
  - Acceptance:
    1. Recurring X windows are observed with finite bounds, and activation and deactivation are recorded.
    2. Each method (volume, controversy, engagement, semantic shift) has a live outcome or a recorded `not_assessable`/blocked reason. Live alert readiness is claimed only under an accepted W02; otherwise the row records `blocked_by_decision`.
    3. X and model charges reconcile, or remain unknown.
    4. The saturation rate over the readiness period is recorded against the U3 choice.
- **S33 `detail-route-readiness`**:
  1. Authorized detail receipts for each field reopen through public owners.
  2. Unsupported fields are explicitly unavailable.
  3. Charges reconcile, or remain unknown.
- **S34 `email-readiness`**:
  1. One explicitly authorized test email goes to the configured recipient.
  2. Provider acceptance and actual recipient receipt are recorded separately.
  3. The governed link is verified from the intended access context.
  4. Uncertain-delivery handling is exercised with a simulated failure only, with no extra live sends.

#### S35 `human-pilot-acceptance`

- **Dependencies:** as in 4a.
- **Scope:** add "Incorporates the four readiness rows. A recorded blocked row is a valid input; the affected journey is recorded as blocked rather than passed."
- **Check 1:** refers to S25.

#### Renderer rules (`build_plan.py`)

- **`UI_OBLIGATION`:** the checklist venue becomes "executed at {{interaction-checkpoint}} or {{human-pilot-acceptance}}". Drop `{{early-marketer-checkpoint}}`.
- **New shared rule, stated once:** "Integration with a spec that has not landed is a conditional check, never a hidden blocker. Each conditional check is mirrored in its partner spec. When both exist, the spec that lands second makes the check pass unconditionally."

### 4c. Requirement-ID moves

| Spec (slug) | Change |
| --- | --- |
| `operator-commands` | Add FR-C01, FR-S01, OFR-E03, OFR-S03, UD-02 |
| `early-marketer-checkpoint` | Keep FR-A01, FR-B01, OFR-E01, PROP-16. Add PROP-03. Remove UD-01 and UD-03 (to `interaction-checkpoint`) |
| `interaction-checkpoint` | Add FR-A01, FR-B01, UD-01, UD-03, R2-CHAT |
| `local-runtime` | Add PROP-27 |
| `source-capabilities` | Remove FR-P01 (to `discovery-operations-screen`). Keep the others |
| `discovery-operations-screen` | FR-P01, FR-P02, FR-L01, OFR-E03, PROP-34, UD-03 |
| `monitoring-depth-and-timing` | Add FR-C03 |
| `provider-readiness` | Keep FR-S01, OFR-S01, OFR-S03, OFR-E03, PROP-28, UD-02. Remove FR-C01, FR-C02, FR-P04, FR-P09, PROP-23, UD-05 (moved below) |
| `monitoring-readiness` | FR-C01, FR-C02, FR-C03, FR-P09, FR-S01, OFR-S01 |
| `detail-route-readiness` | FR-P04, PROP-23, FR-S01, OFR-S01 |
| `email-readiness` | UD-05, FR-C05 |
| `client-foundation`, `interactive-graph`, `monitoring-history`, `conversations` | Unchanged (reducer moves need no ID change) |

Every ID keeps at least one spec. FR-P01 stays on `local-runtime`, UD-05 on `live-feasibility-probes` and `inbox-email`, and FR-C02/C03 on their method specs.

Update `user_decisions[].affects`:

| Decision | Affects |
| --- | --- |
| U1 | live-feasibility-probes, early-marketer-checkpoint, provider-readiness, monitoring-readiness, detail-route-readiness, email-readiness |
| W02 | monitoring-depth-and-timing, engagement-anomalies, semantic-shift, monitoring-readiness |
| U3 | live-feasibility-probes, monitoring-depth-and-timing, monitoring-history, monitoring-readiness |
| U5 | client-foundation, interactive-graph, monitoring-history, interaction-checkpoint |
| U7 | live-feasibility-probes, inbox-email, email-readiness, hosted-actors-tenancy |

### 4d. Narrative corrections

#### `implementation-sequence.md`

Mostly regenerated by `write_sequence.py`; the hand-written parts follow.

**Opening paragraphs:**

- Probes run in S05 once the operator commands (S03) exist, and are recorded finally in the four readiness rows S31–S34.
- Human evidence comes at S08 (early real-data check on pre-UI paths) and S25 (browser check of graph, chart, campaign and chat), before S35.
- Open decisions: W01 blocks S39. W02 is retitled, asked at plan start and blocks no spec.

**Milestones:**

| Milestone | Specs | Content |
| --- | --- | --- |
| M0 | S01–S08 | Baseline, configuration, operator commands, client foundation, probes, interpretation and retrieval, ending at the early real-data check S08 |
| M1 | S09–S16 | Runtime with maintenance, workspace and inspector, source capabilities, campaign, task progress, approval, chat, and the D1 plus health screen |
| M2 | S17–S18 | Graph reads and the interactive graph |
| M3 | S19–S25 | Live-window comparability, M1, chart, investigation, engagement, semantic shift, and browser checkpoint S25 |
| M4 | S26–S30 | Spending, acquisition plan and route, inbox plus email, planning and quality packets |
| M5 | S31–S35 | Four readiness rows and the release record |
| Later | S36–S45 | Unchanged content, renumbered |

**Critical paths** (computed from the 4a graph; the generator may break equal-depth ties differently):

| Path | Depth chain | Illustrative weighted chain |
| --- | --- | --- |
| First live evidence | S01→S02→S03→S05 (depth 4) | 3.5 |
| Early real-data check | S01→S02→S03→S05→S08 (depth 5) | S01→S07→S08, 4.5 |
| Headline journeys | S12, S15, S18 at depth 4; S21 at depth 5 | — |
| Deepest pilot build | S01→S02→S11→S27→S28 (depth 5) | 7 |
| Release record | S01→S04→S10→S20→S21→S25→S35 (depth 7, was 8) | two co-critical chains at 9.5: S01→S07→S17→S18→S25→S35 (graph) and S01→S02→S09→S29→S34→S35 (email) |

**Safe parallel waves:**

| Depth | Specs |
| --- | --- |
| 1 | S01 |
| 2 | S02, S04, S06, S07, S19 |
| 3 | S03, S09, S10, S11, S17, S24 |
| 4 | S05, S12, S13, S15, S16, S18, S20, S23, S26, S27, S29 |
| 5 | S08, S14, S21, S22, S28, S30, S31, S32, S34 |
| 6 | S25, S33 |
| 7 | S35 |

**Integration sentence:** replace it with the shared rule in 4b (renderer rules).

**User-decision table:** replace it with 4e.

**Engineering choices:**

- graph library versus hand-built layout (S18, first deliverable),
- configuration file format (S02),
- retrieval index mechanism and ranking rule (S07),
- event table versus derived phases (S13),
- interpretation before publication (S06),
- live-page method versioning (S19),
- notification Message-ID derivation (S29).

**Prerequisites paragraph:**

- Cost configuration and X activation are recorded operator commands (S03); keyword schedules use the legacy `/schedules` form, then S16; topic forms come in S20.
- Premises that depend on probe results: S19's live-page premises, S23, S28's fields and S29's transport.
- Contingency: if U3 is answered (a) or (b), add one M spec "Extend live X monitoring depth" after S19 and S03 that blocks S32.

#### `gap-analysis.md`

- **Pilot composition row (`:30`):** add "No shipped command configures cost scopes, route bindings or ceilings, or activates and runs X polling; every live route refuses without them." Target S02, S03.
- **Monitoring depth and timing row (`:34`):** replace the gap with: "Live windows are stored partial with unknown capture times, and the installed volume and controversy methods (ADR 0019/0020) accept only complete windows, so no live alert can fire. Receipt time and next_token are already stored in the acquisition JSON but not projected." Specs S19, S23; decision W02.
- **Monitoring foundation and methods rows (`:20-21`):** renumber to S09/S19/S20/S32 and S23/S24/S32/S35.
- **Hosted/copies row (`:35`):** add "Payload expiry runs only through `smi-ingest expire`; the local runtime schedules it (S09); hosted governance stays in S41."
- **Boundaries paragraph (`:40`):**
  - "S01–S30 build the pilot, with probes S05, the early real-data check S08 and the browser checkpoint S25; S31–S34 record per-capability readiness; S35 is the release record."
  - Renumber the S20/S26 references to S11/S28.

#### `architecture-target.md`

- **Owner table:**
  - `smi_review`: S02, S03 (the operator commands live in the composition root), S04, S10, S12–S16, S18, S20–S22, S26, S29, S30.
  - Runtime: S09, with "bounded lifecycle maintenance through existing expire/reconcile ports".
  - Monitoring: S19–S24.
  - Costs: S03 (commands) and S26.
- **Client foundation paragraph (`:58`):** remove the reducers and the library decision. State that S18, S21 and S15 own the graph, chart and composer reducers.
- **Interaction table:** the M1 row becomes S19–S21 and S23–S24; the D1 row becomes S09/S11/S16/S27/S28; the S1 row becomes S03/S26.
- **Runtime and controls section:** "Cost configuration and X activation are explicit, attributable operator commands; configuration never applies cost settings implicitly." Also: "Live-page comparability is a proposed method version subject to W02; installed v1 methods are unchanged."

#### Other files

- **`wayfinder/issues/002-x-metric-measurement-time.md`:** rewrite per 4e. Set `Blocks: none (no build or validation spec). Informs monitoring-depth-and-timing, engagement-anomalies and semantic-shift; its state is recorded by monitoring-readiness.` Update the product map's W02 title.
- **`verify_plan.py`:** allow a decision whose `Blocks:` line names no spec. Keep "S01 is the only dependency-free spec". Optionally add the review's check that no decision issue's "blocks only" claim is contradicted transitively.

### 4e. User decisions, with recommended defaults

None blocks the start of the pilot build or any spec except W01→S39.

| ID | Decision | Default if unanswered | Affects |
| --- | --- | --- | --- |
| U1 (extended) | Grant bounded live authorization and credentials early: model; Bright Data keyword, including a bounded discovery corpus for S08 (up to 10 keywords, a few hundred posts); X recent for one topic over a bounded number of windows; the email mailbox's semantics. Per-capability call counts and one spending ceiling. | Request at plan start with the smallest useful caps. If not granted, S05 and S08 stay blocked, the build continues on fixtures and premise-dependent specs stay provisional. | S05, S08, S31–S34 |
| W02 (widened; ask at plan start) | For live X: (a) may the recorded receipt time bound capture and metric measurement time from above; (b) may an unsaturated single page count as a complete sample of the provider's recent-search results for the literal query; (c) may a saturated window support only lower-bound crossing claims? This amends ADR 0019, ADR 0023 and `docs/monitoring.md:168` through new method versions. | Accept all three as a narrowly scoped amendment, with market coverage still unknown and installed v1 unchanged. If rejected, live windows stay not assessable, there are no live alerts and no live engagement, and S32 records `blocked_by_decision`. | S19, S23, S24, S32 |
| U3 (widened; revisited after S05's X row) | Pilot X monitoring depth: (a) counts endpoint as the volume series; (b) bounded multi-page collection; (c) shorter cadence within configured cost; (d) accept a saturated lower-bound display. (a) and (b) need an ADR 0023 successor and more recurring paid authority. | (c)+(d). S05's X row records the saturation rate and a recommendation, and the coordinator re-asks. Choosing (a) or (b) adds one M spec before S32. | S05, S19, S21, S32 |
| U4 | Which supplementary detail route, and is tiktok-web source use permitted? | Bright Data profile/post detail fields; tiktok-web stays unavailable. | S28, S33 |
| U5 (re-asked narrowly) | Permit scoped headless-browser tests against the loopback app, either (i) in CI only, with no agent browsing, or (ii) also by agents? | Keep declining. The stated cost: graph and chart interaction stay human-verified only, at S25 and S35, with Node state tests in between. | S04, S18, S21, S25 |
| U6 | W01 initial direction: agent-drafted scope for human approval, and validated fluent synthesis. | Unchanged: proceed with the disabled candidate under the recommended "yes" branches as non-binding assumptions; enabling stays decision-blocked. | S37, S39 |
| U7 (extended) | Pilot email goes to one configured recipient through SMTP submission from an operator-supplied mailbox account. Multi-recipient preferences come later. | Yes, with SMTP submission. If the user has only an HTTP email API account, S29 uses it behind the same delivery-identity model. | S05, S29, S34, S40 |

Engineering choices, not user decisions: listed in 4d under the sequence.

External prerequisites, not decisions:

- a named marketer and a KR/JP reader for S08, S25 and S35;
- an operator mailbox account (U7);
- live accounts under U1.
