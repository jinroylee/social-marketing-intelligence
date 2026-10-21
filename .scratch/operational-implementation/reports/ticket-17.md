# Ticket 17 — Optional attributable shortlist curation

Scope: only published ticket 17. Confirmed the fresh `smi/operational-ticket-17` worktree clean at the verified integration base `501a3f7360f2e7e7f32ec32da802c70700a131b4`, with that exact ancestor. Runtime/tests/docs commit: `f6c0380741b1e0126c0d0864166e1fdb5ff1c14e`. Merged latest integration metadata `f55357058b2132d43bde42aebd77bbd936758b39` before freezing the clean tree at `9fc164fca493a43bc15e26da42a7033bd73fd1c6`. Ticket remains **claimed** for the merger.

## Delivered

- Extended the existing public `CampaignStore.save_shortlist` and comparison successor form with optional `source_shortlist_id`. Human tuple order becomes zero-based selection positions in a new attributable human draft or separately confirmed revision. The new method is `human-shortlist-curation-v1`, with `human_selected_order` and an explicit human execution label. Curation can select/reorder or record empty deferral without a mandatory review gate or model/source call.
- Added one nullable self-reference on `shortlist_revisions`; the owner checks exact campaign/comparison/source and current brief/shortlist heads under its existing campaign lock. Shortlist and campaign readers expose the source link. Browser positions are distinct positive integers; form errors retain permitted edits, exact source/head and retry identity. Server-derived actor, Origin and CSRF remain authoritative; actor/method/confirmation/model/configuration fields are rejected.
- Original deterministic/model order, producer, rationale, support/profile, assessment and absence of human review remain unchanged. Starting reasons show their existing provenance; newly saved human wording is attributed as human input. Explicit confirmation still requires its separate review acknowledgement and positive relevance/unknown checks.
- Exact retries reopen the original before current-head checks, including after restart, newer revisions and withdrawal. Changed body/order/source/confirmation/head/synthetic visibility or actor conflicts. Competing requests serialize, stale source revisions cannot be retargeted to a newer expected head, and stale briefs fail visibly.
- Copied/edited human reasons inherit the comparison's complete pinned candidate dependencies. Denied, superseded or unprocessable support cannot enter a new source-dependent curation reason; unavailable membership can remain in an unconfirmed draft without source text. Recoverable forms withhold unavailable reasons, retention withdrawal purges copies, and retries never reconstruct them. Source-only account support remains usable without fabricated caption evidence.
- Omitted source context preserves historical human request digests and unrecorded order/method. Migration adds no invented predecessor, review or rank metadata. The migration regression reopens old draft/confirmed decisions, frozen comparisons, proposed plans and human notes unchanged. Product contracts, architecture, physical ERD, reader dictionary, implementation-status paragraph and existing module guidance are aligned. Both `CLAUDE.md` siblings remain relative symlinks to their `AGENTS.md` source.

## TDD and seams

Applied TDD and writing-for-agents. Used the already approved public campaign operations and HTTP seams, real local PostgreSQL with isolated schemas, public source revocation and simulated external ranking I/O. Schema-drop DDL reproduces the prior schema; assertions use public readers. No private-method tests, internal-store mocks, direct-SQL outcome assertions or subagents.

Recorded red → green slices:

1. Public ordered curation first failed on the absent `source_shortlist_id` parameter; the minimal owner/schema extension passed.
2. The HTTP successor first lacked source context; protected context/position parsing and policy-aware rendering passed.
3. A new withdrawn-source human reason was accepted; rejecting source-dependent curation inputs while preserving content-free membership passed. The first test attempt accidentally reused an existing request identity and was corrected before the meaningful policy red.
4. A curated ranked result incorrectly reopened with the deterministic `unranked` execution label; the distinct human execution overlay passed without another model dispatch.

Additional regressions cover supported citations/acknowledgements and separate confirmation, concurrent exact retries and competing heads, actor/body conflicts, stale brief/source versions, protected/recoverable HTTP, display denial, immutable generated/model history and prior-schema human/planning reopening. One positive-support fixture initially used the wrong sample product ID; correcting it required no runtime change. One focused command named a nonexistent legacy test and collected no tests; the corrected command below passed. An initial red was accidentally invoked twice while handling its tool session; later dependent slices and the final broad gate ran sequentially.

## Verification

- Public first green: **1 passed in 0.70s**. Public + HTTP green: **2 passed in 2.50s**. Withdrawal union: **3 passed in 3.18s**. Retry/model union: **5 passed in 4.43s**.
- Protected/stale HTTP: **1 passed in 1.84s**; migration: **1 passed in 2.46s**; exact supported-reason/confirmation case: **1 passed in 1.23s**; display-denial case passed in its focused union.
- `UV_OFFLINE=1 uv run --locked pytest -q tests/test_shortlist_curation.py tests/test_recommendations.py::test_legacy_human_upgrade_keeps_status_author_history_and_unrecorded_order tests/test_campaigns.py::test_concurrent_retries_and_conflicting_saves_are_transactional tests/test_review.py::test_http_retry_and_stale_save_preserve_edits_without_overwriting`: **12 passed in 14.72s** (nine new curation tests plus three existing compatibility cases).
- `UV_OFFLINE=1 uv run --locked python tools/check.py --static`: passed Ruff, product links, physical ERD coverage and relative instruction symlinks. `git diff --check` passed.
- Frozen `UV_OFFLINE=1 uv run --locked python tools/check.py`: **passed with exit 0**, including PostgreSQL preflight, Ruff, product links, physical ERD coverage, relative instruction symlinks and **452 tests in 296.65s** against `9fc164fca493a43bc15e26da42a7033bd73fd1c6`; completed session `15670`, log `/tmp/smi-ticket-17-check-9fc164f.log`. No runtime/test/docs edits followed gate start; only this report and the claimed ticket checklist changed afterward. This passing frozen gate was preserved without a redundant broad rerun.
- `UV_OFFLINE=1 uv build --wheel --out-dir /tmp/smi-ticket-17-wheel-9fc164f`: passed. Wheel `/tmp/smi-ticket-17-wheel-9fc164f/smi_ingestion-0.1.0-py3-none-any.whl` matches all **eight** changed packaged files byte for byte: the six changed runtime/schema/guidance files plus both sibling instruction symlink targets. Full wheel listing: `/tmp/smi-ticket-17-wheel-9fc164f/wheel-contents.txt`; exact source/archive names and SHA-256 values: `/tmp/smi-ticket-17-wheel-9fc164f/byte-verification.json`.

## Limits

This extends the existing selection/history journey; it adds no mandatory review, richer semantic assessment, source/model dispatch, acquisition authority or future-ticket feature. Original conservative candidate-scoped policy cleanup remains synchronous on public reads/commit checks. Historical human order remains unrecorded unless a human explicitly creates a new ordered successor. Draft wording is human input rather than independently verified prose. Technical tests do not establish language interpretation or marketer usefulness. No real source/model/paid call, external message, push, PR, deployment or cleanup occurred. No external blocker is known; integration and root shared verification remain the merger's responsibility.

## Merger handoff

Latest integration tip `f55357058b2132d43bde42aebd77bbd936758b39` was already merged in the checked frozen tree and remained unchanged at gate completion. The final worker commit contains report/checklist metadata only; its exact head is supplied in the final handoff. The offline wheel and eight-file byte-verification manifest match that unchanged runtime tree. Ticket 17 remains claimed with its technically demonstrated acceptance checklist checked; the root merger owns integrated validation and resolution.
