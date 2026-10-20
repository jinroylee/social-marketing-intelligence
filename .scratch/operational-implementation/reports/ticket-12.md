# Ticket 12 — Save visible executable campaign criteria

Implemented only [ticket 12](../issues/12-save-visible-executable-campaign-criteria.md) in `/tmp/smi-operational-ticket-12`, branch `smi/operational-ticket-12`. Starting ancestry and clean state were confirmed against `b6c78c97d95fea9357231e826b012d5317ad65b8`. Integration metadata tip `e7ef85a` was fast-forward merged before the final shared gate. Only ticket 12 was claimed; it remains **claimed** for the merger's integration gate. Root planning, findings and continuation-manifest files have no implementer changes.

## Installed interfaces and behavior

- Existing `Brief` accepts optional `original_input`, retaining exact human prose alongside structured criteria. Structured-only callers keep their prior serialized request identity. Criteria retain stable IDs, requirement/preference flags, inclusion/exclusion operators and explicit acknowledge/defer policies.
- Existing human `CampaignStore.start` and `revise_brief` atomically persist the exact brief and one immutable `executable_profile` JSONB snapshot on `campaign_briefs`. The profile identifies its exact brief ID/version and human structured-input basis. Attribution/time remain on the immutable brief revision. Expected-version and request/body/actor conflict checks remain authoritative; identical retries reopen the original revision.
- `read_campaign` exposes every saved brief/profile; `read_comparison` exposes its pinned brief's profile. Current criteria version is `structured-caption-criteria-v1`, using existing caption method `campaign-caption-comparison-v1`. Ranking version `unranked-caption-comparison-v1` explicitly labels marketer-known then dataset-encounter order as unranked. Coverage version `fixed-selected-observations-v1` is descriptive only, with sufficiency assessment explicitly not implemented.
- Existing comparison and confirmation rules remain unchanged. Structured audience, fee, availability and sales needs remain unknown with no support IDs; baseline unknowns remain explicit. Human labels and prose cannot assert source facts.
- Existing protected HTTP create/revise routes accept original prose and show the saved profile beside original input and exact current/historical brief references. Stable criteria IDs, prose, retry identity and expected version survive recoverable stale saves. Prose is escaped and displayed with preserved whitespace. Server-owned profile versions are not accepted as submitted authority.
- The additive, idempotent migration leaves legacy profile values null rather than inventing historical execution versions. Old request retries retain their original brief and identity; a successor records the installed profile. UI explicitly identifies legacy unrecorded profiles.
- Product contracts, implementation coverage, architecture, physical ERD, table dictionary, local review behavior and both existing owner instructions are aligned. Existing relative `CLAUDE.md -> AGENTS.md` symlinks remain valid; no new owner/module abstraction was introduced.

## TDD evidence and seams

Applied the TDD skill at the already-approved public `CampaignStore` and real local HTTP boundaries, using existing isolated PostgreSQL schemas. Applied writing-for-agents for owner guidance. No internal-store mock or direct SQL outcome assertion was added; the upgrade fixture uses DDL only to simulate the prior schema and verifies outcomes through public operations. No subagent was spawned.

1. Public create/reopen slice: red on unsupported `Brief.original_input`; green with original prose, exact brief/profile reference, stable criteria policies, truthful installed version labels and restart/retry inspection.
2. Public successor slice: red because comparison reads lacked the pinned executable profile; green with attributable successors, unchanged historical profile, stale-edit/body/actor conflicts, original retry identity and audience/fees/availability/sales remaining unknown through actual comparisons.
3. HTTP journey: red because the create form lacked original input; green with create, inspect, revise, preserved stale-edit context, escaped original prose, stable criterion ID and restart inspection of both exact revisions.
4. Supplemental upgrade regression: removed the new column to simulate the pre-profile schema, migrated twice, reopened unchanged legacy history, retried its original start and saved an explicitly profiled successor.

## Validation

- `UV_OFFLINE=1 uv run --locked pytest -q tests/test_campaigns.py tests/test_review.py tests/test_monitoring_planning.py`: **81 passed in 94.78 seconds**. Includes existing human shortlist, measurement-plan, decision-note, source-policy, actor and protected/recoverable-form behavior.
- `UV_OFFLINE=1 uv run --locked python tools/check.py --static`: **passed** Ruff, documentation links, physical ERD coverage and relative instruction symlinks.
- Final frozen `UV_OFFLINE=1 uv run --locked python tools/check.py`: **passed**, including PostgreSQL preflight and **342 tests in 219.51 seconds**. Log: `/tmp/smi-ticket-12-shared.log`. No runtime/test changes followed gate start, and no other test suite overlapped it.
- `UV_OFFLINE=1 uv build --wheel --out-dir /tmp/smi-ticket-12-wheel`: **passed**. Archive `/tmp/smi-ticket-12-wheel/smi_ingestion-0.1.0-py3-none-any.whl` was compared byte-for-byte with all seven changed packaged runtime/schema/assets: `smi_campaigns/comparison.py`, `contracts.py`, `schema.sql`, `store.py`; `smi_review/app.py`, `views.py`, `static/review.css`.
- `git diff --check`: **passed**. The metadata-only integration merge did not require a redundant focused rerun; the final shared gate covered the frozen final tree.

## Limits

No LLM interpretation, current-KB retrieval, discovery, ranking algorithm, sufficiency assessment or automatic shortlist authority was added. Profiles describe the installed frozen-caption workflow, and future assessment/coverage work must use truthful successor versions. Original prose is human input, not source verification. Earlier unprofiled history remains explicitly unrecorded. There is no blocker for ticket 12; software checks do not establish language or marketer-usefulness validation. Execution remained offline/local: no source/provider/model network calls, external messages, push, PR or deployment.

## Integrated validation

- Fast-forward integrated and checked commit: `7d42792ab0f65ab58bd72c9f20bb433c04d3b337` on `integration/operational-tickets-11-39`, after confirming a clean root worktree and ancestry from `e7ef85a371c4f9810ce2715190fb1a08d0dcaf2c`.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **342 tests in 216.08 seconds**. No runtime/test change occurred during the gate.
- Independently compared `/tmp/smi-ticket-12-wheel/smi_ingestion-0.1.0-py3-none-any.whl` with the integrated tree: all seven changed runtime/schema/asset files match byte for byte (`smi_campaigns/comparison.py`, `smi_campaigns/contracts.py`, `smi_campaigns/schema.sql`, `smi_campaigns/store.py`, `smi_review/app.py`, `smi_review/views.py`, `smi_review/static/review.css`).
- Local ticket 12 is resolved. Continuation evidence preserves ticket 11 and the historical first-batch manifest. Ticket 13 remains pending for fresh dispatch by the orchestrator. Only tracker/planning/report metadata changed after verification; no runtime edit, live call, external message, push, PR or cleanup occurred.
