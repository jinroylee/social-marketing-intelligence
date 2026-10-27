# Ticket-planning findings

- Source spec: 70 user stories, 30 acceptance scenarios, six proposed milestones. Accepted behavior remains authoritative; no additional product interview is required.
- All proposed feature slices should expose a public operation and a usable local surface, with real PostgreSQL integration coverage and simulated external I/O by default.
- There is no need for a speculative wide refactor. Existing collectors, mappers, ingestion checkpoints, public stores, actor boundaries, form protections, and isolated-schema tests are reusable.
- The only initial baseline repair is the source-evidence save completion contract: the runner supplies a completion argument absent from the current signature and the save implementation references an undefined completion value. Fix it as a separate bounded recovery/regression ticket; do not perform that repair during ticket generation.
- Distinguish minimal publication by identity from broader current-KB search and pinned retrieval results; task execution can reuse the first without waiting for graph or LLM work.
- Split task happy path, exact assistant approval, recovery/partial outcomes, worker concurrency, and completion inbox. Treat each as a complete visible operational behavior.
- Split spending into attributable actual/forecast reporting, coordinated admission, and uncertain/delayed reconciliation; no live route should precede the applicable controls.
- Schedule configuration, daily unique-post allowance, retrieval avoidance, broad query discovery, and live enablement are separate behaviors. Scheduled live activation must depend on the daily allowance; on-demand live discovery need not wait for keyword configuration.
- Current-KB comparisons, automated save authority, LLM assessment, optional human curation, coverage discovery, and explicit regeneration are distinct campaign behaviors.
- Recent X observations can start independently after the baseline repair. Full KB publication is never a per-post prerequisite for X detection.
- Model-backed consumers may reuse one explicitly metered provider transport introduced through a real user journey; no generic model-framework ticket is needed.
- Final human quality evaluation must use genuine reviewer input and report pending if absent; implementation tests cannot fabricate a usefulness or original-language pass.
- The tracker is still not configured in the supplied instructions; drafts are local and not published. to-tickets requires approval of the breakdown before either local ready-for-agent files or real tracker issues are published.
- Final draft: 39 tickets, with 9 S and 30 M scopes, each 150–500 words and an explicit scope guard. Word limits are an artifact check, not a claim about implementation effort; scope was separated by observable behavior and distinct failure boundaries.
- Full coverage: every user story 1–70 and acceptance scenario T01–T30 has an identified owner/extension ticket. The numbered breakdown includes both traceability tables.
- Dependency audit: all blockers precede dependents, there are no cycles or redundant transitive edges. Initial frontier is ticket 01; after it completes, 02, 12, and 29 can start independently.
- Source-policy/synthetic visibility, simulated cost labeling, and failed new-post-admission reconciliation were checked explicitly in the drafted criteria.
- Required breakdown review was requested asynchronously after all drafts were concrete. No response or approval has been assumed. The published issues directory does not exist.
- Fresh shared check still fails Ruff F821 at the unchanged source-evidence completion value and stops before pytest. Direct documentation link/ERD/instruction checks, draft-link/coverage/DAG checks, and whitespace checks pass.

## Completed batch

- All first ten tickets are resolved; authoritative commits and checks are in execution-manifest.json and reports/final.md.
- Original-baseline standards/spec reviews found three standards findings and one publication-ownership defect; all were repaired in one implementer context and verified with 325 integration tests.
- Publication recovery now requires an atomic task receipt plus exact prepared support and source-run lineage, while current policy still governs values.
- Live operations, commercial billing reconciliation and tickets after 10 remain outside this completed batch.

## Remaining-ticket continuation

- Tickets 11–39 are approved and published. The previous first-ten manifest/reports remain completed history.
- Ticket13 explicitly requires current primary-provider contract verification; no existing model/provider configuration or captured primary model contract was found in repository text. The user approved read-only primary-documentation lookups only; model/source execution stays local and simulated while ticket11 proceeds.
- Tickets24/25/34 require actual live prerequisites; ticket39 explicitly requires a named real human reviewer. Simulated tests cannot create those readiness/usefulness receipts.

- Primary-provider contract research is captured in research/model-provider-contract.md. Official HTML API reference exceeded the web reader size limit, and its Markdown variant was unsupported by that reader. Bounded read-only HTTPS retrieval of official Markdown succeeded; no API execution or credentials were used.

- Ticket13 pre-merge review found a scope gap: a simulated-only transport left the selected provider adapter unimplemented, with no later model-live ticket. Offline execution does not preclude concrete adapter code tested with simulated HTTP. The implementer is closing the gap with explicit server enablement, a current primary-verified model context bound, and truthful provider-reported/synthetic accounting provenance. No live call or commercial receipt is authorized.

## Ticket 13 pre-merge gap closure

- Closed the earlier root scope gap in `2420af1de46a1756d370914a555ae826e574a306`: concrete fixed-host bounded Responses adapter, disabled by default; explicit verified model contract; strict returned model/tier/final-usage handling; separate provider/synthetic basis; exact provider-basis final reconciliation and separate health recovery. Root shared validation passed **381 tests in 253.68 seconds** with all HTTP intercepted simulation.
- Primary-contract verification and software implementation are complete. Future live enablement, real credentials/rates/configuration, account readiness, live receipts and human quality remain unestablished; no readiness or commercial-invoice claim follows from the simulated tests.

## Coordinator clarification: implementation and live prerequisites

