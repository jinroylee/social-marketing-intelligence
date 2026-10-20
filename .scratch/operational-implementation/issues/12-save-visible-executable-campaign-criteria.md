# 12: Save visible executable campaign criteria

**What to build:** A marketer can save and inspect a versioned executable criteria/ranking profile for a campaign using structured inputs.

**Blocked by:** 01: Restore ingestion completion and safe resume.

**Status:** claimed

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Extend the existing brief workflow with a visible structured profile; no LLM interpretation, current-KB retrieval, or new ranking algorithm.

- [x] Campaign editing records stable criteria identifiers, requirements/preferences/exclusions, explicit unknown handling, and the applicable ranking/coverage profile versions.
- [x] The saved interpretation is visible alongside the marketer's original input and pins the exact brief revision.
- [x] Stale edits conflict through expected-version checks; changed input creates an attributable successor rather than rewriting history.
- [x] Unknown audience, fees, availability, and sales assumptions remain unknown unless supported; structured labels cannot assert source facts.
- [x] Existing human campaign, measurement-plan, decision-note, and protected form behavior remains compatible.
- [x] A public-store and HTTP journey can create, revise, restart, and inspect the exact profile.

**Spec coverage:** user stories 1, 2, 3, 4, 20; acceptance scenarios T11, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
