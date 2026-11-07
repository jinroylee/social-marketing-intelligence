# S26. Inspect and operate independent spending controls

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Operator forms over installed UsageAccounting operations and the operator command layer.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_costs owns accounting/admission/reconciliation/recovery; smi_review owns operator-only S1 forms
Direct spec blockers: [Establish the bilingual client foundation, shell and client verification](04-client-foundation.md) (S1 forms render in the shell with governed reads.), [Give the operator recorded commands for cost controls and bounded X polling](03-operator-commands.md) (Forms reuse the operator command layer for scope, route and ceiling instead of a second path.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

An authorized operator sees actuals, commitments, forecasts and meter health and can reconcile or recover an exact operation without reissuing acquisition.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_costs/store.py](../../src/smi_costs/store.py)
- [src/smi_costs/admission.py](../../src/smi_costs/admission.py)
- [tests/test_cost_admission.py](../../tests/test_cost_admission.py)
- [tests/test_cost_reconciliation.py](../../tests/test_cost_reconciliation.py)

## Scope and non-goals

Add protected operator forms for scope/route/ceiling configuration, pause, final reconciliation and meter health recovery. Preserve separately classified measured/synthetic/provider/forecast-only views. No invented provider prices or cross-currency totals.

## Owners, interfaces and data shapes

Use UsageAccounting.configure_scope/configure_route/configure_ceiling/allowance/list/read/reconcile_usage/recover_meter through an explicit configured human operator context. Commands require immutable scope identity, exact currency/period, expected configuration version where mutable, request ID, targeted portions and attributable evidence. Add public revision guards/receipts where current trusted Python operations lack adapter-safe retry semantics. Render amounts as decimal strings with accounting basis and measured_at. The configure forms call the S03 command layer; reconciliation and meter recovery stay here, with the receipts this spec already owns.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Prefer existing ledger; add operator command claims/config revision metadata if required. Never rewrite historical rates or measurements. Update costs, interface, architecture, ERD, evaluation and local-review operator contract.

## UI reads, commands and agent integration

S1 exposes allowance based on measured actual plus all outstanding commitments, exact operation task/attempt attribution, rate/unit version, unknown portions and health. Budget/meter refusals link back to safe task waits. Agent tools can read allowance but cannot reconcile or attest meter health. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Human acquisition approval does not override control. Forecast-only is visibly unenforced. Failed expected meter blocks future scope calls until separate recovery; final reconciliation settles named liability once but cannot restore a lost response. Bound violations are recorded truthfully even over ceiling.

## Failure and recovery

Stale operator edits preserve input and conflict. Duplicate equal final evidence reopens, conflicting/overlapping settlement is rejected. Unknown liability remains outstanding; no timeout write-off or silent forecast downgrade.

## Acceptance

### S26-A01

Race two public workers under one scope and observe admitted commitments prevent an extra dispatch.

### S26-A02

Fail the expected meter, reconcile exact final portions and observe health still blocked until separate attributable recovery.

### S26-A03

Repeat/conflict final evidence through HTTP; observe once-only settlement and no task/source reissue.

### S26-A04

Show synthetic actual, provider-reported usage, forecast and unknown side by side with exact currency/period and no pooled total. Reject wrong operator, foreign scope and forged measurement provenance.

### S26-A05

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-P05, FR-S01, FR-S02, FR-S03, OFR-S01, OFR-S02, OFR-S03, OFR-S04, OFR-E02, OFR-E03, PROP-15, PROP-28, PROP-34, UD-08. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
