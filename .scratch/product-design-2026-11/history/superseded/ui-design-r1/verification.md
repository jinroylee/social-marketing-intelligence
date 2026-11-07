# Verification record for design r1

The delivered artifact is a self-contained design prototype. These checks establish source/fixture behavior and traceability only. Actual browser use, human design approval, language usefulness, live providers, commercial billing, production publication and email delivery were not established.

| Check | Actual result | Evidence |
| --- | --- | --- |
| Inline JavaScript parsing and fixture-state harness | 29 checks passed | [verify-prototype.cjs](verify-prototype.cjs), [actual output](verification-results.txt) |
| Task 1 stable requirement ID coverage | 99 unique IDs, no missing or extra design mappings | [generator](build_traceability.py), [matrix](fr-ui-traceability.md) |
| Primary palette text contrast, computed from sRGB values | White/red 4.77:1; white/graphite 11.24:1; graphite/petal 6.04:1 | Contrast lines in actual fixture-check output |
| Required `uv run --locked python tools/check.py` | Failed at the already documented freshness-sensitive assistant fixture; 1 failed, 51 passed before fail-fast stop. Ruff, local product-doc links, physical ERD and instruction symlinks passed | [full check output](shared-check-results.txt), [known baseline limitation](../../../docs/development.md#current-test-fixture-limitation) |
| Browser interaction and screenshots | Blocked by declined preview permission relayed by the coordinator. No bypass attempted | Coordinator message `msg_58b5b6958d74`; manual review scenarios remain pending |
| Responsive layout, actual keyboard/focus/dialog behavior, visual quality and screen-reader output | Source hooks inspected, actual behavior unverified | [M10 review scenarios](review-guide.md#m10-check-states-keyboard-and-narrow-layouts) |
| Actual human UI and language/usefulness approval | Pending | [review gate](review-guide.md#material-choices-for-actual-human-review) |

The source harness evaluates the actual inline JavaScript with a minimal element stub. It checks exact approval gating/revision invalidation, one visible logical task, retrieved-versus-published state, explicit successor regeneration, fixed historical membership, human curation, unknown-response waiting, KB-only alert context, selected-promotion gating, graph basis/depth/evidence/withdrawal, bilingual drafts/stable select values, role-state withholding, ten-keyword cap, no network assets/storage, target monitoring success/baseline/failure cases and empty new-campaign generation. It does not implement real browser event dispatch, DOM layout, accessibility trees, network or backend authorization. Passing it cannot replace browser or owner acceptance tests.

The baseline failure is at `tests/test_assistant_enrichment.py:261`, expecting no gap for a fixed October 1 capture; the current clock produces `stale_published_information`. The current development documentation records that same issue. No production test or source fix was made in this design-only task, and the remaining shared suite was not claimed as passing.

Reproduce the isolated artifact checks from the repository root:

```sh
node .scratch/product-design-2026-11/task3/verify-prototype.cjs
python .scratch/product-design-2026-11/task3/build_traceability.py
```

See [artifact-manifest.json](artifact-manifest.json) for SHA-256 identities of the review files. The actual reviewer must identify the exact revision/digest when approving it. Task 4 remains blocked on that actual human UI approval; an agent verification record cannot close that gate.
