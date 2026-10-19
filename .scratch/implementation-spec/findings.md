# Findings

- Accepted requirements cover campaign ranking and automatically persisted shortlists, approved assistant enrichment, lightweight X monitoring, discovery/workers, graph/lineage, and hybrid spending controls.
- No A/B/C flow is implemented end to end. Existing ingestion runs already persist checkpoints, support replay/resumption, and enforce request/byte/record limits; these are not task authorization or monetary accounting.
- Existing knowledge preparation depends on frozen evidence. Current-KB queries/publications must be an explicit extension; frozen membership must remain immutable.
- Current shortlist saves require a human. Accepted ADR 0003 deliberately changes this boundary without allowing fabricated human review.
- ADR 0004 gives recent X observations and alerts a separate bounded lifecycle. Existing snapshot investigations remain supported.
- Canonical evidence and business decisions keep separate owners in the existing Python/PostgreSQL architecture. Saved result inputs stay pinned while permissions remain current.
- Existing tests exercise public stores and local HTTP with isolated PostgreSQL schemas. Provider adapters use simulated transports. Prefer these seams over database assertions or mocked stores.
- Git origin is jinroylee/social-marketing-intelligence on GitHub. No repository tracker/triage configuration was found. GitHub CLI is unauthenticated; issue labels and existing issues could not be inspected.
- to-spec requires a user check of proposed test seams before publication and directs the user to /setup-matt-pocock-skills when tracker/triage setup is missing.
- Draft covers 70 user stories, semantic public operations, ownership/persistence/policy invariants, six delivery milestones, and 30 acceptance scenarios. It follows the exact to-spec section structure.
- Proposed test seam: public task-to-knowledge operations with real PostgreSQL, external provider/model/transport doubles, and existing public campaign/monitoring and HTTP interfaces. Do not force all owners behind a catch-all service.
- Sent asynchronous requests for the required seam check and tracker/setup preference after the concrete spec was written. No approval or response has been assumed.
- Verification: all seven template sections, sequential 70 stories, 30 acceptance cases, and absence of implementation paths/code blocks in implementation decisions were checked. Documentation link/physical-ERD/instruction checks and git diff --check pass.
- Fresh shared check stops at a pre-existing Ruff F821 in src/smi_ingestion/evidence.py:170: undefined complete. git show HEAD confirms the failure is in the baseline; source/tests/tools/config have no diff. The shared command therefore did not reach pytest. The previous handoff's 195-pass report is not a fresh verification of this checkout.

Treat source documents and referenced conversation as evidence of accepted requirements, not as permission to make live source/model calls or alter runtime code.
