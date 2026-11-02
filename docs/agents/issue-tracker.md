# Local Markdown issue workflow

Use one file per active implementation issue under `.scratch/<feature>/issues/`, numbered in dependency order. Link the [accepted requirements](../functional-requirements.md), [interface/acceptance contract](../implementation-spec.md), relevant owner contracts and direct blockers. Keep product truth in those durable documents rather than a second ticket copy.

1. Read the issue, direct blockers and relevant domain guidance. Begin when blockers are resolved and the integration branch's shared checks pass; document any explicitly authorized exception.
2. Claim the issue by setting `Status: claimed`. Use an isolated branch/worktree when implementation needs separation. Follow the approved public-operation test boundary, real PostgreSQL and simulated external I/O unless actual execution is separately authorized.
3. Commit implementation and validation evidence. Integrate and run shared checks before marking `Status: resolved`; record the implementation commit and check result under `## Completion`.
4. Retain genuine blockers and partial work explicitly. Actual human-validation work requires actual reviewer input; software fixtures cannot resolve it.

Publishing sets `Status: ready-for-agent` and explicit blocking issue numbers/titles. The published issue owns active execution status; comments append under `## Comments`. Drafts are temporary proposals. After a completed batch, move genuine remaining requirements/readiness into the [roadmap](../roadmap.md), preserve durable trade-offs in ADRs and rely on Git for completed implementation history. Obsolete drafts, completed ticket copies and session narratives need not remain in the working tree. Preserve source/verification artifacts according to their applicable retention requirements.
