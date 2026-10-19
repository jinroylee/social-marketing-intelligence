# Offline acquisition tasks

Own campaign-authorized task admission, immutable scope/limits, attempts, phase/outcome counts and links to ingestion runs and knowledge publications. Public interfaces are `AcquisitionTasks`, trusted `OfflineRoute` configuration and `OfflineTaskWorker.run_one`; see [the task contract](../../docs/tasks.md) before changing authority or lifecycle.

Read campaigns through `CampaignStore`; ingestion owns source persistence/normalization and exact support; `KnowledgePublications` owns availability and unchanged-support comparison. Keep dependencies toward these public owners and task-table writes within this package. Retain actual initiator/worker identities and exact brief, run, support and publication IDs. Store source-free metadata rather than raw payloads or copied source wording.

Construct actors at trusted CLI/HTTP boundaries. Campaign admission establishes its origin from an existing workspace campaign, never a supplied origin string or model text. Persist scope/configuration digest and hard limits before acknowledgment; queued execution verifies that digest. The task worker registers only synthetic local `fixture-json` capability and runs at most one task. Keep collection, ingestion, publication and usable-update meanings distinct. Terminal retries reopen existing effects.

Interrupted active attempts remain explicit until a public recovery contract is added. Recovery, assistant approval, claims, notifications and cost admission must extend this owner without granting broader authority through a generic submit method. Update the contract, architecture and physical ERD together when changing persistence or interfaces. Verify public task/worker and local HTTP seams with real PostgreSQL and simulated external I/O.
