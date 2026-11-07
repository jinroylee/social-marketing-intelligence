VERDICT: YES — the review is worth accepting (fully or with modifications)

# Round-1 validation of the Task 4 spec review

Validated: `spec-review/round-1/review.md`, findings R1-F01 to R1-F14 and the reordering table in its section 3. Package under review: `task4/`. Paths are repository-relative. `specs/` means `.scratch/product-design-2026-11/task4/specs/`.

Method: I re-read every cited `file:line` myself in `src/`, `tests/`, `docs/`, `docs/adr/`, `tools/`, the specs, `plan.json` and the goal sources. I recomputed dependency depths from `plan.json`. I did not run the test suite, open a browser, use the network or call a provider. Old spec IDs are written `old-Sxx`. The revised IDs in section 4 are written `Sxx`.

Summary: the three code-level gaps the review found (R1-F01, R1-F02, R1-F05) are real and decisive. Without them, the campaign-first and chat journeys would be useless on automatically discovered data. The risk-inverted ordering (R1-F03, R1-F07, R1-F08) is also real. I accept most of the review, with these changes:

- Fewer new specs: one probe spec instead of four, two human checkpoints instead of four, a two-way split of old-S02 instead of three-way, no split of old-S06 or old-S14.
- Corrections to several overstated claims: no single token name is needed, "no new code" is wrong for probes, the gap-analysis wording is incomplete rather than wrong, and the freshness timer stays.
- Two ADR conflicts the review missed: ADR 0023 fixes one ten-post page, and ADR 0017 implies a single model influence per answer.
- A test-baseline problem the review missed: `--maxfail=1` hides the real state of roughly 600 tests.

## 1. Verdict

VERDICT: YES — the review is worth accepting (fully or with modifications).

## 2. Per-finding decisions

| Finding | Evidence re-verified | Decision | Change in one line |
| --- | --- | --- | --- |
| R1-F01 retrieval scale and question-blind chat | Yes, all cited lines | ACCEPT-MODIFIED | New S06: deterministic per-turn and brief scope only (no model-proposed terms in the pilot); index owned by ingestion; the graph also gets it (S14→S06) |
| R1-F02 no automated interpretation | Yes | ACCEPT-MODIFIED | New S05: interpret prepared support *before* the publication commit in the same fenced worker; needs a new support-based `prepare` port |
| R1-F03 live feasibility validated last | Yes, but "no new code" is wrong | ACCEPT-MODIFIED | One early probe spec (S04) with four capability rows; final readiness record S29 kept |
| R1-F04 no frontend foundation or client test strategy | Yes | ACCEPT-MODIFIED | New S03 client foundation (absorbs shell/nav/theme/i18n from old-S02); Node state tests; human browser checks run at checkpoints, not as per-spec human gates |
| R1-F05 no pilot configuration path | Yes; token-name claim overstated | ACCEPT-MODIFIED | New S02 configuration; recorded activations must stay recorded human actions; name each route's secret explicitly rather than force one name |
| R1-F06 monitoring depth and metric timing | Yes; missed ADR 0023 | ACCEPT-MODIFIED | New S16 within ADR 0023 (one page, cadence, saturation reporting, retrieval time recorded); measurement-time semantics becomes decision W02 blocking S21 only |
| R1-F07 artificial or inverted edges | Yes (depth 9 path confirmed) | ACCEPT-MODIFIED | Remove the listed edges, plus old-S16→old-S06; add S14→S06, S09→S05/S06/S02, S12→S06/S02; fill the empty edge rationales |
| R1-F08 human feedback only at the end | Yes | ACCEPT-MODIFIED | Two checkpoints (H1 real-data campaign and chat, H2 browser interaction for graph and chart) plus the final S30, not four |
| R1-F09 S01 under-scoped clock problem | Yes, and worse than stated | ACCEPT-MODIFIED | Inventory the whole suite without `--maxfail`; one relative-date helper; date-shift check limited to the Python fixture base |
| R1-F10 uneven sizes, overloaded S02 | Yes | ACCEPT-MODIFIED | Split old-S02 two ways, old-S10 (M1/M2) and old-S16 (plan model / named route); do not split old-S14 (move KR/JP packet preparation to S28); add sizes |
| R1-F11 hosted-grade machinery | Partly | ACCEPT-MODIFIED (partial) | Implement freshness once in S03 *including* the timer; S04 latitude and single-recipient S27 UI accepted; cursor and S15 receipt points rejected |
| R1-F12 chat usefulness and richer-agent path last | Yes | ACCEPT-MODIFIED | Retrieval fixed in the pilot (S06); W01 re-asked without blocking; drop S22→S21/S16 and S21→S20; extractive answer contract unchanged |
| R1-F13 S16 route undecided, gap wording | Facts yes; "inaccurate" overstated | ACCEPT-MODIFIED | Name the route in S26 (default: Bright Data profile/post detail); tiktok-web source use is a user decision; reword the gap row |
| R1-F14 legacy forms and D1 owner | Yes | ACCEPT-MODIFIED | D1 configuration UI goes to S20; each UI spec retires the forms it replaces after parity; no separate cleanup spec |
| Section 3 reordering table | Depths recomputed | ACCEPT-MODIFIED | Use the 40-row list in section 4a (10 net additions instead of about 17) |

### R1-F01: ACCEPT-MODIFIED

Verified:

- `QueryScope` defaults to `limit=100` with a maximum of 100 (`src/smi_knowledge/queries/store.py:24-40`).
- `publication_limit = 100` (`:129`). The search lists publications newest first (`:163-164`) and fills members until `scope.limit`, setting `result_limit_reached` (`:194-196`).
- Chat defaults to `QueryScope(limit=20, max_age_seconds=2592000)` and caps scope at 20 (`src/smi_assistant/store.py:60-61`). The question text is never turned into scope.
- Campaigns use `QueryScope(platforms=…, max_age_seconds=…)` with no text (`src/smi_campaigns/store.py:362`).
- `specs/07-conversations.md` never says how per-turn scope is derived. FR-B1 requires answers "from current permitted KB knowledge" (`docs/functional-requirements.md:34`), so this is a core-FR pilot gap, not depth work.

The review also missed that the graph has the same bound. `GraphScope.member_limit=100` feeds `QueryScope(limit=self.member_limit)` (`src/smi_knowledge/graph/store.py:34-40`). The "Neo4j-style" graph over a real KB would therefore show only entities reachable from the newest ≤100 members.

Modifications:

1. In the pilot, S06 derives per-turn and per-brief scope deterministically: normalized literal terms, CJK n-grams, and catalog alias→subject IDs. ADR 0017 says "one model select[s] only exact … IDs". A second, model-proposed term step would add another model influence on the answer that the ADR does not cover, so leave it to later S31.
2. Any text index sits on ingestion-owned columns through an ingestion migration and public port. `smi_knowledge/queries/AGENTS.md` forbids "a second source-value cache", and withdrawal must purge index content with the source.
3. S14 (graph pages) depends on S06.
4. Accept dropping old-S21→old-S20.

### R1-F02: ACCEPT-MODIFIED

Verified:

