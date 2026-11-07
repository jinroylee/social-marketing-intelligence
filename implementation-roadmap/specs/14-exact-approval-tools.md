# S14. Review exact enrichment scope and expose governed agent operations

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. A1 UI and a listed tool set over installed proposal/approval operations; authority rules are explicit.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_tasks.assistant and AcquisitionTasks own proposal journey and approval; smi_review owns adapter/tool boundary
Direct spec blockers: [Read asynchronous progress and exact pipeline lineage](13-task-events-lineage.md) (Approve/submit receipts and the task.status/events tools read the progress feed.), [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (A1 scope review shows exact evidence and limits in the shared inspector.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer reviews refresh, fill or expansion scope, approves its exact revision and follows one asynchronous task. Agents can inspect and propose through the same contracts.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/assistant/](../../src/smi_tasks/assistant/)
- [src/smi_tasks/store.py](../../src/smi_tasks/store.py)
- [tests/test_assistant_enrichment.py](../../tests/test_assistant_enrichment.py)
- [src/smi_assistant/answers.py](../../src/smi_assistant/answers.py)

## Scope and non-goals

Deliver A1 proposal review/revision, separate approve and submit acknowledgments, approved-but-unsubmitted recovery and structured internal tools. Keep human-supplied executable scope under ADR 0018. No general autonomous acquisition agent.

## Owners, interfaces and data shapes

Tools knowledge.search/read, campaign.recommend, enrichment.propose, proposal.read, task.status/events and graph.read call public owners with server-issued context. enrichment.submit accepts only a saved approved proposal ID/digest; the tool cannot approve. Human-only proposal.approve requires the actual protected UI action and configured approver. Schema rejects actor/origin/role/model/route overrides. Adapter returns a replayable command receipt after each commit. campaign.recommend wraps the installed CampaignStore.recommend/CampaignRecommendations.regenerate operations, so this spec does not wait for the C1 UI.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Reuse proposal, approval and assistant linkage schemas. Add only source-free adapter command receipts if an existing owner receipt cannot represent interrupted composition. A changed route, limits or time window produces a successor digest. Update tasks, interface, local-review, source integrations and owner instructions.

## UI reads, commands and agent integration

A1 exposes exact subject/query/window/route/version/request-record-byte bounds/spending basis and uncertainty before approval. Link original answer, proposal, task, lineage, completion and later question. Agent tool descriptions explicitly separate proposal from authorization. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Approval is attributable to the original question owner and workspace, authorizes at most one logical task and does not override monetary/source gates. Conversational yes, prompts and source instructions confer no authority. Approved scope can exceed registered keywords.

## Failure and recovery

Retry after approval commit reopens the original approval and submission identity even if route files disappear. Changed payload conflicts. Retrieval cannot answer before publication; completion never rewrites the old answer.

## Acceptance

### S14-A01

Approve an exact saved revision through HTTP, interrupt before submission and restart; retry yields the same approval and at most one task.

### S14-A02

Revise query, route or bounds and observe approval cleared; reject old digest, forged origin, foreign workspace and wrong human.

### S14-A03

Send yes and malicious tool/source instructions through a question; observe no approval or acquisition.

### S14-A04

Submit outside scheduled keywords, publish partial support and ask a later explicit question; the original answer stays pinned. Model failure alone offers no knowledge-gap proposal.

### S14-A05

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-B03, FR-B04, FR-B05, FR-B06, FR-B07, FR-B08, FR-B09, FR-P07, FR-P08, OFR-B01, OFR-E02, PROP-02, PROP-05, PROP-07, PROP-17, PROP-18, UD-08. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