- Re-read published tickets 24, 25 and 34: default tests explicitly simulate transport, and any paid live receipt requires separate authorization. Missing live credentials, source-use policy, required runtime configuration or authorization must keep the live capability unavailable; their absence alone does not block concrete adapter implementation and simulated validation when the current permitted contract is verifiable. Do not preemptively block these implementation tickets solely because no live call is authorized. An inaccessible/unverifiable required contract or other unmet required proof can still be a genuine external blocker. Recorded external runtime prerequisites and absence of readiness receipts remain unchanged.
- Re-read ticket 39: it requires actual named-human feedback on exact permitted examples. Software simulation or model output cannot complete that human-validation ticket.

## Resume audit — 2026-10-27

- Maps, published tickets, continuation manifest and git agree: tickets 01–25 are resolved; ticket 26 was selected but its interrupted implementer committed no code and never claimed the issue. Integration is clean at `6a43ec7f429bbaa184ff288e9fa513f5475605c1`; runtime/tests/tooling match the previously verified ticket-25 runtime exactly. Preserve the 630-test root PASS and original final-review baseline.
- Temporary worktree directories and ephemeral artifacts/logs are absent; durable reports/manifests and branches remain. Removed only the missing ticket-26 worktree registration and recreated the unchanged branch at `/Users/makinarocks/workspace/personal/.smi-agent-worktrees/ticket-26` to avoid another temporary-directory loss. Other historical registrations/branches were left alone.
- The local test PostgreSQL service was stopped. Restoring the existing Compose service with the locally available image (`--pull never`), without external execution or new provider authorization. Updated repository tracker/triage/domain guidance is present and has been read. No product/spec/code conflict requiring user input was found.

## Ticket 26 review in progress

- The resumed implementer claimed ticket26 and selected exact explicitly approved profile URL/native ID plus one nickname through the existing Bright Data profile transport. Supplementation joins the original run/budgets and preserves the profile namespace rather than merging keyword identity. Primary documentation was rechecked by the implementer on 2026-10-27; all execution remains simulated.
- Early root review found persisted-selection recovery could bypass current runtime/source permission checks, and profile source counts were declared before schema validation. Both were sent to the implementer for public-operation regression coverage and repair before freezing. They are not completion evidence. Local PostgreSQL restoration/preflight succeeded.


## Ticket 26 integrated review-gap closure

- Frozen runtime `c461a49ff89e9057973848ba049a9273095016bd` closes the earlier root findings: resumed persisted selections reopen current runtime/source/cost gates; source counts derive from validated schema/identity outcomes; ordinary permitted current-KB nickname support prevents redundant paid profile refill; pinned supplementary policy does not confer profile-target authority on live schedules; provider `status=error` rows are rejected. Final public owner/adapter and integrated gates cover the repaired bytes. No open blocking root finding remains.
- Root fast-forward checked `ca4bd0a4da32cb1944d5013dc882999a2a267423` with all static/preflight stages and **656 tests / 454.35 seconds**, exit 0. Persistent wheel identity and 68 source/archive pairs independently match. Primary profile contract was verified on 2026-10-27; concrete nickname-only software validation is complete with real PostgreSQL/simulated HTTP. Exact URL/native-ID authority, original cumulative limits and separate `tiktok:public` support remain without identity merging.
- The local PostgreSQL prerequisite was restored using its cached image and ticket 26 resumed in a persistent worktree; earlier completed runtime/test checks were preserved. Actual keys/source-use/live/profile-operation authorization, enablement, commercial configuration and live receipt remain unmet independent runtime gates, not alone software blockers. Shared local declared Bright Data allowance and unknown profile costs do not establish commercial billing or readiness/human-quality evidence.

## Ticket 27 review in progress

- The new assistant application composes current published-KB queries and the established bounded Responses transport, with model-selected exact support IDs and no source-value answer cache or acquisition authority. Full model-input support remains a dependency, including unselected evidence. Initial ten public ask/read/accounting/HTTP cases passed.
- Root review identified a pre-dispatch permission timing gap: evidence could lose process permission while model admission waits after retrieval. Requested a current exact-input permission guard at dispatch and a public real-PostgreSQL regression proving no model call after denial, preserving one-use accounting and truthful dispatch/uncertainty states. This finding remains pre-freeze work, not completion evidence.


## Ticket 27 dispatch-time permission closure

- Frozen runtime `6110c01839e1742a1f8986f9b25f8335c9e97544` closes the pre-dispatch permission race: the optional trusted shared-admission guard runs after accounting contention, reopens every exact model-input dependency and holds current source locks through admission commit. No I/O transaction is introduced. The public real-PostgreSQL lock regression proves visible refusal, zero model calls and zero outstanding liability; the complete 15-case owner suite passed, followed by 131-case compatibility and the required root **671 tests / 466.67 seconds**, exit 0, at `c37f76a71d2a739c6c44936dd27b604824960fba`. No open blocking root finding remains.
- The independent root artifact check matches all 67 source/archive pairs, ten SQL schemas, both review assets, all 23 guidance pairs, exact wheel hash/size and 154 unique archive entries. Installed behavior is bounded extractive exact published findings with full-input dependencies and no source-value answer cache/acquisition/tools. Schema validity does not establish semantic relevance/entailment, human language quality or marketer usefulness; model configuration/keys/rates/enablement and live receipt remain unestablished independent runtime/quality gates.

## Ticket 28 review in progress

- Resumed the same persistent claimed-ticket implementer on 2026-10-28 after a usage-limit interruption; uncommitted work, six passing public/HTTP cases and local PostgreSQL were intact. No completed implementation or check was repeated.
- Root review reproduced recovery failure between a committed proposal save and missing journey linkage when route inputs disappeared. The implementer added proposer-bound public `AcquisitionTasks.find_proposal` and recovered via the server-owned nested request identity. Fault-only DDL regression passed: same proposal/digest/config, no duplicate or task, and no route reread. No remaining blocking root finding in the reviewed composition; compatibility/docs/full gate remain pending.
