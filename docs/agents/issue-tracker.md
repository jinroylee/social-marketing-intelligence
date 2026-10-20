# Local Markdown issue tracker

Implementation issues live one per file under `.scratch/<feature>/issues/`, numbered in dependency order. The operational source spec remains [the implementation specification](../implementation-spec.md); do not create a second authoritative copy.

## Implementation workflow

1. Read the ticket, its direct blockers, the source spec and relevant domain documentation. A ticket can start after all its blockers are resolved and the integration branch's shared checks pass. Ticket 01 is the approved baseline-repair exception because it fixes the currently failing shared check.
2. Claim one ticket by setting its `Status` to `claimed`. Implement on a fresh branch/worktree based on the current integration tip. Use the ticket's approved public-operation testing boundaries, real PostgreSQL, and simulated external I/O.
3. Commit the implementation and validation evidence. Merge into the integration branch, run the shared checks, and only then set the ticket to `resolved` with the implementation commit and check result under `## Completion`.
4. Resolve test/review failures within the approved scope. Record a genuine external blocker explicitly; preserve partial work and do not claim the ticket complete.

Publishing creates one file per approved ticket with `Status: ready-for-agent`. Blocking edges use ticket numbers and titles. Drafts are historical proposals; the published file is authoritative for execution status. Comments append under `## Comments`.

The completed first run covers tickets 01–10 on `integration/operational-tickets-01-10`. The user approved continuing tickets 11–39 in the same workflow on `integration/operational-tickets-11-39`; see `.scratch/operational-implementation/continuation-manifest.json`. Execute one fresh implementer at a time after its dependencies and shared checks pass. Record genuine external prerequisites without falsely resolving them; continue other dependency-ready work sequentially. Keep execution offline/local with simulated I/O and completion through local commits, without a PR, push, or external tracker update. The user permits read-only primary-documentation lookups for current contract verification; source/model execution remains local and simulated, with live calls disabled. Human-validation tickets require real reviewer input.
