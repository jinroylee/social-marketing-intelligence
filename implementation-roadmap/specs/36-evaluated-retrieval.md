# S36. Improve multilingual retrieval with pinned, rebuildable support

Status: planned, no implementation or validation claimed.
Lane: later-core-depth
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Research-led retrieval depth with evaluation design. Decisions to chart before implementation: held-out bilingual evaluation set; semantic retrieval candidates and stores; index rebuild and pinning.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_knowledge.queries owns retrieval selection; ingestion owns source truth; campaign/assistant consume exact results
Direct spec blockers: [Select question-, brief- and graph-scoped governed support at pilot scale](07-pilot-scale-retrieval.md) (The deterministic baseline to beat.), [Preserve measurement planning and prepare attributable KR/JP quality packets](30-plans-and-quality.md) (Held-out bilingual evaluation packets.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

Marketers find relevant Korean/Japanese support beyond literal matches with inspectable recall and ranking limits.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_knowledge/queries/](../../src/smi_knowledge/queries/)
- [src/smi_campaigns/store.py](../../src/smi_campaigns/store.py)
- [src/smi_assistant/store.py](../../src/smi_assistant/store.py)
- [docs/knowledge.md](../../docs/knowledge.md)

## Scope and non-goals

Define a held-out bilingual question/candidate set and compare literal/relationship plus semantic retrieval candidates. Use PostgreSQL first; select embeddings or specialized stores only when evidence justifies them. Keep installed exact-finding answers valid during this depth extension. Compare against the deterministic S07 baseline.

## Owners, interfaces and data shapes

Version QueryScope/method and support manifests with original query, market versus language, exact ranked members, score meaning, input/index frontier and truncation. Public search/read contracts continue current-policy checking and immutable result membership. Model retrieval tools return support IDs and uncertainty, never factual authority.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Any search index/vector table is an owner-managed rebuildable projection with model/version/dependency/expiry/tombstone metadata. Backfill from permitted publications, never unrestricted payloads. Update knowledge, evaluation, architecture, ERD and query instructions.

## UI reads, commands and agent integration

C1/K1/G1 display actual retrieval method and sample limits. New retrieval can inform a new recommendation/question; it does not rewrite prior decisions. Source-free index health exposes lag and rebuild status.

## Invariants and authorization

Permission filtering occurs before exposing labels, scores or snippets and again on selected use. Index membership cannot make unpublished support usable. Compare relevance and cost under stated corpus/coverage; no invented speedup or quality percentage.

## Failure and recovery

Index lag/failure either returns a clearly labelled configured literal method for a new request or blocks; an existing saved request never changes method silently. Withdrawal propagates to retained derivatives and rebuilds.

## Acceptance

### S36-A01

Run held-out KR/JP retrieval evaluation with exact corpus, methods, denominators and negative queries, and preserve all results.

### S36-A02

Rebuild an index, replay duplicate updates and reopen old query results without changed membership.

### S36-A03

Withdraw support during retrieval/admission and observe no prohibited result/score/snippet or resurrection on rebuild.

### S36-A04

Demonstrate measurable user relevance need before adding a specialized store. A benchmark claim needs its own measurement review.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A02, FR-B01, FR-B02, PROP-05, PROP-26, PROP-32, PROP-35. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
