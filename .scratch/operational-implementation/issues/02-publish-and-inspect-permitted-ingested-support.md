# 02: Publish and inspect permitted ingested support

**What to build:** An operator can publish a bounded selection of already-ingested evidence and reopen a knowledge-publication detail page with exact usable support.

**Blocked by:** 01: Restore ingestion completion and safe resume.

**Status:** resolved

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Deliver publication by identity for a bounded source-only selection and supported existing caption interpretations; no general search, background tasks, embeddings, or new ontology.

- [x] A trusted operation publishes validated observation/derivation/assertion references with method versions, source times, publication time, coverage, and actual producer.
- [x] A source-backed account can be published with unknown profile/interpretation attributes; unsupported claims and un-ingested references cannot be published as facts.
- [x] A local publication detail surface reopens the committed selection and exact support after restart; partially prepared support is never visible as a committed publication.
- [x] Identical concurrent publication requests return one logical publication; changed payload under the same request identity conflicts.
- [x] Process/display/retention policy, commit-time withdrawal, superseded support, and later redaction or copy purge retain the existing evidence-owner contract.
- [x] Adding a new publication never mutates imported evidence-set membership or previously pinned support; existing pilot reads and explicit development-only synthetic visibility remain compatible.

**Spec coverage:** user stories 5, 6, 9, 10, 14, 32, 38, 68, 69; acceptance scenarios T01, T03, T05, T08, T09, T29 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.

## Implementation evidence

Implemented on `smi/operational-ticket-02` and integrated after passing the shared checks. See [the implementation report](../reports/ticket-02.md) for public interfaces, red/green evidence and validation.

## Completion

- Implementation commit: `09f3d18d9a4195c8f14fd670e51c1b157a7f2ced`, fast-forward integrated into `integration/operational-tickets-01-10`.
- Integrated verification: `UV_OFFLINE=1 uv run --locked python tools/check.py` passed Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **223 tests in 128.48 seconds**.
- All acceptance criteria are checked. Delivery remained offline and local, with real PostgreSQL and simulated external I/O; no push or PR occurred.
