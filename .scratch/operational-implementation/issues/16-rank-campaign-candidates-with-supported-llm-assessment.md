# 16: Rank campaign candidates with supported LLM assessment

**What to build:** A marketer receives an automatically saved campaign shortlist ordered by validated LLM assessment of a bounded current-KB candidate set.

**Blocked by:** 13: Interpret natural-language criteria with one metered model; 15: Automatically save an attributed ordered shortlist.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One configured method/profile and bounded candidate batch using the established model transport; no discovery, model-driven tool loop, or new provider.

- [x] Deterministic eligibility/requirements run before the bounded LLM assessment; incomplete supported accounts remain eligible subject to explicit unknown handling.
- [x] The saved result records actual assessed support, candidate ordering, reasons/gaps, model/method/profile versions, and automated producer.
- [x] Generated judgments may cite only permitted support belonging to assessed candidates; invented accounts, unsupported reasons, and malformed output fail or remain explicitly unassessed.
- [x] Source content cannot change tools, task origin, approvals, scope, or spending; model failure cannot be mislabeled as successful LLM ranking.
- [x] All model calls use the existing metering/admission contract; retrying a completed recommendation reopens its saved revision without another model call.
- [x] Public recommendation and UI tests cover missing attributes, constrained criteria, empty candidates, unsupported output, withdrawal, and restart.

**Spec coverage:** user stories 6, 8, 9, 10, 11, 14, 68; acceptance scenarios T10, T11, T12, T13 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Completion

- Runtime implementation commit: `285d7b2f9f80100f18de48c0356d13d5d597fbe2`. Final worker head and integrated checked commit: `650950bf2f80ad53488e3bc11b1fee12063f975b`, fast-forward integrated into `integration/operational-tickets-11-39`; the final worker commit changes only report/checklist metadata.
- Root `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **443 tests in 511.85 seconds**; log `/tmp/smi-ticket-16-integrated-shared.log`. The gate completed during the usage interruption and was preserved without rerun. All acceptance criteria are checked.
- The independently verified worker wheel matches all 19 listed packaged files in the integrated tree byte for byte. [The implementation report](../reports/ticket-16.md) retains focused slices, the corrected regression, the frozen worker gate and integrated evidence.
- Verification used real PostgreSQL and simulated external I/O. No live/paid provider/source call, readiness/invoice/human-quality claim, external message, push, PR or deployment occurred.
