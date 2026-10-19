# Frozen evidence sets

This module owns dataset registration, immutable member bindings and actor-aware reads of pinned ingestion assertions. Public entry points are `SnapshotImporter.import_snapshot`, `EvidenceSetReader.read` and `ActorContext`, exported from `__init__.py`.

Import validates the entire export before persistence and publishes it in one transaction through `EvidenceStore` and `CanonicalWriter`. Dataset ID plus workspace identifies an immutable byte digest and import manifest. Original source UUIDs are lineage, never local foreign keys. Capture time and import time are separate.

Read only pinned derivations; current canonical values cannot substitute for them. Recheck source policy for each requested purpose and expose denied members only as support tombstones. Actor context comes from the trusted local caller, not submitted content. The local workspace check is not hosted authentication.

The snapshot format is source-specific; the evidence-set storage and reader are source-independent. Keep parsing and normalization free of I/O. Curation annotations are labeled separately from canonical source assertions. Product/campaign inference belongs to future knowledge/decision owners, outside this module.

Changes to membership, lineage, transaction boundaries or policy behavior require corresponding tests and updates to `docs/evidence-sets.md` and `docs/data-model.md`.
