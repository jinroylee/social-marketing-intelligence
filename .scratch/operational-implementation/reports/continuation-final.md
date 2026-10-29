# Operational implementation handoff

Tickets **01–38 are resolved** on `integration/operational-tickets-11-39`. Ticket **39 remains claimed / ready-for-human**, with all six acceptance criteria unchecked. Its preparation is committed; actual human review remains an external prerequisite.

## Commits and scope

- Original final-review baseline: `6220fff49b5b8e982ef5a8d54b7c788e45b0f648`.
- Final application corrections: `7418e5bc0af72d70017b5eb612dcd2c37f265c57`.
- Live-promotion regression fixture using current UTC time: `a70341a9db36b8f081869483cc1c3ceb32eee750`; application source is unchanged from the final corrections.
- Shared active cost-period and runtime-meter attestation fixtures: `ecc011fd647c531d78aefdacf966b91eeb2f1578`, frozen after integration metadata at `99539925af5fd6c619e9eec04fc249ecab7a6cc5`. Exactly three test files differ from the final application runtime.
- Exact per-ticket implementation, integration and validation commits are retained in `execution-manifest.json` (01–10) and `continuation-manifest.json` (11–38). Original draft proposals remain historical; published `issues/` are authoritative.

The delivered software covers governed evidence ingestion/publication/search, campaign criteria and persisted supported rankings, bounded task execution/recovery/scheduling, shared cost admission/reconciliation, approved assistant enrichment and supported answers, recent monitoring and alerts with existing-KB context, selected promotion, governed graph exploration, lineage and review packets. Live routes remain disabled pending their documented runtime prerequisites.

## Validation

All shared checks use `UV_OFFLINE=1 uv run --locked python tools/check.py`, real local PostgreSQL and simulated external I/O.

| Final gate | Checked commit | Tests | Seconds | Exit / session |
| --- | --- | --- | --- | --- |
| Worker | `99539925af5fd6c619e9eec04fc249ecab7a6cc5` | 903 | 639.58 | 0 / 38137 |
| Integration | `46321bfa577653104e1868dd76d37f121106b829` | 903 | 635.98 | 0 / 88182 |

Exact commands, heads and start/finish/exit evidence are in the retained [worker gate](../verification/retained-workers/final-cost-fixtures/.scratch/operational-implementation/verification/final-cost-fixtures/shared.json) and [integration log](../verification/final-cost-fixtures-integrated/shared.log). Later commits change only tracker/report metadata; the protected tree was verified again after cleanup.

Earlier completed ticket gates and final-review passes remain preserved. The expired live-promotion fixture was reproduced and repaired, passing three lifecycle cases, 83 compatibility cases and worker/root full checks (903/625.37s and 903/641.63s). The subsequent cost-fixture correction passed 170 compatibility cases before the final gates above. Its shared active period ends 365 days after test import; one runtime-meter case derives stable later attestations from the public failure record. Historical measurements, inactive periods, half-open endpoints, early-attestation rejection and exact retries remain covered.

Final Standards review closed **3 documented findings and 1 heuristic**. Final Spec review closed **1 finding**, overlapping the ranking permission race. All four unique findings were fixed in the same implementer context and independently rechecked by the original reviewers. The fixes enforce current ranking-input policy through dispatch commit, consistent context/promotion lock order, full quantitative alert evidence permissions and shared Responses-envelope parsing. See `reviews/standards.md`, `reviews/spec.md`, `reviews/fix-checklist.json` and `reports/final-review-fixes.md`.

The retained wheel is **450808 bytes / 215 unique entries**, SHA-256 `de6929ea94473a7c20961f1776d0fed742c02edda62f6c0d37dc2bf64c23fc8a`. Its standalone verifier matches all **211 packaged source/archive pairs**, **19 SQL schemas**, **2 assets**, **33 packaged / 35 total guidance pairs**, and every byte/hash/relative target in the **344-file corrected protected snapshot**. All **174** packaged paths changed since the original review baseline are covered. Application source is identical to `7418e5bc0af72d70017b5eb612dcd2c37f265c57`; the three test-fixture changes are outside the package.

## Preserved evidence and cleanup

Ticket 26–38 logs/wheels/manifests/verifiers, ticket 39 preparation and all three final-fixer evidence snapshots have persistent archives and usable extracted copies under `verification/worker-archives/` and `verification/retained-workers/`. `reports/worker-artifact-relocation.md` records archive hashes; the excluded `verification/worker-archives/relocation-index.json` includes every member's size/hash, original absolute path and current retained path. All **15 available clean merged worker worktrees** have been removed without force; only the integration worktree remains. All branch refs survive. The latest retained verifier was run successfully after removal against the integration tree and retained wheel (exit 0; `verification/post-cleanup-wheel-verification.json`). All **17 archives / 583 retained files** were hash-verified before final removal. The relocation index SHA-256 at cleanup is `6adf7bcb207b0a2411845005ae44fca261db50ffd7bf674bc7cb70e4d1d4c011`. The local archive/copy directory is intentionally excluded from Git and must accompany this checkout when moving its evidence.

Older untracked verification files for tickets 11–25 had already disappeared from temporary worktrees before this cleanup. Their committed reports/manifests and branch history survive; those missing raw logs/wheels remain unavailable. The latest complete shared checks validate the current integrated tree.

## Remaining prerequisites

Ticket 39 needs an actual named reviewer and permitted result workspace/examples, followed by actual baseline-before-assisted observations, task times/counts, attributed translations and campaign/assistant/alert feedback. `reports/ticket-39-handoff.md` provides the procedure and `reports/ticket-39-inventory.json` records the scoped read-only availability check. That check discovered no selectable records in the inspected public/local workspace. Qualified adjudication is required to validate Japanese-original accuracy; other review dimensions remain distinct.

Actual source/model credentials, source-use and live-operation authority, current commercial/rate/ceiling configuration and separately authorized live acceptance receipts remain external runtime gates. All source/model execution during implementation was simulated. No push, PR, deployment or external message occurred. The overall objective remains pending ticket 39.

Current links: [per-ticket commit map](../continuation-manifest.json), [first-batch commit map](../execution-manifest.json), [artifact relocation](worker-artifact-relocation.md), [human review procedure](ticket-39-handoff.md).
