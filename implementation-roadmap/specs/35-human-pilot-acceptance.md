# S35. Record pilot release acceptance on live data

Status: planned, no implementation or validation claimed.
Lane: human-validation
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Human-run release record aggregating checkpoints and readiness rows.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: Actual marketer and named Korean/Japanese reviewers, supported by UI and quality maintainers
Direct spec blockers: [Review exact enrichment scope and expose governed agent operations](14-exact-approval-tools.md) (The approved-research to later-question journey.), [Check shortlist and answer usefulness with a marketer on real discovered data](08-early-marketer-checkpoint.md) (Incorporates H1 findings and fixes.), [Investigate alerts with existing KB context and promote selected evidence](22-alert-investigation-promotion.md) (The alert to KB-context journey.), [Check graph, chart, campaign and chat interaction in a real browser](25-interaction-checkpoint.md) (Incorporates H2 findings and fixes.), [Preserve measurement planning and prepare attributable KR/JP quality packets](30-plans-and-quality.md) (KR/JP adjudication packets.), [Record live discovery, model and recurring-work readiness](31-provider-readiness.md) (Usefulness must be judged on live discovery and model capabilities; a recorded blocked row is a valid input.), [Record live X monitoring and alert-method readiness](32-monitoring-readiness.md) (Alert journeys are judged on live monitoring readiness; a recorded blocked row is a valid input.), [Record supplementary detail-route readiness](33-detail-route-readiness.md) (Acquisition journeys are judged on the live detail route; a recorded blocked row is a valid input.), [Record email send readiness](34-email-readiness.md) (Notification journeys are judged on live email; a recorded blocked row is a valid input.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Requires actual human reviewers and permission for browser execution. Prior denied agent browser access remains denied until separately changed. No browser workaround is authorized by this plan.

## User outcome

The implemented pilot has attributable browser, language and usefulness evidence beyond approval of its design.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [docs/evaluation.md](../../docs/evaluation.md)
- [.scratch/product-design-2026-11/task3/r2/review-guide.md](../../.scratch/product-design-2026-11/task3/r2/review-guide.md)
- [.scratch/product-design-2026-11/ui-review-status.md](../../.scratch/product-design-2026-11/ui-review-status.md)

## Scope and non-goals

The release record that incorporates S08 and S25 results and covers the remaining journeys: approved research to later question, alert to KB context, spending, inbox/email and lineage, plus KR/JP adjudication on live data. Include empty/partial/stale/conflict/withdrawn/meter/unknown-response states, accessibility and narrow CJK layouts. Keep failures and reviewer disagreement visible. Incorporates the four readiness rows; a recorded blocked row is a valid input, and the affected journey is recorded as blocked rather than passed.

## Owners, interfaces and data shapes

Use S30 exact review packets and public application operations. Record deployed build/config/artifact identities, reviewer, language, exact member set/denominator, task success, semantic correctness/uncertainty and corrections. Actual Japanese-original review is distinct from translated review.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

No production schema change beyond quality-owner records already specified. Update evaluation and roadmap with actual outcomes and unresolved acceptance. Preserve governed artifact retention and do not claim UI source checks as rendered tests.

## UI reads, commands and agent integration

Use r2 M01–M11 plus R2-CHAT/STREAM/GRAPH production cases. Check complete EN/KO catalogs and unchanged original evidence. Exercise pointer and keyboard/list alternatives. Review provider results only where S31 permits them; synthetic review remains explicitly synthetic.

## Invariants and authorization

Actual design approval is already recorded and is not asked again. Implementation/browser/language/usefulness acceptance remains separate. A model cannot be its own human reviewer or select only favorable examples.

## Failure and recovery

Failed or unavailable methods remain blocked with exact failing examples, owner and next validation action. Fixes rerun the affected review set; do not rewrite denominators or claim pass from a demo click.

## Acceptance

### S35-A01

Record actual browser runs for r2 review scenarios not already passed in S25 at the same build identity, or re-run them if the build changed.

### S35-A02

Obtain named KR/JP adjudications for criteria, ranking, extractive relevance and provisional monitoring coding, including negative and ambiguous cases.

### S35-A03

Have a real marketer complete brief-to-shortlist, approved research-to-later-question and alert-to-KB-context journeys and record usefulness/gaps.

### S35-A04

Separate passed technical checks, accepted UI design, live-provider readiness and actual human acceptance in the release record.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A01, FR-C02, FR-C03, OFR-E01, OFR-E02, PROP-03, PROP-09, PROP-16, PROP-35, UD-02, UD-03, UD-06, UD-07. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
