# 27: Answer free-form questions from permitted knowledge

**What to build:** A marketer can ask a free-form KB question and receive an answer with inspectable support, dates, uncertainty, and explicit missing information.

**Blocked by:** 03: Search current knowledge and pin result support; 13: Interpret natural-language criteria with one metered model.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Bounded knowledge retrieval and one model-backed answer journey using the established metered transport; no enrichment submission or external search tools.

- [ ] A local question/answer surface delegates to current permitted KB queries and records the actual support manifest and model/method context used.
- [ ] Supported claims cite relevant permitted observations/interpretations and dates; missing, stale, ambiguous, or unsupported information remains explicit.
- [ ] Reading existing knowledge requires no enrichment approval; no provider acquisition results or pending publication can support an answer.
- [ ] Generated output is validated against the allowed support; evidence text cannot authorize tools, broaden scope, change actor authority, or override spending.
- [ ] Model calls use shared cost admission and attributable usage; missing model/configuration or invalid output is a visible limitation/failure.
- [ ] Reopened answer/support views and later questions respect current source policy and new publications without rewriting historical support.

**Spec coverage:** user stories 21, 22, 23, 24, 33, 68; acceptance scenarios T08, T09, T12, T16 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
