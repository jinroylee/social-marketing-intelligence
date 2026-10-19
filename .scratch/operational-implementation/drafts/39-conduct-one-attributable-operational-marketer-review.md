# 39: Conduct one attributable operational marketer review

**What to build:** A named human reviewer completes one bounded evaluation of the operational campaign, assistant-enrichment, and X-alert journeys with recorded evidence and limitations.

**Blocked by:** 20: Offer explicit regeneration after campaign updates; 28: Turn assistant knowledge gaps into approved enrichment; 32: Explain X alerts using existing KB context only; 38: Prepare and validate operational quality-review packets.

**Status:** draft — awaiting breakdown approval; not published

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
