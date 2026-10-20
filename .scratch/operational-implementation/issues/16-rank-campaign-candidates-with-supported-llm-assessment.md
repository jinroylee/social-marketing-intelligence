# 16: Rank campaign candidates with supported LLM assessment

**What to build:** A marketer receives an automatically saved campaign shortlist ordered by validated LLM assessment of a bounded current-KB candidate set.

**Blocked by:** 13: Interpret natural-language criteria with one metered model; 15: Automatically save an attributed ordered shortlist.

**Status:** ready-for-agent

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One configured method/profile and bounded candidate batch using the established model transport; no discovery, model-driven tool loop, or new provider.

- [ ] Deterministic eligibility/requirements run before the bounded LLM assessment; incomplete supported accounts remain eligible subject to explicit unknown handling.
- [ ] The saved result records actual assessed support, candidate ordering, reasons/gaps, model/method/profile versions, and automated producer.
- [ ] Generated judgments may cite only permitted support belonging to assessed candidates; invented accounts, unsupported reasons, and malformed output fail or remain explicitly unassessed.
- [ ] Source content cannot change tools, task origin, approvals, scope, or spending; model failure cannot be mislabeled as successful LLM ranking.
- [ ] All model calls use the existing metering/admission contract; retrying a completed recommendation reopens its saved revision without another model call.
- [ ] Public recommendation and UI tests cover missing attributes, constrained criteria, empty candidates, unsupported output, withdrawal, and restart.

**Spec coverage:** user stories 6, 8, 9, 10, 11, 14, 68; acceptance scenarios T10, T11, T12, T13 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
