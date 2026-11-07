# S44. Measure actual outcomes and rule-based attribution

Status: planned, no implementation or validation claimed.
Lane: later-proposal
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Outcome ingestion and attribution design. Decisions to chart before implementation: outcome source and permission model; matching and deduplication; attribution rules and windows.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Proposed measurement owner consumes authorized outcome/campaign matching evidence; planning remains separate
Direct spec blockers: [Preserve measurement planning and prepare attributable KR/JP quality packets](30-plans-and-quality.md) (Proposed measurement plans to observe against.), [Move the proven pilot to authenticated workspace tenancy](40-hosted-actors-tenancy.md) (Outcome data needs tenant access.), [Reconcile retained copies and rebuildable projections with operational recovery](41-projection-governance.md) (Governed retention of outcome copies.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Actual authorized outcome access, metric/matching definitions and source/privacy terms are required. Build fixtures cannot establish outcome readiness.

## User outcome

A marketer can inspect observed campaign performance and attribution under an explicit rule with quality and access gaps.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_campaigns/planning/](../../src/smi_campaigns/planning/)
- [docs/planning.md](../../docs/planning.md)
- [GLOSSARY.md](../../GLOSSARY.md)
- [POPOSAL.md](../../POPOSAL.md)

## Scope and non-goals

Add authorized outcome ingestion, metric definitions, campaign/content/outcome matching, deduplication and rule-based attribution windows. Keep planned targets and human notes distinct from observed outcomes. No causal lift claim.

## Owners, interfaces and data shapes

OutcomeObservation records native identity, metric/unit/value/currency, event and reporting windows, population, source permission and measurement revision. AttributionRun pins rule/matching/window/input versions, eligible/unmatched denominators and allocation. Deterministic joins/calculations are public reproducible operations with correction/retraction support.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Create measurement-owned observation/run/allocation/support tables and source ingestion contracts. Backfill only actual authorized data, never convert a note/plan to an observation. Update planning versus measurement docs, architecture/ERD, glossary and new module AGENTS.md with sibling symlink.

## UI reads, commands and agent integration

Measurement & learning shows proposed versus observed versus attributed in separate states, with reconciliation and unknown access. K1 can cite published accepted outcomes only through governed support. No tool modifies connected marketing systems.

## Invariants and authorization

Attribution allocates observed outcomes under a rule and does not establish incremental effect. Audience, engagement and traffic are not inferred sales. No pooled currencies or incomparable windows. Tenant and source rights follow every join/export.

## Failure and recovery

Late/corrected/duplicate outcomes reconcile idempotently and retain prior run identity. Unmatched records stay explicit. Source revocation withholds dependent results and future recomputation cannot restore forbidden data.

## Acceptance

### S44-A01

Ingest actual authorized sample outcomes separately from plans and reproduce exact dedup/match/attribution counts through public operations.

### S44-A02

Exercise late corrections, duplicate events, refunds where applicable and unmatched identities without double counting.

### S44-A03

Show rule/window changes produce new runs and do not rewrite historical attributed results.

### S44-A04

Obtain real data access, measurement quality and human acceptance before displaying observed revenue/conversion claims.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-X01, PROP-01, PROP-02, PROP-04, PROP-12, PROP-15, PROP-33. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
