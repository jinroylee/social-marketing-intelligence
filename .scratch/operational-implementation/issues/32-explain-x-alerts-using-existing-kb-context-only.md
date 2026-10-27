# 32: Explain X alerts using existing KB context only

**What to build:** A marketer can open an X alert and see relevant existing KB context separately from the recent evidence that triggered detection.

**Blocked by:** 03: Search current knowledge and pin result support; 30: Detect quantitative X anomalies with retained alerts.

**Status:** claimed

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Bounded existing-KB context lookup and explanation for the shared alert contract; no new external searches or automatic campaign initiation.

- [ ] The investigation reads only committed permitted KB knowledge available to its bounded query and pins the exact supporting context selected.
- [ ] Alert detail distinguishes recent monitoring evidence, existing KB context, and derived explanation with dates, coverage, and uncertainty.
- [ ] An investigation has no authority/capability to submit enrichment, forge scheduled collection, broaden configured topics, or create campaigns.
- [ ] Missing KB context yields an explicit gap rather than external fallback or invented facts.
- [ ] Current policy and newer publications do not substitute new evidence into a saved alert's context; denied dependencies redact copied explanations.
- [ ] Public integration tests count external/model acquisition transports as forbidden and verify the same behavior for any supported alert method.

**Spec coverage:** user stories 22, 52, 54, 57, 68; acceptance scenarios T08, T09, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
