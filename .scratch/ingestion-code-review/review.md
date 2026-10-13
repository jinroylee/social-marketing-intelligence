# Ingestion code review — 2026-10-13

The review found six reproducible correctness defects, all fixed, plus one deferred architecture judgment. The updated full suite passes **80 tests**. The separate Standards and Spec reviews are retained below; they are not combined into one ranking.

## Scope and evidence

The builder requested the existing `src/smi_ingestion` module as a whole. The working tree was clean and HEAD was pinned to `1b7df0291f122eafcbcd35ff3d55e4c1c2d5f36c` (`1b7df02 initial commit with data ingestion pipeline`). A whole-module baseline was therefore used instead of inventing a user-supplied revision:

```bash
git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904 1b7df0291f122eafcbcd35ff3d55e4c1c2d5f36c -- src/smi_ingestion
```

The first object is Git's empty tree, so a two-tree comparison is intentional. The validated scope contained 20 files and 2,591 inserted lines. Callers, schema, examples, tests, and relevant local specifications were also read. Standards and Spec reviewers worked independently and read-only; the coordinating reviewer alone made edits.

Standards came from [root engineering guidance](../../AGENTS.md), [adapter guidance](../../src/smi_ingestion/adapters/AGENTS.md), README, GLOSSARY, and `pyproject.toml`, plus the code-review skill's Fowler smell baseline. There is no CONTRIBUTING or CODING_STANDARDS file. Private-interface concerns below are labeled as judgment rather than tool-enforced formatting violations.

The governing implementation sources were the [approved acquisition design](../beauty-intelligence-pilot/source-to-canonical-design.md), [first acquisition milestone](../beauty-intelligence-pilot/first-acquisition-milestone.md), and tickets [04](../beauty-intelligence-pilot/issues/04-select-pilot-evidence-scope.md), [12](../beauty-intelligence-pilot/issues/12-implement-local-ingestion-slice.md), [16](../beauty-intelligence-pilot/issues/16-implement-live-oembed-reference-adapter.md), [18](../beauty-intelligence-pilot/issues/18-validate-bright-data-japan-sample.md), and [19](../beauty-intelligence-pilot/issues/19-prototype-direct-tiktok-web-collection.md). The [2026-10-12 API retry](../brightdata-source-readiness/api-retry-2026-10-12.md) supersedes older failed-access statements. The [minimum domain contract](../beauty-intelligence-pilot/minimum-domain-contract.md) and [pilot acceptance](../beauty-intelligence-pilot/pilot-acceptance.md) describe a future build; missing future importer, frozen-set, campaign, or shortlist capabilities were not classified as regressions.

## Standards

**3 findings: 2 fixed documented-standard violations, 1 deferred architecture judgment. Worst within this axis: S1, uncounted HTTP redirects (P2, fixed).**

