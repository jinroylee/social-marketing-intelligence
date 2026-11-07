# S02. Compose the local pilot from one validated configuration

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. One composition module with a pinned contract (load, compose, readiness); the file format is a small local choice.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_review composition root plus a small proposed configuration module; route owners keep their own validation
Direct spec blockers: [Restore a complete, time-stable verification baseline](01-stable-verification-clock.md) (Configuration changes touch every composition root and need a trustworthy full-suite result.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: A local configuration file and environment-held secrets supplied by the operator. Simulated routes are valid configuration.

## User outcome

One operator starts the review server, runtime and CLIs against simulated or provider routes from one validated, versioned local configuration.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_review/server.py](../../src/smi_review/server.py)
- [src/smi_review/app.py](../../src/smi_review/app.py)
- [src/smi_monitoring/polling/store.py](../../src/smi_monitoring/polling/store.py)
- [src/smi_ingestion/cli.py](../../src/smi_ingestion/cli.py)
- [docs/user-guide.md](../../docs/user-guide.md)

## Scope and non-goals

A TOML or JSON file with secrets referenced only by environment-variable name; explicit simulated/provider classification for the model, X recent, Bright Data keyword/profile and email routes; process gates, thresholds, caps, cadence defaults and an interpretation catalog bound; a source-free readiness() read; and one compose(config) used by smi-review main, the runtime and the CLIs, wiring ResponsesRoute, LiveXConfig and the Bright Data routes. Name the exact secret variable per route with a named missing-secret diagnostic; an alias for the two documented Bright Data names is optional. Non-goals: hosted secrets management; any configuration that confers topic activation or live schedule authority.

## Owners, interfaces and data shapes

Proposed PilotConfig.load(path) -> validated, versioned config with digest; compose(config) -> ReviewApp plus runtime/CLI owners; readiness(config) -> per-route classification, missing named prerequisites (including a missing cost scope or route binding per route) and configuration digest, never secret values or handles. Existing CLI flags keep working or map one-to-one.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No business tables. Document the file schema, every secret variable name and the readiness read in docs/development.md, docs/user-guide.md and docs/architecture.md. Add the configuration module's AGENTS.md with its sibling relative CLAUDE.md symlink.

## UI reads, commands and agent integration

The runtime, live probes, notification transport and capability registry consume this one configuration. UI reads only the source-free readiness projection.

## Invariants and authorization

Configuration routes, credentials, process gates, thresholds and caps. Topic activation and live schedule activation remain recorded operator commands under ADRs 0015 and 0023; no file or environment key confers them.

## Failure and recovery

An invalid or unknown key, or a missing referenced secret, fails start-up with a sanitized named reason rather than a provider-looking failure. Changing the file never alters already admitted task, window or occurrence scope.

## Acceptance

### S02-A01

An invalid or unknown key, or a missing referenced secret, fails start-up with a sanitized named reason.

### S02-A02

With a simulated model configured and its cost scope set up through the public UsageAccounting operation in the test, the shipped server runs ranked recommendation, criteria interpretation and a knowledge answer end to end. The shipped operator sequence is accepted in S03.

### S02-A03

With live X configured but no recorded activation, no X request is dispatched.

### S02-A04

readiness() never exposes secret values or provider handles.

### S02-A05

Existing CLI flags keep working or map one-to-one, and the documentation names every secret variable.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: OFR-E03, PROP-34, UD-02. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
