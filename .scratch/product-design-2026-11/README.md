# Product design, November 2026

This folder holds the inputs and working history of the November 2026 product-design effort. The implementation roadmap built from them now lives at the repository root in [`implementation-roadmap/`](../../implementation-roadmap/README.md). Nothing here is an accepted product contract or implemented behavior.

## Layout

| Path | What it is |
| --- | --- |
| [`task1-recovery/`](task1-recovery/requirements-matrix.md) | Approved requirements analysis, the 99-ID requirement matrix and the user's decisions |
| [`task2/`](task2/codebase-analysis.md) | Backend and agent codebase analysis |
| [`task3/r2/`](task3/r2/design-spec.md) | Approved UI design r2, with its prototype, design spec and requirement mapping |
| [`ui-review-status.md`](ui-review-status.md) | The user's recorded UI feedback and r2 approval |
| [`history/`](history/run-state.md) | Orchestration log, task briefs, both spec-review rounds and superseded drafts |

The roadmap's specs link to the first four entries, and its verifier reads requirement IDs and UI hashes from them. Keep their names and positions. The r2 UI package is locked by its manifest's file hashes. Its links reach `task1-recovery/`, `task2/`, `ui-review-status.md` and `task3/shared-check-results.txt` by relative path.

## History

- [`history/spec-review/`](history/spec-review/) holds both review rounds of the roadmap. Each round has the reviewer and validator prompts, the review, the validation verdict, the script that applied the accepted changes, and `applied.md`. Round 1 grew the plan from 30 to 40 specs, and round 2 from 40 to 45.
  - Spec numbers in these records use the numbering of their round, not the current one.
  - Snapshots of the earlier spec lists were deleted.
  - The `apply_*.py` and `classify.py` scripts have already been applied and cannot be rerun.
- [`history/run-state.md`](history/run-state.md), [`history/task1-recovery-brief.md`](history/task1-recovery-brief.md) and [`history/task4-brief.md`](history/task4-brief.md) record the original Orca run. Task 4 produced the roadmap.
- `history/superseded/` holds two pieces of replaced work:
  - `task1-draft/` is the abandoned first requirements attempt, replaced by `task1-recovery/`.
  - `ui-design-r1/` is the first UI design, replaced by r2 after the user's feedback. Its files are kept byte-for-byte to match their manifest, so their links to sibling folders no longer resolve.

  Neither is needed for implementation.
