# S18. Explore the production graph with camera, pins and incremental branches

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. L-sized client whose first deliverable is itself a library decision. Decisions to chart before implementation: layout library (spike) and licence; relationship/compact layouts and pinning; camera and branch state model; keyboard/list alternative design.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_review graph client owns layout/camera/branch state; smi_knowledge.graph owns evidence
Direct spec blockers: [Page governed graph branches with stable identities and policy frontiers](17-graph-reads.md) (Consumes branch pages, cursors and generations.), [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (Selection opens the shared inspector.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer uses the approved interactive graph with pointer or keyboard and retains context as branches expand.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_review/graph_views.py](../../src/smi_review/graph_views.py)
- [src/smi_knowledge/graph/store.py](../../src/smi_knowledge/graph/store.py)
- [.scratch/product-design-2026-11/task3/r2/design-spec.md](../../.scratch/product-design-2026-11/task3/r2/design-spec.md)

## Scope and non-goals

First deliverable: a time-boxed spike (at most 3 working days) that renders S17 fixture branch pages with the candidate library and records the engineering decision. Recommended: a vendored, pinned, licence-recorded library such as Cytoscape.js with its SHA-256 in the repository; a hand-built layout only if the spike fails. Offer an optional, non-gating 30-minute human look. Deliver pan, pointer-anchored wheel/pinch zoom, Fit, drag, explicit pin/unpin, deterministic relationship/compact layouts, relayout/reset, expand/collapse, filters, inspector and equivalent paginated list. Simplified r2 mockup is not the production acceptance bar.

## Owners, interfaces and data shapes

Separate camera, coordinates/pins, selected ID, branch membership and request generations. branch -> node/edge membership reference sets preserve a shared node when one branch collapses. Increment generation on scope change. Abort superseded reads and discard mismatched late pages by search/root/branch/filter/support/generation. Merge stable IDs, never labels/coordinates. Client positions contain only IDs and geometry and cannot restore source fields. This spec owns the graph branch/generation reducer and the layout library decision.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No canonical schema change. Optional local geometry persistence is scoped by search and stores no labels/evidence. Reset has explicit semantics. Update local-review/knowledge interaction documentation and new substantial client-module instructions with the required sibling symlink.

## UI reads, commands and agent integration

G1 inspector exposes identity, relationship direction/basis, conflicts, support, dates and methods. Language changes retain selection. Arrow navigation/Enter/expand/collapse/pin controls and labelled camera controls duplicate pointer affordances. Announce loading/additions/truncation/unavailable selection. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Camera/layout actions never change evidence scope or task authority. A collapsed or withdrawn selection has a source-free placeholder rather than a silently substituted node. Color is supplemented by shapes, line styles and labels.

## Failure and recovery

Loading/failed branch retains still-governed members and offers same-read retry. Policy response removes forbidden values immediately. Out-of-order, cancelled and expired-cursor results cannot repopulate them. No offline evidence cache.

## Acceptance

### S18-A01

Node reducer tests: expand two overlapping branches, collapse one and retain shared members, selection and pinned positions.

### S18-A02

Node reducer tests: change filters during a slow page and deliver the stale response late; observe no stale merge. A governed withdrawal response removes affected nodes immediately.

### S18-A03

Explicit Load more/truncation drives bounded server work through the public API with no unbounded recursive fetch.

### S18-A04

Deliver the S25 checklist covering pointer drag/pin, pointer-anchored zoom, Fit, reduced motion and keyboard/list-only search, selection, traversal, evidence, pin and fit.

### S18-A05

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-G01, FR-G02, OFR-G01, PROP-07, UD-03, UD-06, UD-07, R2-GRAPH. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
