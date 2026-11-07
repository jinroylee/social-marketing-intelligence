# S11. Describe usable source routes and bounded selection policy

Status: planned, no implementation or validation claimed.
Lane: pilot-build
Size: M (S = up to a few days, M = about one week, L = multi-week)
Execution mode: wayfinder. Its registry contract is consumed by four specs and its selection policy is product-semantic. Decisions to chart before implementation: capability registry schema and versioning; recency/engagement/trend selection semantics and unknown disposition; which capability changes are material to approved scope.
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: smi_ingestion.adapters owns route capabilities/provenance; smi_tasks owns approved route scope; smi_review exposes D1
Direct spec blockers: [Compose the local pilot from one validated configuration](02-pilot-configuration.md) (The readiness read extends the configuration's source-free readiness.)
Direct decision blockers: None.
Configuration or actual-evidence prerequisites: Provider/account, quotas, field support, rates and source-use authorization come from the S05 rows and the final S31 record. No commercial price or readiness is assumed.

## User outcome

Operators and planners can distinguish a route's installed capability, actual access/use permission and field/time coverage before work is admitted.

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

- [src/smi_ingestion/adapters/](../../src/smi_ingestion/adapters/)
- [src/smi_tasks/discovery/](../../src/smi_tasks/discovery/)
- [src/smi_tasks/supplementation/policy.py](../../src/smi_tasks/supplementation/policy.py)
- [tests/test_live_discovery.py](../../tests/test_live_discovery.py)
- [docs/source-integrations.md](../../docs/source-integrations.md)

## Scope and non-goals

Add a typed versioned capability registry and public readiness read. Describe installed fixture, Bright Data keyword/profile, official recent-X and other existing adapters truthfully. Add bounded broad-discovery prioritization using available recency/engagement/trend evidence. Do not invent missing API/oEmbed/web routes. Describe the oEmbed and tiktok-web adapters as existing for supplied references but not task-integrated. The D1 screen is S16.

## Owners, interfaces and data shapes

Proposed SourceCapabilities.read(route, actor) -> operations/fields/native namespace/time semantics/limits/policy/readiness. SelectionPolicy(version, recency rule, comparable engagement rule, supported trend baseline, unknown disposition) orders normalized candidates inside the original finite sample before eligible admission. Save selection basis and omission reasons. Supplemental request capability declares exact field/subject/billing and allowed parent scope. Provider secrets and opaque handles never enter presentation.

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

Registry configuration is operator-owned and versioned; persist pinned capability/selection versions in task scope and receipts. Existing scope digests remain unchanged; new versions require new approval/activation as material. Add fields only with explicit legacy-unrecorded migration. Update source-integrations, tasks, architecture, ERD and adapter instructions.

## UI reads, commands and agent integration

The public readiness read exposes installed, access-unknown, permission-denied, configuration-blocked and activated states separately for S16. Registered keyword count and day allowance remain owner-enforced. Selection results expose rank inputs and unknown trend evidence rather than a trending claim without a baseline. The agent planner consumes this contract, never adapter internals.

## Invariants and authorization

Source reference/profile lookup is not keyword discovery. Namespace equality is never inferred from matching handles/native numbers across routes. Selection is deterministic/versioned and cannot expand acquisition or guarantee fifty posts. Current policy and monetary gates recheck at dispatch.

## Failure and recovery

Absent ranking inputs remain explicit unknowns. Changed capability before dispatch blocks/reviews scope; it cannot silently select fallback. Unknown capture dates cannot establish freshness. Partial/malformed/out-of-scope returns keep request/cost history with no invented usable facts.

## Acceptance

### S11-A01

Read every enabled route capability and compare its operations/field/time support with its actual public collector receipt using simulated I/O.

### S11-A02

Order a bounded mixed candidate sample with configured recency/engagement/trend inputs and reopen exact policy/version/omissions.

### S11-A03

Remove access, field support or permission between planning and dispatch and observe refusal without fallback.

### S11-A04

Exercise profile-only, minimal URL-only, unknown-capture and mismatched-native-ID results; none becomes broad discovery or verified creator identity.

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker](../../docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: FR-A06, FR-P02, FR-P03, FR-P04, FR-P06, OFR-E03, PROP-23, PROP-24, PROP-34. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
