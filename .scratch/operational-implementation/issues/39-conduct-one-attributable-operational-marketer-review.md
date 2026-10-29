# 39: Conduct one attributable operational marketer review

**What to build:** A named human reviewer completes one bounded evaluation of the operational campaign, assistant-enrichment, and X-alert journeys with recorded evidence and limitations.

**Blocked by:** 20: Offer explicit regeneration after campaign updates; 28: Turn assistant knowledge gaps into approved enrichment; 32: Explain X alerts using existing KB context only; 38: Prepare and validate operational quality-review packets.

**Status:** claimed

**Triage label:** ready-for-human

**Size:** S — one bounded human validation activity in a fresh implementation context.

**Scope guard:** A validation activity using implemented review tools and a fixed permitted corpus/window selection; no code feature, invented benchmark, or generalized accuracy/sales claim.

- [ ] Select exact permitted reviewed examples and record reviewer identity/time, prior exposure, task order, and corpus/window membership before making a quality claim.
- [ ] Capture actual manual baseline inputs and observed assisted task times/inspected evidence where the existing procedure requires them, plus a useful finding and reusable candidate decision or deliberate deferral.
- [ ] Record actual feedback for campaign rank/rationale, assistant gaps/approval/publication behavior, and quantitative/semantic alert interpretation using the prepared packets.
- [ ] Material unsupported claims, translation errors, or usability failures are documented with corrections or follow-up defects; they cannot be hidden to manufacture a pass.
- [ ] Language and usefulness conclusions retain their actual denominators and qualifications; Japanese-original accuracy stays unvalidated without qualified original-language adjudication.
- [ ] A named reviewer and permitted examples are explicit external prerequisites. If unavailable, keep the review pending and do not mark this validation ticket complete or replace the reviewer with model output.

**Spec coverage:** user stories 70; acceptance scenarios T30 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. This ticket is genuine human validation, not an automated test or implementation claim.

## Comments

- Claimed on fresh branch `smi/operational-ticket-39` at `b75b8b6a454ae9abdb5f7f7450837b79d7801753`, after blockers 20/28/32/38 resolved and the independent root **890-test / 666.47s / exit 0** technical gate passed (session `22406`). Fast-forwarded coordinator metadata commit `3f6ab86e4f19ea248436d44653ff7ffd7f294ec9` before handoff. No source/test/product-contract changes, new data, acquisition/model calls, full-gate rerun or verification wheel rebuild occurred.
- [Concrete human handoff](../reports/ticket-39-handoff.md) supplies the current export/record/reopen commands, same-corpus baseline-before-assisted procedure, reviewer/translator attribution, task order/exposure/timing/count requirements, exact labels/denominators and correction limits. [Read-only inventory](../reports/ticket-39-inventory.json) checked only explicit `127.0.0.1:6543/smi`, schema `public`, workspace `local` through public owners with an automation inventory actor and read-only PostgreSQL transactions. Four list operations returned `UndefinedTable`/`42P01`; quantitative/semantic notification lists were empty, including their optional-owner qualification. No selectable saved examples or permitted corpus/window membership were discovered in that scope. No other schema was searched; no guessed/test UUID was reused and no migration/import/packet export was run.
- **Genuine external prerequisites; ready-for-human:** an actual named reviewer and attestation; an existing permitted local result workspace/schema and explicit recommendation, answer/enrichment and quantitative/semantic alert IDs with exact corpus/window membership; actual baseline collected before assisted results; prior exposure/task order, observed assisted times/counts, actual translations/method attribution, campaign/assistant/alert feedback, useful finding and reusable keep/exclude/defer decision or honest negative outcome; and material errors/corrections. The handoff lists each precise input. These cannot be inferred from actor strings, software fixtures or model output. Japanese-original accuracy remains `not_validated` without qualified original-language adjudication. All human acceptance boxes remain unchecked; ticket 39 is **claimed/pending**, not resolved, and no human quality pass or whole-goal completion is claimed.
- Preparation validation passed: own inventory JSON, local links, claimed/ready-for-human state, six still-pending criteria, whitespace and unchanged source/tests/tools/product contracts against coordinator commit `3f6ab86e4f19ea248436d44653ff7ffd7f294ec9`. Current CLI help was checked without invoking any action/migration. This metadata-only validation activity introduces no code behavior or applicable TDD cycle; the completed independent technical gate is preserved separately.
