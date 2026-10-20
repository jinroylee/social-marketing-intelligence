# Acquisition and canonical evidence

Own source observations, bounded acquisition checkpoints, source policy, canonical identity/mapping and their schema. Collectors implement `Collector`; deterministic mappers implement `Mapper`; `IngestionRunner` coordinates them through `EvidenceStore` and `CanonicalWriter`. Downstream owners read exact support through `smi_ingestion.support` and retain their own task/publication decisions.

Commit each observation and its collection frontier together, then commit canonical mapping. `resume(..., on_commit=...)` notifies only after durable evidence/canonical commits; observer exceptions propagate. `inspect` reads committed counts without collection or state advancement. Recover retained pending observations and reuse committed derivations; unavailable replay stays an explicit failure rather than an implicit refetch.

For no-observation results, commit checkpoint, completion/waiting metadata and actual request use together through `EvidenceStore.advance`. A pending wait promises safe resume of that saved operation; an ambiguous wait stays blocked until route-specific reconciliation. Keep opaque operation handles in ingestion, exposing only sanitized wait reasons/resumability to tasks. Apply persisted bounds before every collector call.

Keep admission authority, publication availability, notifications and monetary decisions with their owners. Verify public ingestion/task operations with real PostgreSQL and simulated external I/O; align schema, physical ERD and source/task contracts when progress semantics change.
