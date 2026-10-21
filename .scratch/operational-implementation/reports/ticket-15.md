# Ticket 15 — Automatically saved ordered shortlists

Scope: only published ticket 15. Fresh `smi/operational-ticket-15` worktree confirmed ancestor `d0e71f89534df88f5b915f0f26e892fa7b42bf2b`; integration metadata `7f9926491e5fe5cd7d9ec2113da3e4ab1b50924d` merged before final validation. Implementation commit: `a80da4dca903b95d2c9aa9fe6bf8f845a6415a4c`. Ticket stays **claimed** for the merger's integrated gate.

## Delivered

- `CampaignStore.recommend` atomically composes the current-KB comparison with an ordered `generated` shortlist revision. It records the actual automation producer, exact brief/selected profile/method, deterministic rationale, explicit gaps and pinned support. It requires an existing human-initiated campaign and no human review, approval, confirmation or acknowledgement.
- Only candidates meeting the existing deterministic required/exclusion/unknown policies are selected, in their comparison order. Empty results persist with source-free candidate/selection/exclusion/deferral counts and an explicit reason. Unsupported references stay discovery gaps. Encounter order remains unranked and makes no LLM-assessment/global-score claim.
- Identical requests reopen the original before reassessment, across restart and changed knowledge/briefs. Changed body/actor conflicts; new requests check both heads. A fresh server-created nested comparison identity prevents client-chosen retry strings from supplying a historical assessment. Query/comparison/shortlist writes roll back together on failure, with source/publication/brief locks held through commit.
- Legacy human statuses, actors, timestamps, reasons, acknowledgements and history survive migration; historical method/order/selection summary/positions stay unrecorded. Current policy hides dependent rationale/gaps/support, retention purges copies, and permitted order/membership/producer remain pinned. Human save/confirmation remains compatible.
- The protected HTTP recommendation form supplies server automation, rejects forged authority/status fields, preserves exact retry/profile/version context on recoverable errors, and reopens generated results without a review form. Contracts, ADRs, architecture, physical ERD/dictionary and existing owner guidance are aligned; relative instruction symlinks remain intact.

## Red → green and verification

Approved seams: public owner operations and HTTP, real isolated-schema PostgreSQL, simulated external I/O. Fault/legacy/lock setup uses DDL and source-policy setup only; outcomes use public readers/HTTP. No internal-store mocks or SQL outcome assertions were added.

Initial operation red: absent `CampaignStore.recommend`; green: ordered automatic persistence and attribution. HTTP red: absent recommendation form; green: immediate save/reopen with server producer and no human flags. Empty-outcome red: missing durable selection summary; green: explicit no-support versus required-criteria outcome. Review-found collision red: client-chosen nested identity reopened a revoked historical comparison; green: a new recommendation takes a fresh server-created comparison identity and saves the current empty scope.

- `UV_OFFLINE=1 uv run --locked pytest -q tests/test_recommendations.py`: initial **12 passed in 11.10s**, covering save/order/empty, actual producer/no acknowledgement, retry without reassessment, actor/body/version conflicts, concurrency/commit locks, policy withdrawal, legacy upgrade, exclusions, exact selected model profile with no additional dispatch, rollback and forms/restart.
- Compatibility command: `UV_OFFLINE=1 uv run --locked pytest -q tests/test_recommendations.py tests/test_campaigns.py tests/test_current_comparisons.py tests/test_review.py tests/test_monitoring_planning.py tests/test_criteria_interpretation.py --tb=short --maxfail=1`: **142 passed in 148.17s**. The later collision fix's focused regression (`-k client_chosen`) then passed **1 test in 0.35s**; final shared verification includes all **13** ticket tests.
- `UV_OFFLINE=1 uv run --locked python tools/check.py --static`: passed Ruff, product links, physical ERD coverage and relative instruction symlinks after documentation updates.
- Final `UV_OFFLINE=1 uv run --locked python tools/check.py`: **404 passed in 263.25s**. Ruff, product links, physical ERD coverage, relative instruction symlinks and real PostgreSQL preflight all passed. This tested frozen implementation `a80da4d`; only this report and ticket checklist metadata changed afterward.
- `UV_OFFLINE=1 uv build --wheel --out-dir /tmp/smi-ticket-15-wheel`: built `/tmp/smi-ticket-15-wheel/smi_ingestion-0.1.0-py3-none-any.whl`. ZIP inspection matched all **9** changed packaged files byte for byte: `smi_campaigns/{AGENTS.md,CLAUDE.md,__init__.py,schema.sql,store.py}` and `smi_review/{AGENTS.md,CLAUDE.md,app.py,views.py}`. Both relative instruction symlinks resolve to their matched owner guidance.

## Limits

Uses existing bounded current-KB deterministic rules and exact query support. No LLM ranking/assessment, acquisition/discovery, new source/provider framework or richer human curation is included. No actual provider/source call, external message, push, PR or deployment occurred. Tests do not establish human-language or marketer-usefulness validation.

## Integrated validation

- Confirmed clean root and ancestry from `7f9926491e5fe5cd7d9ec2113da3e4ab1b50924d`, then fast-forward integrated final head `567236079b3573daacbef9bd67379d793e7261f2` on `integration/operational-tickets-11-39`. Runtime implementation is `a80da4dca903b95d2c9aa9fe6bf8f845a6415a4c`; the final worker commit changes only this report and checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **404 tests in 262.27 seconds** on that exact final head. No runtime/test change occurred during the gate; existing worker gates were retained without redundant reruns.
- Independently compared `/tmp/smi-ticket-15-wheel/smi_ingestion-0.1.0-py3-none-any.whl` with the integrated tree: all nine changed packaged files match byte for byte, including the two instruction symlinks. The exact list is retained in continuation-manifest.json.
- Local ticket 15 is resolved; ticket 16 is pending for fresh dispatch. Prior continuation evidence, historical execution-manifest.json and original review baseline are preserved. Only tracker/planning/report metadata changed after verification; no runtime edit, actual provider/source call, external message, new implementation, push, PR, deployment or cleanup occurred.
