# Product documentation

Start with the [complete user and operator guide](user-guide.md) for setup, every implemented workflow, exact execution/recovery steps, IDs and the technical path behind each action. The root [README](../README.md) provides a concise quickstart. Read the [architecture](architecture.md) for the current system, the [requirements](functional-requirements.md) for accepted behavior, and the [roadmap](roadmap.md) for live/human readiness and the larger product destination. The [glossary](../GLOSSARY.md) defines shared domain language.

## Current system and target

| Document | Purpose |
| --- | --- |
| [User and operator guide](user-guide.md) | Numbered end-to-end manual, feature coverage matrix, environment/startup, offline smoke walkthrough, explicit workers, configuration, recovery and troubleshooting |
| [Architecture](architecture.md) | Runtime, module ownership, end-to-end data flow, authority and failure boundaries |
| [Data model](data-model.md) | All 85 physical tables/ERDs, table dictionary, sample lineage and separately marked conceptual domain |
| [Functional requirements](functional-requirements.md) | A/B/C workflows, acquisition, spending and explorer requirements with current coverage |
| [Interface and acceptance contract](implementation-spec.md) | Shared operation semantics, invariants and T01–T30 acceptance obligations |
| [Roadmap and readiness](roadmap.md) | Outstanding human/live validation and preserved long-term goals |
| [Implementation roadmap](../implementation-roadmap/README.md) | Proposed, unimplemented 45-spec build order from the installed system to the approved product, with open decisions |
| [Product proposal](../POPOSAL.md) / [core flows](../FR.md) | Product thesis, multilingual ontology, measurement ambitions and concise target workflows |

## Implemented contracts

| Owner / workflow | Contract |
| --- | --- |
| Frozen import and exact source support | [Evidence sets](evidence-sets.md) |
| Catalog, interpretations, publication, queries, answers and graph | [Shared knowledge](knowledge.md) |
| Briefs, model criteria, comparisons, shortlists, coverage and regeneration | [Campaigns](campaigns.md) |
| Proposal approval, tasks, schedules, recovery, completion and lineage | [Tasks](tasks.md) |
| Usage, forecasts, admission, reconciliation and meter recovery | [Costs](costs.md) |
| Snapshot investigations, recent X, alerts, context, promotion and polling | [Monitoring](monitoring.md) |
| Proposed measurement and human learning | [Planning](planning.md) |
| Browser routes, protected forms and configuration | [Local review](local-review.md) |
| Source capability, provenance and live prerequisites | [Source integrations](source-integrations.md) |
| Human review rules and exact operational packets | [Evaluation](evaluation.md) |
| Local/CI checks | [Development](development.md) |

## Design decisions

[ADRs](adr/) preserve durable rationale, alternatives and consequences. They cover [evidence ownership](adr/0001-canonical-evidence-ownership.md), [pinned support/current policy](adr/0002-pinned-support-current-policy.md), [automatic saves](adr/0003-automatic-shortlist-persistence.md), [lightweight monitoring](adr/0004-lightweight-monitoring-evidence.md), task/session ownership, spending, constrained model outputs, stable schedule accounting, source-response uncertainty, explicit enrichment scope and monitoring lifecycle inheritance. Follow links from the relevant feature contract for the specific decision.

## Agent workflow and maintenance

Use [domain documentation rules](agents/domain.md) before domain/interface changes, [local issue workflow](agents/issue-tracker.md) for active tickets, and [configured labels](agents/triage-labels.md) for triage roles.

Maintain one authoritative description of each contract. Update architecture for responsibility/deployment changes, physical ERDs and the dictionary for schema changes, and owner contracts for interface/invariant changes. Label accepted future design separately from installed software and from live/human validation. Keep durable trade-offs in ADRs; use Git for code/design chronology. Temporary implementation notes may live in `.scratch/` while useful; completed plans, duplicate ticket drafts and session histories need not be retained. Keep genuine outstanding work in the roadmap. Raw source/verification evidence remains subject to its own retention policy.
