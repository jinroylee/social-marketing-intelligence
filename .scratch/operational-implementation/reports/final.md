# Completed approved implementation batch

Tickets 01–10 are implemented and resolved on `integration/operational-tickets-01-10`. Each ticket used a fresh implementer context and worktree, in order, after the preceding merge passed shared checks. Tickets 11–39 remain drafts.

Starting review baseline: `6220fff49b5b8e982ef5a8d54b7c788e45b0f648`. Final runtime repair: `08317376094487fb1310d3466ee3f65e512d8463`. Integration validation evidence: `0bb62aef6419549a2076c98b292be23939459733`.

## Ticket commits

| Ticket | Delivered slice | Implementation commit | Integration tests |
| --- | --- | --- | --- |
| [01](../issues/01-restore-ingestion-completion-and-safe-resume.md) | Restore ingestion completion and safe resume | `11bc6cbe9c25fde9443b2785dbf5482b2ae18c0a` | 209 |
| [02](../issues/02-publish-and-inspect-permitted-ingested-support.md) | Publish and inspect permitted ingested support | `09f3d18d9a4195c8f14fd670e51c1b157a7f2ced` | 223 |
| [03](../issues/03-search-current-knowledge-and-pin-result-support.md) | Search current knowledge and pin result support | `e3e55d3e89684bf3a5696d3caf0c1d257dde107c` | 235 |
| [04](../issues/04-run-one-authorized-offline-acquisition-task.md) | Run one authorized offline acquisition task | `a27b433cdac2ba1d23fe409bb0f15aff65f82b4c` | 248 |
| [05](../issues/05-approve-an-exact-assistant-enrichment-proposal.md) | Approve an exact assistant enrichment proposal | `7ba1c46fe1b355afb6f2e42e703e0079fc359f3d` | 256 |
| [06](../issues/06-recover-interrupted-tasks-and-expose-partial-outcomes.md) | Recover interrupted tasks and expose partial outcomes | `19b65407b2b52082314916f2a744f54bd6bc1cf2` | 263 |
| [07](../issues/07-coordinate-competing-workers-without-duplicate-effects.md) | Coordinate competing workers without duplicate effects | `b8c232945859cf40b1c1ec1340dbcad66aee32f2` | 278 |
| [08](../issues/08-deliver-durable-task-completion-notifications.md) | Deliver durable task completion notifications | `96754561b3c39caa8f31c102a9eeda671ddc735e` | 291 |
| [09](../issues/09-show-attributable-actual-costs-and-forecasts.md) | Show attributable actual costs and forecasts | `02f931faba0fb5a2136b01141a92031646c40224` | 301 |
| [10](../issues/10-enforce-shared-monetary-admission-before-work.md) | Enforce shared monetary admission before work | `ce86f8caaf36d0be3c5fc01dc8b5553f6d525c7f` | 315 |

Local tracker/configuration publication was committed in `a2187ff`. Review repairs were committed in `0831737`, followed by evidence-only commit `4575fd0`. All commits and local branch refs are retained.

## Validation

- Final integration command: `UV_OFFLINE=1 uv run --locked python tools/check.py` — **325 passed in 269.09 seconds**, plus Ruff, documentation links, physical ERD coverage, relative instruction symlinks and PostgreSQL preflight.
- Review repairs: **129 focused tests passed**; static checks, whitespace checks and wheel build/content verification passed.
- Tests used real isolated-schema PostgreSQL, simulated external I/O, and actual competing connections/processes. Public worker fault injection covered evidence, canonical, publication, completion and cost-dispatch/settlement boundaries.
- [Independent baseline review](final-review.md): standards 3 findings addressed, 0 remaining; spec 1 finding addressed, 0 remaining. Original worst severity was P2 within each axis. [Repair report](review-fixes.md) records individual regressions and interface changes.

## Tracker and cleanup

- [Local tracker configuration](../../../docs/agents/issue-tracker.md) and [execution manifest](../execution-manifest.json) record publication, dependency gates, commits and results. All ten published issues are resolved with checked acceptance criteria.
- Removed all ten ticket worktrees and the review-fix worktree after checking that every worktree was clean and merged. The pre-existing `kokanee` worktree and all local branch refs were preserved.
- Execution stayed offline/local. No push, PR, deployment, live provider/model call or external messaging was performed. Existing completed tickets and reviews were preserved across usage-limit interruptions.

## Remaining limits

- Acquisition uses the bounded synthetic fixture route; proposals are supplied directly, queries are literal and the inbox is local. Live providers, conversational generation and later-ticket features are not enabled.
- Monetary enforcement covers the configured bounded synthetic service. Measurements are synthetic, not commercial charges. Delayed billing, uncertain-operation reconciliation, legacy commitment release and worker control-period rotation remain deferred; uncertain commitments stay conservative.
- A connected paused worker retains its task session. Local fencing and one-use admission do not promise provider-side exactly-once execution.
- A pre-repair interrupted publication without an atomic task receipt cannot prove ownership and now fails safely instead of creating a false success. No automatic repair of that ambiguity was added.
- Technical checks do not establish human-language quality, marketer usefulness or complete market coverage.

The authorized batch is complete and execution stops after ticket 10.
