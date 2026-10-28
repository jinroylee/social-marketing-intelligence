# 34: Enable one verified live recent-X route

**What to build:** An operator can enable one configured live recent-X collection route for monitoring topics and inspect bounded recent windows without full KB ingestion.

**Blocked by:** 07: Coordinate competing workers without duplicate effects; 11: Reconcile delayed charges and failed meters; 29: Collect bounded recent X evidence offline.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One provider and recent-post query type wired to existing topic/window collection; no new anomaly method or external follow-up research.

- [x] Verify the selected route's current primary contract, permitted use, identities, pagination, limits, and bounded response shape during implementation.
- [x] Configured periodic polling uses coordinated worker execution and creates exact recent windows under topic authority, independently of KB publication.
- [x] Source limits, request/byte/record bounds, shared spending admission, usage/reconciliation, and retention apply before and after each call.
- [x] Pending/ambiguous outcomes and concurrent due polls do not blindly repeat chargeable work or duplicate logical windows.
- [x] Missing credentials/policy/cost configuration or explicit live authorization remains an external prerequisite; never invent a successful readiness receipt.
- [x] Default tests simulate transport. Any separately authorized bounded live receipt records actual attempts, timestamps, missingness, coverage and derivable costs without secrets.

**Spec coverage:** user stories 47, 48, 53, 54, 56, 58, 59, 63; acceptance scenarios T07, T19, T21, T22, T23, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

- Runtime implementation `94a0e3347dddf6cce96c86e1fa6d4627b965eae3`; latest integration through `b87862c` merged into clean frozen worker `e94a226f6c2fe80462320bbabdf0d3aa107ff4ae`.
- Required exact offline locked shared gate passed **829 tests in 688.76 seconds**, exit **0**, completed session **42296**, with static/documentation/physical-ERD/relative-symlink/PostgreSQL checks. Completed unchanged gate was preserved, never rerun.
- Subsequent required offline wheel build passed exit **0**. Existing wheel is **412506 bytes**, SHA-256 `5c4aaa23c79397062e297e8f0c0955163887db90e385d108b08a8f5b32796480`, **198 unique entries**. Recording and independent replay passed **88 exact source/archive pairs**, every changed packaged path, all **17** SQL schemas, both review assets, all **30** packaged guidance pairs and root guidance; all **293** protected hashes/link targets remain frozen.
- [Report](../reports/ticket-34.md), [primary-source verification](../research/ticket-34-x-recent-contract.md), [manifest](../reports/ticket-34-wheel-manifest.json) and [standalone verifier](../reports/verify-ticket-34-wheel.py) retain implementation, review-closure, execution and artifact evidence. Persistent worker `verification/ticket-34/` retains actual gate/build/replay logs/status and artifact.
- Issue remains **claimed** for independent integration checks and merger-owned resolution. All six software criteria are verified with fake external HTTP and real PostgreSQL. Actual source-use/commercial/display/storage/deletion clearance, credential, explicit operation authority and bounded live receipt remain unmet external runtime prerequisites; no readiness receipt or actual source/model/paid call is claimed. No external message, push, PR, deployment or cleanup occurred.