- The worker calls `publications.publish(support, actor, request_id=f'task:{task_id}', …)` without `interpretation_ids` (`src/smi_tasks/worker.py:343`). The parameter exists (`src/smi_knowledge/publications/store.py:41-42`).
- `KnowledgeStore.prepare` is called only from the manual CLI (`src/smi_ingestion/cli.py:290`) and from frozen-dataset review paths (`src/smi_review/app.py:648`, `:715`). The only caller that passes `interpretation_ids` is the CLI (`src/smi_ingestion/cli.py:256`).
- Members without claims are flagged `caption_interpretations_not_published` (`queries/store.py:120-121`). Brand and product criteria default to `state = "unknown"` without supported claims (`src/smi_campaigns/comparison.py:81-90`).

Two implementation facts the review did not see change the design:

- `KnowledgeStore.prepare(dataset_id, catalog_id, …)` reads a *frozen evidence set* (`src/smi_knowledge/store.py:129-139`). Task runs are not frozen datasets, so a new port that prepares interpretations over exact `SupportReference`s is required.
- The review proposed publishing interpretations "as a successor publication". That would make the same observation appear twice in query results, because the query de-duplication identity includes claim IDs (`queries/store.py:189-193`).

So S05 interprets the prepared support inside the same `TaskExecution` before the publication transaction and publishes members and claims together. If interpretation fails, the members still publish, with an explicit `interpretation_failed` state. Any later re-interpretation publishes a successor publication, and the query owner then de-duplicates by observation, preferring the newest current publication. This is deterministic rule work with no external I/O, so the fenced worker can do it without runtime registration.

### R1-F03: ACCEPT-MODIFIED

Verified:

- In `plan.json`, old-S19 depends on old-S13, S14, S16, S17 and S18. Computed depths: S19 is 8 and S20 is 9.
- Old-S13 requires measurement-age capability (`specs/13-engagement-anomalies.md` scope).
- Old-S16 requires "at least one verified supplementary route" without naming it.

The claim "probing them needs credentials and authorization, not new code" is only true for Bright Data keyword discovery (`run-live-discovery-task`, `src/smi_ingestion/cli.py:211-214`):

- The model and live X cannot be configured outside tests. No `src/` code constructs `ResponsesRoute(` or a non-default `LiveXConfig(`, and `smi-review` `main` passes no model route (`src/smi_review/server.py:131`). That is why the probes depend on S02.
- No email transport exists at all, so an early email row can only settle provider acceptance and idempotency semantics and sender readiness. The real product send stays in S29.

Use one probe spec, S04, with independently completable capability rows rather than four specs. That keeps the authorization request and record format in one place without adding nodes. Keep the final per-capability readiness record as S29.

### R1-F04: ACCEPT-MODIFIED

Verified:

- The client is one 56-line `review.js` plus `review.css`. There is no `package.json`.
- `tools/check.py` runs only ruff, the docs check and pytest (`:33-43`).
- Agent browser access is declined (`task4-brief.md`, "Actual approval").
- The central old-S09/S11 checks are browser-only (old-S09-A01/A04; old-S11-A04). Old-S02 offers only "bundled browser JS and CSS".
- Node v25 is available locally.

Modifications:

- Split old-S02 two ways. S03 holds the client foundation plus shell, navigation, theme and the i18n *mechanism*. S08 holds the campaign index and detail plus the shared governed inspector. The review's three-way split makes F0→S02a→S02b a serial chain with no parallel benefit.
- Library versus hand-built layout is an engineering choice owned by S03, not a user decision.
- Each UI spec *prepares* a short human browser checklist as a build deliverable. A human executes it at H1, H2 or S30. Requiring a human for every UI spec's completion would blur the build/human lane separation that the review itself asks to keep (review §4).
- Scoped headless-browser testing is a genuine user decision (U5).

### R1-F05: ACCEPT-MODIFIED

Verified: the server wiring (`server.py:131` versus `app.py:110-113`), the test-only constructors, and the disabled default `LiveXConfig()` (`src/smi_monitoring/polling/store.py:33`).

Corrections:

1. The two Bright Data variables are not an accidental mismatch. `docs/user-guide.md:942` documents `BRIGHT_DATA_API_TOKEN` (keyword route) as deliberately distinct from `BRIGHTDATA_API_TOKEN` (older direct adapter). S02 should name each route's secret variable explicitly in one schema and report a missing one as a named readiness gap. It may add an alias, but a single name is not required.
2. The review's "authority opt-ins" must not turn recorded human activations into configuration. `RecentPolling` states that "no daemon or environment key confers activation" (`polling/store.py:26-28`). ADR 0015 (recorded live schedule authority) and ADR 0023 (one explicit operator activation per topic revision) require recorded actions. S02 configures routes, credentials, process gates, thresholds and caps. Topic activation and live schedule activation remain recorded operator commands.

### R1-F06: ACCEPT-MODIFIED

Verified:

- `MAX_RECORDS = 10` and one page with `max_results` 10 (`src/smi_monitoring/polling/route.py:21-24`, `:79-89`).
- The seven-day limit (`:84`).
- `next_token` is "not authority to fetch" and "metric measurement times remain unknown" (`docs/monitoring.md:166-168`).
- `collection_incomplete` (`src/smi_monitoring/alerts/store.py:54-55`).

The review missed that ADR 0023 (accepted and implemented) states: "Only the first ten-post page is collected. A remaining page … stays a coverage limitation rather than triggering a pagination loop." Bounded multi-page collection therefore needs a successor ADR and more recurring paid authority. The goal keeps ADR invariants in force, and the extra spending is the user's call (U3).

S16 therefore stays inside ADR 0023:

- configurable shorter cadence, with probe data choosing the value,
- an explicit `collection_saturated` limitation whenever `next_token` is present, so volume and shift over saturated windows are reported as bounded and not as complete counts,
- recording the successful-response receipt time on metric support as `metrics_retrieved_at`, a fact rather than a source timestamp.

Treating that receipt time as the matched-age *measurement* time changes the documented evidence semantics. It is decision W02, with a recommended default, and it blocks only S21 (engagement). Old-S13 drops its old-S11 dependency.

### R1-F07: ACCEPT-MODIFIED

Recomputed: the longest `plan.json` path is S01→S02→S04→S05→S10→S11→S13→S19→S20 (9). The stated "main chain" in `implementation-sequence.md:58` (8) is not the longest.

I accept every removal in the review's table:

- S13/S14→S11
- S10→S05
- S18→S17/S07/S10
- S19→{S13, S14, S16, S17, S18}
- S20 on everything except checkpoints and readiness
- S06→S03, which only exists for the `campaign.recommend` tool; that tool can wrap the installed `CampaignStore.recommend`/`CampaignRecommendations.regenerate`
- S07→S06
- S16→S15/S05
- S17→S10/S15
- S12→S04, S15→S04
- S21→S20, S22→S21
- S08→S02

Differences from the review:

- Also drop old-S16→old-S06. The plan model's successor-approval path uses installed `AcquisitionTasks` proposal operations, and the A1 UI integration becomes a conditional check.
- Keep S27 (inbox/email)→S07 (runtime), so one spec owns delivery registration.
- Add edges the review omitted: S14→S06 (graph seeds), S09→S05/S06/S02 (real mention judgments, scale, model composition) and S12→S06/S02.

Note that every `plan.json` spec has an empty `rationale: {}`. No edge in the current plan has a recorded reason, and section 4a supplies one per edge.

### R1-F08: ACCEPT-MODIFIED

