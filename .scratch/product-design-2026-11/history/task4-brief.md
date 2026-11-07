# Task 4 consolidated handoff

This brief supplements the original Orca Task 4 spec. Read it first. It updates input paths and records the satisfied human gate without changing the requested model or destination.

## Actual approval

The user responded to the delivered r2 approval request with "I love it" on November 3, 2026. The coordinator records this as acceptance of the revised UI, with no further changes requested. The exact record is [UI review status](../ui-review-status.md#actual-r2-approval). The approved manifest SHA-256 is `1c1875228eab75585e865b10f3d68003bc09b251d5ca72754a63beb0774d24b5`; all file hashes were rechecked unchanged. Orca gate `gate_2659342d33b8` is resolved on that actual user response. Do not re-ask UI approval or the settled requirements interview.

Agent browser access was declined earlier and remains declined. UI acceptance is distinct from completed browser tests, language/usefulness review, provider access or production acceptance. Do not attempt browser automation or a workaround. Task 4 is planning only.

## Authoritative inputs

Read the following paths from the repository root:

- `POPOSAL.md`, `FR.md`, `docs/functional-requirements.md`, `GLOSSARY.md`, relevant accepted ADRs, owner contracts and actual code.
- `.scratch/product-design-2026-11/task1-recovery/requirements-analysis.md`, `requirements-matrix.md`, and `decisions.md`. The old `task1/` directory is superseded prior work.
- `.scratch/product-design-2026-11/task2/codebase-analysis.md`.
- `.scratch/product-design-2026-11/task3/r2/prototype.html`, `design-spec.md`, `fr-ui-traceability.md`, `changes.md`, `review-guide.md`, `verification.md`, and `artifact-manifest.json`. The parent `task3/` r1 files are prior work, not the approved current input.
- `.scratch/product-design-2026-11/ui-review-status.md` for actual user answers and approval.
- Root and relevant local `AGENTS.md`, `docs/agents/domain.md`, `docs/agents/issue-tracker.md`, and `docs/agents/triage-labels.md`.

The 99 stable upstream analysis IDs and the three r2 mappings `R2-CHAT`, `R2-STREAM`, and `R2-GRAPH` must receive an explicit implementation or later-proposal path. Preserve the source distinction between core FR and proposal extensions.

## Destination and scope

The deliverable is a sequential list of implementable specs closing the gap from actual code to the full approved UI and product. Apply `wayfinder` to chart genuine decision uncertainty and maintain one canonical map, while honoring the user's explicit implementation-spec destination. Do not stop at a decision-only map or a generic recommendation list. No feature implementation, code fixes, database changes, provider calls, actual email, commits or deployment are part of this run.

The confirmed first delivery is a campaign-first, single-workspace local pilot. It includes actual automated discovery, monitoring and task consumption, a familiar EN/KO chat interface, a current-highlighted monitoring time series, inbox plus email, and a genuinely interactive production knowledge graph. Hosted accounts/tenancy remain later work. Richer agent research and grounded synthesis belong in the target roadmap and require explicit evidence/validation and ADR successor work.

Every approved UI action needs a real backend/read-model/command and agent support path, not only a frontend task. The r2 conversation contract covers threads, turns, bounded context, drafts, retry/version state and per-turn evidence. Monitoring history covers bounded windows, metric-specific denominators, missing versus zero, latest versus selected window, current-policy evidence and baseline/method failures. Actual graph requirements cover pan/zoom/fit, drag/pin/layout, incremental branch expansion/collapse, filters, stable selection, cursors, stale-response rejection, withdrawal, and keyboard/list alternatives. Their simplified mockup is not permission to defer the actual graph interaction requirements out of the pilot without saying so.

Preserve the existing modular Python/PostgreSQL owner boundaries where useful. Verify material gap claims against composition roots, public operations and representative tests. Do not choose microservices, a graph database, a new agent framework, a queue vendor or a wholesale rewrite just to match a UI metaphor. Name new module ownership, public signatures/data shapes, migrations and documentation obligations in the specs where needed, but keep those as proposed implementation contracts rather than secretly accepted durable ADRs.

Maintain automatic shortlist saving, incomplete-account eligibility, visible versioned criteria, explicit successor regeneration, exact human approval for each assistant-origin external task, configured campaign/schedule authority, publication before answers, KB-only monitoring investigation, separate light monitoring evidence, source lifecycle, finite acquisition bounds and independent spending control. A conversational yes or model plan cannot create approval. Completion, publication, current availability, notification event and transport delivery remain separate states.

## Map and specs

Own only `.scratch/product-design-2026-11/task4/` and `.scratch/product-design-2026-11/wayfinder/`. Do not alter approved UI, prior reports, root review records, production code, durable docs or existing untracked skill files.

Use the supplied local Markdown tracker. It has no native parent/blocking relationships and no Wayfinding operations section. Record the exact fallback in the map Notes. Put the canonical map and child decision issues under the wayfinder directory, with explicit parent, assignee/claim, status and named blockers, and only `wayfinder:` labels. Keep implementation specs in `task4/specs/`, distinct from decision tickets; connect specs to direct decision blockers and each other with names and real local links. Do not invent human resolutions, auto-close HITL issues, pre-fill fake research or create unnecessary fog.

The destination, priorities, deployment scope and UI are already settled by actual exchanges. Reuse those decisions as evidence. Choose routine, reversible engineering recommendations with rationale and proposed status. Ask through your live Orca `ask` only for a newly surfaced material product/domain fork that cannot be resolved from accepted input. Continue independent work while an answer is pending. Do not ask the user to provide facts available in code or to choose provider/credential details that can remain explicit configuration. Do not spawn workers for facts wholly inside this repo; coordinate any genuinely necessary external research first.

Deliver `gap-analysis.md`, `architecture-target.md`, `implementation-sequence.md`, individually implementable numbered spec files, and explicit FR/UI/contract/spec/acceptance traceability. The sequence is the main reader entry. State the first executable spec, direct blockers, useful vertical milestones, critical path and safe parallel work. Each spec needs concrete outcome, current evidence, scope/non-goals, owners and interfaces/data shapes, migrations and documentation/AGENTS obligations, UI and agent integration, authority/invariants, failure/recovery, direct dependencies and meaningful public-operation acceptance checks. Specify actual completion evidence, including empty, partial, conflict, withdrawn, failed meter and unknown-response cases where material. Avoid a giant final catch-all integration spec or a scaffold-only sequence.

Distinguish executable pilot build specs, blocked contracts, provider/live/human readiness work and later proposal extensions. A live authorization or actual reviewer input cannot be marked done by code/fixtures. Core FR capabilities cannot be moved to the optional proposal lane merely because their installed version is narrow. Later multimodal, richer ontology, portfolio, actual outcomes/attribution/causal methods and hosted operation remain visible with explicit prerequisites, without making every proposal ambition a first-release blocker.

Build a small rerunnable planning verifier if useful. It should check complete ID coverage, real links, unique spec identities, an acyclic dependency graph, valid decision blockers and consistency of the claimed executable frontier. Passing structure cannot establish implementation quality or resolve a human choice. Link the actual verification output.

## Existing baseline and boundaries

The installed code is a bounded local modular system with explicit worker operations, tool-free exact-finding model selection, PostgreSQL and local evidence files. It lacks a hosted identity system, continuous consumer, real conversational synthesis, broad progressive acquisition and the richer full target methods, as the reports detail.

The full shared check has an existing documented aging-fixture failure at `tests/test_assistant_enrichment.py:261`: a fixed October 1 capture is stale beyond 30 days. Prior actual runs stopped with 51 passed and 1 failed; static checks pass. Include a narrow fixture-maintenance/readiness prerequisite so implementation does not weaken freshness policy or falsely claim a green baseline. Do not fix it during planning or rerun the unchanged full suite repeatedly. Use static/planning checks appropriate to these scratch artifacts and report inherited limits honestly.

After finishing, check coordinator follow-ups, send `worker_done` exactly once with your live Task/Dispatch and succeeded/failed outcome, real files and report path, then idle. The coordinator reviews the package, owns lifecycle cleanup and reports the final sequence to the user.
