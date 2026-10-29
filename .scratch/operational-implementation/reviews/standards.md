# Standards

Reviewed `6220fff49b5b8e982ef5a8d54b7c788e45b0f648...b75b8b6a454ae9abdb5f7f7450837b79d7801753`; both refs resolve and the diff is nonempty. Read the supplied standards inventory and relevant owner contracts. Existing broad passing checks were preserved.

## Documented breaches

1. **P1 — Recheck ranking inputs at dispatch.** `src/smi_campaigns/ranking/__init__.py:89–92` calls shared admission without a `dispatch_guard`. ADR 0002:5 requires source permissions/withdrawal to be evaluated “at each use”; ADR 0009 retains that current-policy contract for governed ranking inputs. Public repro: block ranking on its cost-scope lock, revoke its observation through `EvidenceStore.revoke`, then release admission. One simulated model call still receives the withdrawn candidate input and settles `0.175`; only final publication becomes `stale`. Pass an owner-provided exact-input policy/derivation guard through the existing shared admission port, retaining source locks through dispatch commit.

2. **P2 — Remove the context/promotion lock cycle.** `src/smi_monitoring/context/store.py:68–82` holds recent policy before requesting the knowledge frontier; `promotion/store.py:50–51` takes them in reverse order. This conflicts with the documented frontier-before-recent composition order (`docs/monitoring.md:136`, promotion `AGENTS.md:5`) and root `AGENTS.md:9,16` explicit failure/boundary handling rules. Concurrent public `investigate`/`promote` reproduced PostgreSQL `DeadlockDetected` (`40P01`), aborting promotion. Establish a consistent owner lock order through public ports.

3. **P2 — Withhold quantitative alert evidence after process denial.** `src/smi_monitoring/alerts/store.py:144–155` hides the comparison but returns display-only window bodies despite failed process checks. Its `AGENTS.md:9` requires current process/display/retention permission for displayed alert evidence. Public repro: set `can_process=False`, retain display/retention, reopen the alert: `current_support=unavailable`, yet five source bodies remain. Apply the alert owner's full-permission overlay to nested windows and HTTP rendering.

## Baseline heuristic — judgment, not violation

4. **Possible Duplicated Code.** `src/smi_campaigns/interpretation/__init__.py:38–50` repeats `responses/__init__.py:119–131`: “`contents = []`”, message validation, “`contents.extend(item['content'])`”, refusal detection and JSON extraction. Reuse public `generated_document`, preserving criteria-specific refusal mapping, so envelope fixes have one owner.

Reproductions/evidence: `standards-verification.py`, `standards-ranking-verification.py`, `standards-findings.json` beside this report. Only local PostgreSQL and simulated model I/O were used; no live provider/source/model calls or external network.

**Standards total: 3 documented breaches, 1 heuristic. Worst: withdrawn ranking input can still dispatch and spend.**
