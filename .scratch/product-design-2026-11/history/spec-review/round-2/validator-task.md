ROLE: independent validator of a spec review (round 2). Read-only except your one output file.

CONTEXT
Repository: /Users/makinarocks/workspace/personal/social-marketing-intelligence
A planning package of 40 ordered implementation specs lives in .scratch/product-design-2026-11/task4/ (entry: implementation-sequence.md; specs/01-*.md..40-*.md; plan_source.json is the single editable source keyed by slug, rendered by build_plan.py into the specs, plan.json and traceability; gap-analysis.md; architecture-target.md; decision issues in .scratch/product-design-2026-11/wayfinder/issues/). It was already revised once; that round's records are in .scratch/product-design-2026-11/spec-review/round-1/ (review.md, validation.md, applied.md) and you may read them to weigh consistency with decisions already taken. Another agent wrote a critical review of it:
.scratch/product-design-2026-11/spec-review/round-2/review.md
Your job is to decide whether that review is actually worth accepting, and if so, turn it into a concrete revision suggestion that the coordinator will apply to the spec list.

ULTIMATE GOAL (the yardstick for every judgment)
Close the gap from the actual installed code to the approved product and UI with an ordered set of individually implementable specs that a team of agents can execute. The user-confirmed first delivery is a campaign-first, single-workspace LOCAL PILOT with: real automated discovery, monitoring and background task processing; a familiar EN/KO-switchable chat assistant; a monitoring time-series chart highlighting current data; in-product inbox plus email; and a genuinely interactive Neo4j-style knowledge graph. Every FR must keep an implementation or explicit later path. Richer agent research/synthesis is target-roadmap scope; hosted tenancy is later. Existing authority/evidence invariants (ADRs in docs/adr/) stay in force.
Goal sources: .scratch/product-design-2026-11/task4-brief.md; .scratch/product-design-2026-11/task1-recovery/requirements-analysis.md and decisions.md; .scratch/product-design-2026-11/task3/r2/design-spec.md (approved UI); .scratch/product-design-2026-11/ui-review-status.md; FR.md; docs/functional-requirements.md; src/ and tests/.

WHAT TO DO
1. For EVERY finding in review.md (R2-F01..R2-F14) and for its proposed reordering table, independently re-verify the cited evidence in the code/specs (spot-check file:line claims yourself; do not take them on trust), then decide: ACCEPT, ACCEPT-MODIFIED (say exactly what you change), or REJECT (say why). Be skeptical in both directions: reject findings that are wrong, overstated, would cause churn without moving the ultimate goal, add process overhead, or contradict accepted ADRs/user decisions; and also note anything material the review missed.
2. Give an overall verdict line, exactly one of:
   VERDICT: YES — the review is worth accepting (fully or with modifications)
   VERDICT: NO — the review should not change the spec list
3. If YES, produce a REVISION SUGGESTION precise enough for the coordinator to apply mechanically:
   a. The complete revised ordered spec list (final IDs in execution order), each row with: stable slug (keep existing slugs for unchanged specs), title, lane (pilot-build / live-validation / human-validation / later-core-depth / later-candidate / human-validation-later / decision-blocked / later-proposal), size (S/M/L), milestone (M0-M5 or Later), direct spec dependencies, and a one-line rationale for EACH dependency edge. If only a few rows change, you may instead list just the changed/added/removed rows plus the final order of slugs.
   b. For each new, split, merged or materially changed spec: the outcome, scope/non-goals, owner, key interface/data-shape notes, and 3-5 acceptance checks.
   c. Which requirement IDs (FR-*, OFR-*, PROP-*, UD-*, R2-*) move to which new/split specs, when coverage changes.
   d. Corrections needed in gap-analysis.md / architecture-target.md / implementation-sequence.md narrative (milestones, critical path, parallel work).
   e. Items that are genuine USER decisions (not engineering choices) listed separately, with a recommended default so the plan is not blocked on them.
   This is the final review round, so the revised list must be ready to execute. Prefer the smallest revision that captures most of the value; avoid churn on parts round 1 already settled unless the evidence shows they are wrong; do not split or add specs unless it clearly improves executability or risk ordering toward the goal.

OUTPUT
Write exactly one file: .scratch/product-design-2026-11/spec-review/round-2/validation.md
Structure: (1) VERDICT line; (2) per-finding decision table with one-paragraph justification each; (3) missed issues, if any; (4) REVISION SUGGESTION (sections a-e) if YES.

CONSTRAINTS
- Do not edit any file other than validation.md. Do not modify specs, plan.json, generators, code, docs, git state or wayfinder issues; the coordinator applies changes.
- No browser automation, no external network or paid provider calls, no email, no commits. Read-only commands only; do not run the full test suite.
- Own the judgment yourself; use sub-agents only to speed up reading.

OBSERVABLE ACCEPTANCE
validation.md exists with the VERDICT line and the sections above. Then send worker_done exactly once with --outcome succeeded (or failed), --files-modified and --report-path pointing to validation.md, and put the verdict (YES/NO) in the first sentence of the summary.
