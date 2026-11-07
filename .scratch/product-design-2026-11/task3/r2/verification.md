# Verification record for design r2

The revision is a self-contained design prototype with deterministic in-memory fixtures. Checks below establish source, fixture, markup, and traceability behavior only. Browser access remains declined. No CUA, browser automation, alternate origin, screenshot workaround, external source/model request, or email was used.

| Check | Actual result | Evidence |
| --- | --- | --- |
| Inline JavaScript syntax and fixture transitions | 45 checks passed | [Source harness](verify-prototype.cjs), [actual output](verification-results.txt) |
| Requirement coverage | All 99 upstream IDs retained exactly once, no missing or extra IDs; all three review requests mapped | [Generator](build_traceability.py), [mapping](fr-ui-traceability.md), [artifact checks](artifact-check-results.txt) |
| Local links and generated markup | All local Markdown links and heading targets resolve. Six generated EN/KO chat, monitoring, and graph snapshots have balanced explicit tags and unique IDs | [Artifact checker](verify-artifacts.py), [actual output](artifact-check-results.txt) |
| Shared repository static mode | Passed Ruff and documentation-link, physical ERD, and instruction-symlink checks | [Actual static output](shared-static-check-results.txt) |
| r1 identity | All 11 original task3 files match the start-of-dispatch SHA-256 snapshot | [Snapshot](r1-integrity.json), [artifact checks](artifact-check-results.txt) |
| r2 identity | Manifest lists actual SHA-256s for every r2 file except the manifest itself | [Manifest](artifact-manifest.json), `verify-artifacts.py --check-manifest` |
| Browser, actual keyboard events, layout, visual quality, screen-reader output, and responsiveness | Not performed. Source hooks and markup checks do not establish these properties | [Pending review scenarios](review-guide.md) |
| Actual human approval and Task 4 | Pending. No gate was resolved and no next task was launched | [Review boundary](review-guide.md#material-choices-for-actual-human-review) |

The fixture harness evaluates the actual inline JavaScript with a minimal element stub. New checks cover turn creation, escaping, Send/Enter, Shift+Enter, IME withholding, empty messages, separate thread drafts, scroll retention, EN/KO and navigation, conversational yes without approval, immutable proposal snapshots, publication/policy behavior, current versus selected windows, missing/zero/unscheduled intervals, metric alignment, table/point selection, evidence linkage, bounded history, and per-method insufficient/failed states. Retained checks cover campaigns, explicit regeneration, approval, tasks, graph support, promotion, keyword bounds, and no network code. This is not DOM event dispatch or a browser simulation.

The markup check parses generated strings without browser repair or rendering. It can find unbalanced tags and duplicate IDs but cannot establish computed layout, accessibility trees, focus behavior, or correct native interaction. Palette contrast remains computed from the accepted hex values, at 4.77:1 white/red, 11.24:1 white/graphite, and 6.04:1 graphite/petal. These calculations do not certify every rendered component.

The full shared suite was not rerun for this isolated prototype revision. The [inherited r1 output](../shared-check-results.txt) records 51 passed and 1 failed before fail-fast stopped. The known failure at `tests/test_assistant_enrichment.py:261` uses a fixed October 1 capture beyond its 30-day freshness threshold. See the [documented baseline limitation](../../../../docs/development.md#current-test-fixture-limitation). No unrelated source or test was fixed, and no full-suite pass is claimed.

Reproduce from the repository root:

```sh
node .scratch/product-design-2026-11/task3/r2/verify-prototype.cjs
python .scratch/product-design-2026-11/task3/r2/build_traceability.py
python .scratch/product-design-2026-11/task3/r2/verify-artifacts.py --check-manifest
uv run --locked python tools/check.py --static
```

The production graph pan, drag, pin, layout, expansion, pagination, stale-response, and policy-race contracts are specified, not implemented or verified here. The current backend still has bounded one-question published-finding selection; fixture follow-ups do not establish conversational synthesis. Live providers, commercial billing, continuous local workers, language/usefulness acceptance, and email delivery remain separate future checks.
