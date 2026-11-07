# Route from the installed system to the approved intelligence workspace

Issue: W00
Labels: wayfinder:map
Parent: none
Assignee: coordinator / local product-design effort
Status: charted, implementation specifications planned
Blockers: none for charting. The Task 4 UI gate is satisfied by actual r2 approval.

## Destination

Deliver a shared decision map and an ordered set of individually implementable specifications closing the gap between actual code and the full approved UI/product. Preserve every FR and distinguish the first local pilot, actual readiness and later proposal depth.

## Notes

The user's explicit destination includes implementation specifications. It overrides wayfinder's usual decisions-only deliverable. The main deliverable is [the implementation sequence](../implementation-sequence.md), supported by [gap analysis](../gap-analysis.md), [target architecture](../architecture-target.md), [traceability](../traceability.md) and individual files under `task4/specs/`. These specs are build/validation contracts, not decision tickets.

Use [the repository's local Markdown tracker](../../docs/agents/issue-tracker.md). It has no native parent/dependency relationship or Wayfinding operations section. This directory is the explicit fallback for this effort. One issue file is one identity. Every issue carries Parent, Assignee, Status and named Blockers fields. Map uses only `wayfinder:map`; children use only their `wayfinder:<type>` label. Open plus unassigned plus no open decision blocker is the decision frontier. External implementation/evidence prerequisites are listed separately and must also be satisfied before a final resolution. Specs link their direct decision blockers and other specs by real relative paths.

Run `python implementation-roadmap/source/verify_plan.py --frontier` from the repository root to query children/frontier. The map intentionally does not list open issues. Find them by the query or directory. Claim a decision by assigning its actual driver before working through it. Charting closes no tickets. This session will not resolve more than one decision issue and will not simulate a human exchange.

Apply wayfinder, grilling and domain-modeling. Preserve the root glossary's evidence, observation, interpretation, task, approval, publication and human decision distinctions. Consult the accepted ADRs and owner contracts before changing any interface. This planning run wrote only `task4/` and `wayfinder/`, now `implementation-roadmap/` and its `decisions/`; proposed glossary/ADR work is specified for implementation, not silently accepted now.

Accepted upstream evidence lives once in [the actual Task 1 decisions](../../.scratch/product-design-2026-11/task1-recovery/decisions.md) and [actual r2 approval](../../.scratch/product-design-2026-11/ui-review-status.md#actual-r2-approval). The authoritative current UI is [r2 design](../../.scratch/product-design-2026-11/task3/r2/design-spec.md). Upstream decisions are not newly resolved child tickets. Browser access remains declined. No code, providers, spending, email, commits or external publication are authorized here.

## Decisions so far

No child decision has been resolved in this charting session. This section indexes actual future resolution comments by named links and does not duplicate their content.

## Not yet specified

Candidate evaluation may expose specific unsupported claim classes or irreducible scope ambiguity. Revisit those after actual candidate evidence. The known successor-contract question is already a ticket and is not duplicated here. No provider-selection fog is invented where validated operator configuration is sufficient.

## Out of scope

Feature implementation, production schema/doc changes, real provider/model execution, actual email, browser automation, deployment and commits are outside this planning effort. Creator contact, content publishing, media buying and external campaign activation remain outside the product boundary. Specialized stores or multiple agents solely for UI appearance are not requirements.
