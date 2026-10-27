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
| [Offline acquisition tasks](tasks.md) | Configured daily keyword, campaign and exact approved-proposal submission, bounded synthetic worker and exact outcomes |
| [Offline cost accounting](costs.md) | Attributable synthetic usage, forecasts, shared bounded admission, final-evidence reconciliation, meter recovery and local cost detail |
| [Campaign decisions](campaigns.md) | Versioned campaign workflow, automatic deterministic/model-ordered shortlist persistence, bounded ranking provenance and explicit discovery regeneration |
| [Independent monitoring](monitoring.md) | Frozen investigations, bounded offline X topics/windows/captures and configured quantitative and provisional semantic alerts with policy-aware history and bounded existing-KB context |
| [Measurement and feedback](planning.md) | Proposed campaign plans and human decision-note revisions |
| [Local review application](local-review.md) | Browser workflow, named local actor, evidence panels, saves and failure behavior |
| [Development verification](development.md) | The shared local/CI check command and test prerequisites |
| [Agent workflow configuration](agents/issue-tracker.md) | Local ticket publication, dependency gates, claiming, validation and resolution |
| [Quality review](evaluation.md) | Separate technical, translation-assisted and marketer-usefulness gates |
| [Canonical evidence ownership](adr/0001-canonical-evidence-ownership.md) | Why source evidence and business decisions have separate owners |
| [Explicit assistant gap scope](adr/0018-explicit-assistant-gap-scope.md) | Why explicit keyword bounds and task-side linkage preserve exact approval and answer history |
| [Pinned support and current policy](adr/0002-pinned-support-current-policy.md) | Why reproducible decisions pin support while permissions remain current |
| [Exact supplementary profile authority](adr/0016-explicit-bounded-profile-supplementation.md) | Why one approved nickname fill shares parent limits while retaining separate source identity |
| [Recorded live schedule authority](adr/0015-recorded-live-schedule-authority.md) | Why explicit operator activation pins a route independently of process switches and preserves bounded snapshot recovery |
| [Live discovery uncertainty](adr/0014-live-discovery-response-and-billing-identity.md) | Why source response recovery and final billing retain separate stable identities |
| [Capture-based discovery avoidance](adr/0013-capture-based-discovery-avoidance.md) | Why original captures, complete support and current permissions govern reuse without transferring task receipts |
| [Atomic scheduled post admission](adr/0012-atomic-scheduled-post-admission.md) | Why daily new-post consumption commits with canonical effects while refreshes remain separate |
| [Stable schedule accounting day](adr/0011-stable-schedule-accounting-day.md) | Why daily keyword history and accounting boundaries survive configuration edits |
| [Save before discovery admission](adr/0010-save-before-coverage-discovery-admission.md) | Why immutable recommendations survive automatic discovery refusal and admission retries |
| [Automatic shortlist persistence](adr/0003-automatic-shortlist-persistence.md) | Why saving generated recommendations requires no human review or approval |
| [Lightweight monitoring evidence](adr/0004-lightweight-monitoring-evidence.md) | Why X detection owns bounded recent evidence separately from full KB publication |
| [Source-free quantitative alert history](adr/0019-source-free-quantitative-alert-history.md) | Why configured sample-volume assessments and notifications retain exact window lineage without copied source claims |
| [Bounded semantic positions](adr/0020-bounded-semantic-positions-full-input-policy.md) | Why provisional fixed positions and every actual model input govern semantic alert history |
| [Pinned local alert context](adr/0021-pinned-local-alert-context.md) | Why one existing-KB query and original recent dependencies govern a deterministic explanation without acquisition authority |
| [Task session effect ownership](adr/0005-task-session-effect-ownership.md) | Why each task's execution lock and effect transactions share one PostgreSQL session |
| [Bounded synthetic admission](adr/0006-bounded-synthetic-admission.md) | Why scope decisions and ledger writes share a lock while uncertain dispatches keep their commitments |
| [Generated criteria preserve human constraints](adr/0008-generated-criteria-preserve-human-constraints.md) | Why generated additions stay separate from human briefs and require exact visible selection |
| [Final cost evidence and meter recovery](adr/0007-final-cost-evidence-and-meter-recovery.md) | Why named liabilities require final evidence and meter health has separate operator recovery |
| [Exact supported answers](adr/0017-exact-supported-answers.md) | Why bounded extractive answers retain every model input and render only governed source values |
| [Constrained supported ranking](adr/0009-constrained-supported-ranking.md) | Why one bounded model order uses constrained candidate-scoped judgments and durable no-reissue claims |

The root [glossary](../GLOSSARY.md) defines domain language; the [README](../README.md) explains local commands.

## Maintenance

- Update the architecture when responsibilities, dependencies or deployment boundaries change.
- Update the physical ERD with schema changes. Keep accepted future objects in the separately marked conceptual model until they are implemented.
- Update interface documentation when inputs, outputs, invariants or failure behavior change.
- Add ADRs for durable decisions with meaningful alternatives and consequences. Describe the product trade-off; preserve superseded ADR links when a decision changes.
- Prefer Markdown and Mermaid as reviewable source. Keep one authoritative description of each contract and link to it from other documents.

Implementation tickets, experiment results and session chronology live in `.scratch/`.
