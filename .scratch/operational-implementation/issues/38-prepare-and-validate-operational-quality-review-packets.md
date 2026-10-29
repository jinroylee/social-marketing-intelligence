# 38: Prepare and validate operational quality-review packets

**What to build:** A reviewer can obtain and record attributable language/relevance review packets for a saved recommendation, a KB answer, and an X semantic alert.

**Blocked by:** 16: Rank campaign candidates with supported LLM assessment; 27: Answer free-form questions from permitted knowledge; 31: Detect supported semantic X anomalies.

**Status:** claimed

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

Status remains **claimed** pending independent merger review, integrated root checks and resolution. Runtime implementation `b195f2818a001b7d236edb67b0e88d65c3603be7`; latest-integration merged frozen checked head `0132bce9823936d422b7a1b23c6784775dc6f82f`. Required offline worker shared gate passed **890 tests in 630.96s**, exit **0**, completed session `14390`; final owner suite **29 passed in 15.73s**; static checks passed. Durable evidence: `verification/ticket-38/shared.*`, protected pre-gate `freeze.json`, one persistent wheel, recorded manifest and separate replay.

[Report](../reports/ticket-38.md), [exact wheel manifest](../reports/ticket-38-wheel-manifest.json), [standalone verifier](../reports/verify-ticket-38-wheel.py). Existing wheel: **449183 bytes**, SHA-256 `3c62e24f4c7d87a2eb6bfb659c533b49986e6be77c0fc3e223c810a9351181ac`, **215 unique entries**, **93 exact source/archive pairs**, all **12 changed packaged files**, **19 SQL schemas**, both assets, **33 packaged guidance pairs** plus root pair, and all **314 protected file hashes/sizes/targets**.

The bounded public/CLI export/record/reopen journey is implemented for saved generated current-KB recommendations, KB answers and semantic X alerts. Exact publication/subject provenance, full-input current-policy checks, rejected-write/new-export cleanup commit, serial bounded history and old retry recovery are covered through public PostgreSQL tests with simulated I/O. Existing same-corpus records/tool semantics are unchanged. Synthetic reviewers/translations are software fixtures, not actual human quality receipts; technical, translation-assisted, Japanese-original and marketer-usefulness dimensions remain separate. Actual named human review belongs to ticket 39. No actual source/model/paid call, credential lookup, external message, push, PR or deployment occurred.
