# Validate the integrated decision brief with the brand marketer

Label: wayfinder:prototype
Type: prototype
Mode: HITL
Status: resolved
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 04

## Question

What concrete pilot output lets the marketer independently inspect market insights and initiate campaign planning, compare and save a justified creator shortlist, record a measurement plan, and retain the decision's assumptions and evidence?

Use a cheap outline or mock decision brief based on the chosen workflow and obtainable fields. Mark any invented sample data explicitly. Test whether the marketer can distinguish observed facts, derived judgments, unknowns, and review requests. Resolve this ticket through the human's reaction to the artifact; creating an attractive mockup alone is not resolution.

Following the modular-pipeline scope change, this prototype may use proposed fields and explicitly synthetic examples before live-source selection. That can validate the shape of the workflow, not actual evidence availability or usefulness. Live evidence readiness is handled separately in [Select the first live source and evidence scope](11-select-live-source-and-evidence-scope.md).

## Progress — 2026-09-30

Prepared a self-contained, throwaway [interactive decision-brief prototype](../prototypes/decision-brief-prototype.html). It lets the marketer inspect a mock signal, open evidence for discovered and known creator candidates, record a reason, save a shortlist, add a descriptive sales measurement plan, state an audience assumption, and request Japanese-language review. A guided incomplete-evidence case and an out-of-order case show what the brief blocks or leaves unknown. Every example is explicitly synthetic; no live database data is presented as a campaign finding. The HTML opens locally and its script passed a syntax check and visual inspection. Awaiting the brand marketer's reaction before resolving this HITL ticket.

## Comments

### Marketer review and clarification — 2026-10-12

The builder reviewed the prototype with the marketer and returned three questions: how an aggregate cushion-mention signal connects to the listed creators; whether comparison requires human actions or is performed by an LLM/agent; and what saving a shortlist means, including whether it writes to the local database. This feedback exposes missing workflow semantics rather than confirming the original flow.

The revised prototype makes the proposed bridge explicit: a campaign brief and optional signal suggest a content angle; relevant posts provide candidate accounts; each candidate needs its own evidence against the brief. An aggregate mention increase alone establishes neither creator fit nor sales potential. The signal is now optional, with a walkthrough that starts directly from the campaign brief.

The proposed division of work is automated candidate retrieval, evidence assembly, and draft comparison, followed by marketer review and confirmation of the selected set. The prototype remains a manual simulation with fixed synthetic candidates, without an LLM or agent. Its save action changes in-memory state only. The intended persisted shortlist would be a campaign-linked, versioned decision record carrying stable subject references, reasons, evidence references, unknowns, and reviewer context; application storage is not implemented in the current ingestion schema.

These are clarifications and proposed revisions for the ongoing human discussion, not an accepted domain contract or a resolved ticket. No database schema or production behavior changed.

### Accepted workflow correction — 2026-10-12

The builder agreed to the clarified automation and shortlist-save semantics, with one explicit correction: signal detection and monitoring must be an independent feature that informs the marketer and may enrich shared knowledge. A human initiates a new campaign and creator selection. Monitoring and shortlisting share evidence, but they are not an automatically connected procedure, and a signal must not trigger campaign creation or shortlist generation.

## Answer

Resolved through the builder's live follow-up after reviewing the prototype with the marketer and explicitly accepting the clarified workflow with the correction above.

- **Independent monitoring:** market insights and signal investigation remain usable without a campaign or shortlist. They can inform a later human decision and contribute evidence to the shared knowledge. Signal methodology and ongoing-monitoring scope remain for the domain and acceptance decisions.
- **Human campaign initiation:** the marketer starts campaign planning from a campaign brief. The brief determines creator-selection criteria. Monitoring insights are optional context, not a required predecessor or an automatic trigger.
- **Automated preparation, human selection:** after campaign initiation, the system prepares candidate discovery, evidence assembly, and draft comparisons and reasons. The marketer reviews or changes the selection and confirms the candidate set. The prototype manually simulates these operations and contains no running agent.
- **Saved decision:** a shortlist is a campaign-linked, versioned record containing selected subject references, reasons, evidence references and relevant times, unknowns, and reviewer context. The accepted local implementation direction is separate decision-owned tables in the existing PostgreSQL database; the precise domain contract and schema are still to be defined. The HTML persists nothing, and the current ingestion schema has no shortlist storage.
- **Measurement and limitations:** the brief includes a descriptive sales measurement plan and explicit missing audience, fee, sales, and source-coverage information. Neither synthetic examples nor the curated post sample establish creator sales performance, a representative market trend, or comparison-grade creator coverage.

The [revised prototype](../prototypes/decision-brief-prototype.html) demonstrates monitoring without campaign creation and campaign review without signal investigation. [Shared domain language](../../../GLOSSARY.md) records monitoring, market signals, and campaign briefs. Workflow semantics are accepted; measurable usefulness, Japanese-language review responsibilities, extraction quality, and live evidence readiness have not been validated by this prototype review.

Verification: the revised JavaScript passed its syntax check; all five walkthroughs reached their intended states. Monitoring alone leaves the campaign unstarted and the shortlist empty; a campaign can reach a review package without signal investigation; inspecting a signal leaves existing campaign decisions unchanged. The map and ticket's relative artifact links resolve. No production schema or ingestion behavior changed.
