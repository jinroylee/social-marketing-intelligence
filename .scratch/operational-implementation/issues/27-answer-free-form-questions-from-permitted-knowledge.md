# 27: Answer free-form questions from permitted knowledge

**What to build:** A marketer can ask a free-form KB question and receive an answer with inspectable support, dates, uncertainty, and explicit missing information.

**Blocked by:** 03: Search current knowledge and pin result support; 13: Interpret natural-language criteria with one metered model.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Bounded knowledge retrieval and one model-backed answer journey using the established metered transport; no enrichment submission or external search tools.

- [x] A local question/answer surface delegates to current permitted KB queries and records the actual support manifest and model/method context used.
- [x] Supported claims cite relevant permitted observations/interpretations and dates; missing, stale, ambiguous, or unsupported information remains explicit.
- [x] Reading existing knowledge requires no enrichment approval; no provider acquisition results or pending publication can support an answer.
- [x] Generated output is validated against the allowed support; evidence text cannot authorize tools, broaden scope, change actor authority, or override spending.
- [x] Model calls use shared cost admission and attributable usage; missing model/configuration or invalid output is a visible limitation/failure.
- [x] Reopened answer/support views and later questions respect current source policy and new publications without rewriting historical support.

**Spec coverage:** user stories 21, 22, 23, 24, 33, 68; acceptance scenarios T08, T09, T12, T16 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

Bounded extractive KB question/answer journey implemented; the issue remains **claimed** pending independent root integration validation. Runtime/frozen `6110c01839e1742a1f8986f9b25f8335c9e97544`; worker shared gate **671 passed in 466.02 seconds**, exit 0. Focused **131 passed in 105.44 seconds**, exit 0; exact wheel verification **67 source/archive pairs**, ten SQL schemas, both review assets and 23 guidance pairs. See [implementation and verification report](../reports/ticket-27.md). Model-selected exact findings do not establish semantic entailment, human language quality, marketer usefulness or live readiness. No enrichment generation/submission, external search or real source/model/paid call occurred.
