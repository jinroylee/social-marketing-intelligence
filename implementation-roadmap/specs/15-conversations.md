# S15. Save conventional chat threads with question-scoped extractive turns

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. New owner with four tables and retention rules; L-sized. Decisions to chart before implementation: context selection and omission rules; retention, deletion and expiry policy; thread-head concurrency and exact retry; composer/draft reducer design.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Proposed smi_assistant.conversations owns threads/turns/drafts; KnowledgeAssistant owns answers; tasks own research
Direct spec blockers: [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (Per-turn sources open in the shared inspector.), [Select question-, brief- and graph-scoped governed support at pilot scale](07-pilot-scale-retrieval.md) (Each turn's pinned retrieval scope is derived from the question.), [Compose the local pilot from one validated configuration](02-pilot-configuration.md) (The shipped server needs the configured model route.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Require finite user-turn/draft retention, bounded context bytes/turns and explicit persistence enablement. The recommended server-side configuration is reversible and does not invent a retention duration.

## User outcome

A marketer returns to saved conversations, sends follow-ups and preserves each thread's draft and exact evidence.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_assistant/store.py](../../src/smi_assistant/store.py)
- [src/smi_assistant/answers.py](../../src/smi_assistant/answers.py)
- [tests/test_assistant.py](../../tests/test_assistant.py)
- [docs/adr/0017-exact-supported-answers.md](../../docs/adr/0017-exact-supported-answers.md)

## Scope and non-goals

Implement R2-CHAT rail, log, composer, per-thread draft and bounded history. Pilot answers remain labelled extractive selections under ADR 0017. Each turn pins the S07 scope derived from its question, and carries bounded prior human questions and answer IDs as context references with explicit context selection/omission. Fluent synthesis and inferred executable scope await later specs.

## Owners, interfaces and data shapes

Proposed Conversations.create/read/send/save_draft/delete(actor, request_id, expected_head). Turn has id, conversation_id, ordinal, human input, parent/context turn IDs, context manifest digest, answer_id, state and timestamps. send commits accepted user turn before answer preparation and returns its receipt. KnowledgeAssistant accepts an optional explicit bounded question-context port; full actual evidence inputs remain pinned. Prior human prose remains a human claim. Draft uses separate version, not thread-head mutation. This spec owns the composer/draft/IME reducer with Node tests.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add assistant_conversations, conversation_turns, turn_context_members and conversation_drafts with workspace/actor ownership, request uniqueness and retention/deletion metadata. No copied source text in turns. Legacy answers remain standalone or explicitly linked without fabricated conversation history. Define finite configured retention for user prose and drafts, explicit Delete conversation and expiry behavior before enabling persistence. Update knowledge, evaluation, ERD, local-review and new submodule instructions/symlink.

## UI reads, commands and agent integration

Enter sends, Shift+Enter inserts newline, IME composition never sends. Keep scroll/draft/thread/selection across language/navigation. Per-turn sources include original input, exact context, query/full-input IDs, method/model and dates. Research status reads A1/T1, not generated prose. Show accepted/preparing/partial/complete/invalid/interrupted/unavailable states. The research-status disclosure is a conditional check, verified once S14 exists. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Expected thread head rejects concurrent sends while preserving draft. Retried exact send reopens the same turn/answer and possible charge. Context cannot silently broaden retrieval scope or convert prior statements into source evidence. Any lost full input withholds its dependent answer. No factual streaming before validation.

## Failure and recovery

An interrupted preparation retains an explicit unknown state without model reissue. Cancel stops local answer preparation where safe, never cancels or reissues an acquisition task. Expired drafts disappear with clear UI feedback; source policy loss clears dependent display even in an open log.

## Acceptance

### S15-A01

Create two threads, type distinct drafts, switch EN/KO/routes/restart and observe correct persisted drafts and ordered turns.

### S15-A02

Race two sends at one head; one is accepted and the other preserves its draft with a conflict. Retry the winner without a second model call.

### S15-A03

Ask a follow-up and inspect exact included/omitted prior context and query evidence; unsupported human assertions remain unverified.

### S15-A04

Withdraw one actual input, including unselected input, and observe dependent turn unavailable with no cached excerpt. Test IME, empty input, multiline send, delete/expiry and interrupted preparation.

### S15-A05

Two different questions over the same KB of more than 100 publications select different, relevant support, and the pinned scope reopens exactly.

### S15-A06

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-B01, FR-B02, FR-B09, OFR-B02, PROP-27, UD-03, UD-08, R2-CHAT. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
