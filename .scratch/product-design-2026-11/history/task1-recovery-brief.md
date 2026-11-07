# Task 1 recovery brief

This brief supplements the original Task 1 spec for the authorized replacement attempt. Read it before writing or asking questions.

## Accepted user decisions

The user answered the first decision round with these exact replies.

1. Main review journey. "Campaign-first (recommended)".
2. Next implementation sequence. "Complete a single-workspace local pilot first".
3. Interface language. "english and korean bilingual with switch".
4. Target agent design. "Include richer agent design in the target roadmap (recommended)".
5. Notifications. "Include email in the first delivery".

The user then answered "Yes, proceed with this design brief" to the consolidated understanding below. This is actual shared-understanding confirmation, not an inferred approval.

The confirmed brief is a campaign-first UI covering every FR, including the Neo4j-style graph, using `#E6002A`, `#F4ABAF`, `#3E3A39`, and `#FFFFFF`, with a working EN/KO switch. The implementation sequence completes a single-workspace local pilot first, including automated workers, an in-product inbox, and email notifications. The target roadmap also designs richer agent research and grounded synthesis. Automatic shortlist saving, explicit regeneration, exact approval for assistant-origin external enrichment, publication before answers, and monitoring investigations using existing KB context remain intact. Human review of the actual UI is required before Task 4 starts.

The user's later reply "Cancel this attempt and restart Task 1 (recommended)" explicitly authorizes the replacement after the original worker stopped showing progress.

## Ownership

The original attempt is fenced in Orca. Its terminal could not be closed because Orca marked it user-owned. Its process exit is unproven. Therefore, the replacement must write ONLY `.scratch/product-design-2026-11/task1-recovery/`. This ownership supersedes the original spec's task1 output directory.

Read `.scratch/product-design-2026-11/task1/requirements-matrix.md` as prior work. Verify and reuse the useful matrix in the new directory. Do not overwrite the original worker's files. Read `task2/codebase-analysis.md` relative to this brief for the completed backend analysis.

## Remaining work

Complete the goal/FR analysis, traceability matrix, decision record, and Task 3 brief in the recovery directory. Use the original sources, glossary, ADRs and skills. Do not repeat the answered interview or request another shared-understanding confirmation. Raise only a newly discovered material contradiction that cannot be resolved from accepted scope.

The full FR UI is the target. Local-first is a deployment choice, not permission to defer automated acquisition, monitoring, background task processing or email. Hosted multi-user identity and tenancy remain later work. Richer agent capabilities require explicit evidence/validation contracts and future ADR work. Do not silently replace accepted bounded-answer ADRs 0017/0018.

Record accepted product decisions as analysis decisions. Do not edit production code, durable owner contracts, glossary or ADRs during this recovery. No feature implementation, commits, external spend or actual email sending is in scope.

## Existing verification

The coordinator ran `uv run --locked python tools/check.py`. Ruff and documentation/ERD/symlink checks passed. Pytest stopped at the documented aging-fixture assertion in `tests/test_assistant_enrichment.py:261`, with 1 failed and 51 passed. Do not rerun or fix the unrelated baseline test in this analysis.
