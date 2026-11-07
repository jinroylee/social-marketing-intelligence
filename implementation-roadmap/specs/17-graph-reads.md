# S17. Page governed graph branches with stable identities and policy frontiers

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Cursor and policy-frontier protocol with an explicitly open mechanism choice. Decisions to chart before implementation: cursor token versus page manifest; policy frontier: revision port versus pinned dependency digest; branch membership model; per-call work bounds.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_knowledge.graph owns search/traversal/page contracts; smi_review adapts G1
Direct spec blockers: [Select question-, brief- and graph-scoped governed support at pilot scale](07-pilot-scale-retrieval.md) (Graph seeds and continuation must use pilot-scale selection, not the newest 100 members.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A graph client can expand bounded branches without fetching an unrestricted graph or restoring withdrawn support.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_knowledge/graph/store.py](../../src/smi_knowledge/graph/store.py)
- [src/smi_knowledge/graph/AGENTS.md](../../src/smi_knowledge/graph/AGENTS.md)
- [tests/test_graph.py](../../tests/test_graph.py)

## Scope and non-goals

Extend the existing projection with scoped continuation pages, branch membership, current-policy frontier and unavailable IDs. Preserve PostgreSQL and existing native identities. Do not claim traversal work_limit bounds the existing initial projection build. Graph seeds and continuation use the S07 selection port instead of the newest 100 members.

## Owners, interfaces and data shapes

Proposed KnowledgeGraph.page(search_id, actor, root_id, traversal, cursor, generation, branch_id, include_synthetic=False) -> search/support digest, request generation, policy frontier, stable nodes/edges, branch memberships, cursor, work/coverage/truncation and unavailable IDs. Cursor binds workspace/requester/search/root/filter/observation scope/support digest/frontier and ordered continuation, authenticated by server. Each page reopens policy. Changed scope or frontier invalidates cursor and requests a restart. Per-call scan/member/projection/edge/byte bounds are explicit and independently reported.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Prefer source-free cursor tokens or small owner-owned page manifests with expiry. Store no graph values or excerpts. Add a monotonic source-policy revision port only with its natural ingestion/recent owner, or derive a complete pinned dependency digest under current owner locks; do not invent a global atomic frontier. Update knowledge, architecture, local-review, ERD and graph instructions where changed.

## UI reads, commands and agent integration

G1 supports direction, predicates/bases, kind/platform/namespace, capture range, exact observations, 1–3 hops and finite work. Existing search pins support; new publications require explicit new search. Agent reads use this same bounded contract.

## Invariants and authorization

Filter every traversed neighbor and all label/detail support. Unselected observations cannot contribute shared labels or bridges. Read-only expansion acquires no sources and asserts no Creator equivalence, endorsement or causation.

## Failure and recovery

Expired cursor or policy-frontier change returns restart_required and forbidden IDs. Failed page retains only still-governed prior members. Concurrent source loss returns tombstones, clears dependent edges/aggregates and cannot be hidden by a cached layout.

## Acceptance

### S17-A01

Page a cyclic multi-branch graph with exact-source filtering and observe no duplicate identities or hidden bridges; each limit reports its actual bound.

### S17-A02

Reuse a cursor under another actor/workspace/root/filter and observe rejection. Publish later support and observe unchanged saved selection.

### S17-A03

Withdraw an observation between pages, restart the bounded read and observe no stale labels/edges/counts.

### S17-A04

Exercise empty, truncated, unknown root and denied derivation states via public API and inspect exact edge basis/dates/support.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-G01, FR-G02, FR-P08, OFR-G01, PROP-18, PROP-20, PROP-26, PROP-27, PROP-32, UD-06, R2-GRAPH. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