Verified: old-S20 blocks on S09, S11, S13, S14, S18 and S19 and covers every journey. The only human input so far is approval of the r2 fixture prototype (`ui-review-status.md:23`).

Four checkpoints add process load for one pilot marketer. Two capture most of the value:

- **H1 (S13): brief→shortlist and chat on real discovered data.** This tests the R1-F01 and R1-F02 premises with a marketer early.
- **H2 (S23): real-browser interaction of the graph and history chart.** These are the two client behaviors agents cannot verify while browser access stays declined.

The monitoring alert journey, spending, inbox/email and lineage remain in the final S30.

### R1-F09: ACCEPT-MODIFIED

Verified: commits `ecc011f` and `a70341a` are prior fixture-aging fixes. My grep found 207 hard-coded September/October 2026 date matches in 33 test files (the review said 192 in 30; same order).

The review missed a larger problem. `tools/check.py:42` runs `pytest --maxfail=1`, and the suite has about 652 test functions in 47 files. The inherited "51 passed, 1 failed" baseline (`gap-analysis.md:42`) therefore says nothing about roughly 600 tests after the first failure. Old-S01's "change only the fresh-evidence scenario" cannot be shown to produce a green baseline.

S01 must first run the full suite without `--maxfail` to inventory every failure. Then it fixes the clock-aging class with one relative-date or controlled-clock test helper, without changing product freshness, retention or window policy. A full +365-day time-travel harness covering PostgreSQL `now()` is not cheap without new tooling. The date-shift check is therefore limited to fixtures built from the helper's base offset, and any test that depends on database `now()` uses relative SQL intervals.

### R1-F10: ACCEPT-MODIFIED

Verified:

- Old-S02 bundles the shell, catalogs "complete EN/KO" (impossible before later screens exist), `/api/v1` and the freshness contract.
- Old-S10 carries 17 requirement IDs across two owner sets: recent/polling/alerts versus context/promotion/snapshot.
- Old-S16 combines a plan/step engine with an unnamed new route.

Accepted splits:

- old-S02 into S03 and S08 (two ways, see R1-F04),
- old-S10 into S17 (M1) and S19 (M2), so the chart can start after M1,
- old-S16 into S25 (plan model) and S26 (named route), so the route choice can wait for probe evidence without blocking the engine.

Rejected: splitting old-S14. Its only separable part, KR/JP evaluation-packet preparation (old-S14-A04), belongs to the quality-packet owner, so it moves to S28. Add an S/M/L `size` field to `plan.json`.

### R1-F11: ACCEPT-MODIFIED (partial)

Accepted:

- Implement the `display_valid_until` behavior once in S03 as a shared client utility with its own tests. UI specs reference it and keep one integration check instead of re-accepting the whole contract four times.
- S10 (old-S04) may derive progress from existing `acquisition_attempts.phases` (`src/smi_tasks/schema.sql:59`, a phase list without per-phase timestamps). It adds an event table only where a resumable cursor or timestamps are missing. The acceptance checks stay; the storage choice belongs to the owner.
- S27 pilot UI manages one configured recipient. Keep the recipient-plus-channel logical key and attributable reissue, which is the only safe recovery after an ambiguous send.

Rejected:

1. Moving the freshness timer to S25. Once centralized, a bounded revalidation timer is cheap, and it is part of the documented shared contract (`architecture-target.md:73`).
2. Weakening old-S08 cursors. Binding a cursor to search, root, filter and frontier is a correctness requirement for stale-page rejection, and the extra workspace/requester binding is a few lines.
3. Removing old-S15 receipts. Exposing trusted Python accounting operations through browser forms needs retry-safe command receipts against double submission.

### R1-F12: ACCEPT-MODIFIED

The chain S21(→S18, S20)→S22(→S06, S07, S16, S21) is confirmed. W01 says "actual direction can constrain candidate work" and was deferred (`wayfinder/issues/001-richer-agent-boundary.md`, Comments).

Accepted:

- fix retrieval in the pilot (S06),
- drop S22→S21, S22→S16 and S21→S20,
- re-ask W01 as a non-blocking user decision (U6), with "W01 initial direction" as an *informing* prerequisite of S32 rather than a decision blocker,
- keep S34 (old-S24) decision-blocked.

The extractive answer contract does not change. The user's "typical, regular chatbot ui" request was met by the r2 *UI*, which the user approved ("I love it"), and ADR 0017 governs answer content.

### R1-F13: ACCEPT-MODIFIED

Verified:

- `default_registry()` registers `tiktok-oembed`, `brightdata-tiktok` and `tiktok-web` (`src/smi_ingestion/adapters/registry.py:29-37`).
- oEmbed declares post history, follower, view and engagement counts unavailable (`tiktok_oembed.py:26-29`).
- `tiktok-web` is a "direct public-page experiment" with WAF markers and post metrics (`tiktok_web.py:1-5`, `:31-36`).

"Inaccurate" overstates it. `gap-analysis.md:36` says unsupported routes "remain unavailable", and old-S12 already says to describe "other existing adapters truthfully". The gap wording is incomplete rather than wrong: these adapters exist for supplied references but are not task-integrated.

Naming the route is accepted. S26's default is Bright Data profile/post detail fields: same vendor, account and cost-binding family as the keyword route, and the nickname transport already exists in `BrightDataTransport.fetch_profile_field`. `tiktok-web` stays unavailable unless the user grants source use (U4). oEmbed is limited to identity and title.

### R1-F14: ACCEPT-MODIFIED

Verified: `architecture-target.md:56` keeps the form routes, and no spec retires them. The D1 owner is split across old-S05 ("operations screens"), old-S12 ("exposes D1") and old-S16.

Changes:

- S20 owns the D1 configuration UI: ten-keyword limit, activation, day allowance, route health and selection basis.
- S07 owns only runtime health.
- Each UI spec retires the legacy English-only form routes and views it replaces once parity tests pass ("parity-then-remove"). A separate cleanup spec at the end would keep two UIs alive for the whole build.

### Section 3 reordering table: ACCEPT-MODIFIED

The direction is right. Use section 4a instead. Its differences from the review's table:

- one probe spec,
- H1/H2 instead of H1-H4,
- no split of S06 or S14,
- graph reads depend on retrieval,
- the plan model does not wait for the A1 UI.

The review's "five build specs deep" claim excluded the validation specs. In section 4a:

- the main journeys reach completion at depth 4: S09 campaign, S12 chat, S15 graph,
- the chart (S18) and engagement (S21) are at depth 5,
- the deepest pilot build spec is S26 at depth 6,
- live probes are at depth 3 and the first real-data human checkpoint (S13) at depth 5,
- the final readiness and release records are at depths 7 and 8, compared with 8 and 9 before.

The main gain is risk ordering and parallel width, not raw depth.

## 3. Material issues the review missed