| ID | Finding and evidence | Disposition |
| --- | --- | --- |
| S1 — P2 | Web and oEmbed transports used `urlopen`, whose automatic redirect dispatch occurred before the final URL check. A mocked 302 followed by 200 produced two dispatches under one recorded attempt. This violates the adapter guidance's bounded I/O responsibility and ticket 16's “10 HTTP attempts total per run.” | **Fixed.** All three transports use [one-request dispatch](../../src/smi_ingestion/adapters/http.py#L13), which rejects redirect following. Existing Bright Data behavior was moved into this small shared adapter helper. [Regression](../../tests/test_http.py#L15) intercepts urllib dispatch itself, rather than faking the transport result. |
| S2 — P2 | `_posts()` discarded non-object entries before assigning source indices. For `[null, valid_post]`, the caption and metrics pointed to `itemList[0]`, although the source entry was index 1. Adapter guidance requires source provenance; wrong locations prevent evidence tracing. | **Fixed.** [Post extraction](../../src/smi_ingestion/adapters/tiktok_web.py#L173) retains each original index, and mapping uses it. [Regression](../../tests/test_tiktok_web.py#L241) checks field and metric locators after a malformed preceding row. |
| S3 — P3, judgment | `canonical.py` imports private policy helpers from `evidence.py`; `_report()` reaches through `evidence.db` and embeds persistence queries. Root guidance asks for “small, explicit interfaces” and to avoid “reaching through a module's interface into its internals.” Possible Feature Envy / responsibility leakage. | **Deferred.** The behavior is tested and no separate failure was demonstrated. A cohesive policy/read-model boundary belongs in the planned evidence-interface work; mechanically introducing wrappers now would broaden this repair. |

## Spec

**4 findings: all fixed. Worst within this axis: P3 below, committed transient observations misclassified after interruption (P2, fixed). No substantiated scope creep.**

| ID | Requirement and reproduced failure | Disposition |
| --- | --- | --- |
| P1 — P2 | The design says “Otherwise retain the conflict or unknown” (canonical dataset, line 90). Provider A's observed caption plus provider B's explicit removal returned the caption as observed, even while provenance listed both sources. | **Fixed.** [Current-field selection](../../src/smi_ingestion/canonical.py#L191) compares state and value after selecting comparable source observations, including removal versus observation. [Regression](../../tests/test_pipeline.py#L244) expects a conflict and both sources. JSON key ordering does not create false value differences. |
| P2 — P2 | “Interrupted runs resume from durable state” (acceptance 5, line 118). A final batch saved at `max_records=1`, followed by interruption before run completion, resumed its mapping but reported `record_limit_reached` forever: `batch.complete` had only existed in memory. | **Fixed.** [Evidence save](../../src/smi_ingestion/evidence.py#L108) atomically commits `input_complete` with observation/checkpoint/counters. [Resume](../../src/smi_ingestion/runner.py#L135) processes pending mappings, then checks completion before another collection or limit check. [Regression](../../tests/test_pipeline.py#L258) forbids further collection and verifies completed coverage. |
| P3 — P2 | “Reapplying a committed derivation is safe” (acceptance 5, line 118). After a canonical commit but before the separate applied marker, resume tried to reload non-retained bytes and quarantined a successful transient observation with `replay_unavailable`. | **Fixed.** [Canonical application](../../src/smi_ingestion/canonical.py#L60) commits facts and applied status together. [Reconciliation](../../src/smi_ingestion/canonical.py#L27) repairs legacy pending markers backed by an active derivation before resume loads bytes. [Regression](../../tests/test_pipeline.py#L280) covers both new atomic writes and a simulated legacy pending marker. |
| P4 — P2 | “Fields distinguish … not returned, unavailable with a reason” and “Report … missing fields” (design lines 79 and 104). A web post lacking caption/date/share count produced `partial_result` but no missing-field candidates or report entries. | **Fixed.** [Web mapping](../../src/smi_ingestion/adapters/tiktok_web.py#L430) emits `not_returned` for absent expected fields and `unavailable` with a reason for invalid values, retaining observed zero counts. [Regressions](../../tests/test_tiktok_web.py#L255) cover absent and invalid data through the runner. |

Web mapper version is now `v2` to identify its changed field/provenance interpretation. The schema migration is additive and idempotent. No existing source observations or canonical assertions were rewritten during this review.

## Verification

- Initial baseline: `uv run pytest -q` — **70 passed**.
- Before fixes, six targeted tests failed for redirect dispatch (two routes), removal conflicts, durable final-capture completion, transient recovery, and shifted source locators. The direct-web missing/invalid-field cases then failed separately (two parameter cases). Reviewers also reproduced the two crash windows directly against isolated PostgreSQL schemas.
- After fixes, `uv run pytest -q tests/test_http.py tests/test_pipeline.py tests/test_tiktok_web.py tests/test_tiktok_oembed.py tests/test_bright_data.py` — **77 passed**. One schema-upgrade regression was subsequently added.
- Final `uv run pytest -q` — **80 passed in 10.57s**, including CLI subprocess tests, new/legacy crash recovery, idempotent schema upgrade, identity/provenance/history, revocation/expiry, transport bounds, and provider mocks.
- `git diff --check` — passed. Local report/walkthrough links and Python compilation were checked before delivery.

Tests use unique temporary PostgreSQL schemas and clean them up; HTTP behavior is mocked. No live provider/platform request, original source collection, credential-file read, purchase, commit, or push was performed.

README now records the successful 2026-10-12 one-profile/ten-post Bright Data check, resolved planning status, and remaining source-readiness limits. It also states the required migration command. This documentation correction is reported separately from the six code defects.

## Remaining limits

Run `uv run smi-ingest migrate` against an existing local database before using the updated runner. Old completed runs remain recognizable through their existing status. Old unfinished runs cannot gain a trustworthy completion flag retroactively because the old schema never stored one; the migration conservatively defaults it to false. Reconciliation repairs committed **pending** observations, not historic quarantines or issue records already produced by an earlier failed recovery.

Web HTML is intentionally non-retained. Mapper v2 applies to subsequent permitted observations; it cannot retroactively reconstruct old HTML or repair its locators through replay. No new web fetch was performed to change those records.

The runner supports one observation envelope per collector call; its record/page counters are envelope counts, while a provider response can contain multiple posts. Current reads are policy-filtered current fields and active metric history, not a frozen evidence-set API. Raw-file removal and read filtering do not physically erase canonical assertion values. The future pilot explicitly owns offline snapshot import, frozen membership, source-copy invalidation, and saved campaign/shortlist contracts. See the [walkthrough](walkthrough.md) for those boundaries.

No execution blocker remains for this review. Broader source coverage, repeat captures, actual charges, and automatic fallback are still unverified source-readiness work.

Standards: **3 findings, 2 fixed / 1 deferred; worst S1 (P2, fixed).** Spec: **4 findings, 4 fixed / 0 deferred; worst P3 (P2, fixed).**
