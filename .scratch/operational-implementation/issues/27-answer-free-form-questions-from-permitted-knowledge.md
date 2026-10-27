# 27: Answer free-form questions from permitted knowledge

**What to build:** A marketer can ask a free-form KB question and receive an answer with inspectable support, dates, uncertainty, and explicit missing information.

**Blocked by:** 03: Search current knowledge and pin result support; 13: Interpret natural-language criteria with one metered model.

**Status:** resolved

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

At worker handoff, the bounded extractive KB question/answer journey was implemented and the issue was **claimed** pending independent root integration validation; completed evidence follows. Runtime/frozen `6110c01839e1742a1f8986f9b25f8335c9e97544`; worker shared gate **671 passed in 466.02 seconds**, exit 0. Focused **131 passed in 105.44 seconds**, exit 0; exact wheel verification **67 source/archive pairs**, ten SQL schemas, both review assets and 23 guidance pairs. See [implementation and verification report](../reports/ticket-27.md). Model-selected exact findings do not establish semantic entailment, human language quality, marketer usefulness or live readiness. No enrichment generation/submission, external search or real source/model/paid call occurred.


## Completion

- Runtime implementation and frozen worker checked commit: `6110c01839e1742a1f8986f9b25f8335c9e97544`. Final worker handoff and root integrated checked commit: `c37f76a71d2a739c6c44936dd27b604824960fba`, fast-forward integrated from clean `a96bb2ac08ecae8dc644b6a488cfcdcc8ca8a663`. Frozen-to-final changes are limited to this checklist/handoff, the ticket's report and exact wheel manifest.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **671 tests in 466.67 seconds**, exit **0**, session `59103`. Durable root log `.scratch/operational-implementation/verification/ticket-27-integrated/shared.log` and siblings `shared.started`, `shared.finished`, `shared.head`, `shared.command`, `shared.session`, `shared.exit` retain exact execution identity/status. Worker and earlier completed passing gates are preserved; all six acceptance criteria are checked.
- Independently verified the persistent wheel: **326214 bytes**, SHA-256 `176a591e0d36aa93b2548a96e5b3fe0e5e619d0046cf97ee986a299295567d9d`, **154 unique archive entries** and all **67 source/archive pairs**, including all ten SQL schemas, both review assets, all 23 packaged guidance pairs and every changed packaged file. Source/archive bytes, sizes, hashes and relative sibling targets match integrated root. [Report](../reports/ticket-27.md), [exact manifest](../reports/ticket-27-wheel-manifest.json), [verifier](../reports/verify-ticket-27-wheel.py) and root `verification/ticket-27-integrated/wheel-verification.json` retain exact artifact evidence.
- Dispatch-time permission race is repaired in the frozen runtime: after accounting contention, the trusted dispatch guard reopens every exact model input and holds current source locks through admission commit; no I/O transaction is introduced. Public real-PostgreSQL regression proves refusal, zero model calls and zero outstanding liability. The 15-case owner suite, 131-case compatibility suite and required root full gate cover final bytes; no blocking root finding remains.
- `smi_assistant` provides bounded extractive exact published findings with full-input dependencies, no arbitrary generated factual prose, source-value cache, acquisition or tools. Model configuration, real keys/rates/enablement, live receipt and human language/usefulness remain unestablished independent runtime/quality gates. Schema-valid selection does not establish semantic relevance, entailment or usefulness. No actual source/model/paid call, external message, push, PR or deployment occurred.
