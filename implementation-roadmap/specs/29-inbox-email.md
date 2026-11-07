# S29. Deliver durable task and alert notifications through inbox and email

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. New smi_notifications module with four or more tables and transport semantics. Decisions to chart before implementation: event sync and reconcile ports per owner; retry, backoff and uncertain-state policy; template and governed-link design; activation frontier and historical backfill.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Proposed smi_notifications owns recipient preferences, attention and channel delivery; task/alert owners retain outcome events
Direct spec blockers: [Run bounded local work continuously with restart, health and lifecycle maintenance](09-local-runtime.md) (Delivery.run_due is registered as a runtime component.), [Compose the local pilot from one validated configuration](02-pilot-configuration.md) (Recipient, sender, link and transport configuration come from the validated configuration.), [Open saved campaigns and inspect governed evidence in the shared inspector](10-workspace-and-evidence.md) (Inbox items open governed task, alert and evidence links in the shared inspector.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer receives a source-free completion or alert notification, opens governed evidence and distinguishes read attention from email transport state.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_tasks/notifications/store.py](../../src/smi_tasks/notifications/store.py)
- [src/smi_tasks/notifications/AGENTS.md](../../src/smi_tasks/notifications/AGENTS.md)
- [src/smi_monitoring/alerts/store.py](../../src/smi_monitoring/alerts/store.py)
- [src/smi_monitoring/semantic/store.py](../../src/smi_monitoring/semantic/store.py)

## Scope and non-goals

Implement inbox composition/read-unread, the single configured recipient and sender, durable email attempts, bounded retries and visible final/uncertain failure. Email is required for the first pilot. Multi-recipient preferences are later (S40). Provider credentials and actual sending are authorized readiness work. The transport is SMTP submission through the configured operator mailbox by default (U7); an HTTP email API is used behind the same delivery-identity model only if that is what the operator has. Every email carries a Message-ID derived from the logical delivery key. An ambiguous accepted response stays uncertain and appears prominently in the channel status with a one-action attributable reissue that uses a new Message-ID linked to the original.

## Owners, interfaces and data shapes

Proposed Notifications.sync/read/mark_read/configure_channel and Delivery.run_due. External event key is workspace + owner kind + stable completion/alert ID. Logical delivery key adds recipient + channel and is unique across retries. Pin original template/config/preference versions on that delivery; later edits never generate another email for the same logical key. Any deliberate reissue requires a separate attributable human action/reissue identity with its own bounds. Owners expose bounded event cursors or reconcile-by-ID ports; notification owner reads no foreign SQL. Email contains fixed source-free outcome/status and a validated configured application link, with no source excerpt, query text or generated factual claim. Persist exact template/config identity and sanitized transport receipt.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add notification_preferences, notification_attention, notification_events and notification_deliveries/attempts with unique identities and finite retention. Backfill missing historical references without auto-sending old events; activation records a delivery start frontier. Add module AGENTS.md and sibling symlink. Propose source-free external notification ADR for review with implementation; update tasks, monitoring, costs, ERD, architecture and operator guide.

## UI reads, commands and agent integration

Inbox shows historical outcome, current publication availability, attention and channel status separately. Delivery failure never marks task failed or regenerates work. Email link may require access to the local review machine; no implicit public hosting. Runtime registers finite delivery processing. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Only configured human operator can authorize recipients and activate transport. Recheck current policy when opening application evidence, and do not export source values. Provider-side exactly-once is not assumed. Sending/retry cost belongs to configured accounting if chargeable.

## Failure and recovery

Crash before dispatch safely retries original local delivery; crash after ambiguous provider acceptance becomes uncertain and cannot blindly resend. Use provider idempotency only after verified support, otherwise an attributable operator decision governs a new delivery. Backoff and terminal failure stay distinct from underlying event/read state.

## Acceptance

### S29-A01

Complete a task and create each alert method, reconcile repeatedly and observe one inbox/event/delivery identity for the configured recipient and each channel.

### S29-A02

Use a simulated transport to fail, restart and retry safe attempts; an ambiguous accepted response stays uncertain without duplicate send.

### S29-A03

Withdraw all source support and observe source-free historical email status with governed links withholding content, while task outcome remains unchanged.

### S29-A04

Revise template/config/preferences during a retry or event reconciliation and observe the same logical delivery and original pinned versions, never a second email. Test separate attributable reissue and recipient disablement.

### S29-A05

Configure read/unread, invalid link/sender and channel activation frontier through public operations. Actual email receipt/delivery validation remains S31.

### S29-A06

Each email's Message-ID derives from its logical delivery key; a reissue carries a new linked ID.

### S29-A07

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A07, FR-B09, FR-C05, PROP-27, UD-05. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