1. **The baseline is unknown beyond the first failure.** `tools/check.py:42` uses `--maxfail=1` on a suite of about 652 tests, so the recorded 51/1 result covers about 8% of it. S01 must inventory the full suite (see R1-F09).
2. **The graph has the same 100-member bound** (`graph/store.py:34-40`). S06 must cover graph seed selection, and S14 depends on it.
3. **ADR 0023 fixes one ten-post page.** The review's multi-page option needs a successor ADR and user agreement to spend more (U3). S16 works within the ADR by default.
4. **S05 needs a new interpretation input port**, because `prepare` reads frozen datasets (`knowledge/store.py:129-139`). A successor publication would duplicate query members, because the de-duplication identity includes claim IDs (`queries/store.py:189-193`). S05 interprets before the publication commit.
5. **ADR 0017 ("one model select[s] only exact … IDs") is compatible with deterministic per-turn scope.** Model-proposed retrieval terms would need an ADR amendment, so they stay later (S31).
6. **Configuration must not confer activation** (`polling/store.py:26-28`; ADRs 0015 and 0023). S02 must keep recorded activations as recorded human commands.
7. **The early probes are not code-free.** The model and live X need S02 composition. Email has no transport, so its early row covers provider semantics only.
8. **`plan.json` has empty `rationale` objects for all 30 specs.** No dependency edge records why it exists, which is partly how the artificial edges in R1-F07 survived. Section 4a supplies one rationale per edge.
9. **The current search does a full `publications.read` of each of up to 100 publications per query** (`queries/store.py:168-176`). Raising the bounds without an indexed selection would make every chat turn and comparison slower as the KB grows. S06 needs an explicit latency and work bound.
10. **Minor:** `UD-09` (the pre-Task-4 UI review gate) has an empty spec list in `traceability.json`. Record it as "satisfied by the actual r2 approval; no spec" rather than leaving it empty.

## 4. Revision suggestion

### 4a. Revised ordered spec list

Lanes are as defined in the task. Sizes: S = up to a few days, M = about one week, L = multi-week. "Ext" lists a human or external prerequisite that is not a spec edge. Old IDs are given for mechanical renaming. Every edge has its own rationale. All dependencies precede their consumers.

| ID | Slug | Title | Lane | Size | Direct deps | Rationale per edge | Old ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | stable-verification-clock | Restore a complete, time-stable verification baseline | pilot-build | M | — | — | old-S01 (rescoped) |
| S02 | pilot-configuration | Compose the local pilot from one validated configuration | pilot-build | M | S01 | S01: config changes touch every composition root and need a trustworthy full-suite result | new (R1-F05) |
| S03 | client-foundation | Establish the bilingual client foundation, shell and client verification | pilot-build | L | S01 | S01: adds Node checks to the shared check, which must be green first | new, split from old-S02 (R1-F04) |
| S04 | live-feasibility-probes | Probe bounded live model, discovery, X and email-provider feasibility early | live-validation | M | S02 | S02: model and live-X routes, credentials and caps are only constructible through the pilot configuration | new, split from old-S19 (R1-F03). Ext: bounded live authorization and credentials (U1) |
| S05 | automated-interpretation | Publish catalog-scoped caption interpretations from automated tasks | pilot-build | M | S01 | S01: changes task publication behavior covered by the existing worker suites | new (R1-F02) |
| S06 | pilot-scale-retrieval | Select question-, brief- and graph-scoped governed support at pilot scale | pilot-build | L | S01 | S01: changes query bounds exercised across the campaign, assistant and graph suites | new (R1-F01) |
| S07 | local-runtime | Run bounded local work continuously with restart and health | pilot-build | L | S02 | S02: the runtime reads routes, gates, budgets and cadence from the validated configuration | old-S05 |
| S08 | workspace-and-evidence | Open saved campaigns and inspect governed evidence in the shared inspector | pilot-build | M | S03 | S03: needs the shell, API client/envelope, i18n mechanism and freshness utility | old-S02 (remainder) |
| S09 | campaign-decisions | Complete brief to saved recommendation and explicit regeneration | pilot-build | L | S08, S06, S05, S02 | S08: C1 renders evidence through the shared inspector and campaign index. S06: the candidate pool must reach eligible creators beyond the newest 100 members. S05: brand/product criteria need published interpretations on discovered support. S02: model ranking and criteria interpretation must be operable from the shipped server | old-S03 |
| S10 | task-events-lineage | Read asynchronous progress and exact pipeline lineage | pilot-build | S | S08 | S08: the T1 timeline opens lineage evidence in the shared inspector | old-S04 (slimmed) |
| S11 | exact-approval-tools | Review exact enrichment scope and expose governed agent operations | pilot-build | M | S10, S08 | S10: approve/submit receipts and the `task.status/events` tools read the progress feed. S08: A1 scope review shows exact evidence and limits in the inspector | old-S06 |
| S12 | conversations | Save conventional chat threads with question-scoped extractive turns | pilot-build | L | S08, S06, S02 | S08: per-turn sources open in the shared inspector. S06: each turn's pinned retrieval scope comes from the question. S02: the shipped server needs the configured model route | old-S07 |
| S13 | early-marketer-checkpoint | Check brief→shortlist and chat with a marketer on real discovered data | human-validation | S | S04, S07, S09, S12 | S04: requires passed Bright Data keyword and model probe rows (real data and model). S07: discovery must run automatically, not by hand. S09: the brief→shortlist journey under test. S12: the chat journey under test | new, split from old-S20 (R1-F08). Ext: marketer and KR/JP reader |
| S14 | graph-reads | Page governed graph branches with stable identities and policy frontiers | pilot-build | M | S06 | S06: graph seeds and continuation must use pilot-scale selection, not the newest 100 members | old-S08 |
| S15 | interactive-graph | Explore the production graph with camera, pins and incremental branches | pilot-build | L | S14, S08 | S14: consumes branch pages, cursors and generations. S08: selection opens the shared inspector (the S03 vendored layout and client modules come through S08) | old-S09 |
| S16 | monitoring-depth-and-timing | Make monitoring saturation, cadence and metric retrieval time explicit | pilot-build | M | S02 | S02: cadence, saturation and cost bounds are validated configuration | new (R1-F06) |
| S17 | monitoring-workspace | Operate independent topics, activation and alert history | pilot-build | M | S08 | S08: M1 renders windows and alerts through the shell and inspector | old-S10 (M1 half) |
| S18 | monitoring-history | Plot current and selected monitoring windows without fabricated data | pilot-build | M | S17 | S17: the chart is a view of topic windows and alert history composed in M1 | old-S11 |
| S19 | alert-investigation-promotion | Investigate alerts with existing KB context and promote selected evidence | pilot-build | S | S17 | S17: investigation and promotion start from an alert and window selected in M1 | old-S10 (M2 half) |
| S20 | source-capabilities | Describe usable source routes, bounded selection and D1 schedule configuration | pilot-build | M | S08, S02 | S08: D1 and capability screens use the shell and inspector. S02: the readiness read extends the configuration's source-free readiness | old-S12 (+D1 UI) |
| S21 | engagement-anomalies | Detect supported engagement changes with comparable measurement ages | pilot-build | M | S16, S20 | S16: matched-age comparison consumes the recorded `metrics_retrieved_at` and saturation fields. S20: metric capability per route comes from the registry. Decision blocker: W02 (live-X measurement semantics; default in 4e) | old-S13 |
| S22 | semantic-shift | Detect provisional semantic shifts with a comparable baseline | pilot-build | L | S01 | S01: extends the installed semantic owner whose suites must be green; chart and alert integration are conditional checks | old-S14 (packet preparation moved to S28) |
| S23 | interaction-checkpoint | Check graph and history-chart interaction in a real browser | human-validation | S | S15, S18 | S15: graph drag/pin/branch/stale-page behavior under test. S18: chart latest/selected/gap behavior under test | new, split from old-S20 (R1-F08). Ext: human browser session |
| S24 | spending-operations | Inspect and operate independent spending controls | pilot-build | M | S08 | S08: S1 forms render in the shell with governed reads | old-S15 |
| S25 | progressive-acquisition | Plan finite field-capability acquisition steps and stop honestly | pilot-build | L | S20 | S20: steps are planned only over declared route/field capability and selection policy | old-S16 (plan/step half) |
| S26 | supplementary-detail-route | Task-integrate one named supplementary detail route | pilot-build | M | S25 | S25: the route executes as plan steps under the plan model's scope and stop rules. Ext: S04 Bright Data row informs the fields; U4 for any web route | old-S16 (route half) |
| S27 | inbox-email | Deliver durable task and alert notifications through inbox and email | pilot-build | L | S07, S02, S08 | S07: `Delivery.run_due` is registered as a runtime component. S02: recipient, sender, link and transport configuration. S08: the inbox renders in the shell with governed links | old-S17 |
| S28 | plans-and-quality | Preserve measurement planning and prepare attributable KR/JP quality packets | pilot-build | M | S09 | S09: plans and notes bind to exact brief/shortlist revisions produced by C1 | old-S18 (+old-S14-A04) |
| S29 | provider-readiness | Record actual per-capability provider, billing, recurrence and send readiness | live-validation | M | S04, S07, S21, S22, S24, S26, S27 | S04: reuses the probe authorizations and findings. S07: the recurring-work row needs the runtime. S21: the X engagement row. S22: the semantic model row. S24: the billing reconciliation row needs operator controls. S26: the supplementary route row. S27: the email send row | old-S19 (rescoped) |
| S30 | human-pilot-acceptance | Record pilot release acceptance on live data | human-validation | M | S11, S13, S19, S23, S28, S29 | S11: the approved-research→later-question journey. S13: H1 findings and fixes. S19: the alert→KB-context journey. S23: H2 findings and fixes. S28: KR/JP adjudication packets. S29: usefulness must be judged on live, ready capabilities | old-S20 (rescoped) |
| S31 | evaluated-retrieval | Improve multilingual retrieval with pinned, rebuildable support | later-core-depth | L | S06, S28 | S06: the deterministic baseline to beat. S28: held-out bilingual evaluation packets | old-S21 |
| S32 | agent-candidate | Prepare a bounded research and synthesis candidate for decision review | later-candidate | L | S11, S12 | S11: draft research compiles to exact proposal/approval operations and tools. S12: candidate turns live in conversation records. Ext (informing, non-blocking): W01 initial direction | old-S22 |
| S33 | agent-human-evidence | Obtain actual adjudication for the richer-agent successor | human-validation-later | M | S32 | S32: adjudicates the candidate's outputs | old-S23 |
| S34 | enable-richer-agent | Enable only the accepted grounded research and synthesis contract | decision-blocked | L | S33 | S33: acceptance needs actual adjudication evidence. Decision blocker: W01 | old-S24 |
| S35 | hosted-actors-tenancy | Move the proven pilot to authenticated workspace tenancy | later-proposal | L | S30 | S30: hosting follows an accepted local pilot | old-S25 |
| S36 | projection-governance | Reconcile retained copies and rebuildable projections with operational recovery | later-proposal | L | S31, S35 | S31: governs the retrieval index and projections it introduces. S35: managed storage, secrets and restore are hosted concerns | old-S26 |
| S37 | multimodal-ontology | Add evidenced multimodal and richer ontology concepts | later-proposal | L | S31, S36 | S31: new concepts need evaluated retrieval. S36: retained copies must already reconcile | old-S27 |
| S38 | objective-portfolios | Compare objective-specific creator factors and feasible portfolios | later-proposal | L | S31, S37 | S31: factor retrieval depth. S37: richer creator concepts | old-S28 |
| S39 | outcomes-attribution | Measure actual outcomes and rule-based attribution | later-proposal | L | S28, S35, S36 | S28: proposed measurement plans to observe against. S35: outcome data needs tenant access. S36: governed retention of outcome copies | old-S29 |
| S40 | causal-measurement | Estimate incremental effect only under an accepted causal design | later-proposal | L | S39 | S39: needs observed outcomes and attribution | old-S30 |

