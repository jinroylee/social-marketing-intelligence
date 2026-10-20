# Product documentation

These documents describe the Social Marketing Intelligence product, its architecture and its data contracts. They are maintained with the code. Accepted design that is not yet implemented is identified explicitly.

| Document | Purpose |
| --- | --- |
| [Operational functional requirements](functional-requirements.md) | Target A/B/C flows, automatic shortlist persistence, acquisition/approval, explorer surfaces and hybrid spending; implemented versus missing coverage |
| [Operational implementation specification](implementation-spec.md) | Consolidated implementation draft: user stories, public contracts, acceptance scenarios and bounded delivery milestones |
| [Reader guide](reader-guide.md) | Plain-language walkthrough, sample data, UI-to-code map, table dictionary and current automation boundaries |
| [Architecture](architecture.md) | Product boundaries, module ownership, data flow and current implementation coverage |
| [Data model and ERD](data-model.md) | Implemented PostgreSQL relationships and the accepted business model |
| [Evidence sets](evidence-sets.md) | Offline import, provenance, immutable membership, actor context and policy-aware reads |
| [Shared knowledge](knowledge.md) | Brand/Product references, caption interpretations, dependency cleanup and translation-assisted review packets |
| [Source integrations](source-integrations.md) | Implemented route capabilities, retained verification evidence and remaining discovery/readiness work |
| [Offline acquisition tasks](tasks.md) | Campaign and exact approved-proposal durable submission, bounded synthetic worker and exact outcomes |
| [Offline cost accounting](costs.md) | Attributable synthetic measured usage, forecasts, declared commitments, uncertainty and local cost detail |
| [Campaign decisions](campaigns.md) | Current versioned campaign workflow and future ranked recommendations with automatic shortlist persistence |
| [Independent monitoring](monitoring.md) | Investigation scopes, literal snapshot findings, counts and policy-aware history |
| [Measurement and feedback](planning.md) | Proposed campaign plans and human decision-note revisions |
| [Local review application](local-review.md) | Browser workflow, named local actor, evidence panels, saves and failure behavior |
| [Development verification](development.md) | The shared local/CI check command and test prerequisites |
| [Agent workflow configuration](agents/issue-tracker.md) | Local ticket publication, dependency gates, claiming, validation and resolution |
| [Quality review](evaluation.md) | Separate technical, translation-assisted and marketer-usefulness gates |
| [Canonical evidence ownership](adr/0001-canonical-evidence-ownership.md) | Why source evidence and business decisions have separate owners |
| [Pinned support and current policy](adr/0002-pinned-support-current-policy.md) | Why reproducible decisions pin support while permissions remain current |
| [Automatic shortlist persistence](adr/0003-automatic-shortlist-persistence.md) | Why saving generated recommendations requires no human review or approval |
| [Lightweight monitoring evidence](adr/0004-lightweight-monitoring-evidence.md) | Why X detection owns bounded recent evidence separately from full KB publication |
| [Task session effect ownership](adr/0005-task-session-effect-ownership.md) | Why each task's execution lock and effect transactions share one PostgreSQL session |

The root [glossary](../GLOSSARY.md) defines domain language; the [README](../README.md) explains local commands.

## Maintenance

- Update the architecture when responsibilities, dependencies or deployment boundaries change.
- Update the physical ERD with schema changes. Keep accepted future objects in the separately marked conceptual model until they are implemented.
- Update interface documentation when inputs, outputs, invariants or failure behavior change.
- Add ADRs for durable decisions with meaningful alternatives and consequences. Describe the product trade-off; preserve superseded ADR links when a decision changes.
- Prefer Markdown and Mermaid as reviewable source. Keep one authoritative description of each contract and link to it from other documents.

Implementation tickets, experiment results and session chronology live in `.scratch/`.
