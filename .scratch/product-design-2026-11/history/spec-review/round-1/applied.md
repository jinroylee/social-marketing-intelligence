# Round-1 revision as applied by the coordinator

Inputs: [review](review.md) (14 findings) and [validation](validation.md) (VERDICT: YES, all findings accepted with modifications). The coordinator applied validation.md section 4 mechanically through [apply_round1.py](apply_round1.py) on `task4/plan_source.json`, then regenerated specs, `plan.json`, traceability and the sequence.

## Applied

- 4a: the 40-spec order, lanes, sizes and every dependency edge with its one-line rationale (72 edges). Computed depths match validation.md: probes 3; campaign, chat and graph 4; chart and engagement 5; deepest build spec 6; readiness 7; release 8 (was 8 and 9).
- 4b: new specs S02, S03, S04, S05, S06, S13, S16, S19, S23 and S26 written from the validator's outcome/scope/owner/acceptance text; rescoped S01, S08, S10, S11, S12, S14, S15, S17, S18, S20, S21, S22, S25, S27, S28, S29 and S30. The cross-cutting UI rule (shared freshness utility, EN/KO keys, parity-then-retire legacy forms, human checklist) is stated once in the renderer and applied to every UI-bearing spec, replacing the four repeated `-A05` freshness checks.
- 4c: requirement-ID moves and additions. UD-09 was already recorded as `satisfied-upstream` with no spec, so no change was needed.
- 4d: gap-analysis rows for test baseline, composition, client, retrieval scale, interpretation and monitoring depth; corrected oEmbed/web wording and the `--maxfail=1` baseline statement; architecture "Pilot composition and client foundation" section, owner-table and interaction-table renumbering, and parity-then-retire wording; sequence now generated from `plan.json` (milestones, computed critical paths, parallel waves, user decisions).
- 4e: W02 charted as `wayfinder/issues/002-x-metric-measurement-time.md` blocking S21 only; U1–U7 recorded in `plan.json` and the sequence with defaults. No user decision was resolved.

## Tooling changes

- `plan_source.json` is now the single editable source keyed by slug; `build_plan.py` renders it (refactor verified byte-identical on the original 30-spec package before any revision).
- `verify_plan.py` now enforces one non-empty rationale per edge, an S/M/L size per spec, S01 as the only dependency-free spec, and that each decision issue's `Blocks:` line names the spec it blocks.

## Not applied or deviations

None material. The freshness timer stays (validator rejected moving it to hosted), as do S08 cursor binding and S15 command receipts.
