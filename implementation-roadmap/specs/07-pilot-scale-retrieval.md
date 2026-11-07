# S07. Select question-, brief- and graph-scoped governed support at pilot scale

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. L-sized; its index and ranking choices decide chat and campaign usefulness on KR/JP data. Decisions to chart before implementation: index mechanism for Korean/Japanese (term table, pg_trgm or tsvector); normalization and CJK n-gram rules; ranking rule among matches; scan bounds and keyset continuation; purge-with-source index ownership.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_knowledge.queries owns selection; smi_ingestion owns the governed index columns and migration
Direct spec blockers: [Restore a complete, time-stable verification baseline](01-stable-verification-clock.md) (Changes query bounds exercised across the campaign, assistant and graph suites.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

Chat, campaign comparison and graph seeds select relevant permitted support from a KB much larger than 100 publications, with explicit, reported bounds.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_knowledge/queries/store.py](../../src/smi_knowledge/queries/store.py)
- [src/smi_assistant/store.py](../../src/smi_assistant/store.py)
- [src/smi_campaigns/store.py](../../src/smi_campaigns/store.py)
- [src/smi_knowledge/graph/store.py](../../src/smi_knowledge/graph/store.py)
- [src/smi_knowledge/queries/AGENTS.md](../../src/smi_knowledge/queries/AGENTS.md)

## Scope and non-goals

An indexed selection port owned by ingestion (governed text and normalized-term index on ingestion-owned columns, purged with the source) used by KnowledgeQueries; configurable member and scan bounds with keyset continuation reported in coverage; a deterministic per-turn scope derived from the question (NFKC normalization, literal terms, CJK n-grams, catalog alias to subject_ids) pinned in the answer/turn record; brief-driven, account-centric candidate selection for prepare_current_comparison; GraphScope seeds use the same port. Non-goals: embeddings and semantic ranking (S36); model-proposed terms, which would add a second model influence not covered by ADR 0017. Record the index mechanism (own term table, pg_trgm or tsvector; PostgreSQL has no Korean or Japanese text-search parser) with benchmark results on the 1,000-post fixture, and a deterministic, versioned ranking rule among matches (recommended: exact subject-ID matches, then derived-term match count, then recency, with stable tie-breaking). Wire derive_scope into the installed question-to-answer and brief-to-comparison paths whenever the caller supplies no explicit terms, so the early real-data check exercises the new retrieval.

## Owners, interfaces and data shapes

Proposed QueryScope gains derived_terms, subject_ids, scan_bound and continuation; KnowledgeQueries.search reports actual scanned publications, members, truncation and continuation. Proposed derive_scope(question|brief, catalogs) -> pinned, digest-stable scope. Retrieval never broadens authority or source scope.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Ingestion migration for the governed index with purge-with-source semantics; no second source-value cache. Update docs/knowledge.md, smi_knowledge/queries/AGENTS.md and the ERD.

## UI reads, commands and agent integration

S15 pins each turn's derived scope, S12 uses brief-driven selection and S17 uses the same seed selection. Coverage text in the UI reports the actual bounds.

## Invariants and authorization

Current process/display/retention policy filters every selected member. Withdrawal removes index content with the source. Historical results reopen their pinned membership exactly.

## Failure and recovery

A bound reached is reported as result_limit_reached with a continuation, never as completeness. An index rebuild is idempotent and never resurrects withdrawn values.

## Acceptance

### S07-A01

On a fixture KB of at least 1,000 published posts across at least 200 publications, a question about a brand published only in old publications returns that support with derived terms pinned.

### S07-A02

A comparison includes an eligible creator whose only support is older than the newest 100 members, and its coverage reports the actual scan bounds.

### S07-A03

Withdrawing a source removes it from the index and from new results; a historical result reopens exactly.

### S07-A04

Per-query work stays inside the configured bound, with a recorded latency budget on the reference fixture.

### S07-A05

Exact retries remain digest-stable.

### S07-A06

The recorded index mechanism and ranking rule are documented with fixture benchmark results, and the installed answer and comparison paths (legacy form and CLI) pin the derived scope.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A02, FR-B01, FR-B02, FR-G01, PROP-32, PROP-35. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
