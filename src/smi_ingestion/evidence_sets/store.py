"""Atomic materialization of validated exports through ingestion persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from ..canonical import CanonicalWriter
from ..contracts import ObservationDraft, RunLimits, SourcePolicy, SourceReference
from ..evidence import EvidenceError, EvidenceStore, policy_allows
from .access import ActorContext
from .snapshot import FORMAT_VERSION, MAPPER_VERSION, load_snapshot, normalize_record, timestamp


class SnapshotImporter:
    """Publish a complete frozen dataset or roll back all database changes."""

    version = "v1"

    def __init__(self, evidence: EvidenceStore, workspace_id: str = "local"):
        self.evidence = evidence
        self.workspace_id = workspace_id

    def import_snapshot(
        self, manifest_path: Path, actor: ActorContext, policy: SourcePolicy,
    ) -> dict[str, Any]:
        """Import once per workspace/dataset; reject changed bytes or interpretation metadata.

        The source files are operator-managed inputs. Only files created in the
        evidence store are cleaned up if the transaction fails.
        """
        actor.require_workspace(self.workspace_id, importing=True)
        if not policy_allows(policy, "process"):
            raise EvidenceError("processing_not_permitted")
        snapshot = load_snapshot(manifest_path)
        manifest = snapshot.manifest
        dataset_id = manifest["dataset_id"]
        # A location is not dataset identity: moving identical inputs must stay idempotent.
        stored_manifest = {k: v for k, v in manifest.items() if k != "snapshot"}
        stored_manifest["collection_runs"] = list(snapshot.collection_runs)
        created_paths: list[Path] = []
        writer = CanonicalWriter(self.evidence.db)
        try:
            with self.evidence.db.connect() as connection:
                connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))",
                                   (f"evidence-set:{self.workspace_id}:{dataset_id}",))
                existing = connection.execute(
                    "SELECT * FROM evidence_sets WHERE workspace_id=%s AND dataset_id=%s",
                    (self.workspace_id, dataset_id),
                ).fetchone()
                if existing:
                    if existing["digest"] != manifest["sha256"] or existing["manifest"] != stored_manifest:
                        raise EvidenceError("dataset_version_conflict")
                    # Reimport is not a source-policy grant; withdrawn members stay withdrawn.
                    return {"status": "duplicate", "dataset_id": dataset_id,
                            "digest": existing["digest"], "run_id": str(existing["run_id"])}
                total = len(snapshot.records)
                limits = RunLimits(total, total, total, 16 * 1024 * 1024)
                run_id = self.evidence.start_run(
                    manifest_path, manifest["sha256"], "snapshot-json", limits, connection=connection, workspace_id=self.workspace_id,
                )
                connection.execute(
                    "INSERT INTO evidence_sets(workspace_id,dataset_id,digest,manifest,run_id,"
                    "synthetic,importer_version,imported_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (self.workspace_id, dataset_id, manifest["sha256"], Jsonb(stored_manifest), run_id,
                     snapshot.synthetic, self.version, actor.actor_id),
                )
                for position, record in enumerate(snapshot.records):
                    origin = record["provenance"]
                    draft = ObservationDraft(
                        source_item_key=record["post_id"], adapter_id="snapshot-json",
                        provider_id=origin["provider"], format_version=FORMAT_VERSION,
                        reference=SourceReference(record["url"], "tiktok", "video", record["post_id"],
                                                  record["author"]["handle"]),
                        payload=json.dumps(record, ensure_ascii=False).encode(), media_type="application/json",
                        captured_at=timestamp(record["captured_at"]), source_as_of=None,
                        policy=policy, synthetic=snapshot.synthetic,
                        coverage={
                            "scope": "selected_post_observation", "origin": origin,
                            "source_namespace": manifest["namespace"],
                            "snapshot_format": FORMAT_VERSION, "importer_version": self.version,
                            "annotations": {"basis": "development_annotation", "values": record.get("curation", {})},
                            "unavailable_fields": ["profile", "followers", "recent_post_history",
                                                   "audience_geography", "fees", "availability", "media", "sales"],
                        },
                    )
                    observation = self.evidence.save(
                        run_id, position, draft, {"index": position + 1}, connection=connection,
                    )
                    if observation.payload_path:
                        created_paths.append(Path(observation.payload_path))
                    result = writer.apply(
                        observation.id, normalize_record(record), f"snapshot-json:{MAPPER_VERSION}",
                        connection=connection,
                    )
                    connection.execute(
                        "INSERT INTO evidence_set_members(workspace_id,dataset_id,position,origin_observation_id,"
                        "origin_run_id,observation_id,derivation_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (self.workspace_id, dataset_id, position, origin["source_observation_id"],
                         origin["run_id"], observation.id, result["derivation_id"]),
                    )
                    connection.execute("UPDATE source_observations SET status='applied' WHERE id=%s", (observation.id,))
                connection.execute("UPDATE ingestion_runs SET status='completed' WHERE id=%s", (run_id,))
        except Exception:
            for path in created_paths:
                path.unlink(missing_ok=True)
            raise
        return {"status": "imported", "dataset_id": dataset_id, "digest": manifest["sha256"],
                "run_id": run_id, "posts": total, "accounts": manifest["expected_accounts"]}
