# Final baseline review repairs

Scope: the four findings in [the independent final review](final-review.md), covering approved tickets 01–10 only. Work began from integration commit `bf41d05` in `/tmp/smi-operational-review-fixes` on `smi/operational-review-fixes`. Its ancestry was confirmed before editing. No ticket was claimed, reopened or closed; later tickets and root planning files were untouched.

## Finding dispositions

| Review finding | Disposition and behavior |
| --- | --- |
| Standards P2 — campaign owner boundary | Fixed. `CampaignStore.require_current_brief` validates exact workspace/brief/version and retains its campaign share lock through the caller's transaction. Task admission invokes it on the same connection as the acknowledgment. The task owner no longer selects campaign tables. Existing duplicate requests still reopen their original acknowledgment after a successor brief, while new stale submissions fail. |
| Standards P2 — recoverable forms discard edits | Fixed. Proposal, campaign-task and proposal-approval/submission error pages render editable escaped user fields and the original request identity. Approval recovery uses the durable original approval request when one exists. Brief membership and proposal scope/digest are reopened from their owners; arbitrary origin, actor, approval and route inputs are excluded from hidden state. Stale recognized briefs retain their exact historical basis and point to current-brief review. Origin/Host/CSRF validation remains in force. |
| Standards P3 — possible Data Clumps heuristic | Addressed narrowly. Worker checkpoint, completion, notification and controlled-collector helpers derive task identity and actor from `TaskExecution`; `_run_one` also receives that handle. Attempt identity and original producer remain explicit where needed. No new execution abstraction or change to fencing/cost attribution was introduced. |
| Spec P2 — publication request collision | Fixed. The existing task/publication relation is now an ownership receipt inserted in the actual fenced publication transaction. Recovery requires that receipt, exact durable prepared membership and validated attempt/run lineage. Public publication using `task:TASK_ID` cannot authorize completion, including identical support/actor and a race after the initial lookup. Conflicts preserve actual task coverage without a task publication link or usable-update claim. Legitimate lost acknowledgments retain the original publication, actual producer and historical outcome after current-policy withdrawal. |

## Public contracts and persistence

- `CampaignStore.require_current_brief(campaign_id, brief_id, actor, expected_version=..., connection=...)` owns current-brief validation and the transaction-duration lock. It grants no additional actor role.
- `KnowledgePublications.find_request(..., connection=None)` now returns source-free exact ordered support/interpretation IDs with original producer/coverage. It reads no source values and establishes publication idempotency only.
- `IngestedEvidence.require_run_support(run_id, references, actor, include_synthetic=False, connection=None)` validates exact applied observation/derivation/assertion/metric lineage in its owning workspace/run without reading values. Historical lineage remains valid after policy withdrawal or derivation supersession; value-use/publication authority does not follow from it.
- `AcquisitionTasks.read_committed_publication(..., connection=None)` composes those owner interfaces with task-owned prepared support/receipts. Missing or mismatched ownership raises `publication_request_conflict`; task detail does not promote a collision to publication-committed progress.
- Publication and receipt commit atomically; terminal outcome, attempt completion and completion event commit later on the same fenced session. An externally created duplicate is rejected rather than converted into a receipt. No tables or columns were added. The schema comment, physical ERD lifecycle, contracts, architecture, reader guide and ADR 0005 describe this boundary. Updated owner instructions retain their relative `CLAUDE.md -> AGENTS.md` symlinks.

## TDD and regression evidence

Applied the TDD skill at the already approved public HTTP, task/worker, campaign, source/publication/query and inbox seams, using real isolated-schema PostgreSQL and simulated fixture I/O. The writing-for-agents skill aligned the affected owner instructions. No internal store was mocked and no direct SQL served as an outcome assertion.

1. Proposal tracer: red because a valid purpose with 31 subjects returned 422 with no editable form; green with escaped retained purpose, intent, subject/search text and request identity. Correction succeeds, while changed search scope under the saved request returns 409 with edits retained and one proposal.
2. Campaign task tracer: red because validation errors had no form; green with editable purpose/retry identity, stale-brief conflict recovery, server-owned replacement of a forged brief and rejection of submitted authority. A changed purpose under an acknowledged request retains edits without overwriting the task.
3. Approval tracer: red because the approval-required error had no form; green with exact trusted digest and reviewed action retained. A changed manifest interrupts submission after approval, and recovery reuses the saved approval request. Changed request identity conflicts; restoring the fixture finishes the same task. CSRF and foreign-Origin rejections remain covered.
4. Campaign lock tracer: red on the absent owner operation; green with an actual competing brief revision blocked until the dependent caller transaction commits. Subsequent stale validation fails; existing task retry/stale-basis regressions remain green.
5. Collision tracer: red because an empty acknowledged task adopted unrelated public support and reported `usable_update`; green with publication conflict, zero task-collected/published members, no task link and stable terminal retry. Additional public regressions cover unrelated and identical support after preparation, untrusted task-detail promotion, and an identical public publication racing the worker's commit.
6. Legitimate recovery: a lost publication acknowledgment followed by source withdrawal and input-file removal preserves the receipted publication, original producer, exact support/coverage and one completion. Current queries return no withdrawn values; the inbox reports historical publication with zero current availability and no value navigation. Public metadata/source tests separately reject mismatched runs and assertion membership while preserving source-free lineage after withdrawal.
7. Existing real-process/connection competition, session-loss commit fencing, partial outcomes, independent task progress, waiting operations, cost admission and actual producer attribution remain covered by the focused and shared suites.

## Validation

- Focused command: `UV_OFFLINE=1 uv run --locked pytest -q tests/test_tasks.py tests/test_task_concurrency.py tests/test_publications.py tests/test_review.py tests/test_completion_inbox.py tests/test_cost_admission.py tests/test_costs.py --tb=short --maxfail=1`: **129 passed**, 126.59 seconds. The final shared run additionally includes the later proposal request-conflict assertion.
- `UV_OFFLINE=1 uv run --locked python tools/check.py`: **passed**, including Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **325 tests in 267.00 seconds**. This includes all ten new regression cases and the final proposal request-conflict assertion.
- `UV_OFFLINE=1 uv run --locked python tools/check.py --static`: passed Ruff, documentation links, physical ERD coverage and instruction symlinks. `git diff --check`: passed.
- `UV_OFFLINE=1 uv build --wheel --out-dir /tmp/smi-operational-review-fixes-wheel`: passed. Archive inspection matched the exact current bytes of all nine changed runtime/schema modules.
- Implementation commit: `08317376094487fb1310d3466ee3f65e512d8463` contains all runtime, test, contract and owner-instruction repairs plus this report. This final evidence-only update records that commit's SHA.
- `git merge --no-edit integration/operational-tickets-01-10`: **Already up to date** against `bf41d05` before completion. Final static checks and `git diff --check` passed after recording the shared result; root planning files remained unchanged.

## Limits

- Existing completed tasks retain their outcomes and links. A pre-repair interrupted publication lacking an atomic task receipt cannot prove task ownership and now fails safely; request text or exact support alone cannot repair that ambiguity. This deliberately prevents the reported false success. No automatic reconciliation feature was added.
- Receipts establish historical task effects. Current source-policy and derivation availability still govern values and inbox navigation; a historical usable update does not promise permanent current availability.
- Existing connected-worker, ambiguous-provider and synthetic-cost limits remain. This repair enables no live provider/model calls, commercial spending, hosted authentication or later-ticket features. Technical checks do not establish language quality or marketer usefulness.
- Work remained local/offline with no push, PR, external messages, approval pause or subagents. No unresolved review finding or external blocker remains.
