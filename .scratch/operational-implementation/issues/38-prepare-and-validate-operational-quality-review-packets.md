# 38: Prepare and validate operational quality-review packets

**What to build:** A reviewer can obtain and record attributable language/relevance review packets for a saved recommendation, a KB answer, and an X semantic alert.

**Blocked by:** 16: Rank campaign candidates with supported LLM assessment; 27: Answer free-form questions from permitted knowledge; 31: Detect supported semantic X anomalies.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** A small shared review-record contract and public export/record/reopen journey for one bounded example of each result type; no automatic judgments or new evaluation platform.

- [x] Packets identify exact reviewed membership, result/support IDs, methods/model versions, source spans/dates, and source-permitted original text with pending translation/reviewer fields.
- [x] Recorded judgments require actual reviewer/translator/method attribution, supported/unsupported/ambiguous/not-assessable labels, material errors/corrections, and explicit denominators.
- [x] The recorder rechecks support on export/record/read and excludes unavailable evidence rather than counting copied text toward a pass.
- [x] Technical correctness, translation-assisted labels, Japanese-original validation, and marketer usefulness remain separate statuses; missing human inputs remain pending.
- [x] Existing same-corpus monitoring/campaign review records and their semantics remain compatible or have a deliberate migration.
- [x] Integration tests prove packets do not fabricate times, translations, usefulness, source truth, or original-language accuracy; the software ticket alone establishes no human quality pass.

**Spec coverage:** user stories 9, 22, 50, 54, 68, 70; acceptance scenarios T08, T30 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Implementer handoff

At implementer handoff status was **claimed** pending independent integration checks; those checks passed below and the ticket is now resolved. Runtime implementation `b195f2818a001b7d236edb67b0e88d65c3603be7`; latest-integration merged frozen checked head `0132bce9823936d422b7a1b23c6784775dc6f82f`. Required offline worker shared gate passed **890 tests in 630.96s**, exit **0**, completed session `14390`; final owner suite **29 passed in 15.73s**; static checks passed. Durable evidence: `verification/ticket-38/shared.*`, protected pre-gate `freeze.json`, one persistent wheel, recorded manifest and separate replay.

[Report](../reports/ticket-38.md), [exact wheel manifest](../reports/ticket-38-wheel-manifest.json), [standalone verifier](../reports/verify-ticket-38-wheel.py). Existing wheel: **449183 bytes**, SHA-256 `3c62e24f4c7d87a2eb6bfb659c533b49986e6be77c0fc3e223c810a9351181ac`, **215 unique entries**, **93 exact source/archive pairs**, all **12 changed packaged files**, **19 SQL schemas**, both assets, **33 packaged guidance pairs** plus root pair, and all **314 protected file hashes/sizes/targets**.

The bounded public/CLI export/record/reopen journey is implemented for saved generated current-KB recommendations, KB answers and semantic X alerts. Exact publication/subject provenance, full-input current-policy checks, rejected-write/new-export cleanup commit, serial bounded history and old retry recovery are covered through public PostgreSQL tests with simulated I/O. Existing same-corpus records/tool semantics are unchanged. Synthetic reviewers/translations are software fixtures, not actual human quality receipts; technical, translation-assisted, Japanese-original and marketer-usefulness dimensions remain separate. Actual named human review belongs to ticket 39. No actual source/model/paid call, credential lookup, external message, push, PR or deployment occurred.


## Completion

- Runtime implementation `b195f2818a001b7d236edb67b0e88d65c3603be7`; frozen worker checked merge `0132bce9823936d422b7a1b23c6784775dc6f82f`; final handoff/independently checked integration `9ec2a6a6e36562549979b8f28b20488e5d82b781`. Clean ancestry and frozen-to-final four own scratch files were verified before fast-forward integration.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed all static/documentation/preflight stages and **890 tests in 666.47 seconds**, exit 0 / session 22406. Started `2026-10-29T05:20:00.166374+00:00`; finished `2026-10-29T05:31:07.476123+00:00`. Exact durable execution identity/result: `.scratch/operational-implementation/verification/ticket-38-integrated/shared.*`. The root gate completed during usage interruption. Resume inspected matching clean head/runtime/frozen identity, full log, exit and finish evidence and retained the unchanged PASS without rerun; existing wheel/archive identities were reconfirmed without rebuilding or retesting. Worker full **890/630.96s**, final owner **29/15.73s**, earlier compatibility **139/113.69s** and all prior gates are preserved without rerun; the earlier compatibility precedes final additions, covered by final owner/full gates.
- Independently verified existing wheel **449183 bytes**, **215 unique entries**, SHA-256 `3c62e24f4c7d87a2eb6bfb659c533b49986e6be77c0fc3e223c810a9351181ac`; all **93** exact source/archive pairs, all **12** changed packaged paths, **19** SQL schemas, **2** assets, **33** packaged guidance pairs plus root relative guidance and all **314** frozen protected file bytes/sizes/hashes/relative targets match the integrated root. Exact manifest/verifier and `.scratch/operational-implementation/verification/ticket-38-integrated/wheel-verification.json` / `freeze-verification.json` retain evidence; no rebuild occurred.
- Coordinator-created archive 38 is independently verified and preserved: **424864 bytes**, **30 members**, SHA-256 `7fd59cd93bce0a0ae3a8302ac40cd2c81ddca738cb1e8299fabb3122f1c2ded4`. All indexed member bytes/sizes/hashes match original worker files. The relocation index retains original paths/member identities; actual worker files and the committed 26–37 relocation report remain untouched.
- All six software criteria are checked. Public RED/GREEN regressions close exact publication/manifest/interpretation/assertion/subject span attribution and per-text-subject source dates (unknown on ambiguity). Required retention cleanup commits even for invalid/conflicting record submissions and denied new exports, preventing restoration of purged annotation bodies. Strict boolean/canonical UUID boundaries, 50 records per packet, 5,000 workspace packets, 256 KiB bodies and old exact retries at caps are verified. Real PostgreSQL source-policy races prove full-input locks through the record commit using actual public owner ports. Existing same-corpus tool/records remain compatible and unchanged.
- Recorded annotation and pending/missing input remain distinct from technical quality. Technical correctness, translation-assisted labels, Japanese-original validation and marketer usefulness remain separate. Synthetic reviewer/translation fixtures are software evidence only. Actual named reviewers, permitted reviewed examples, actual feedback/times, attributable translations/original-language adjudication and actual usefulness evidence remain unmet ticket-39 prerequisites; agent output cannot substitute. No actual source/model/paid I/O occurred, and no live readiness or human-quality pass is claimed. Operator-managed exported/submission files require source-permitted handling; reconciliation is synchronous with no background deletion guarantee.
