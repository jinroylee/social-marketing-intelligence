# S03. Give the operator recorded commands for cost controls and bounded X polling

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: S (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Thin CLI adapters over installed UsageAccounting and RecentPolling operations.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_costs and smi_monitoring.polling keep validation and SQL; the pilot composition module owns argument parsing and the trusted operator identity
Direct spec blockers: [Compose the local pilot from one validated configuration](02-pilot-configuration.md) (Commands act on the owners, routes and trusted operator identity composed from the validated configuration.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

An operator can configure spending controls and run bounded live X polling from the shipped tools, so live probes and recurring work have a recorded, attributable path.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_costs/store.py](../../src/smi_costs/store.py)
- [src/smi_monitoring/polling/store.py](../../src/smi_monitoring/polling/store.py)
- [src/smi_ingestion/cli.py](../../src/smi_ingestion/cli.py)
- [src/smi_campaigns/responses/__init__.py](../../src/smi_campaigns/responses/__init__.py)

## Scope and non-goals

Subcommands on the composed operator CLI from S02: configure-cost-scope (a CostScope from an explicitly named file section), bind-cost-route (adapter, scope and the owner's required max_units), set-cost-ceiling (amount, currency, period, pause), read-allowance, activate-x-topic (topic key, expected topic version, first window end, request ID), deactivate-x-topic and run-x-due --once (one bounded RecentPolling.run_due pass). Non-goals: browser forms (S20, S26); reconciliation and meter recovery (S26); any daemon or loop (S09); new receipt tables; applying cost settings implicitly at start-up.

## Owners, interfaces and data shapes

Thin adapters over UsageAccounting.configure_scope/configure_route/configure_ceiling/allowance and RecentPolling.activate/deactivate/run_due with source-free JSON output. Errors are owner reason codes such as cost_scope_conflict, unsupported_cost_route_contract, monitoring_poll_already_active and monitoring_topic_version_conflict. A changed immutable scope requires a new scope ID. Actor and workspace are never taken from arguments.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No schema change and no new receipt model; owners keep their existing request claims. Document the operator sequence in docs/user-guide.md, docs/costs.md and docs/monitoring.md.

## UI reads, commands and agent integration

S05 and recurring work use these commands; S26 later calls the same command layer from its forms; S09 owns continuous polling.

## Invariants and authorization

Each command is an explicit, attributable operator action. Configuration never applies cost settings or activation implicitly, and activation remains one recorded command per topic revision under ADR 0023.

## Failure and recovery

Re-running an identical command reopens the original result. A conflicting change writes nothing and returns the owner's conflict reason. An unknown X response keeps its liability and is never re-dispatched by a retry.

## Acceptance

### S03-A01

On a fresh database, the documented sequence (scope, route binding, ceiling) through the shipped commands makes the simulated model route admissible from the shipped server and the S02 model journeys run; before the sequence, readiness() names the missing cost scope.

### S03-A02

Re-running the same scope or route command changes nothing. A changed rate under the same scope ID fails with the owner's conflict reason and writes nothing.

### S03-A03

With fake HTTP, activate, run-x-due --once N times and deactivate produce N windows and a recorded deactivation; a further run dispatches no request.

### S03-A04

Output and logs never contain secrets or provider handles, and a forged actor or workspace argument is rejected.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-C01, FR-S01, OFR-S03, OFR-E03, UD-02. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
