# Establish a local-first operating envelope within USD 100 per month

Label: wayfinder:research
Type: research
Mode: AFK
Status: resolved
Assignee: pilot-builder (via Codex budget research)
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: none

## Question

What explicitly bounded workloads and service choices could support local development with very low recurring cost and eventual operation around USD 100 per month for one builder and an initial brand-marketer pilot?

Use current primary pricing and billing documentation. Separate confirmed rates from proposed allocations and workload assumptions. Include infrastructure, persistent storage and backup, LLM input/output and embeddings where relevant, source/API allowance, and contingency; identify excluded or unknown costs. Show calculations for modest text-based usage and the cost implications of adding media processing. Explain usage ceilings and failure behavior needed to prevent a nominally cheap plan from overrunning the budget. Compare a minimal local setup and one plausible hosted shape without selecting a provider, buying services, or promising feasibility for unspecified workloads. An illustrative LLM allowance is not user approval of that spend.

Write findings to `../research/03-operating-budget.md` and link the artifact in the resolution. Coordinate with the access investigation only when a specific source fee is needed; this research can proceed using an explicitly labeled reserve for data access.

## Answer

Resolved on 2026-09-28 through primary-source research. A bounded text-based pilot is arithmetically plausible within the user's total envelope; it is not yet validated against actual data availability, Japanese-language output quality, or measured hosting load. The worked example costs approximately USD 5.51 in models and USD 19.91 including one small hosted server and backups, before source fees and other costs. Local development can omit that server subscription. The proposed total allocation reserves USD 35 for as-yet-unselected data and USD 20 for tax, currency effects, and contingency within the USD 100 total.

The [operating-budget findings](../research/03-operating-budget.md) hold the official rates, reproducible workload calculations, storage assumptions, usage ceilings, exclusions, and failure behavior. The calculations and principal model/hosting rates were independently checked by the parent session. These figures establish an operating hypothesis, not a provider selection or spend commitment. Actual source fees, initial development allowance, and useful workload remain inputs to [Select the first live source and evidence scope](11-select-live-source-and-evidence-scope.md).
