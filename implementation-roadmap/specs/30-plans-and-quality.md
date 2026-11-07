# S30. Preserve measurement planning and prepare attributable KR/JP quality packets

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: single-pass. Forms and packets over installed planning and quality owners.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_campaigns.planning owns plans/notes; smi_review.quality owns exact review packets and real review records
Direct spec blockers: [Complete brief to saved recommendation and explicit regeneration](12-campaign-decisions.md) (Plans and notes bind to exact brief/shortlist revisions produced by C1.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: None beyond the shared test prerequisites.

## User outcome

A marketer records proposed measurement and human learning, while reviewers receive exact bilingual output/evidence packets.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_campaigns/planning/](../../src/smi_campaigns/planning/)
- [src/smi_review/quality/](../../src/smi_review/quality/)
- [tests/test_monitoring_planning.py](../../tests/test_monitoring_planning.py)
- [tests/test_operational_reviews.py](../../tests/test_operational_reviews.py)
- [docs/evaluation.md](../../docs/evaluation.md)

## Scope and non-goals

Deliver P1 plan/note forms, exact brief/shortlist linkage, proposed outcome/source/matching/attribution assumptions and quality packet preview. No actual conversions, revenue, lift or automated human review.

## Owners, interfaces and data shapes

Compose CampaignPlanning.save_plan/add_note/read and quality owner packet/record operations. Add presentation envelope for exact membership, reviewer identity, original language, translation method, denominator, negatives/ambiguities and pending verdict. A saved review requires an actual attributable human action over that packet, not a model confidence field.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Reuse plan/review schemas unless required packet fields are missing. Pin new method/version members explicitly without rewriting old packets. Update planning, evaluation, local-review and ERD for actual additions.

## UI reads, commands and agent integration

Measurement & learning is independently reachable and linked from C1. Notes are visibly human supplied; source-dependent copied wording inherits exact support. UI catalogs cover review/error states, while original KR/JP evidence remains unchanged. UI spec obligations: use the shared S04 freshness utility rather than a screen-specific revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this screen, executed at S25 or S35, not as a build-completion gate.

## Invariants and authorization

Plan is proposed, attribution is a stated rule, and causation requires later design/data. Automatic shortlist save, UI approval and packet generation are distinct from usefulness/language review. Marketers cannot fabricate verified outcomes by entering a note.

## Failure and recovery

Stale brief/shortlist edits conflict. Lost source support withholds copied note/review text but retains safe attribution. Incomplete reviewer denominator remains pending; missing or ambiguous reviews cannot become pass.

## Acceptance

### S30-A01

Save a plan and decision note against exact versions, revise the campaign and reopen original links/assumptions unchanged.

### S30-A02

Withdraw source support and observe governed note/packet redaction without losing safe authorship.

### S30-A03

Prepare exact KR/JP packets with negative/ambiguous examples and correct denominators; no human review record exists until a real reviewer submits it.

### S30-A04

Verify UI still states proposed measurement and contains no fabricated observed performance or external campaign/contact action.

### S30-A05

Prepare exact KR/JP original-language evaluation cases, including packaging/product ambiguity and negative examples. Build completion does not mark human semantic quality passed.

### S30-A06

Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful revalidation through the shared freshness utility. The S04 catalog completeness check passes with this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A01, OFR-E01, OFR-X01, PROP-01, PROP-02, PROP-03, PROP-04, PROP-15, PROP-16. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
