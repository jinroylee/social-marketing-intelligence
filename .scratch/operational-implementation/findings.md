# Ticket-planning findings

- Source spec: 70 user stories, 30 acceptance scenarios, six proposed milestones. Accepted behavior remains authoritative; no additional product interview is required.
- All proposed feature slices should expose a public operation and a usable local surface, with real PostgreSQL integration coverage and simulated external I/O by default.
- There is no need for a speculative wide refactor. Existing collectors, mappers, ingestion checkpoints, public stores, actor boundaries, form protections, and isolated-schema tests are reusable.
- The only initial baseline repair is the source-evidence save completion contract: the runner supplies a completion argument absent from the current signature and the save implementation references an undefined completion value. Fix it as a separate bounded recovery/regression ticket; do not perform that repair during ticket generation.
- Distinguish minimal publication by identity from broader current-KB search and pinned retrieval results; task execution can reuse the first without waiting for graph or LLM work.
- Split task happy path, exact assistant approval, recovery/partial outcomes, worker concurrency, and completion inbox. Treat each as a complete visible operational behavior.
- Split spending into attributable actual/forecast reporting, coordinated admission, and uncertain/delayed reconciliation; no live route should precede the applicable controls.
- Schedule configuration, daily unique-post allowance, retrieval avoidance, broad query discovery, and live enablement are separate behaviors. Scheduled live activation must depend on the daily allowance; on-demand live discovery need not wait for keyword configuration.
- Current-KB comparisons, automated save authority, LLM assessment, optional human curation, coverage discovery, and explicit regeneration are distinct campaign behaviors.
- Recent X observations can start independently after the baseline repair. Full KB publication is never a per-post prerequisite for X detection.
- Model-backed consumers may reuse one explicitly metered provider transport introduced through a real user journey; no generic model-framework ticket is needed.
- Final human quality evaluation must use genuine reviewer input and report pending if absent; implementation tests cannot fabricate a usefulness or original-language pass.
- The tracker is still not configured in the supplied instructions; drafts are local and not published. to-tickets requires approval of the breakdown before either local ready-for-agent files or real tracker issues are published.
- Final draft: 39 tickets, with 9 S and 30 M scopes, each 150–500 words and an explicit scope guard. Word limits are an artifact check, not a claim about implementation effort; scope was separated by observable behavior and distinct failure boundaries.
- Full coverage: every user story 1–70 and acceptance scenario T01–T30 has an identified owner/extension ticket. The numbered breakdown includes both traceability tables.
- Dependency audit: all blockers precede dependents, there are no cycles or redundant transitive edges. Initial frontier is ticket 01; after it completes, 02, 12, and 29 can start independently.
- Source-policy/synthetic visibility, simulated cost labeling, and failed new-post-admission reconciliation were checked explicitly in the drafted criteria.
- Required breakdown review was requested asynchronously after all drafts were concrete. No response or approval has been assumed. The published issues directory does not exist.
- Fresh shared check still fails Ruff F821 at the unchanged source-evidence completion value and stops before pytest. Direct documentation link/ERD/instruction checks, draft-link/coverage/DAG checks, and whitespace checks pass.

## Completed batch

- All first ten tickets are resolved; authoritative commits and checks are in execution-manifest.json and reports/final.md.
- Original-baseline standards/spec reviews found three standards findings and one publication-ownership defect; all were repaired in one implementer context and verified with 325 integration tests.
- Publication recovery now requires an atomic task receipt plus exact prepared support and source-run lineage, while current policy still governs values.
- Live operations, commercial billing reconciliation and tickets after 10 remain outside this completed batch.

## Remaining-ticket continuation

- Tickets 11–39 are approved and published. The previous first-ten manifest/reports remain completed history.
- Ticket13 explicitly requires current primary-provider contract verification; no existing model/provider configuration or captured primary model contract was found in repository text. The user approved read-only primary-documentation lookups only; model/source execution stays local and simulated while ticket11 proceeds.
- Tickets24/25/34 require actual live prerequisites; ticket39 explicitly requires a named real human reviewer. Simulated tests cannot create those readiness/usefulness receipts.

- Primary-provider contract research is captured in research/model-provider-contract.md. Official HTML API reference exceeded the web reader size limit, and its Markdown variant was unsupported by that reader. Bounded read-only HTTPS retrieval of official Markdown succeeded; no API execution or credentials were used.

- Ticket13 pre-merge review found a scope gap: a simulated-only transport left the selected provider adapter unimplemented, with no later model-live ticket. Offline execution does not preclude concrete adapter code tested with simulated HTTP. The implementer is closing the gap with explicit server enablement, a current primary-verified model context bound, and truthful provider-reported/synthetic accounting provenance. No live call or commercial receipt is authorized.

## Ticket 13 pre-merge gap closure

- Closed the earlier root scope gap in `2420af1de46a1756d370914a555ae826e574a306`: concrete fixed-host bounded Responses adapter, disabled by default; explicit verified model contract; strict returned model/tier/final-usage handling; separate provider/synthetic basis; exact provider-basis final reconciliation and separate health recovery. Root shared validation passed **381 tests in 253.68 seconds** with all HTTP intercepted simulation.
- Primary-contract verification and software implementation are complete. Future live enablement, real credentials/rates/configuration, account readiness, live receipts and human quality remain unestablished; no readiness or commercial-invoice claim follows from the simulated tests.
