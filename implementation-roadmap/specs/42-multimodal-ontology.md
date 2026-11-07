# S42. Add evidenced multimodal and richer ontology concepts

Status: planned, no implementation or validation claimed.
Lane: later-proposal
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Per-slice ontology and modality extensions. Decisions to chart before implementation: which modality and concept first; reversible association decisions; evaluation per slice.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Ingestion owns modality observations; knowledge owns versioned interpretations/catalog/identity decisions; graph remains a projection
Direct spec blockers: [Improve multilingual retrieval with pinned, rebuildable support](36-evaluated-retrieval.md) (New concepts need evaluated retrieval.), [Reconcile retained copies and rebuildable projections with operational recovery](41-projection-governance.md) (Retained copies must already reconcile.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Real use case, permitted modality/source data, evaluated model and domain-owner acceptance are prerequisites per extension.

## User outcome

Marketers inspect supported beauty, creator, topic and event relationships without turning mentions into identity or verified effects.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_ingestion/canonical.py](../../src/smi_ingestion/canonical.py)
- [src/smi_knowledge/graph/store.py](../../src/smi_knowledge/graph/store.py)
- [GLOSSARY.md](../../GLOSSARY.md)
- [POPOSAL.md](../../POPOSAL.md)

## Scope and non-goals

Implement one narrowly evaluated modality and ontology extension per slice, then expand. Candidate concepts include Creator/account association, Collaboration, Audience Segment, Social Event, product variant/aspects and effective-dated market policies. Illustrative proposal objects are not all mandatory at once.

## Owners, interfaces and data shapes

Define typed observed/derived/human assertions with original modality/time coordinates, evidence/method/version/uncertainty and reversible entity-association decisions. Public correction operations require exact evidence/reason/actor and expected head. Localized labels extend stable IDs. Graph predicates expose only accepted supported concepts; no matching-handle identity merge.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add only required typed source/interpretation/association tables, version policy applicability and new source dependency purge ports. Migrate existing account/content IDs without changing namespace identity. Update glossary on accepted domain decisions, architecture/ERD, knowledge/evidence/source contracts and owner instructions with sibling symlinks.

## UI reads, commands and agent integration

C1/K1/G1 inspectors expose modality evidence and conflicting associations; unsupported concepts are unavailable. Source language, UI language, market, audience geography and product origin remain separate. Multimodal model tools are read/proposal-only without acquisition authority.

## Invariants and authorization

Audio/video/image access, extraction, display and retention require actual rights and model quality. Product-family mention is not shade/variant identity or substantiation. Human correction remains attributable and reversible.

## Failure and recovery

Ambiguous associations coexist as conflicts. Source withdrawal purges all dependent modality extracts and graph values. Wrong association correction invalidates dependent interpretations prospectively while historical decisions retain original basis/limitations.

## Acceptance

### S42-A01

Ingest one permitted modality sample and trace an exact derived assertion to coordinates and current source policy.

### S42-A02

Record and reverse a corroborated Creator/account association; matching handles alone cannot create it.

### S42-A03

Evaluate original-language beauty/aspect examples including ambiguity and errors with named reviewers.

### S42-A04

Withdraw the original asset and observe no retained transcript/thumbnail/vector/derived relationship leak.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-B05, PROP-03, PROP-08, PROP-16, PROP-18, PROP-19, PROP-20, PROP-21, PROP-22, PROP-23, PROP-24. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