Old-to-new mapping summary: old-S01→S01; old-S02→S03+S08; old-S03→S09; old-S04→S10; old-S05→S07; old-S06→S11; old-S07→S12; old-S08→S14; old-S09→S15; old-S10→S17+S19; old-S11→S18; old-S12→S20; old-S13→S21; old-S14→S22; old-S15→S24; old-S16→S25+S26; old-S17→S27; old-S18→S28; old-S19→S04+S29; old-S20→S13+S23+S30; old-S21..S30→S31..S40. New: S02, S05, S06, S16.

Decisions in `plan.json`:

- keep W01 (blocks S34),
- add W02 "Live X metric measurement-time semantics" (blocks S21; recommended default in 4e),
- U3 (X collection depth) is a user decision that blocks nothing; the default keeps ADR 0023.

### 4b. New, split and materially changed specs

Cross-cutting rule for every UI-bearing spec (S08, S09, S10, S11, S12, S15, S17, S18, S19, S20, S24, S27, S28):

- Replace the repeated `-A05` freshness acceptance with "uses the S03 freshness utility; one integration check that revoked support disappears on the next successful revalidation".
- Add "retire the legacy form routes and views this screen replaces after parity tests pass, and migrate their tests".
- Add "add EN/KO catalog keys for this screen; the S03 completeness check passes".
- Add "deliver a short human browser checklist, executed at S13, S23 or S30, not as a build-completion gate".

**S01 stable-verification-clock (rescoped).**

- Outcome: a complete, attributable baseline in which no test depends on the real calendar date.
- Scope: run the whole suite once without `--maxfail` against real PostgreSQL; classify every failure (clock-aging versus other); add one shared relative-date/controlled-clock test helper; convert freshness-, retention-, seven-day-window- and accounting-period-sensitive fixtures to it; use relative SQL intervals where the database clock decides.
- Non-goals: no product policy change; no time-travel tooling for the PostgreSQL server.
- Owner: test infrastructure.
- Acceptance:
  1. The full-suite inventory is recorded with exact failures.
  2. All clock-aging failures pass, and the `src/` diff contains no freshness, retention or window constant change.
  3. The clock-sensitive subset passes with the helper base shifted +90 days.
  4. Stale and unknown-capture cases still report explicit limitations.
  5. `uv run --locked python tools/check.py` passes, and the `docs/development.md` limitation section is updated.

**S02 pilot-configuration (new).**

- Outcome: one operator can start the review server, runtime and CLIs against simulated or provider routes from one validated, versioned local configuration.
- Scope:
  - a TOML or JSON file with secrets referenced only by environment variable names,
  - explicit simulated/provider classification for the model, X recent, Bright Data keyword/profile and email routes,
  - process gates, thresholds, caps, cadence defaults and an interpretation catalog bound,
  - a source-free `readiness()` read,
  - one `compose(config)` used by `smi-review` `main`, the runtime and the CLIs, which wires `ResponsesRoute`, `LiveXConfig` and the Bright Data routes,
  - the exact secret variable name per route, with a named "missing secret" diagnostic and an optional alias for the two Bright Data names.
