"""Replay validated snapshot records without treating an export as a new web fetch."""

from ..contracts import RawObservation
from ..evidence import EvidenceError
from ..evidence_sets.snapshot import FORMAT_VERSION, MAPPER_VERSION, decode_json, normalize_record, validate_record


class SnapshotImportOnlyCollector:
    """Require the importer to validate and publish complete dataset membership."""

    def collect(self, manifest, checkpoint, limits):
        raise EvidenceError("snapshot_requires_import_command")


class SnapshotMapper:
    version = MAPPER_VERSION

    def normalize(self, observation: RawObservation, payload: bytes):
        """Replay one retained export record using its preserved acquisition lineage."""
        if observation.format_version != FORMAT_VERSION:
            raise EvidenceError("unsupported_snapshot_format")
        record = decode_json(payload)
        validate_record(record, (observation.coverage["origin"]["run_id"],))
        if (record["post_id"] != observation.reference.native_id_hint
                or record["provenance"] != observation.coverage["origin"]):
            raise EvidenceError("snapshot_reference_mismatch")
        return normalize_record(record)
