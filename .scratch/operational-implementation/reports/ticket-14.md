# Ticket 14 — Current-KB account comparison

Scope: only published ticket 14. Fresh `smi/operational-ticket-14` worktree confirmed ancestor `d1cab87fd6c10c8ea27b9a8c3938fa7f3460448a`; latest integration metadata `f2969b7` merged before the final gate. Ticket remains **claimed** for the merger's integrated gate.

## Delivered

- Public `CampaignStore.prepare_current_comparison` and protected HTTP form compare bounded current permitted publications using existing deterministic caption rules. Legacy frozen-dataset comparison remains compatible.
- Stable platform/namespace/native account identity plus one permitted ingested observation qualifies, including missing-profile and metric-only support. Unsupported/un-ingested references remain discovery gaps. Required exclusions/defer policies, explicit audience/contracts/sales unknowns, source dates and freshness remain visible.
- Exact immutable query/support manifests and brief/selected criteria interpretation/execution versions preserve history. Actual method is `current-kb-caption-comparison-v1`, unranked. Preparation performs no model/source dispatch or automatic shortlist save.
- Workspace publication-frontier and source/derivation locks extend through result/draft commit. Public reopen applies current policy/supersession; retention purges copied explanations and dependent human notes without refreshing membership/order. Human notes use the campaign owner's public transaction-aware support reader for both source modes.
- Product contracts, architecture, physical ERD/dictionary and existing owner guidance are aligned. Relative instruction symlinks remain intact.

## Red → green evidence

Approved seams: owning public operations and HTTP, real isolated PostgreSQL, simulated external I/O. Setup/commit-gate DDL and policy mutation coordinate faults; product outcomes are asserted only through public readers/HTTP. No internal-store mocks or SQL outcome assertions were added.

Observed reds included missing current-comparison operation, absent explicit empty-scope outcome, missing HTTP journey, missing actual execution profile, notes incorrectly requiring a frozen dataset, and a stale form dropping its exact selected interpretation. Each was followed by the relevant public/HTTP green. Compatibility checks exposed and repaired frozen evidence-panel ID assumptions and restored the existing planning evidence-reader attribute.

- `UV_OFFLINE=1 uv run --locked pytest -q tests/test_current_comparisons.py`: **10 passed in 7.54s**, covering minimal support, namespace/new-publication/history, empty results, escaped HTTP/restart/withdrawal, caption exclusions without audience/contract/sales inference, explicit model-profile selection without another dispatch, commit races, metric-only human-note policy, process/display/retention/supersession, and stale form recovery.
- Earlier compatibility run: **98 passed in 94.74s** across current comparisons, monitoring/planning, review and criteria interpretation. Final focused union (`tests/test_current_comparisons.py tests/test_campaigns.py tests/test_knowledge_queries.py tests/test_publications.py tests/test_review.py tests/test_monitoring_planning.py tests/test_criteria_interpretation.py`): **156 passed in 145.57s**; the final stale-form fix was then verified by the full 10-test ticket file above.
- `UV_OFFLINE=1 uv run --locked python tools/check.py --static`: passed Ruff, product links, physical ERD table coverage and relative instruction symlinks.
- Final `UV_OFFLINE=1 uv run --locked python tools/check.py`: **391 passed in 251.62s**, with Ruff, product links, physical ERD coverage, relative instruction symlinks and real PostgreSQL preflight passed. The final coverage-table documentation adjustment also passed a separate static-only check; no runtime/test changes followed the shared gate.
- `UV_OFFLINE=1 uv build --wheel --out-dir /tmp/smi-ticket-14-wheel`: built `/tmp/smi-ticket-14-wheel/smi_ingestion-0.1.0-py3-none-any.whl`; ZIP inspection matched all **22** changed packaged runtime/schema/guidance files (including six sibling `CLAUDE.md` symlinks) byte for byte against this tree.

## Limits

At most 100 newest publications, 100 support bundles and 100 account candidates; truncation/incomplete-market coverage stays explicit. Freshness without a configured threshold is not assessed. No ranking, discovery/acquisition, automatic shortlist save, new model assessment or live external execution is included. Technical checks do not establish Japanese-language or marketer-usefulness validation. No push, PR, deployment or external message occurred.

## Integrated validation

- Confirmed clean root and ancestry from `f2969b7ae97905f594b8cb0550abb2661fd6747e`, then fast-forward integrated and checked `b9f371db5dccf13e13d8491cc31e94745d5b761f` on `integration/operational-tickets-11-39`.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **391 tests in 251.61 seconds** on that exact integrated commit. No runtime/test change occurred during the gate; passing worker gates were retained without redundant reruns.
- Independently compared `/tmp/smi-ticket-14-wheel/smi_ingestion-0.1.0-py3-none-any.whl` with the integrated tree: all 22 changed packaged runtime/schema/guidance files match byte for byte, including six sibling instruction symlinks. The exact list is retained in continuation-manifest.json.
- Local ticket 14 is resolved; ticket 15 is pending for fresh dispatch. Prior continuation evidence, historical execution-manifest.json and original review baseline are preserved. Only tracker/planning/report metadata changed after verification; no runtime edit, external call/message, new implementation, push, PR, deployment or cleanup occurred.