- Non-goals: hosted secrets management; any configuration that confers topic activation or live schedule authority (those stay recorded human commands under ADRs 0015 and 0023).
- Owner: `smi_review` composition root plus a small configuration module.
- Acceptance:
  1. An invalid or unknown key, or a missing referenced secret, fails start-up with a sanitized named reason.
  2. With a simulated model configured, the shipped server runs ranked recommendation, criteria interpretation and a knowledge answer end to end.
  3. With live X configured but no recorded activation, no X request is dispatched.
  4. `readiness()` never exposes secret values or handles.
  5. Existing CLI flags keep working or map one-to-one, with documentation updated.

**S03 client-foundation (new, from old-S02).**

- Outcome: every later UI spec builds on one tested client structure.
- Scope:
  - plain ES modules served from `smi_review/static` with no build step,
  - one recorded engineering decision on graph layout and rendering. Recommended: a vendored, pinned, licence-recorded graph library (for example Cytoscape.js) with a SHA-256 in the repository, because a hand-built incremental force layout with pinning is multi-week work. The chart is plain SVG.
  - an API client with envelope parsing, CSRF, request-ID generation and retry kinds,
  - the versioned `/api/v1` adapter framework,
  - the i18n catalog mechanism (catalogs grow per spec),
  - shell, navigation, the four-colour theme and the EN/KO switch,
  - the shared `display_valid_until` freshness utility (focus, navigation, explicit read and bounded timer; fail closed at the deadline; a stale response never restores),
  - reducer modules for graph branch/generation, chart series and composer/draft/IME state, tested with `node --test` from `tools/check.py` (CI installs Node; `docs/development.md` lists it).
- Non-goals: framework rewrite; CDN dependencies; browser automation.
- Acceptance:
  1. `tools/check.py` runs the Node tests and fails on a broken reducer.
  2. The graph reducer discards a late page with a mismatched generation and keeps shared members when one of two overlapping branches collapses.
  3. The composer state never sends during IME composition, and Shift+Enter inserts a newline.
  4. The freshness utility withholds content at `display_valid_until` without successful revalidation and ignores an older response.
  5. The catalog completeness check fails on a missing KO key, and the EN/KO switch preserves inputs and IDs over loopback HTTP.

**S04 live-feasibility-probes (new, from old-S19).**

- Outcome: the premises of S16, S21, S26 and S27 are settled by bounded real evidence before those specs finish.
- Scope: one capability row each, independently completable:
  - model: schema adherence, latency, cost basis;
  - Bright Data keyword: fields, capture times, cost basis, KR/JP yield;
  - X recent: posts per window, `next_token` frequency, `public_metrics` fields and timing, counts-endpoint availability for the account tier;
  - email provider: acceptance and idempotency semantics, sender-domain readiness. No product send, because no transport exists yet.
- Each row records operator, authorization, caps, configuration digest, request/response/evidence IDs, billing basis and unresolved portions, using the S29 record format.
- Non-goals: production readiness claims; fixture substitution.
- Owner: operator plus the relevant owner modules.
- Ext: U1.
- Acceptance:
  1. Each row has an actual authorized receipt or an explicit refused/blocked state.
  2. The X row records saturation and metric fields that feed the S16 configuration and the W02 decision.
  3. The Bright Data row names candidate S26 detail fields.
  4. The billing basis reconciles against the commitments or is recorded as unknown.

**S05 automated-interpretation (new).**

- Outcome: task-discovered posts carry published brand/product interpretations, so C1 criteria and graph mention edges work on real data.
- Scope:
  - a new `KnowledgeStore.prepare_support(support: tuple[SupportReference,...], catalog_ids, actor, *, request_id, connection)` reading exact support through `smi_ingestion.support` (the existing `prepare` reads frozen datasets only),
  - the worker interprets prepared support against the workspace's active catalogs (bounded by S02) inside its `TaskExecution`, before the publication transaction, and publishes with `interpretation_ids`,
  - on failure it publishes the members anyway with `interpretation_status=failed` on the task coverage,
  - an explicit re-interpretation creates a successor publication, and queries de-duplicate the same observation/derivation by keeping the newest current publication,
  - the idempotent request ID is task + catalog + method version.
- Non-goals: model-based interpretation; new catalog semantics.
- Owner: `smi_knowledge` (port) and `smi_tasks` worker. Update `docs/knowledge.md`, `docs/tasks.md` and the ERD if schema changes.
- Acceptance:
  1. A keyword task over a corpus that mentions a registered brand yields supported claims in the query result, and the member is no longer flagged `caption_interpretations_not_published`.
  2. A forced interpretation failure still publishes the members and shows `interpretation_failed`.
  3. A re-interpretation never produces duplicate members in search.
  4. A crash between interpretation and publication recovers without duplicate claims.
  5. A withdrawn source purges its interpretation copies.

**S06 pilot-scale-retrieval (new).**

- Outcome: chat, campaign comparison and graph seeds select relevant permitted support from a KB much larger than 100 publications, with explicit, reported bounds.
- Scope:
  - an indexed selection port owned by ingestion (governed text and normalized-term index on ingestion-owned columns, purged with the source) used by `KnowledgeQueries`,
  - configurable member and scan bounds with keyset continuation, reported in coverage,
  - a deterministic per-turn scope derived from the question (NFKC normalization, literal terms, CJK n-grams, catalog alias→`subject_ids`), pinned in the answer/turn record,
  - a brief-driven, account-centric candidate selection for `prepare_current_comparison`,
  - `GraphScope` seeds use the same port.
- Non-goals: embeddings and semantic ranking (S31); model-proposed terms (ADR 0017).
- Owner: `smi_knowledge.queries` with an `smi_ingestion` index migration. Update `docs/knowledge.md`, `queries/AGENTS.md` and the ERD.
- Acceptance:
  1. On a fixture KB of at least 1,000 published posts across at least 200 publications, a question about a brand published only in old publications returns that support, with derived terms pinned.
  2. A comparison includes an eligible creator whose only support is older than the newest 100 members, and its coverage reports the actual scan bounds.
  3. Withdrawing a source removes it from the index and from new results; a historical result reopens exactly.
  4. Per-query work stays inside the configured bound, with a recorded latency budget on the reference fixture.
  5. Exact retries remain digest-stable.

**S08 workspace-and-evidence (remainder of old-S02).**

- Scope: campaign index/detail reads (`ReviewWorkspace.campaigns`/`evidence`), the shared governed inspector (observed/derived/human bases, dates, conflicts, full-input membership, truncation, availability), and the EN/KO keys for these screens.
- Keep old-S02 checks A01, A03 and A04. Replace A02 with "the EN/KO switch preserves brief input and IDs on these screens". Replace A05 per the cross-cutting rule.
- Requirement IDs: PROP-01, PROP-15, UD-01.

**S09 campaign-decisions.** Old-S03 unchanged, except it adds two acceptance checks:

- a shortlist over task-discovered support shows real supported or unknown brand/product judgments (S05),
- a comparison over a KB of more than 100 publications reports its scan bounds and includes an older eligible creator (S06).

**S10 task-events-lineage.** Same acceptance as old-S04. The owner may implement `events()` over the existing `acquisition_attempts.phases` and adds a table only where cursor or timestamp requirements are unmet.

