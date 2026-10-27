# 29: Collect bounded recent X evidence offline

**What to build:** An operator can configure an X monitoring topic, run a bounded offline collection window, and inspect retained recent observations independently of the full KB.

**Blocked by:** 01: Restore ingestion completion and safe resume.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One deterministic recent-X route, one topic/window collection journey, and retention/policy-aware timeline; no alerts, live provider, or full KB ingestion.

- [x] Persist monitoring topic configuration separately from scheduled keywords with explicit cadence/window, bounded collection, source policy, and retention settings.
- [x] A public bounded poll entry point retains recent observations with stable source references/identities, capture/publication times, window coverage, and acquisition context.
- [x] The topic/window/timeline surface reopens observations after restart without creating campaigns or requiring knowledge publications for every post.
- [x] Retries do not duplicate a logical window's observations; missing fields and incomplete coverage remain visible.
- [x] Process/display/retention permissions, expiry, and withdrawal govern retained monitoring copies and their detail views.
- [x] Offline integration tests prohibit external I/O and prove existing frozen-snapshot investigations keep their original independent behavior.

**Spec coverage:** user stories 47, 48, 53, 54, 56, 57, 68, 69; acceptance scenarios T08, T24, T26, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

- Runtime `4aa3535eb5ba3987b9e7aa93b888665e808d7197`; latest integration merged and frozen at `51ce0aec6ca3c83d43991f9492c3c970ef3a8830`.
- Required offline locked shared check passed exit 0: **706 tests in 480.99s**, completed session `19612`; persistent worktree `verification/ticket-29/shared.{json,log}` records exact execution evidence.
- Offline wheel and 72 exact source/archive pairs verified, covering all changed packaged files, 12 SQL schemas, both review assets and 25 packaged guidance pairs. See [the implementer report](../reports/ticket-29.md), manifest and standalone verifier.
- Status remains **claimed** for independent integration verification and merger-owned resolution. No runtime/test/product-doc/guidance edit followed freeze; no live call, paid operation, external message, push, PR, deployment or cleanup occurred.
