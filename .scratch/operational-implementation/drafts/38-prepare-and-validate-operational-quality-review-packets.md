# 38: Prepare and validate operational quality-review packets

**What to build:** A reviewer can obtain and record attributable language/relevance review packets for a saved recommendation, a KB answer, and an X semantic alert.

**Blocked by:** 16: Rank campaign candidates with supported LLM assessment; 27: Answer free-form questions from permitted knowledge; 31: Detect supported semantic X anomalies.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** A small shared review-record contract and public export/record/reopen journey for one bounded example of each result type; no automatic judgments or new evaluation platform.

- [ ] Packets identify exact reviewed membership, result/support IDs, methods/model versions, source spans/dates, and source-permitted original text with pending translation/reviewer fields.
- [ ] Recorded judgments require actual reviewer/translator/method attribution, supported/unsupported/ambiguous/not-assessable labels, material errors/corrections, and explicit denominators.
- [ ] The recorder rechecks support on export/record/read and excludes unavailable evidence rather than counting copied text toward a pass.
- [ ] Technical correctness, translation-assisted labels, Japanese-original validation, and marketer usefulness remain separate statuses; missing human inputs remain pending.
- [ ] Existing same-corpus monitoring/campaign review records and their semantics remain compatible or have a deliberate migration.
- [ ] Integration tests prove packets do not fabricate times, translations, usefulness, source truth, or original-language accuracy; the software ticket alone establishes no human quality pass.

**Spec coverage:** user stories 9, 22, 50, 54, 68, 70; acceptance scenarios T08, T30 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