**S11 exact-approval-tools.** Old-S06 with `campaign.recommend` wrapping the installed `CampaignRecommendations.regenerate`/`CampaignStore.recommend`. Its dependency on old-S03 is removed.

**S12 conversations.** Old-S07 plus:

- each turn pins the S06-derived scope,
- research-status disclosure is a conditional check, verified once S11 exists.

Added acceptance: two different questions over the same KB of more than 100 publications select different, relevant support, and the pinned scope reopens exactly.

**S13 early-marketer-checkpoint (new).**

- Outcome: real-data usefulness defects in the two headline journeys surface while they are cheap to fix.
- Scope: one marketer completes brief→shortlist and three chat questions on automatically discovered live data, in EN and KO. The session records exact build/config identity, outputs, failures and corrections.
- Not a release gate.
- Acceptance:
  1. A named reviewer, build identity and data provenance (live, not fixture) are recorded.
  2. Each journey has a pass/fail with failing examples kept.
  3. Each defect is filed against its owning spec.

**S14 graph-reads.** Old-S08 with seeds from S06. Its dependency on old-S02 is removed, because the HTTP adapter route is owned by S15.

**S15 interactive-graph.** Old-S09, using the S03 vendored layout and graph reducer. The browser-only checks (old-S09-A01 to A04) become the S23 checklist. Node reducer tests stand in for build acceptance.

**S16 monitoring-depth-and-timing (new).**

- Outcome: live monitoring states truthfully how complete each window is and when metrics were retrieved, inside ADR 0023.
- Scope:
  - a `collection_saturated` limitation when `next_token` is present, carried into volume, chart and semantic method limitations,
  - configurable cadence with probe-informed values and cost bounds,
  - `metrics_retrieved_at` recorded on recent metric support as the successful-response receipt time (documented as retrieval time, not a source or measurement timestamp),
  - a proposed W02 ADR text for S21.
- Non-goals: pagination beyond one page (U3); recomputing old windows.
- Owner: `smi_monitoring.polling` and `recent`. Update `docs/monitoring.md` and the ERD.
- Acceptance:
  1. A simulated response with `next_token` yields `collection_saturated` on the window and on dependent volume and chart reads.
  2. A shorter configured cadence produces non-overlapping, equal-duration windows without catch-up loops.
  3. `metrics_retrieved_at` persists exactly once per attempt and is never shown as capture time.
  4. Legacy windows report `metrics_retrieved_at` as unrecorded.

**S17 monitoring-workspace (M1 half of old-S10).**

- Scope: topic revision/activation/pause, method/cadence/bounds/retention controls, last collection and health, alert history and snapshots.
- Acceptance: old-S10-A01 and A04, plus a saturated-window display from S16 when it exists.
- Requirement IDs: see 4c.

**S19 alert-investigation-promotion (M2 half of old-S10).**

- Scope: KB-only investigation and exact promotion review.
- Acceptance: old-S10-A02 and A03.

**S20 source-capabilities.**

- Old-S12 plus ownership of the D1 configuration screen: ten keywords, activation as a recorded command, day allowance, route health and selection basis.
- Added acceptance: an eleventh keyword is refused, the daily cap and occurrence authority are shown truthfully, and configuration edits never alter an existing occurrence's scope.

**S21 engagement-anomalies.**

- Old-S13 without the old-S11 dependency. It consumes `metrics_retrieved_at` only under W02.
- Without W02 acceptance, live X engagement reports `measurement_time_unknown` as unassessable, which is honest but leaves FR-C02 engagement fixture-only in the pilot.
- Chart integration is a conditional check.

**S22 semantic-shift.** Old-S14 without old-S14-A04 (moved to S28). Its dependencies on old-S10/S11 are removed, and chart/alert rendering is a conditional check.

**S23 interaction-checkpoint (new).**

- Scope: a human executes the S15 and S18 checklists: drag/pin, overlapping branches, stale-page discard, keyboard/list equivalence, reduced motion, chart latest/selected/gap behavior, and narrow CJK layouts.
- Acceptance:
  1. The build identity and each checklist item are recorded as pass/fail with evidence.
  2. Each failure is filed against its owning spec.
  3. Accessibility observations are recorded separately.

**S25 progressive-acquisition (plan model half of old-S16).**

- Scope: `AcquisitionPlan`/step model, value-based stopping and cross-route avoidance over the *existing* keyword and nickname routes. The successor-approval path uses installed proposal operations, and A1 UI linkage is a conditional check.
- Acceptance: old-S16-A02, A03 and A04, plus A01 restricted to keyword plus nickname.

**S26 supplementary-detail-route (route half of old-S16).**

- Scope: task-integrate one named route. The default is Bright Data profile/post detail fields (follower count, post metrics, post history window), with exact fields fixed by the S04 Bright Data row. `tiktok-web` only under U4. oEmbed is limited to identity and title.
- Acceptance:
  1. A broad-plus-detail task records one supplementary observation per step within cost and request bounds.
  2. Pending, ambiguous or failed responses are never blindly retried.
  3. Namespaces stay separate from keyword captures.
  4. An unsupported field is explicitly unavailable.

**S27 inbox-email.**

- Old-S17 with the pilot UI managing one configured recipient and the inbox plus email channels. The recipient-plus-channel logical key and attributable reissue stay.
- Its dependencies on old-S10 and old-S15 are removed, because alert notifications come from installed owners and email is not chargeable by default.
- Old-S17-A04 keeps preference-edit pinning for the single recipient. Recipient disablement remains.

**S28 plans-and-quality.** Old-S18 plus old-S14-A04: exact KR/JP original-language semantic evaluation cases, including packaging/product ambiguity and negative examples. Its dependencies on old-S07, S10 and S17 are removed. Packets for chat and monitoring compose installed answer and semantic owners.

**S29 provider-readiness (rescoped).**

- The final signed-off record per capability, reusing S04's authorizations and format.
- Each row can be completed when its own capability spec is done, and none waits on S28.
- Acceptance: old-S19-A01 to A04 unchanged, plus each row links its S04 probe.

**S30 human-pilot-acceptance (rescoped).**

- The release record that incorporates S13 and S23 results and covers the remaining journeys (approved research→later question, alert→KB context, spending, inbox/email, lineage) and KR/JP adjudication on live data.
- Acceptance: old-S20-A02, A03 and A04, plus A01 limited to scenarios not already passed in S23 at the same build identity, or re-run if the build changed.

**S31 evaluated-retrieval and S32 agent-candidate.** Scope unchanged. Their dependencies change as in 4a. S31 compares against the S06 deterministic baseline.

### 4c. Requirement coverage changes

Unlisted IDs keep their current mapping, renamed through the old→new table.

