# S10. Open saved campaigns and inspect governed evidence in the shared inspector

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Two reads and the shared inspector on top of the client foundation; states are fixed by r2.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_review owns the campaign index, detail reads and shared governed inspector; domain owners retain decisions
Direct spec blockers: [Establish the bilingual client foundation, shell and client verification](04-client-foundation.md) (Needs the shell, API client and envelope, i18n mechanism and freshness utility.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer opens all saved campaigns and inspects exact permitted evidence through one shared inspector, in EN or KO.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_review/app.py](../../src/smi_review/app.py)
- [src/smi_review/server.py](../../src/smi_review/server.py)
- [src/smi_review/AGENTS.md](../../src/smi_review/AGENTS.md)
- [tests/test_review.py](../../tests/test_review.py)

## Scope and non-goals

Deliver the campaign index and detail reads and the shared governed inspector (observed/derived/human bases, independent dates, conflicts, full-input membership, truncation and current availability), with the EN/KO keys for these screens. Shell, navigation, theme, i18n mechanism and adapter framework come from S04. No hosted authentication or arbitrary source embedding.

## Owners, interfaces and data shapes

Proposed ReviewWorkspace.campaigns(context, cursor, limit) and evidence(selection_id, purpose='display') return the common response envelope in architecture-target.md through the S04 adapter framework.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Presentation needs no new business tables. Persist only a locale preference if needed, scoped to the local actor. Update docs/local-review.md and the review owner instructions. Retain no source values in browser storage.

## UI reads, commands and agent integration

Campaign index opens real CampaignStore.list_campaigns/read_campaign results. Inspector renders observed, derived and human bases, independent dates, conflicts, full-input membership, truncation and current availability. Agent read tools later use the same envelopes. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Preserve loopback Host, same-origin writes, CSRF, HTML escaping, no-store responses and source URL validation. Locale is presentation state, never evidence or authority. Return server-calculated allowed_actions.

## Failure and recovery

Read failures retain selected record IDs and drafts. Empty, partial, stale, restricted and unavailable views have distinct translated recovery text. A withdrawn inspector clears source text and dependent values.

## Acceptance

### S10-A01

Start the actual loopback app with two saved campaigns and reopen each after process restart.

### S10-A02

The EN/KO switch preserves brief input and semantic IDs on the campaign and inspector screens.

### S10-A03

Withdraw selected support and observe no label, excerpt or aggregate leakage in the response or DOM.

### S10-A04

Reject foreign Host, missing CSRF and forged actor/workspace fields through public HTTP on these reads and commands.

### S10-A05

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: PROP-01, PROP-15, UD-01, UD-03. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
