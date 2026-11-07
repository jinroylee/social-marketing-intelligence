# S09. Run bounded local work continuously with restart, health and lifecycle maintenance

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: L (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. New smi_runtime module; L-sized process and scheduling design. Decisions to chart before implementation: process, supervision and service packaging model; fairness and tick budgets across components; safe-retry classification; multi-runtime safety; maintenance cadence and bounds.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Proposed smi_runtime composes public task, schedule, monitoring and delivery ports; owners keep locks and SQL
Direct spec blockers: [Compose the local pilot from one validated configuration](02-pilot-configuration.md) (The runtime reads routes, gates, budgets and cadence from the validated configuration.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Require explicit enabled components, automation IDs, finite tick bounds, service restart policy, source/model gates and configured authority. Missing configuration reports blocked, never assumed live readiness.

## User outcome

The local pilot advances due discovery, executes admitted tasks and monitors topics without manual per-task commands.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [compose.yaml](../../compose.yaml)
- [pyproject.toml](../../pyproject.toml)
- [src/smi_tasks/worker.py](../../src/smi_tasks/worker.py)
- [src/smi_monitoring/polling/store.py](../../src/smi_monitoring/polling/store.py)
- [src/smi_tasks/schedules/](../../src/smi_tasks/schedules/)

## Scope and non-goals

Add a supervised local process and a finite tick CLI. Use PostgreSQL as the existing durable work source. Each tick has configured task/time/concurrency budgets, fair ordering and not-before handling. Register notification delivery when S29 exists. No broker, workflow-engine or microservice requirement. Add one bounded lifecycle-maintenance component that calls the existing expire, reconcile and reconcile-knowledge operations on a configured cadence with a per-tick bound and reports in health(); no new lifecycle logic. Inbox reconciliation is registered by S29.

## Owners, interfaces and data shapes

Proposed LocalRuntime.tick(actor, TickBounds) -> attempted/busy/waiting/failed/next_due and health(). Add public AcquisitionTasks.runnable(actor, cursor, limit) returning only eligible stable IDs and retry dispositions. Compose ScheduledDiscovery.tick and RecentPolling.run_due; call OfflineTaskWorker.run_one for admitted task IDs. Monitoring handlers register volume and later metric methods idempotently by exact windows/method versions.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

New runtime schema stores source-free process heartbeat, configured component identity and last successful tick. Owners retain work and lock tables. Add CLI packaging and a documented local service definition. Add smi_runtime/AGENTS.md with sibling relative CLAUDE.md symlink. Update tasks, monitoring, architecture, development and operator guide.

## UI reads, commands and agent integration

health() exposes last tick, per-component health, next due and actual activation for S16. A single loop must not let a slow source starve polling or delivery. UI restart does not stop work; pausing a topic or schedule stops future admission only.

## Invariants and authorization

Runtime identity is configured automation, not the browser human. No task-origin conversion, scope expansion, automatic uncertain paid retry or revival of terminal work. Keep owner-specific session locks and independent spending admission.

## Failure and recovery

Process death releases sessions and health becomes stale. Restart reopens durable identities. Exponential capped retry applies only to explicitly safe local/read failures. Unknown dispatched responses wait for verified owner recovery; no catch-up beyond the schedule's accepted current-day rule.

## Acceptance

### S09-A01

Start only the local runtime, configure a due keyword and topic, and observe task completion plus a collection window through public reads.

### S09-A02

Start two runtimes, kill one at an effect boundary and observe one local effect/receipt with independent task progress.

### S09-A03

Make one source slow and one task unknown-response waiting; other task/poll/health work advances within configured tick budgets.

### S09-A04

Restart, pause and change configuration; old work retains its original day/activation/scope and no unapproved call is dispatched.

### S09-A05

With an expired payload and a withdrawn source, a maintenance tick removes the payload and reconciles dependent copies within its bound, and health reports the run.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A03, FR-B08, FR-C01, FR-L01, FR-P01, FR-P02, FR-P09, OFR-P01, OFR-E03, PROP-27, PROP-29, PROP-30, PROP-34, UD-02. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
