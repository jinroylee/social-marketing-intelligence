"""Durable orchestration around replaceable collection and mapping adapters."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from typing import Any

from .adapters.registry import AdapterRegistry
from .canonical import CanonicalWriter
from .contracts import CanonicalAdmission, RawObservation, RunLimits
from .evidence import EvidenceError, EvidenceStore


TransactionScope = Callable[[str], AbstractContextManager]


def _transaction(scope: TransactionScope | None, phase: str):
    return scope(phase) if scope else nullcontext()


class IngestionRunner:
    def __init__(self, evidence: EvidenceStore, writer: CanonicalWriter, registry: AdapterRegistry):
        self.evidence = evidence
        self.writer = writer
        self.registry = registry

    @staticmethod
    def _manifest(path: Path) -> tuple[dict[str, Any], str]:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        manifest = json.loads(raw)
        if not isinstance(manifest, dict) or not isinstance(manifest.get("adapter"), str):
            raise EvidenceError("invalid_acquisition_request")
        manifest["_base"] = str(path.resolve().parent)
        return manifest, digest

    def ingest(self, manifest_path: Path, limits: RunLimits | None = None) -> dict[str, Any]:
        manifest, digest = self._manifest(manifest_path)
        self.registry.resolve(manifest["adapter"])
        selected_limits = limits or RunLimits()
        selected_limits.validate()
        run_id = self.evidence.start_run(manifest_path, digest, manifest["adapter"], selected_limits)
        return self.resume(run_id)

    def _process(self, observation: RawObservation, transient_payload: bytes | None = None, *, transaction=None, admission: CanonicalAdmission | None = None, policy_version: str = "canonical-v1") -> bool:
        try:
            if transient_payload is None:
                observation, payload = self.evidence.load(observation.id)
            else:
                payload = transient_payload
            _, mapper = self.registry.resolve(observation.adapter_id)
            batch = mapper.normalize(observation, payload)
            with _transaction(transaction, 'canonical') as connection:
                self.writer.apply(observation.id, batch, f"{observation.adapter_id}:{mapper.version}", policy_version, connection=connection, admission=admission)
            return True
        except (EvidenceError, ValueError, KeyError, UnicodeError, json.JSONDecodeError) as error:
            code = error.code if isinstance(error, EvidenceError) else "normalization_failed"
            with _transaction(transaction, 'quarantine') as connection:
                self.evidence.issue(observation.run_id, observation.id, code, code, connection=connection)
                self.evidence.mark(observation.id, "quarantined", connection=connection)
            return False

    def _report(self, run_id: str, completed_input: bool, *, finish: bool = True, transaction=None) -> dict[str, Any]:
        run = self.evidence.run(run_id)
        with self.evidence.db.connect() as connection:
            counts = connection.execute(
                "SELECT status,count(*) AS count FROM source_observations WHERE run_id=%s GROUP BY status",
                (run_id,)
            ).fetchall()
            issues = connection.execute(
                "SELECT code,observation_id FROM ingestion_issues WHERE run_id=%s ORDER BY id", (run_id,)
            ).fetchall()
            unresolved = connection.execute(
                "SELECT count(*) AS n FROM unresolved_candidates u JOIN derivations d ON d.id=u.derivation_id "
                "JOIN source_observations o ON o.id=d.observation_id "
                "WHERE o.run_id=%s AND d.active=TRUE", (run_id,)
            ).fetchone()["n"]
            missing = connection.execute(
                "SELECT f.field,f.state,count(*) AS n FROM field_assertions f "
                "JOIN derivations d ON d.id=f.derivation_id "
                "JOIN source_observations o ON o.id=d.observation_id "
                "WHERE o.run_id=%s AND d.active=TRUE AND f.state IN ('not_returned','unavailable') "
                "GROUP BY f.field,f.state ORDER BY f.field,f.state", (run_id,)
            ).fetchall()
            latest_capture = connection.execute(
                "SELECT max(captured_at) AS captured_at FROM source_observations WHERE run_id=%s",
                (run_id,)
            ).fetchone()["captured_at"]
            source_rows = connection.execute(
                "SELECT reference,captured_at,coverage,status FROM source_observations "
                "WHERE run_id=%s ORDER BY item_index", (run_id,)
            ).fetchall()
        source_results = [
            {
                "reference": row["reference"],
                "captured_at": row["captured_at"].isoformat() if row["captured_at"] else None,
                "outcome": row["coverage"]["outcome"],
                "mapping_status": row["status"],
                "http_status": row["coverage"].get("http_status"),
                "provider_error_code": row["coverage"].get("provider_error_code"),
                "attempts": row["coverage"].get("http_attempts", 0),
                "dataset_kind": row["coverage"].get("dataset_kind"),
                "request_phase": row["coverage"].get("request_phase"),
                "row_count": row["coverage"].get("row_count"),
                "returned_records": row["coverage"].get("returned_records", 0),
                "eligible_records": row["coverage"].get("eligible_records", 0),
                "failed_records": row["coverage"].get("failed_records", 0),
                "error_rows": row["coverage"].get("error_rows"),
                "posts_observed": row["coverage"].get("posts_observed"),
                "unavailable_fields": row["coverage"].get("unavailable_fields", []),
            }
            for row in source_rows if "outcome" in row["coverage"]
        ]
        by_status = {row["status"]: row["count"] for row in counts}
        source_failures = {
            "rate_limited", "source_error", "oversized_response", "invalid_response",
            "provider_error", "partial_rows", "unexpected_row_count", "partial_result",
            "challenge", "authentication_failed", "payment_required", "snapshot_failed",
            "snapshot_pending_limit", "snapshot_canceled",
        }
        # Async provider observations form a sequence for one dataset. An
        # initial 202 is superseded by its retrieved snapshot on resume.
        latest_results = {
            (result["reference"], result["dataset_kind"]): result
            for result in source_results
        }
        status = "completed" if completed_input and not issues and not by_status.get("pending") and not any(
            result["outcome"] in source_failures for result in latest_results.values()
        ) else "partial"
        if run["waiting"]:
            status = "waiting"
        if finish:
            with _transaction(transaction, 'ingestion_finished') as connection:
                self.evidence.finish(run_id, status, connection=connection)
        return {
            "run_id": run_id, "status": status, "waiting": run["waiting"],
            "coverage": "complete_for_requested_input" if completed_input else "partial",
            "observations": sum(by_status.values()), "applied": by_status.get("applied", 0),
            "quarantined": by_status.get("quarantined", 0), "skipped": by_status.get("skipped", 0),
            "unresolved": unresolved,
            "missing_fields": [{"field": row["field"], "state": row["state"], "count": row["n"]} for row in missing],
            "latest_captured_at": latest_capture.isoformat() if latest_capture else None,
            "pending": by_status.get("pending", 0),
            "bytes_used": run["bytes_used"], "records_used": run["records_used"],
            "requests_used": run["requests_used"], "source_results": source_results,
            "limits": run["limits"],
            "issues": [{"code": row["code"], "observation_id": str(row["observation_id"]) if row["observation_id"] else None} for row in issues],
        }

    def inspect(self, run_id: str) -> dict[str, Any]:
        """Read committed counts and issues without advancing or finishing the run."""
        return self._report(run_id, self.evidence.run(run_id)["input_complete"], finish=False)

    def resume(self, run_id: str, *, on_commit: Callable[[str, str], None] | None = None,
               transaction: TransactionScope | None = None, admission: CanonicalAdmission | None = None,
               policy_version: str = "canonical-v1") -> dict[str, Any]:
        """Resume checkpoints; notify after durable evidence/canonical commits.

        The callback receives a phase and observation ID. Callback exceptions
        propagate so an operator can stop between commits without undoing work.
        A supplied transaction scope yields the owner's connection for every
        mutation and commits before notification. Collector I/O and normalization
        run outside it; a disconnected owner cannot persist their late results.
        Optional admission joins canonical application after normalization and
        policy validation; excluded records remain explicit skipped observations.
        ``policy_version`` pins canonical processing independently of the actual
        mapper software. It applies to new/pending observations, not already
        applied observations in this run.
        """
        if not isinstance(policy_version, str) or not policy_version.strip() or len(policy_version) > 100:
            raise EvidenceError('invalid_processing_policy_version')
        run = self.evidence.run(run_id)
        manifest, digest = self._manifest(Path(run["manifest_path"]))
        if digest != run["manifest_hash"]:
            raise EvidenceError("input_changed")
        if run['waiting'] and not run['waiting']['resumable']:
            return self._report(run_id, run['input_complete'], transaction=transaction)
        collector, _ = self.registry.resolve(run["adapter_id"])
        with _transaction(transaction, 'reconcile') as connection:
            self.writer.reconcile_applied(run_id, connection=connection)
        for observation in self.evidence.pending(run_id):
            if self._process(observation, transaction=transaction, admission=admission, policy_version=policy_version) and on_commit:
                on_commit("canonical_committed", observation.id)
        if run["status"] == "completed" or run["input_complete"]:
            return self._report(run_id, True, transaction=transaction)
        completed_input = False
        while True:
            run = self.evidence.run(run_id)
            selected_limits = RunLimits(**run["limits"])
            if run["records_used"] >= min(selected_limits.max_pages, selected_limits.max_records):
                with _transaction(transaction, 'collection_limit') as connection:
                    self.evidence.advance(run_id, run["checkpoint"], complete=False, connection=connection)
                    self.evidence.issue(run_id, None, "record_limit_reached", "record_limit_reached", connection=connection)
                break
            if run["requests_used"] >= selected_limits.max_requests:
                with _transaction(transaction, 'collection_limit') as connection:
                    self.evidence.advance(run_id, run["checkpoint"], complete=False, connection=connection)
                    self.evidence.issue(run_id, None, "request_limit_reached", "request_limit_reached", connection=connection)
                break
            remaining_bytes = selected_limits.max_bytes - run["bytes_used"]
            if remaining_bytes <= 0:
                with _transaction(transaction, 'collection_limit') as connection:
                    self.evidence.advance(run_id, run["checkpoint"], complete=False, connection=connection)
                    self.evidence.issue(run_id, None, "byte_limit_reached", "byte_limit_reached", connection=connection)
                break
            bounded = RunLimits(selected_limits.max_requests - run["requests_used"], 1, 1, remaining_bytes)
            # Check the owner session again before dispatch. The transaction ends
            # before I/O; only its still-owned response may enter an effect scope.
            with _transaction(transaction, 'collection_dispatch'):
                pass
            try:
                batch = collector.collect(manifest, run["checkpoint"], bounded)
            except (EvidenceError, OSError, ValueError, KeyError, TypeError) as error:
                code = error.code if isinstance(error, EvidenceError) else "source_unavailable"
                with _transaction(transaction, 'collection_failed') as connection:
                    self.evidence.issue(run_id, None, code, code, connection=connection)
                break
            if batch.waiting and batch.items:
                raise EvidenceError('invalid_collection_wait')
            if not batch.items:
                with _transaction(transaction, 'collection_frontier') as connection:
                    self.evidence.advance(run_id, batch.next_checkpoint, complete=batch.complete,
                                          waiting=batch.waiting, request_attempts=batch.request_attempts, response_bytes=batch.response_bytes, connection=connection)
                completed_input = batch.complete
                break
            if len(batch.items) != 1:
                with _transaction(transaction, 'collection_failed') as connection:
                    self.evidence.issue(run_id, None, "unsupported_batch_size", "unsupported_batch_size", connection=connection)
                break
            for draft in batch.items:
                observation = None
                try:
                    try:
                        with _transaction(transaction, 'evidence') as connection:
                            observation = self.evidence.save(
                                run_id, run["records_used"], draft, batch.next_checkpoint, complete=batch.complete, connection=connection
                            )
                    except BaseException:
                        if observation is not None:
                            self.evidence.discard_uncommitted(observation)
                        raise
                except EvidenceError as error:
                    with _transaction(transaction, 'collection_failed') as connection:
                        self.evidence.issue(run_id, None, error.code, error.code, connection=connection)
                    return self._report(run_id, False, transaction=transaction)
                if on_commit:
                    on_commit("evidence_committed", observation.id)
                if self._process(observation, None if observation.payload_path else draft.payload, transaction=transaction, admission=admission, policy_version=policy_version) and on_commit:
                    on_commit("canonical_committed", observation.id)
            if batch.complete:
                completed_input = True
                break
            if batch.next_checkpoint.get("halted"):
                # The source already recorded why collection stopped. Do not
                # add a misleading request-limit issue at the same boundary.
                break
        return self._report(run_id, completed_input, transaction=transaction)

    def replay(self, observation_id: str) -> dict[str, Any]:
        observation, payload = self.evidence.load(observation_id)
        _, mapper = self.registry.resolve(observation.adapter_id)
        batch = mapper.normalize(observation, payload)
        result = self.writer.apply(observation.id, batch, f"{observation.adapter_id}:{mapper.version}")
        return {"observation_id": observation_id, **result}
