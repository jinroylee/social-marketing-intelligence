# S01. Restore a complete, time-stable verification baseline

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Mechanical, pinned scope: inventory the suite, add one clock helper and convert fixtures; no product decisions.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Test infrastructure maintainers; owning-module maintainers review fixture conversions in their suites
Direct spec blockers: None. This is the first executable spec.
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

Every implementation worker starts from a complete, attributable test baseline in which no test depends on the real calendar date.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [tests/test_assistant_enrichment.py](../../tests/test_assistant_enrichment.py)
- [docs/development.md](../../docs/development.md)
- [tools/check.py](../../tools/check.py)

## Scope and non-goals

Run the whole suite once without --maxfail against real PostgreSQL and classify every failure as clock-aging or other. Add one shared relative-date/controlled-clock test helper and convert freshness-, retention-, seven-day-window- and accounting-period-sensitive fixtures to it; use relative SQL intervals where the database clock decides. Non-goals: no product freshness, retention or window policy change; no time-travel tooling for the PostgreSQL server.

## Owners, interfaces and data shapes

Proposed tests/support clock helper exposing a fixture base instant and relative constructors (days_ago, within_retention) used by test fixtures only. Keep public KnowledgeAssistant/AssistantEnrichment, cost, polling and schedule test journeys; never patch private business outcomes.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No schema migration. Record the full-suite inventory with exact failures. Update docs/development.md: remove the current fixture limitation only after a real passing run, and document the helper and the --maxfail inventory command.

## UI reads, commands and agent integration

No UI or agent behavior changes. Every later spec's completion evidence relies on this baseline.

## Invariants and authorization

Tests must not grant freshness, retention or window eligibility to old or unknown captures. The src/ diff for this spec contains no freshness, retention or window constant change.

## Failure and recovery

A database preflight failure is a failed prerequisite with its exact cause. A non-clock failure found by the inventory is filed against its owning module instead of being masked here.

## Acceptance

### S01-A01

Record the full-suite inventory (no --maxfail) with every failing test and its classification.

### S01-A02

All clock-aging failures pass, and the src/ diff contains no freshness, retention or window constant change.

### S01-A03

The clock-sensitive subset passes with the helper base shifted +90 days.

### S01-A04

Stale-capture and unknown-capture cases still report explicit limitations.

### S01-A05

uv run --locked python tools/check.py passes against real PostgreSQL and docs/development.md reflects the actual result.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-E02. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
