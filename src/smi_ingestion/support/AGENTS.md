# Exact ingested support

Own workspace-scoped selection and reads of exact observation, derivation, assertion and metric identities through `IngestedEvidence` and immutable `SupportReference`. Sources can come from fresh ingestion or frozen imports. Ingestion runs carry the workspace owner; actor context comes from the trusted caller.

Keep source values with ingestion. Validate every selected assertion/metric against the nominated derivation and observation. Return stable subject identities for assertions and metrics so consumers can filter metric-only support through this public interface. Read pinned IDs, preserve missing states, and evaluate the requested process/display purpose independently. Synthetic support requires explicit development visibility.

Expose one-way capture/mapping/selection `content_version` only for permitted support. Keep payload hashes and identity construction with this source owner; equivalent new run UUIDs preserve content identity while later captures, methods or selected logical fields differ.

`require_run_support` validates exact applied support against its immutable workspace/run lineage without reading values, including after policy withdrawal or derivation supersession; it grants no publication or value-use permission. A caller-owned transaction retains source/derivation share locks through dependent commits. Return denied support as metadata-only tombstones and superseded derivations as review-required. Consumers own their retained copies and must reconcile them under source retention policy.

This interface does not publish knowledge, infer business attributes, or mutate imported evidence-set membership. Update the evidence contract, architecture and physical ERD when changing ownership, limits or transaction behavior.

Denied-support tombstones expose content-free current process/display/retention flags as well as derivation health. Consumers use retention flags to purge their own copies; source values, links and dates remain withheld when the requested purpose is denied.


Before source support reads, reconcile inherited source expiry through the public ingestion lifecycle port in this reader's workspace. Hold source/derivation policy locks through the caller commit. Reconciliation must not scan/lock unrelated workspaces; direct publications/queries must enforce inheritance without a promotion reader.

`run_lineage` exposes bounded content-free run/observation/derivation history for operational readers. Retain historical IDs/methods and explicit truncation; source dates require current process/display/retention plus explicit synthetic visibility. Keep raw coverage, issue text, checkpoints and provider handles private; installed waiting codes only.
