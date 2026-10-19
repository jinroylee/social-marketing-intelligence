# 13: Interpret natural-language criteria with one metered model

**What to build:** A marketer can turn natural-language campaign criteria into a visible, versioned executable interpretation using one explicitly configured model route.

**Blocked by:** 11: Reconcile delayed charges and failed meters; 12: Save visible executable campaign criteria.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One provider transport and one bounded criteria-interpretation journey; default tests simulate transport and live enablement requires explicit configuration.

- [ ] Natural-language input produces a contract-validated interpretation with requirements, preferences, exclusions, unknown handling, method/model versions, and original-input linkage.
- [ ] The executable interpretation is visible before it is used for assessment and remains pinned to the exact brief/profile revision.
- [ ] Malformed or unsupported generated criteria fail visibly; source/model text cannot grant task authority, broaden approval, or override constraints.
- [ ] The configured model route records attributable usage, obtains cost admission before calls, reconciles outcomes, and respects request/output bounds.
- [ ] Missing key, model configuration, rate classification, or admission yields a visible unavailable/blocked capability rather than an unbounded call or invented interpretation.
- [ ] Verify the selected provider's current primary contract during implementation; use simulated success/failure/authority-forgery responses in default integration tests and record any separately authorized live receipt.

**Spec coverage:** user stories 2, 3, 4, 58, 59, 63; acceptance scenarios T11, T12, T21, T23 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
