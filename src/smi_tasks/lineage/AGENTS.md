# Read-only task pipeline lineage

Own `TaskLineage.read`, a transient projection of one exact workspace task's authority, attempts/recovery, ingestion runs/observations/derivations, receipted publications and attributable cost operations. Read [the task contract](../../../docs/tasks.md#read-only-task-pipeline-lineage) before changing the projection or its coverage semantics.

Compose only public `AcquisitionTasks.read`, `IngestedEvidence.run_lineage`, `KnowledgePublications.read` and `UsageAccounting.task_operations`. Keep task SQL with the task store, source SQL with ingestion and accounting SQL with costs. No persistence, collection, model execution or graph dependency belongs here.

Preserve original IDs, producer, methods, versions, dates, prepared support and bounded recovery history. Historical outcomes/counts remain historical after source loss; current publication navigation requires process/display/retention permission and current derivation health. Synthetic source visibility is explicit. Keep source wording in governed evidence pages and render only content-free operational metadata here. Use installed failure-code allowlists; opaque provider handles, payload/file paths and arbitrary error text never enter this projection.

Owner reads are independent committed frontiers, not an atomic cross-owner pipeline snapshot. Retain source/cost truncation and unknown coverage. Accounting amounts retain their exact currency/period/synthetic or provider basis; absence is unknown cost, and declaration or forecast is no proof of a charge ceiling. Reconciliation changes accounting, never task/source/publication authority.

Verify through public task/HTTP journeys with real isolated PostgreSQL, fake external I/O and public worker interruption ports. Preserve recovery, partial collection/ingestion, publication failure, no-update, denied support and exact cost attribution. Avoid private-collaborator mocks, cross-owner SQL and database business-outcome assertions.
