# Frozen evidence-set contract

The public interface is [`smi_ingestion.evidence_sets`](../src/smi_ingestion/evidence_sets/__init__.py). It turns a portable captured export into locally addressable support for downstream knowledge and decision modules.

The [target current-KB workflows](functional-requirements.md) do not remove this fixed-input contract. Future retrieval searches current published knowledge and pins the exact observations/assertions/method versions supporting each result. It must define that retrieval-result support interface explicitly rather than treat this snapshot importer as an existing KB-wide query or mutate an imported set when new posts arrive. Source-policy checks continue to apply to both generated and human-authored results.

## Exact ingested support

The source-independent [`smi_ingestion.support`](../src/smi_ingestion/support/__init__.py) interface reads fresh ingestions and imported observations by exact IDs. `IngestedEvidence.select_run` selects applied current derivations; `read` validates explicit `SupportReference` observation/derivation/assertion/metric membership and returns process/display policy-filtered support. Caller-owned transactions retain source/derivation locks through dependent commits. It does not register a dataset or change frozen membership. Knowledge publication uses this interface; frozen pilot consumers continue to use `EvidenceSetReader`.

Ingestion runs carry a trusted `workspace_id`, defaulting to `local` for existing callers. `EvidenceStore.start_run(..., workspace_id=...)` establishes it; snapshot import supplies its configured workspace. Migration preserves imported run workspace ownership. Run ownership is separate from source/canonical entity identity and does not authenticate a network caller.

## Import

```python
from pathlib import Path
from smi_ingestion.contracts import SourcePolicy
from smi_ingestion.evidence_sets import ActorContext, SnapshotImporter

actor = ActorContext("local", "marketer", "human")
policy = SourcePolicy("local-development-snapshot", True, True, True)
result = SnapshotImporter(evidence_store).import_snapshot(
    Path("path/to/snapshot-manifest.json"), actor, policy,
)
```

The importer requires a trusted human operator in its configured workspace and a policy permitting processing. Source-policy configuration describes the local processing context; it is not independent proof of source-use clearance.

The supported format is `tiktok-caption-snapshot-v1`. Its manifest declares:

| Field | Meaning |
| --- | --- |
| `dataset_id` | Immutable dataset identifier within the workspace |
| `format_version` | Export interpretation contract |
| `snapshot` | Local JSON path contained within the manifest directory |
| `sha256` | Digest of the exact export bytes |
| `namespace` | Source identifier namespace; this format requires `web:public` |
| `expected_posts`, `expected_accounts` | Required complete membership and distinct author counts |

The export declares its dataset ID, synthetic state/type, original collection runs and records. Each record supplies a post ID, direct source URL, author native ID/handle, timezone-aware publication and capture times, original caption, metrics, and original observation/run/provider/adapter lineage. Optional curation is preserved as `development_annotation`, separate from source assertions.

This version interprets exports from the direct TikTok web mapper. Public count names map to `tiktok.web.<metric>.v1` with their original native names and count/precision semantics. A missing exported metric becomes `not_returned`; an explicit zero stays zero. Unsupported formats/namespaces/lineage fail rather than borrowing another source's semantics.

Validation checks digest, schema, IDs as strings, source URL/author consistency, temporal order, nonnegative integer metrics, unique post/origin membership, declared runs and expected account counts. Duplicate JSON keys, non-finite values and undeclared manifest fields are rejected. The manifest cannot carry arbitrary source text outside member-level policy checks. Structural validation does not independently verify caption meaning or source truth.

## Transaction and retry behavior

All input validation happens before database writes. An import then holds a transaction-scoped dataset lock, creates the import run/observations, applies canonical mappings, and binds every member in one transaction. Another reader sees either no set or the complete set.

The unique `(workspace_id, dataset_id)` key serializes concurrent imports. Identical export bytes and interpretation metadata return `duplicate`; changed bytes or manifest interpretation return `dataset_version_conflict`. Moving identical files to another directory does not change dataset identity. A new snapshot requires an explicit new dataset identifier.

Imported observations use adapter `snapshot-json`; the original provider and acquisition lineage remain visible. Their local UUIDs are distinct from origin references. Import time does not become capture time. The supplied files are not represented as retained original HTML.

When retention permits, the evidence store saves each exported record as a replayable JSON payload with its own hash. Mapper replay preserves frozen membership and its original derivation pin. A failed import rolls back database rows and removes the payload files it created. A process crash can leave unreferenced files; the existing evidence reconciliation operation removes old orphan payloads. The source export and manifest are operator-managed files outside this cleanup boundary.

Re-import never restores revoked members or changes their existing policy. Import is not a policy-update mechanism.

Retry imports with `import-snapshot`. Imported runs are atomic and do not use the live acquisition runner's `resume` operation. Retained individual observations can still use mapper `replay`.

## Read

`EvidenceSetReader.list_sets(actor)` lists workspace-scoped dataset IDs/digests, imported membership counts and import times without returning source values. Synthetic datasets are excluded unless requested explicitly. These counts describe original fixed membership, not current source availability; a full purpose-aware read determines usable support.

```python
from smi_ingestion.evidence_sets import EvidenceSetReader

visible = EvidenceSetReader(database).read(dataset_id, actor, purpose="display")
processable = EvidenceSetReader(database).read(dataset_id, actor, purpose="process")
```

The reader uses a consistent database snapshot and returns:

- Dataset ID/digest, validated manifest, synthetic state, importer version and import actor/time.
- Ordered origin-to-local observation bindings and pinned derivation IDs.
- For permitted members: source reference, provider/adapter, source and recording times, mapper/canonical-policy versions and derivation time, source policy, actual coverage, annotations, exact assertion and metric IDs, source locators, field states and metric definitions.
- For denied members: an unavailable-support marker and binding metadata, with no caption, source URL, metric values or annotations.
- Total original membership and current available/unavailable member counts. These are selected observations, not population coverage.

`purpose="process"` requires processing permission; `purpose="display"` requires display permission. Neither implies the other. Both honor expiry and revocation. Synthetic sets require explicit `include_synthetic=True`.

Assertions are read from the pinned derivation even if a newer derivation is active. Such a member reports `superseded_review_required`. Later observations and unrelated database rows cannot contaminate the set. No latest-value substitution or silent conflict resolution occurs in this reader; it exposes the pinned assertions for the downstream interpretation method.

The configured workspace and trusted actor context are checked before lookup. This is a local application contract, not a network authentication service. Future application entry points must resolve actor identity server-side. The administrative current-view CLI is not a substitute for this application-facing interface.

`EvidenceSetReader.statuses(dataset_id, actor)` returns content-free process/display/retention permissions and current derivation health keyed by observation ID. Dependent stores use it for cleanup and commit-time support checks. An optional caller-owned connection holds source/derivation share locks through the dependent transaction. Workspace, complete membership and synthetic-input checks still apply.

## Failure behavior and limits

Errors are explicit `EvidenceError` codes such as `snapshot_digest_mismatch`, `snapshot_membership_mismatch`, `snapshot_reference_mismatch`, `dataset_version_conflict`, `workspace_access_denied`, `evidence_set_not_found` and `evidence_set_incomplete`. CLI failures return a sanitized JSON error and nonzero exit code. Invalid input cannot publish a partially usable dataset.

Current withdrawal behavior hides source-dependent output and removes retained payload files when revoked. Canonical assertion values and the original operator-managed input files are not physically erased by a frozen read. Shared knowledge applies its own [dependency-aware redaction and cleanup](knowledge.md#persistence-and-source-policy); future saved decision text requires the same contract. See [architecture](architecture.md#policy-and-operational-limits).
