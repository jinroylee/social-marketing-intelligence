# Product design and implementation planning

This working record tracks the requested Orca run. It is not an accepted product contract.

## Runtime

- Executable is `orca`, version `1.4.237`.
- Run is `run_382ea93773d8`.
- Coordinator is `term_21d115f6-aaaa-4470-9ff6-43f61644589e`.
- All workers use the existing repository with separate report ownership.
- The requested proposal is stored as `POPOSAL.md`.
- Existing untracked `.agents/`, `.claude/`, and `skills-lock.json` are outside this work.

## Tasks

| Work | Orca task | Model and effort | State | Evidence |
| --- | --- | --- | --- | --- |
| Goal and FR analysis | `task_979dcd0801d4` | `gpt-6.1-sol`, `xhigh` | Succeeded on replacement, reports reviewed, worker released | [Requirements handoff](../task1-recovery/requirements-analysis.md), dispatch `ctx_9e25cb279a53` |
| Agent and backend analysis | `task_7aa6b368ce23` | `gpt-6.1-terra`, `high` | Succeeded, report inspected, worker released | [Architecture report](../task2/codebase-analysis.md), dispatch `ctx_2ceadc86ea59` |
| UI design | `task_6c7f44b9170b`, r2 child `task_831ac9447e7f` | `gpt-6.1-sol`, `high` | r2 approved by actual user response; agent browser verification remains unperformed | [Revised prototype](../task3/r2/prototype.html), [design spec](../task3/r2/design-spec.md), [approval](../ui-review-status.md#actual-r2-approval) |
| Gap analysis and sequential specs | `task_a98efbb25aac` | `gpt-6.1-sol`, `xhigh` | Succeeded as planning package; worker released; later successor decision remains open | [30-spec implementation sequence](../../../implementation-roadmap/implementation-sequence.md), [wayfinder map](../../../implementation-roadmap/decisions/000-product-map.md) |

Launch receipts confirmed the effective model and effort for Tasks 1 and 2, including the successful Task 1 replacement. Task 3 was launched after that settlement. Task 4 has not launched.

The Task 3 launch receipt also confirms effective `gpt-6.1-sol` at `high`. It received the authoritative `task1-recovery/` paths and confirmed design choices through Orca message `msg_e5e4e1c39831`.

## Human decisions

Task 1 applies `grill-with-docs`, including `grilling` and `domain-modeling`. Product questions are relayed through the coordinator. Human answers and explicit shared understanding must be recorded before Task 1 settles.

The first question round is pending in the user-facing async form. It covers the primary review journey, local versus staged hosted delivery, interface language, whether richer agent research belongs in the target roadmap, and notification channels. The coordinator omitted a redundant question about full FR coverage because the user already required it. Recommendations in that form are not accepted decisions. The worker's pending Orca question is `msg_a8f9cfa9305b`, delivered in `delivery_adf1bfca2d5b`. Reply with actual user answers before acknowledging that delivery.

Actual user answers received so far are "Campaign-first (recommended)" and "Complete a single-workspace local pilot first". Language, agent design scope, and notification choices remain pending.

Subsequent actual replies are "english and korean bilingual with switch" and "Include richer agent design in the target roadmap (recommended)". Only the notification choice remains unanswered in this round. The design must include an EN/KO switch, and the target roadmap must cover richer agent research and synthesis with an explicit validation contract.

The final first-round answer is "Include email in the first delivery". All five choices have actual user replies and were sent together through Orca reply to `msg_a8f9cfa9305b`. That question delivery is acknowledged. Shared-understanding confirmation is still pending. Email design and implementation planning are in scope; sending actual email is not authorized in this run.

The user subsequently answered "Yes, proceed with this design brief" to the consolidated brief. Task 1's shared-understanding condition is satisfied. The confirmed brief includes campaign-first full FR design, a Neo4j-style graph, the four requested colors, an EN/KO switch, local-pilot-first implementation with automated workers and inbox plus email notifications, richer agent research/synthesis in the target roadmap, and preserved authority/evidence boundaries. Human review of the actual UI remains a separate later gate.

Task 1 recovery checkpoint: Orca reports `unverifiable` agent liveness with `stale_status`, a live terminal, and no new provider transcript records after the worker's earlier factual reads. The saved matrix exists. User answers and confirmation are durably queued, but consumption is unproven. A user question asks whether to explicitly cancel and restart the attempt or keep waiting. No cancellation or retry has occurred. Tasks 3 and 4 remain unlaunched.

The user explicitly chose "Cancel this attempt and restart Task 1 (recommended)". `worker-stop` returned `stop_unknown` because the terminal is user-owned. `worker-abandon` then fenced the original attempt without closing the possibly live terminal, and its task was marked failed for the authorized retry. Replacement dispatch `ctx_9e25cb279a53` is ready on the same Task 1 with effective `gpt-6.1-sol` at `xhigh`. The replacement owns only `task1-recovery/`, as specified in the [recovery brief](task1-recovery-brief.md), to avoid shared file ownership. It received the brief through Orca message `msg_3fae5dd4dfac`. The original `task1/` matrix remains prior work, not the authoritative replacement output.

Task 4 has pending Orca gate `gate_2659342d33b8`. Resolve it only after the user reviews and approves the exact Task 3 design revision. Elapsed time, fixtures, agent review, and task completion are not human approval.

## Task 4 destination

The requested deliverable is an ordered set of implementable specs covering the approved UI and its backend and agent needs. Apply `wayfinder` to chart genuine unresolved decisions, while retaining the user's explicit specs destination. Decision tickets and implementation specs remain distinct. No feature implementation is authorized by this planning run.

## Verification boundaries

Task 2 inspected code and representative tests. It did not execute tests or live integrations. The report does not establish hosted readiness or human usefulness. No production code has changed in this run.

The coordinator ran `uv run --locked python tools/check.py`. Ruff and documentation/ERD/symlink checks passed. Pytest stopped at the previously documented freshness-sensitive assertion in `tests/test_assistant_enrichment.py:261`, with 1 failed and 51 passed. The fixture expects an October 1 capture to remain fresh after its 30-day threshold. This planning run does not change that behavior or test.

## UI review environment

Coordinator-owned preview serves only `task3/` at `http://127.0.0.1:8876/`, shell session `67982`. Port 8765 was occupied and its existing service was not touched. Entry is `prototype.html?variant=A`. The prototype uses fixture data and in-memory state only.

CUA in-app browser was unavailable. CUA Chrome access to the local preview was declined by the browser permission gate. No alternate browser surface, raw browser command, or origin workaround is authorized. The designer was informed through Orca message `msg_58b5b6958d74`. Browser interaction, rendering, screenshot, responsive layout and visual verification are pending. Source/fixture-state checks are separate evidence and cannot establish browser behavior or human approval.

Coordinator static review routed language-switch draft loss and untranslated demo controls to the UI owner. The owner reported draft preservation and localization changes. Coordinator also requested concrete target success designs for engagement spikes and sentiment shifts, rather than showing those required FR methods only as unavailable. Actual final artifact review remains pending.

The designer addressed those findings and delivered r1 with [all 99 requirement mappings](superseded/ui-design-r1/fr-ui-traceability.md), 29 passing source/fixture-state checks, and a [SHA-256 manifest](superseded/ui-design-r1/artifact-manifest.json). The coordinator independently reran the 29 checks, compared the 99 IDs without omissions/extras/duplicates, checked relative links, and reviewed the spec and guide. [Verification](superseded/ui-design-r1/verification.md) states the limits. Browser and actual human review remain pending.

Task 3 settled successfully with `msg_423972a936b6`. Release was requested; Orca retained its terminal with reason `user_takeover`, so no process was closed. The final reclaimable-worker query returned none. The original cancelled worker is also retained by Orca as user-owned. No retained terminal is treated as a new authority to edit this revision.

Task 4 remains pending its dependencies and human gate `gate_2659342d33b8`. Do not launch it or resolve the gate until actual approval of the exact r1 package or a reviewed successor. Read the recovery reports, not the old task1 draft, when dispatching Task 4. Its user-selected model and effort remain `gpt-6.1-sol`, `xhigh`.

## UI review revision r2

The user reviewed r1 and requested a conventional chatbot assistant, a monitoring line/time-series chart highlighting current data, and richer interactions in the actual knowledge graph. The user explicitly allowed the graph mockup to stay simplified. This is a request for changes, so the Task 4 review gate stays pending.

Orca child task `task_831ac9447e7f`, dispatch `ctx_fc0b0bb8814c`, owns only `task3/r2/`. The launch receipt confirms effective `gpt-6.1-sol` at `high`. The original r1 files and manifest remain the prior reviewed artifact. The r2 owner will update the prototype, design/traceability/review handoff and exact hashes together. Actual graph implementation and production feature work remain outside this design-only revision.

The previous browser-permission denial remains in effect. Filesystem permission changes do not authorize a browser workaround. The revised review will distinguish source/fixture-state checks from actual browser/visual verification.

r2 settled successfully with message `msg_363ba93dfaf6`. The coordinator accepted the artifact handoff, released dispatch `ctx_fc0b0bb8814c`, and acknowledged delivery `delivery_6845da7ce4fd`. Release closed its agent terminal and archived its transcript; the reclaimable-worker query returned none. The coordinator independently verified 45 source/fixture checks, all 99 upstream IDs, 42 relative links, unchanged r1 file identities and all 13 r2 manifest hashes. The current candidate and exact digest are recorded in [UI review status](../ui-review-status.md). The existing loopback preview also serves `/r2/prototype.html`. Actual browser/visual checks and human r2 approval remain pending. Task 4 has not started.

## Task 4 active after actual approval

The user replied "I love it" to the r2 review package. The coordinator recorded this contextual acceptance verbatim in [the actual approval record](../ui-review-status.md#actual-r2-approval), rechecked the r2 manifest and all file hashes unchanged, and resolved gate `gate_2659342d33b8`. The earlier pending-review statements above are historical checkpoints, superseded by this approval.

Task 4 dispatch `ctx_deff4c27533e` is ready with effective `gpt-6.1-sol` at `xhigh`, as confirmed by its launch receipt. The [consolidated handoff](task4-brief.md) supplies the approved r2 paths, actual review evidence, 99 upstream IDs plus three review mappings, local-pilot-first destination and planning-only boundaries. A follow-up directs the worker to read it first. No feature implementation or external operation is authorized by this planning stage.

Task 4 question `msg_67c07866cb0c`, in delivery `delivery_037de44e757e`, presents two independent later-target choices: allow an agent to draft exact human-reviewed research scope, and allow fluent synthesis only behind claim/full-input checks and actual KR/JP evaluation with withholding. The coordinator relayed both to the user through an async form. Actual answers are pending; the worker may continue independent pilot specs. Reply with actual user evidence before acknowledging this question delivery. Neither recommendation is a resolution or proof that a validation method works.

After the user questions remained unanswered, the coordinator replied to the Orca ask with explicit deferral, not a human decision: retain both later-target choices unresolved in a HITL successor-contract ticket and continue the independent pilot plan. This supersedes the prior coordinator instruction to keep the delivery unacknowledged until actual answers. The question delivery was acknowledged after that deferral was processed. The user-facing form remains pending, and any later actual replies must be forwarded verbatim and recorded separately. No agent-contract approval or HITL resolution has been inferred.

## Final Task 4 outcome

Task 4 settled successfully with `msg_aa65f71da1fc` from dispatch `ctx_deff4c27533e`. The coordinator reviewed the gap/architecture/map, full sequence, critical chat/graph/runtime/email/successor specs, and source generator. Review corrected numeric dependency ordering, satisfied-versus-future approval evidence, open-view policy freshness, stable email retry identity and the truthful deferred-question record. These are proposed implementation contracts, not executed feature work or accepted successor ADRs.

The final independent `verify_plan.py --frontier` run passed 30 unique sequential specs, 63 acyclic dependency edges, 99 upstream plus three r2 review IDs, 1,279 local links/anchors across 37 Markdown files, the single canonical map/open child, and all 13 approved r2 file hashes. Repository static checks passed separately. The inherited full behavioral-suite failure remains documented, and [the first spec](../../../implementation-roadmap/specs/01-stable-verification-clock.md) repairs its fixture before further implementation. No production code, database, durable product docs or approved UI changed during Task 4.

The [implementation sequence](../../../implementation-roadmap/implementation-sequence.md) is the main handoff. Specs 01–18 are pilot build work; 19–20 require actual provider and human validation; 21–30 preserve deeper and broader target work. [Set the richer research and synthesis boundary](../../../implementation-roadmap/decisions/001-richer-agent-boundary.md) remains an open actual-human decision plus future evaluation prerequisite. It directly blocks only richer-agent production enablement, not any pilot build spec. The first dependency-ready build unit is the time-stable verification baseline, subject to its real environment/database prerequisites.

Release of the final worker succeeded, its transcript was archived and its terminal closed. Delivery `delivery_29139d8d79ce` was acknowledged. The final reclaimable-worker query returned none. Two older user-owned terminals remain retained by Orca as previously recorded. All requested analysis/design/planning task dispatches are settled. The actual product implementation and live/usefulness acceptance remain future work.
