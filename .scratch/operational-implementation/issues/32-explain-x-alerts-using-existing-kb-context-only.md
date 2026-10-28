# 32: Explain X alerts using existing KB context only

**What to build:** A marketer can open an X alert and see relevant existing KB context separately from the recent evidence that triggered detection.

**Blocked by:** 03: Search current knowledge and pin result support; 30: Detect quantitative X anomalies with retained alerts.

**Status:** resolved

**Size:** S — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Bounded existing-KB context lookup and explanation for the shared alert contract; no new external searches or automatic campaign initiation.

- [x] The investigation reads only committed permitted KB knowledge available to its bounded query and pins the exact supporting context selected.
- [x] Alert detail distinguishes recent monitoring evidence, existing KB context, and derived explanation with dates, coverage, and uncertainty.
- [x] An investigation has no authority/capability to submit enrichment, forge scheduled collection, broaden configured topics, or create campaigns.
- [x] Missing KB context yields an explicit gap rather than external fallback or invented facts.
- [x] Current policy and newer publications do not substitute new evidence into a saved alert's context; denied dependencies redact copied explanations.
- [x] Public integration tests count external/model acquisition transports as forbidden and verify the same behavior for any supported alert method.

**Spec coverage:** user stories 22, 52, 54, 57, 68; acceptance scenarios T08, T09, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Completion

- Runtime implementation and frozen worker checked commit: `91d995bc5f0fd814e6c6c20a335ea080d59d7cf7`. Final worker handoff and root integrated checked commit: `2befbb4b0014530659a982ce6800cecc02a3934d`, fast-forward integrated from clean `0ae58b4efb159cd19c9cc93547ec12eed16b0d26`. Frozen-to-final changes are exactly four own scratch handoff files: checklist, report, exact manifest and verifier. Worker freeze evidence preserves all 306 non-scratch files unchanged.
- Required root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **775 tests in 660.52 seconds**, exit **0**, session `24094`. The gate completed during the usage interruption. Resume directly inspected its matching head/log/exit/finished evidence on the unchanged clean tree and retained the completed PASS without rerun. Durable root `.scratch/operational-implementation/verification/ticket-32-integrated/shared.{started,finished,head,runtime,worker-frozen,command,session,log,exit}` retains exact identity/status; all six criteria are checked.
- Independently verified persistent wheel **385942 bytes**, SHA-256 `defa3ef59294b49568e897ca17a8bc1e025dea1e8fe1e94bb74cee7e7e7060a1`, **185 unique archive entries**, all **80 source/archive pairs**, fifteen SQL schemas, both assets and all 28 guidance pairs. Root guidance also matches exact bytes/hash/relative target. The preserved verifier PASS and resumed direct identity/source/archive assertions agree. [Report](../reports/ticket-32.md), [manifest](../reports/ticket-32-wheel-manifest.json), [verifier](../reports/verify-ticket-32-wheel.py) and durable root `verification/ticket-32-integrated/wheel-verification.json` retain exact evidence; no build or test was repeated.
- Root review reported no blocking issue. Final owner 27/18.93s, compatibility 91/59.00s and full 775-test gate cover both current alert methods, caller-owned public alert/query transactions, exact recent/KB dependencies, current process/display/retention/derivation/required-interpretation gates, permanent withholding on observed loss, empty gaps, fresh investigation for newer publications, HTTP/restart/scope/bounds, withdrawal/supersession, atomic rollback and real source-lock contention. External/model/acquisition counters stay zero. The earlier synthetic-fixture `invalid_support_selection` failure is preserved separately; explicit public synthetic select/publish corrected the fixture before final PASS.
- Fixed existing-KB literal context/explanation software is complete without copied source-derived prose or provider/model/acquisition/task/campaign/topic-mutation authority. It establishes no causation, entity equivalence, semantic relevance, market or human-usefulness claim. Actual model/source keys, configuration, rates, enablement, commercial receipts and human quality remain unestablished independent runtime/quality gates; no live readiness is claimed. No runtime/test edit, actual source/model/paid call, external message, push, PR, deployment, archive relocation or cleanup occurred. Worker artifacts remain intact for verified root archival before eventual removal.
