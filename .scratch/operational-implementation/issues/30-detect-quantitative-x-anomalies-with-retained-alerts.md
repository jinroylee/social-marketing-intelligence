# 30: Detect quantitative X anomalies with retained alerts

**What to build:** A marketer receives an inspectable alert when a configured quantitative method finds a justified X volume or engagement anomaly.

**Blocked by:** 08: Deliver durable task completion notifications; 29: Collect bounded recent X evidence offline.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One configured quantitative method and comparable baseline/window pair, with retained alert history and local inbox delivery; no semantic detection or external investigation.

- [ ] Record explicit detection/baseline windows, sampling and metric comparability, method/version, significance configuration, coverage, and necessary evidence.
- [ ] A supported significant change creates a retained alert and concise durable notification with evidence and uncertainty.
- [ ] Absent/incomparable baselines or insufficient coverage cannot produce an unsupported numerical spike claim and are visible as assessment limitations.
- [ ] Alert detail/history survive restart and reflect current policy, expiry, and unavailable support without retaining denied copied wording.
- [ ] Detection requires no full KB publication for all recent observations and cannot create campaigns, expand topic scope, or launch external searches.
- [ ] Public polling/detection/inbox tests use controlled windows for real anomaly, no anomaly, missing baseline, changed sampling, retries, and withdrawal.

**Spec coverage:** user stories 49, 51, 54, 56, 57; acceptance scenarios T24, T26 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
