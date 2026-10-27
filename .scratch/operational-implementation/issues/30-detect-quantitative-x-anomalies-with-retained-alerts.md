# 30: Detect quantitative X anomalies with retained alerts

**What to build:** A marketer receives an inspectable alert when a configured quantitative method finds a justified X volume or engagement anomaly.

**Blocked by:** 08: Deliver durable task completion notifications; 29: Collect bounded recent X evidence offline.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One configured quantitative method and comparable baseline/window pair, with retained alert history and local inbox delivery; no semantic detection or external investigation.

- [x] Record explicit detection/baseline windows, sampling and metric comparability, method/version, significance configuration, coverage, and necessary evidence.
- [x] A supported significant change creates a retained alert and concise durable notification with evidence and uncertainty.
- [x] Absent/incomparable baselines or insufficient coverage cannot produce an unsupported numerical spike claim and are visible as assessment limitations.
- [x] Alert detail/history survive restart and reflect current policy, expiry, and unavailable support without retaining denied copied wording.
- [x] Detection requires no full KB publication for all recent observations and cannot create campaigns, expand topic scope, or launch external searches.
- [x] Public polling/detection/inbox tests use controlled windows for real anomaly, no anomaly, missing baseline, changed sampling, retries, and withdrawal.

**Spec coverage:** user stories 49, 51, 54, 56, 57; acceptance scenarios T24, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementation handoff

Implemented locally at runtime/frozen `2132df92c4df6c77948169701ef1ad4710f63172`; ticket remains **claimed** for independent merger validation and resolution. [Ticket 30 report](../reports/ticket-30.md) records the configured distinct-native-post volume method, governed retained alerts/local inbox notifications and public PostgreSQL/HTTP coverage. Required `UV_OFFLINE=1 uv run --locked python tools/check.py` passed exit 0: **722 tests in 493.31s**, completed session **45901**, durable `verification/ticket-30/shared.{json,log}`. Final owner 16-case and expanded compatibility/CLI checks passed. The passing full gate was preserved without rerun.

The offline wheel passed exact source/archive verification for all changed packaged files, thirteen SQL schemas, both review assets and all 26 packaged guidance pairs; [manifest](../reports/ticket-30-wheel-manifest.json) and [standalone verifier](../reports/verify-ticket-30-wheel.py) retain exact bytes/size/hash/relative-target evidence. No runtime/test/product-doc/guidance change followed freeze; only this checklist/handoff, report and artifact manifest/verifier were written after PASS. No live source/model/paid execution, external message, push, PR, deployment or cleanup occurred. Semantic detection, KB explanation, promotion and live X remain out of scope. Merger-owned integration gating/resolution and eventual archive-before-cleanup remain required.
