# S04. Establish the bilingual client foundation, shell and client verification

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Every UI spec inherits its conventions; the choices are hard to change later. Decisions to chart before implementation: client module, routing and state conventions; /api/v1 adapter framework and envelope shape; i18n catalog format and completeness check; freshness utility bounds and fail-closed UX.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_review owns the client foundation, shell and versioned adapter framework; domain owners retain decisions
Direct spec blockers: [Restore a complete, time-stable verification baseline](01-stable-verification-clock.md) (Adds Node checks to the shared check, which must be green first.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Node available for the shared check. No CDN or network fetch at runtime.

## User outcome

Every later UI spec builds on one tested client structure: shell, navigation, theme, EN/KO switch, API client and shared freshness behavior.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_review/static/review.js](../../src/smi_review/static/review.js)
- [src/smi_review/static/review.css](../../src/smi_review/static/review.css)
- [src/smi_review/server.py](../../src/smi_review/server.py)
- [tools/check.py](../../tools/check.py)
- [.scratch/product-design-2026-11/task3/r2/verify-prototype.cjs](../../.scratch/product-design-2026-11/task3/r2/verify-prototype.cjs)

## Scope and non-goals

Plain ES modules served from smi_review/static with no build step. Deliver the API client (envelope parsing, CSRF, request-ID generation, retry kinds), the versioned same-origin /api/v1 adapter framework, the i18n catalog mechanism and completeness check (catalogs grow per spec), the shell, navigation, four-colour theme and EN/KO switch, the shared display_valid_until freshness utility and the node --test harness. Consumer logic belongs to its consumers: the graph library decision and branch reducer to S18, the chart-series reducer to S21 and the composer reducer to S15. Non-goals: framework rewrite, CDN dependencies, browser automation.

## Owners, interfaces and data shapes

Client modules: api (request(command|read) -> envelope with allowed_actions, display_valid_until and sanitized error), i18n (t(key, params), locale switch preserving inputs and IDs) and freshness (revalidate on focus, navigation, explicit read and a configured bounded timer; fail closed at the deadline; an older response never restores a newer tombstone). Server side: versioned /api/v1 routing that parses each command explicitly and derives RequestContext on the server, beside the existing forms.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No business tables. Add node --test execution to tools/check.py and list Node in docs/development.md and CI. Update docs/local-review.md, docs/architecture.md and smi_review/AGENTS.md with the client structure rules.

## UI reads, commands and agent integration

Every UI-bearing spec reuses these modules and adds its catalog keys; none re-implements freshness, envelopes or locale handling. Agent tools later read the same envelopes.

## Invariants and authorization

Preserve loopback Host, same-origin writes, CSRF, HTML escaping, no-store responses and source URL validation. Locale and client state are presentation only, never evidence or authority. Client-held positions or drafts never contain source values.

## Failure and recovery

A failed read keeps selected record IDs and drafts. Missing translations fail the completeness check rather than rendering raw keys. Expired freshness withholds content until a successful governed read.

## Acceptance

### S04-A01

tools/check.py runs the Node tests and fails on a broken client-module test.

### S04-A02

The freshness utility withholds content at display_valid_until without a successful revalidation and ignores an older response.

### S04-A03

The catalog completeness check fails on a missing KO key, and the EN/KO switch preserves inputs and IDs over loopback HTTP; foreign Host, missing CSRF and forged actor/workspace fields are rejected.

### S04-A04

The API client parses envelopes, generates request IDs and classifies retry kinds; a sanitized error never renders raw server text.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-E02, PROP-03, PROP-15, UD-03, UD-07. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
