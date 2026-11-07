# S40. Move the proven pilot to authenticated workspace tenancy

Status: planned, no implementation or validation claimed.
Lane: later-proposal
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Hosted identity and tenancy design. Decisions to chart before implementation: identity provider and session model; membership and role model; query and file audit for tenant isolation; service identities and multi-recipient preferences.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Proposed application identity/access owner plus every workspace-scoped domain owner
Direct spec blockers: [Record pilot release acceptance on live data](35-human-pilot-acceptance.md) (Hosting follows an accepted local pilot.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Hosting/security/identity-provider choices, actual deployment and account setup remain explicit later operator prerequisites. No hosted operation is a first-pilot blocker.

## User outcome

A hosted user sees and changes only authorized workspace records, while machine workers retain separate service identities.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_review/app.py](../../src/smi_review/app.py)
- [src/smi_review/server.py](../../src/smi_review/server.py)
- [src/smi_ingestion/contracts.py](../../src/smi_ingestion/contracts.py)
- [docs/architecture.md](../../docs/architecture.md)

## Scope and non-goals

Design identity-provider integration, workspace membership/roles, sessions, operator/service identities and source-license grants. Audit all owner queries and file/object references before external exposure. Local actor labels and loopback checks are not hosted authentication. Add multi-recipient notification preferences here, beyond the pilot's single configured recipient.

## Owners, interfaces and data shapes

Trusted RequestContext contains verified subject, workspace membership, capabilities, auth/session identity and correlation ID. Bind public operations to server-resolved ActorContext; never accept workspace/roles as authority from payload. Membership revocation invalidates sessions/tools/jobs as specified. Worker identity is bound to one admitted workspace and exact task/poll scope; approval retains original actor and immutable proposal digest.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Add identity/membership/role/audit/session tables and explicit migration from local workspace with operator-reviewed ownership mapping. Audit all existing 85 physical tables plus later additions for workspace uniqueness, foreign references and reads. Consider PostgreSQL row security as defense only after ownership contracts are proven. Update architecture, data model, interface, tasks, source integrations and new owner instructions/symlink.

## UI reads, commands and agent integration

Add login/workspace selection and role-aware allowed actions without leaking foreign counts/titles. Tools derive tenant context from credentials. Email recipients and source permissions are tenant scoped. Shared provider credentials do not grant cross-tenant source access.

## Invariants and authorization

Separate application roles from source-use licenses and spending authority. A stolen record ID cannot cross tenant boundaries. Original human approval survives as historical attribution but cannot expand membership or bypass current dispatch permissions.

## Failure and recovery

Revocation during queued/running work blocks further protected effects without erasing committed history/liability. Expired session returns reauthentication with preserved safe draft metadata. Migration rollback never reopens public access to unowned records.

## Acceptance

### S40-A01

Run two real authenticated tenants through every owner read/command/tool/event/cursor path and reject foreign IDs, support links and counts.

### S40-A02

Revoke a human, service identity and source license during queued/model/source work; observe current denial and no late unauthorized publication.

### S40-A03

Migrate a pilot workspace and verify historical approvals, source dependencies and cost scopes retain identity without cross-tenant adoption.

### S40-A04

Test session/CSRF/origin protections and secret-free audit records under actual hosted access.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-B01, PROP-22, PROP-27, PROP-29, PROP-34, UD-02. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