| Requirement IDs | Change |
| --- | --- |
| OFR-E03, UD-02, PROP-34 | Add S02. OFR-E03 also stays on S07, S17, S20, S24 and S29 |
| UD-03, UD-07, PROP-03 | Move the mechanism from old-S02 to S03. S08 keeps UD-03 for its screens. S30 unchanged |
| OFR-E02 | Add S03 (independent client-state tests) and keep S01 |
| PROP-01, PROP-15, UD-01 | Stay on S08 (old-S02 remainder). Add PROP-15 to S03 (envelope) |
| FR-C01, FR-P04, FR-P09, FR-S01, OFR-S03, PROP-23, PROP-28, UD-05 | Add S04 (early evidence). The final rows stay on S29 |
| FR-A02, FR-A03, FR-G02, PROP-17 | Add S05 |
| FR-A02, FR-B01, FR-B02, FR-G01, PROP-32, PROP-35 | Add S06. S31 keeps FR-A02, FR-B01, FR-B02, PROP-32 and PROP-35 for semantic depth |
| FR-A01, FR-B01, OFR-E01, UD-01, UD-03, PROP-16 | Add S13 (early human evidence). S30 keeps all its old-S20 IDs |
| FR-C01, FR-C02, FR-P09, OFR-C01, R2-STREAM | Add S16 |
| Old-S10 IDs | Split. S17 (M1): FR-C01, FR-C02, FR-C03, FR-C05, FR-C06, FR-P09, OFR-C01, OFR-E03, PROP-01, PROP-06, PROP-09, PROP-25. S19 (M2): FR-C04, FR-C07, PROP-04, PROP-07, UD-08 |
| FR-P01, FR-P02 | Add S20 (D1 UI owner). They stay on S07 for runtime ticks |
| UD-06, UD-07, R2-GRAPH, R2-STREAM, FR-G01 | Add S23 |
| Old-S16 IDs | Split. S25: FR-A03, FR-B03, FR-B04, FR-B05, FR-P02, FR-P03, FR-P05, FR-P06, FR-P07, FR-S03, PROP-07. S26: FR-P04, FR-P06, PROP-23 |
| PROP-16, OFR-E01 | Add S28 (KR/JP semantic packets moved from old-S14). S22 keeps FR-C03, PROP-09, PROP-17, PROP-33, R2-STREAM |
| UD-09 | Record "satisfied by the actual r2 approval; no spec" instead of an empty list |

Every requirement ID keeps at least one implementation or explicit later path. No core FR moves to a proposal lane.

### 4d. Narrative corrections

`gap-analysis.md`:

- Add rows or notes for each of these:
  - query, chat and graph bounds and the question-blind chat scope (R1-F01, missed issue 2),
  - no interpretation in the task pipeline (R1-F02),
  - no operator path to the model or live X (R1-F05),
  - ADR 0023 one-page saturation and unknown measurement time (R1-F06),
  - the client has no module, test or i18n tooling (R1-F04).
- Reword line 36: oEmbed and tiktok-web adapters exist for supplied references but are not task-integrated; S26 integrates one named detail route.
- Replace the "51 passed, 1 failed" statement at line 42 with: the shared check stops at the first failure (`--maxfail=1`), so the state of the rest of the suite is unknown until S01's inventory.
- Renumber spec paths.

`architecture-target.md`:

- Add a "Pilot composition" subsection: one validated configuration consumed by all entry points, secrets by environment-variable reference, recorded activations never set by configuration.
- Add a "Client foundation" subsection: ES modules, vendored pinned graph library, shared freshness utility implemented once, Node state tests.
- Add to the owner table:
  - `smi_knowledge` support-based interpretation port and ingestion-owned retrieval index (S05, S06),
  - `smi_monitoring.polling` saturation and `metrics_retrieved_at` (S16),
  - `smi_notifications` single recipient in the pilot (S27).
- Replace line 56 ("Keep existing form routes working…") with: "Each UI spec retires the legacy form routes it replaces once parity tests pass."
- Renumber spec IDs in the owner and interaction tables. D1 maps to S07, S20 and S25/S26.

`implementation-sequence.md`:

- Replace the table with 4a.
- Milestones:
  - **M0, start in parallel:** S01, then S02, S03, S05, S06 and S22. S04 runs as soon as S02 and U1 are available.
  - **M1, real-data campaign and chat:** S07, S08, S09, S10, S11, S12, ending at H1 (S13).
  - **M2, graph (parallel from M0):** S14, S15.
  - **M3, monitoring:** S16, S17, S18, S19, S20, S21, plus S22 from M0, ending at H2 (S23) together with S15.
  - **M4, acquisition, spending, notifications, planning:** S24, S25, S26, S27, S28.
  - **M5, release:** S29, S30.
  - **Later:** S31 to S40.
- Critical paths, computed from 4a:
  - main journeys: S01→S03→S08→S09 / S12 (depth 4); S01→S06→S14→S15 (4),
  - deepest build: S01→S03→S08→S20→S25→S26 (6),
  - release: …→S26→S29→S30 (8),
  - first live evidence S04 at depth 3; H1 at depth 5.
- Safe parallel work: after S01, five independent owners (S02, S03, S05, S06, S22). After S03/S08, campaign, chat, task, monitoring, spending, capability and inbox UI specs proceed with one integration owner for shared `smi_review` catalogs and adapters.
- State that U1 (live authorization) is requested at plan start, because it is the long-pole external dependency. Specs whose premises depend on probe results (S16 values, S21, S26 fields) record those premises as provisional until the matching S04 row passes.
- Populate `plan.json` `rationale` per edge from 4a and add `size`. Regenerate the narrative from `plan.json` instead of writing it by hand.

### 4e. Genuine user decisions, with recommended defaults

None of these blocks pilot build start. W02 blocks only S21, and W01 blocks only S34.

| ID | Decision | Recommended default if unanswered | Affects |
| --- | --- | --- | --- |
| U1 | Grant bounded live authorization and credentials early for the S04 probes: the model, Bright Data keyword, X recent and the email provider's semantics, with explicit per-capability call counts and a spending ceiling | Request at plan start with the smallest useful caps. If not granted, S04 stays blocked, the build continues on fixtures, and premise-dependent specs stay marked provisional | S04, S13, S29 |
| W02 | May a successful X response's receipt time serve as the metric measurement time (an upper bound, with a configured tolerance) for matched-age engagement? This amends documented evidence semantics (`docs/monitoring.md:168`) | Accept as a narrowly scoped ADR amendment: label it `metrics_retrieved_at`, never a capture time, and validate it against the S04 X row. If rejected, live engagement is reported as unassessable | S21 (FR-C02 engagement live) |
| U3 | Allow more than one X page per window (a successor to ADR 0023, with more recurring paid authority)? | No at pilot start. Use cadence and saturation reporting, and revisit with S04 X probe data | S16, S29 |
| U4 | Which supplementary detail route, and is `tiktok-web` source use permitted? | Bright Data profile/post detail fields; `tiktok-web` stays unavailable | S26 |
| U5 | Permit scoped headless-browser tests against the loopback app in CI or by agents (currently declined)? | Keep declining. Rely on S03 Node state tests plus the human checkpoints S13, S23 and S30 | S03, S15, S18, S23 |
| U6 | W01 initial direction: re-ask both branches (agent-drafted scope for human approval; validated fluent synthesis) | Proceed with S32 as a disabled candidate under the recommended "yes" branches as non-binding working assumptions. S34 stays decision-blocked | S32, S34 |
| U7 | Pilot email goes to one configured recipient, with multi-recipient preferences later (S35) | Yes | S27 |

The following are engineering choices, not user decisions, and are recorded in their specs: the graph library versus a hand-built layout (S03), the configuration file format (S02), deterministic per-turn retrieval (S06), the event table versus derived phases (S10), and interpretation before publication (S05).

External prerequisites, not decisions: a named marketer and a KR/JP reader for S13, S23 and S30.
