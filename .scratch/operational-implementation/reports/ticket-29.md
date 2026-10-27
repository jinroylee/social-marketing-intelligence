# Ticket 29 — Collect bounded recent X evidence offline

Implemented only the authoritative ticket in persistent worktree `/Users/makinarocks/workspace/personal/.smi-agent-worktrees/ticket-29`, branch `smi/operational-ticket-29`. Clean assigned base `6277575573fedf13f5d88649439c2a05648cc30d` and resolved blocker 01 were confirmed. Latest integration metadata `2e037cfd25e35fa10424d46641014a43e81f67de` was merged before freeze. Ticket remains **claimed** for independent merger validation/resolution. No other ticket, subagent, shared planning/continuation edit or cleanup.

## Delivered behavior

- `smi_monitoring.recent.RecentMonitoring` owns explicit operator source policies, independent topic revisions, logical collection windows, retained native X captures, permanent native withdrawals and bounded policy-aware reads. `OfflineXRoute` reads one bounded local synthetic JSON fixture; no canonical ingestion, campaign, scheduled keyword, knowledge run/publication or provider/model execution is required.
- Topic key plus normalized explicit window end identifies one poll across retries, concurrency, edits and restarts. New windows pin their actual topic revision, query/publication bounds, acquisition route/version, file digest/bytes/request count and policy version. Coverage retains partial/missing/unknown eligibility, duplicate and withdrawn rows, record truncation and field completeness without market absence, baseline or trend claims.
- Native post plus original capture time identifies source support independently of mutable text and fixture labels. Unknown capture uses available original publication/measurement times conservatively and establishes no refresh. Alias re-imports cannot reconstruct purged content or reset first import/retention. Changed values within one source capture conflict; genuinely new capture times remain separate. Capture, publication, measurement and import times stay distinct; future capture/measurement or inconsistent source times reject the window.
- Current process/display permission governs its corresponding read independently; retention denial, revocation, policy/local expiry or native withdrawal permanently removes copied text/metrics. Source-free IDs, times, missingness, original acquisition and coverage remain honest tombstones. Native withdrawal excludes future captures. Reuse can shorten but never extend retention. Synchronous reconciliation makes no background/universal deletion claim; caller-owned fixture input is outside product copy ownership.
- Trusted review constructor/CLI opt-ins compose the offline route and human monitoring operator. Protected topic settings/poll forms and topic/window/capture pages preserve exact retry/version context and escape data. Actor/policy-write/route/clock authority is rejected from forms. Saved views reopen without a fixture route and apply current policy. Existing frozen investigations and their HTTP protections remain independent.
- Explicit finite limits are documented and enforced: one regular file/one request, 262,144 bytes, 200 scanned records, 100 selected captures/window, 4,096 text characters, 50 topics/policies, 100 revisions/topic, 1,000 windows/topic, 20,000 observations/withdrawals, 1–100 timeline captures/page, bounded offset and 1–720 hour retention. X-specific public metric meanings remain separate. The monitoring contract, architecture, physical ERD, source/browser/reader coverage, glossary, ADR 0004 and local guidance align with installed behavior.

## Acceptance and verification

- [x] Topic settings separate from scheduled keywords, with explicit cadence/window/bounds/policy/retention.
- [x] Public bounded offline poll with stable native/source capture/reference, original times, acquisition and honest coverage.
- [x] Restart-safe topic/window/timeline/detail, independent of campaigns and per-post KB publication.
- [x] Logical-window and source-capture retry/concurrency protection; missing/partial coverage remains visible.
- [x] Current process/display/retention, expiry and withdrawal govern all retained body/detail copies; aliases cannot restore purged support.
- [x] Public operation and real loopback HTTP tests prohibit external I/O; existing frozen snapshot behavior is unchanged.

Applied implement-spec, TDD and its test/mocking references, domain-modeling and writing-for-agents. Real isolated-schema PostgreSQL and trusted source/time seams; no internal collaborator mock, private-method test or SQL business-outcome assertion. Durable red/green slices cover initial restart, native withdrawal, missingness/detail, policy/expiry, concurrent windows/configuration edits, hard file/time bounds, protected HTTP, alias-purge recovery, capture mutation and finite history. Root reviewed the source-capture identity repair before freeze.

- Final recent-evidence focused suite: **26 passed in 6.44s**, exit 0, `verification/ticket-29/green-08.log`. Earlier recent/snapshot/CLI compatibility: **51 passed in 33.43s**, exit 0, completed session **11875**, `focused-02.log`.
- Final static locked check: **exit 0**, Ruff/documentation links/physical ERD/relative guidance links, `static-final.log`. `git diff --check` and targeted stale-summary scan passed before freeze.
- Required **`UV_OFFLINE=1 uv run --locked python tools/check.py` PASS**, exit **0**, **706 tests in 480.99s**, completed session **19612**. Started **2026-10-27T16:01:29.514442+00:00**, finished **2026-10-27T16:09:31.008464+00:00**. Durable `verification/ticket-29/shared.json` records command, frozen head, session, timestamps and exit; `shared.log` retains full output. No passing shared gate was rerun.

## Frozen artifact and handoff

Runtime implementation **`4aa3535eb5ba3987b9e7aa93b888665e808d7197`**; merged frozen head **`51ce0aec6ca3c83d43991f9492c3c970ef3a8830`**. All **272** frozen source/test/product-doc/guidance files remained byte-for-byte unchanged during/after the passing gate and wheel build (`freeze.json`, `freeze-verified.log`). After PASS, only this report, the exact manifest/verifier and ticket acceptance/handoff metadata changed. The final metadata commit cannot name itself; its SHA is supplied in the handoff message.

Offline `UV_OFFLINE=1 uv build --wheel --out-dir .scratch/operational-implementation/verification/ticket-29/wheel` passed exit 0. Wheel: `/Users/makinarocks/workspace/personal/.smi-agent-worktrees/ticket-29/.scratch/operational-implementation/verification/ticket-29/wheel/smi_ingestion-0.1.0-py3-none-any.whl`, **351118 bytes**, **166 unique entries**, SHA-256 **`f09819f8e80a4c1a1e93c86b18a6a6316ebb684976b92da9fa5d3640e3dba690`**. `wheel-build.{json,log}` retains build provenance.

[Exact manifest](ticket-29-wheel-manifest.json) and [standalone verifier](verify-ticket-29-wheel.py) cover **72 exact source/archive pairs**: all changed packaged files, **12 SQL schemas**, both browser assets and all **25 packaged guidance target/sibling pairs**. Source/archive bytes, sizes, SHA-256 and relative `CLAUDE.md -> AGENTS.md` targets match. Record and independent verification passed exit 0 (`wheel-verify.log`, `wheel-verify-independent.log`). Reproduce:

```sh
UV_OFFLINE=1 uv run --locked python .scratch/operational-implementation/reports/verify-ticket-29-wheel.py --root . --wheel .scratch/operational-implementation/verification/ticket-29/wheel/smi_ingestion-0.1.0-py3-none-any.whl
```

No actual source/model/paid call, external message, push, PR, deployment or cleanup occurred. Detection/alerts (30/31), live X (34), promotion/full KB modeling (33), daemons and broad generic acquisition frameworks remain outside this slice. Technical tests establish no live readiness or human language/marketer-usefulness validation. Original final-review baseline `6220fff49b5b8e982ef5a8d54b7c788e45b0f648` remains preserved. No local implementation blocker remains; merger-owned integration gating, exact artifact verification and resolution remain required.
