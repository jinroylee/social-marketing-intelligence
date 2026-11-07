# Implementation roadmap

This roadmap is the ordered plan from the installed system to the approved product. It builds a campaign-first, single-workspace local pilot first, then the later depth. It is a proposed plan: nothing in it is implemented behavior or an accepted ADR. The [product documentation](../docs/README.md) describes what the software does today.

## Start here

Read [the implementation sequence](implementation-sequence.md). It lists all 45 specs in build order, with direct blockers, milestones, critical paths, safe parallel waves and each spec's execution mode. It also lists the user decisions that still need answers. Building starts with [S01](specs/01-stable-verification-clock.md), the only spec with no blockers.

## Layout

| Path | Contents |
| --- | --- |
| [`implementation-sequence.md`](implementation-sequence.md) | Entry point: order, blockers, milestones, critical path, parallel waves and user decisions |
| [`specs/`](specs/01-stable-verification-clock.md) | 45 specs. Each header gives size, execution mode, owners and direct blockers |
| [`decisions/`](decisions/000-product-map.md) | Decision map plus open decisions W01 (richer agent, blocks S39) and W02 (live X windows, blocks no spec) |
| [`gap-analysis.md`](gap-analysis.md) | Installed foundations compared with the approved target |
| [`architecture-target.md`](architecture-target.md) | Proposed module ownership and shared contracts |
| [`traceability.md`](traceability.md) | Maps each of the 99 requirement IDs and three r2 UI IDs to its specs and acceptance checks |
| `plan.json`, `traceability.json` | Machine-readable copies of the plan and trace |
| [`source/`](source/plan_source.json) | `plan_source.json`, the only file to edit. Also holds the templates, generators and verifier |
| [`verification/`](verification/verification-results.txt) | Latest verifier and static-check output |

## Implementing a spec

Spec files are plans, not tickets. Publish and claim the work through [the local issue tracker](../docs/agents/issue-tracker.md) before starting. A **single-pass** spec is small and pinned enough for one agent to finish. A **wayfinder** spec lists the decisions to chart first, and is then split into slices.

## Changing the roadmap

Edit [`source/plan_source.json`](source/plan_source.json). Edit the gap-analysis and architecture text in the `.tmpl` files in `source/`. Never edit the rendered files: the specs, the sequence, the gap analysis, the architecture, the traceability files and `plan.json` are all overwritten on regeneration. Specs refer to each other with `{{slug}}` tokens, so S-numbers renumber automatically.

Regenerate and verify from the repository root:

```bash
python implementation-roadmap/source/build_plan.py
python implementation-roadmap/source/write_sequence.py
python implementation-roadmap/source/verify_plan.py --frontier > implementation-roadmap/verification/verification-results.txt
uv run --locked python tools/check.py --static > implementation-roadmap/verification/static-check-results.txt
```

The verifier checks structure only. That covers unique specs, dependency order and rationale, decision blockers, complete requirement coverage, links and the approved UI hashes. It cannot prove that a spec is correct or that a human accepted it.

## Inputs

The approved inputs stay in [`.scratch/product-design-2026-11/`](../.scratch/product-design-2026-11/README.md):

- **Requirements:** the matrix and decisions in `task1-recovery/`.
- **Codebase analysis:** `task2/`.
- **Approved UI design:** r2, in `task3/r2/`.
- **UI approval:** the record in `ui-review-status.md`.

The specs link to these inputs, and the verifier reads the requirement IDs and UI hashes from them. Leave them where they are. The r2 design is locked by file hashes and links to its sibling folders by relative path, so moving any of them breaks it. The same folder keeps the review history for both spec-review rounds.
