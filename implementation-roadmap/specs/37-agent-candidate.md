# S37. Prepare a bounded research and synthesis candidate for decision review

Status: planned, no implementation or validation claimed.
Lane: later-candidate
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Disabled research/synthesis candidate with open validator and planner design. Decisions to chart before implementation: research draft model; claim validator method; tool allowlist and prompt-attack handling.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_assistant candidate planner/validator owns read-only preparation; tasks retain acquisition authority; quality owns evaluation packets
Direct spec blockers: [Review exact enrichment scope and expose governed agent operations](14-exact-approval-tools.md) (Draft research compiles to exact proposal/approval operations and tools.), [Save conventional chat threads with question-scoped extractive turns](15-conversations.md) (Candidate turns live in conversation records.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Informing, non-blocking prerequisite: W01 initial direction (U6). Recommended 'yes' branches are non-binding working assumptions until answered.

## User outcome

A human can review a concrete richer-agent contract and its failures before deciding whether to enable it.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_assistant/answers.py](../../src/smi_assistant/answers.py)
- [src/smi_tasks/assistant/](../../src/smi_tasks/assistant/)
- [docs/adr/0017-exact-supported-answers.md](../../docs/adr/0017-exact-supported-answers.md)
- [docs/adr/0018-explicit-assistant-gap-scope.md](../../docs/adr/0018-explicit-assistant-gap-scope.md)

## Scope and non-goals

Build a disabled candidate using simulated or existing permitted KB input, typed read tools, finite plan drafts and claim-level evaluation outputs. No live external execution, no replacement of current ADRs and no production factual streaming.

## Owners, interfaces and data shapes

Proposed ResearchDraft has purpose, bounded subjects/query/time/routes, exact evidence needs and stop/budget estimates, with state draft_only. SynthesisCandidate has atomic claim text, support spans/IDs, full actual-input manifest, dates/method/model, uncertainty and independent validator verdict per claim. Validator checks semantic support, unsupported joins/causality, contradictions, numbers/time/attribution and whole-input policy. Exact implementation method is a candidate to evaluate, not an accepted guarantee. Planner tools are allowlisted KB reads and proposal-draft save only; executor is deterministic and uses task authority.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Candidate schema is separated from production answers and stores governed claim dependencies plus method/verdict versions. Draft candidate ADR text for 0017/0018 successor, glossary candidates and evaluation protocol with actual next available ADR number at implementation. Keep candidate artifacts outside accepted docs until reviewed. Add module instructions/symlink if substantial.

## UI reads, commands and agent integration

R2 target claim inspector can preview candidate results behind explicit experimental state. Plan/status is separate from chat prose. Use conventional conversation IDs, no multi-agent framework requirement. Candidate fallback is visibly an extractive answer, never a successful validated synthesis label.

## Invariants and authorization

Untrusted source/prompt instructions cannot choose tools, grant roles, approve scope or spend. Read-only monitoring investigation cannot call acquisition. Each paid operation, if later permitted, has independent scope/cost admission and durable retry identity.

## Failure and recovery

Invalid claims are withheld or produce labelled abstention. Partial evidence retains exact gaps. An interrupted/lost model response is uncertain with no blind retry. Source loss invalidates all influenced claims according to full-input policy; no cached validation can override it.

## Acceptance

### S37-A01

Use adversarial source instructions, invented fees/audience, unsupported causal joins, conflicting dates and numeric claims; retain exact independent validator results and false accepts/rejects.

### S37-A02

Propose a plan beyond current scope and observe draft_only with no task until the separate exact human approval path.

### S37-A03

Withdraw an unselected actual input and observe candidate withholding; interrupt model use without duplicate charge.

### S37-A04

Produce reviewable successor ADR candidates and exact KR/JP review packets with stated error criteria. This proves preparation, not accepted synthesis quality.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-B02, PROP-05, UD-04, R2-CHAT. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
