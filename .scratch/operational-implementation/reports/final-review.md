# Final baseline review

Baseline: `6220fff49b5b8e982ef5a8d54b7c788e45b0f648`. Reviewed integration head: `c48ec5d`.
Command: `git diff 6220fff49b5b8e982ef5a8d54b7c788e45b0f648...HEAD`.
Scope: approved tickets 01–10 only; later tickets remain deferred. Independent read-only standards and spec contexts reviewed the diff after the integration check passed 315 tests. Neither reviewer reran the shared suite.

## Standards

Documented violations:

- **P2 — Campaign owner boundary:** `src/smi_tasks/store.py:70` directly executes `SELECT brief_version FROM campaigns … FOR SHARE`. `src/smi_tasks/AGENTS.md` requires “Read campaigns through `CampaignStore`”; root guidance forbids reaching through another module’s interface. Move the current-brief validation and lock behind a public campaign operation accepting the caller’s transaction.
- **P2 — Recoverable submissions discard edits:** New proposal/task POST branches at `src/smi_review/app.py:293–318` fall through to the generic error page instead of redisplaying submitted values. `src/smi_review/AGENTS.md` requires “preserve submitted edits on recoverable errors.” Public `ReviewApp.handle` reproduction: submit a valid purpose and 31 subjects to `/proposals`; response is 422, contains no form, and loses the purpose. Add submitted/error rendering for proposal and campaign-task forms, retaining request identity.

Baseline heuristic:

- **P3 — Possible Data Clumps (judgment):** `src/smi_tasks/worker.py:99,116` repeats `_checkpoint(self, task_id, attempt_id, … actor, execution)` and `_finish(self, task_id, attempt_id, … actor, execution)`, with the same arguments repeated throughout callers. `TaskExecution` already owns the task identity and actor. Derive those from the handle and group attempt context where useful, reducing the chance of pairing an ownership session with different row identities.

No other actionable standards findings identified.

## Spec

Approved requirements missing/partial: none identified. Scope creep: none identified.

- **P2 — Validate task ownership before adopting a publication:** At `src/smi_tasks/worker.py:201`, any publication matching `task:<task_id>` skips ingestion; lines 242–246 then report `usable_update` and link it. Public `publish` accepts that request ID, while `find_request` checks only workspace/request text and returns no support/run linkage. After task acknowledgment, a caller can publish unrelated ingested support using that identity. The worker then completes with zero task observations and the unrelated publication. This violates ticket 04’s “empty or unchanged inputs do not create fictitious update claims” (line 18) and ticket 06’s requirement for “actual coverage” (line 14). Recovery should validate the publication against the task’s durable prepared support and attempt/run lineage.

Standards: 3 findings, worst P2. Spec: 1 finding, worst P2. The axes are assessed separately.

## Resolution

All findings were addressed in one implementer context and committed as `08317376094487fb1310d3466ee3f65e512d8463`; evidence head `4575fd0ef37b6049211bf83f95940f528932ea07`. The completed baseline reviews were reused after quota interruptions; they were not restarted. The repair diff was checked against the existing findings.

| Axis / finding | Resolution |
| --- | --- |
| Standards P2 — campaign boundary | `CampaignStore.require_current_brief` owns exact validation and the caller-transaction lock; a competing real brief revision is blocked until commit. |
| Standards P2 — recoverable forms | Proposal, campaign-task and approval forms retain escaped edits and request identity on validation/conflict errors; Origin/CSRF and server-owned authority remain enforced. |
| Standards P3 — possible Data Clumps | Worker helpers derive task identity and actor from `TaskExecution`, removing redundant paired arguments. |
| Spec P2 — publication ownership | Publication and task receipt commit atomically. Recovery requires the receipt, exact durable prepared membership and public source-run lineage; request text alone cannot complete a task. |

[Repair evidence](review-fixes.md): 129 focused tests, static checks and wheel verification passed. Final integration shared checks passed **325 tests in 269.09 seconds**; evidence commit `0bb62aef6419549a2076c98b292be23939459733`. Legitimate receipt-backed recovery preserves actual publication producer after current-policy withdrawal. Older interrupted publications without a receipt fail safely.

Standards: 3 addressed, 0 remaining. Spec: 1 addressed, 0 remaining. No later ticket was implemented.
