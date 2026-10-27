"""Transactional investigation and insight storage with live source-policy overlays."""

import hashlib
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader
from smi_knowledge import KnowledgeStore

from .contracts import InvestigationScope, require, text
from .recent import RecentMonitoring
from .alerts import QuantitativeAlerts
from .summary import LIMITS, METHOD_VERSION, build_summary


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def request_id_valid(request_id):
    require(text(request_id) and len(request_id) <= 200, "invalid_monitoring_request_id")


class MonitoringStore:
    """Own independent saved scopes and immutable, rule-based snapshot answers."""

    def __init__(self, db: Database, workspace_id: str = "local"):
        self.db = db
        self.workspace_id = workspace_id
        self.knowledge = KnowledgeStore(db, workspace_id)
        self.evidence = EvidenceSetReader(db, workspace_id)

    def migrate(self) -> None:
        """Install monitoring tables after ingestion and knowledge migrations."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text())
        QuantitativeAlerts(RecentMonitoring(self.db, self.workspace_id)).migrate()

    def _human(self, actor):
        actor.require_workspace(self.workspace_id)
        require(actor.kind == "human", "human_action_required")

    def _scope(self, scope, actor):
        document = scope.document()
        catalog = self.knowledge.catalog(scope.catalog_id, actor).document
        for field, group in (("brand_ids", "brands"), ("product_ids", "products"), ("topic_ids", "topics")):
            require(set(document[field]) <= {entry["id"] for entry in catalog[group]}, "investigation_reference_not_found")
        return document

    def _investigation(self, connection, investigation_id, *, lock=False):
        row = connection.execute("SELECT * FROM monitoring_investigations WHERE id=%s AND workspace_id=%s" + (" FOR UPDATE" if lock else ""),
                                 (investigation_id, self.workspace_id)).fetchone()
        require(row is not None, "investigation_not_found")
        return row

    def start(self, scope: InvestigationScope, actor: ActorContext, *, request_id: str):
        """Start an attributable investigation without any campaign side effect."""
        self._human(actor)
        request_id_valid(request_id)
        document = self._scope(scope, actor)
        hashed = digest(document)
        with self.db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"monitoring:{self.workspace_id}:{request_id}",))
            prior = connection.execute("SELECT * FROM monitoring_investigations WHERE workspace_id=%s AND request_id=%s",
                                       (self.workspace_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == hashed and prior["owner_id"] == actor.actor_id, "monitoring_request_conflict")
                first = connection.execute("SELECT id FROM investigation_scopes WHERE investigation_id=%s AND version=1", (prior["id"],)).fetchone()
                return {"status": "duplicate", "investigation_id": str(prior["id"]), "scope_id": str(first["id"]), "scope_version": 1}
            investigation_id, scope_id = str(uuid.uuid4()), str(uuid.uuid4())
            connection.execute("INSERT INTO monitoring_investigations(id,workspace_id,owner_id,request_id,request_digest) VALUES (%s,%s,%s,%s,%s)",
                               (investigation_id, self.workspace_id, actor.actor_id, request_id, hashed))
            connection.execute("INSERT INTO investigation_scopes(id,investigation_id,version,document,request_id,request_digest,recorded_by) "
                               "VALUES (%s,%s,1,%s,%s,%s,%s)", (scope_id, investigation_id, Jsonb(document), request_id, hashed, actor.actor_id))
        return {"status": "created", "investigation_id": investigation_id, "scope_id": scope_id, "scope_version": 1}

    def revise_scope(self, investigation_id, scope: InvestigationScope, actor: ActorContext, *, expected_version: int, request_id: str):
        """Append a scope; changed requests or stale heads cannot overwrite history."""
        self._human(actor)
        request_id_valid(request_id)
        require(type(expected_version) is int and expected_version >= 1, "invalid_scope_version")
        document = self._scope(scope, actor)
        hashed = digest({"scope": document, "expected_version": expected_version})
        with self.db.connect() as connection:
            current = self._investigation(connection, investigation_id, lock=True)
            prior = connection.execute("SELECT * FROM investigation_scopes WHERE investigation_id=%s AND request_id=%s", (investigation_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == hashed and prior["recorded_by"] == actor.actor_id, "monitoring_request_conflict")
                return {"status": "duplicate", "scope_id": str(prior["id"]), "scope_version": prior["version"]}
            require(current["scope_version"] == expected_version, "scope_version_conflict")
            scope_id, version = str(uuid.uuid4()), expected_version + 1
            connection.execute("INSERT INTO investigation_scopes(id,investigation_id,version,document,request_id,request_digest,recorded_by) "
                               "VALUES (%s,%s,%s,%s,%s,%s,%s)", (scope_id, investigation_id, version, Jsonb(document), request_id, hashed, actor.actor_id))
            connection.execute("UPDATE monitoring_investigations SET scope_version=%s WHERE id=%s", (version, investigation_id))
        return {"status": "revised", "scope_id": scope_id, "scope_version": version}

    def list_investigations(self, actor: ActorContext):
        """List workspace-scoped questions/heads without source-derived finding text."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute("SELECT i.*,s.document FROM monitoring_investigations i JOIN investigation_scopes s "
                                      "ON s.investigation_id=i.id AND s.version=i.scope_version WHERE i.workspace_id=%s ORDER BY i.created_at DESC,i.id",
                                      (self.workspace_id,)).fetchall()
        return [{"investigation_id": str(row["id"]), "question": row["document"]["question"], "market_context": row["document"]["market_context"],
                 "scope_version": row["scope_version"], "insight_version": row["insight_version"], "owner_id": row["owner_id"]} for row in rows]

    def read_investigation(self, investigation_id, actor: ActorContext):
        """Reopen exact scope/answer history with attribution and current head versions."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = self._investigation(connection, investigation_id)
            scopes = connection.execute("SELECT * FROM investigation_scopes WHERE investigation_id=%s ORDER BY version", (investigation_id,)).fetchall()
            insights = connection.execute("SELECT id,scope_id,version,prepared_at,prepared_by FROM insight_revisions WHERE investigation_id=%s ORDER BY version",
                                          (investigation_id,)).fetchall()
        return {"investigation_id": investigation_id, "owner_id": row["owner_id"], "scope_version": row["scope_version"], "insight_version": row["insight_version"],
                "scopes": [{"id": str(s["id"]), "version": s["version"], "document": s["document"], "recorded_by": s["recorded_by"],
                            "recorded_at": s["recorded_at"].isoformat()} for s in scopes],
                "insights": [{**r, "id": str(r["id"]), "scope_id": str(r["scope_id"]), "prepared_at": r["prepared_at"].isoformat()} for r in insights]}

    def prepare_insight(self, investigation_id, scope_id, knowledge_run_id, actor: ActorContext, *, expected_version: int, request_id: str,
                        include_synthetic: bool = False):
        """Append a pinned answer with commit-time policy/current support checks."""
        actor.require_workspace(self.workspace_id)
        request_id_valid(request_id)
        require(type(expected_version) is int and expected_version >= 0, "invalid_insight_version")
        with self.db.connect() as connection:
            self._investigation(connection, investigation_id)
            scope_row = connection.execute("SELECT * FROM investigation_scopes WHERE id=%s AND investigation_id=%s", (scope_id, investigation_id)).fetchone()
        require(scope_row is not None, "investigation_scope_not_found")
        scope = InvestigationScope.from_document(scope_row["document"])
        knowledge = self.knowledge.read(knowledge_run_id, actor, purpose="process", include_synthetic=include_synthetic)
        require(scope.catalog_id == knowledge["catalog_id"], "insight_catalog_mismatch")
        source = self.evidence.read(knowledge["dataset_id"], actor, purpose="process", include_synthetic=include_synthetic)
        catalog = self.knowledge.catalog(scope.catalog_id, actor).document
        findings, coverage = build_summary(scope, source, knowledge, catalog)
        hashed = digest({"scope_id": scope_id, "knowledge_run_id": knowledge_run_id, "expected_version": expected_version, "method": METHOD_VERSION})
        with self.db.connect() as connection:
            current = self._investigation(connection, investigation_id, lock=True)
            prior = connection.execute("SELECT * FROM insight_revisions WHERE investigation_id=%s AND request_id=%s", (investigation_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == hashed and prior["prepared_by"] == actor.actor_id and prior["actor_kind"] == actor.kind, "insight_request_conflict")
                return {"status": "duplicate", "insight_id": str(prior["id"]), "version": prior["version"]}
            require(current["scope_version"] == scope_row["version"], "scope_version_conflict")
            require(current["insight_version"] == expected_version, "insight_version_conflict")
            statuses = self.evidence.statuses(source["dataset_id"], actor, include_synthetic=include_synthetic, connection=connection)
            for finding in findings:
                for dependency in finding["dependencies"]:
                    state = statuses[dependency["observation_id"]]
                    require(state["can_process"] and state["can_retain"] and state["current"], "insight_support_changed")
            checked = self.knowledge.read(knowledge_run_id, actor, purpose="process", include_synthetic=include_synthetic)
            valid = {c["id"] for c in checked["interpretations"] if c["state"] == "supported"}
            require(all(d["interpretation_id"] is None or d["interpretation_id"] in valid for f in findings for d in f["dependencies"]), "insight_support_changed")
            insight_id, version = str(uuid.uuid4()), expected_version + 1
            limits = LIMITS + (["Requested caption language is not assessable; no language-filtered subset is asserted."] if scope.caption_language else [])
            connection.execute("INSERT INTO insight_revisions(id,investigation_id,scope_id,version,knowledge_run_id,dataset_id,dataset_digest,method_version,"
                               "coverage,limitations,request_id,request_digest,prepared_by,actor_kind) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (insight_id, investigation_id, scope_id, version, knowledge_run_id, source["dataset_id"], source["digest"], METHOD_VERSION,
                                Jsonb(coverage), Jsonb(limits), request_id, hashed, actor.actor_id, actor.kind))
            for position, finding in enumerate(findings):
                finding_id = str(uuid.uuid4())
                connection.execute("INSERT INTO insight_findings(id,insight_id,position,body) VALUES (%s,%s,%s,%s)",
                                   (finding_id, insight_id, position, Jsonb(finding["body"])))
                for d in finding["dependencies"]:
                    connection.execute("INSERT INTO insight_support(finding_id,observation_id,source_assertion_id,interpretation_id) VALUES (%s,%s,%s,%s)",
                                       (finding_id, d["observation_id"], d["source_assertion_id"], d["interpretation_id"]))
            connection.execute("UPDATE monitoring_investigations SET insight_version=%s WHERE id=%s", (version, investigation_id))
        return {"status": "prepared", "insight_id": insight_id, "version": version, "coverage": coverage}

    def read_insight(self, insight_id, actor: ActorContext, *, purpose: str = "display", include_synthetic: bool = False):
        """Return immutable findings or policy/review tombstones, never substitute evidence."""
        actor.require_workspace(self.workspace_id)
        require(purpose in {"display", "process"}, "invalid_evidence_purpose")
        with self.db.connect() as connection:
            row = connection.execute("SELECT r.* FROM insight_revisions r JOIN monitoring_investigations i ON i.id=r.investigation_id "
                                     "WHERE r.id=%s AND i.workspace_id=%s", (insight_id, self.workspace_id)).fetchone()
        require(row is not None, "insight_not_found")
        knowledge = self.knowledge.read(str(row["knowledge_run_id"]), actor, purpose=purpose, include_synthetic=include_synthetic)
        claims = {c["id"]: c for c in knowledge["interpretations"] if c["state"] == "supported"}
        with self.db.connect() as connection:
            statuses = self.evidence.statuses(row["dataset_id"], actor, include_synthetic=include_synthetic, connection=connection)
            support = connection.execute("SELECT s.* FROM insight_support s JOIN insight_findings f ON f.id=s.finding_id WHERE f.insight_id=%s ORDER BY s.id", (insight_id,)).fetchall()
            withdrawn = {str(s["finding_id"]) for s in support if not statuses[str(s["observation_id"])]["can_retain"]}
            if withdrawn:
                connection.execute("UPDATE insight_findings SET body=NULL WHERE id=ANY(%s::uuid[])", (list(withdrawn),))
            findings = connection.execute("SELECT * FROM insight_findings WHERE insight_id=%s ORDER BY position", (insight_id,)).fetchall()
        output = []
        for finding in findings:
            deps = [s for s in support if s["finding_id"] == finding["id"]]
            states = [statuses[str(s["observation_id"])] for s in deps]
            state = "available"
            if finding["body"] is None or any(not s[f"can_{purpose}"] for s in states):
                state = "unavailable"
            elif any(not s["current"] for s in states):
                state = "review_required"
            elif any(s["interpretation_id"] is not None and str(s["interpretation_id"]) not in claims for s in deps):
                state = "unavailable"
            output.append({"finding_id": str(finding["id"]), "support_state": state, "body": finding["body"] if state == "available" else None,
                           "evidence": [claims[str(s["interpretation_id"])] for s in deps if state == "available" and s["interpretation_id"] is not None]})
        coverage = dict(row["coverage"])
        if any(f["support_state"] != "available" for f in output):
            coverage["actual_observation_ids"] = None
        coverage["matching_membership_state"] = "available" if coverage["actual_observation_ids"] is not None else "unavailable"
        return {"insight_id": insight_id, "investigation_id": str(row["investigation_id"]), "scope_id": str(row["scope_id"]), "version": row["version"],
                "knowledge_run_id": str(row["knowledge_run_id"]), "dataset_id": row["dataset_id"], "digest": row["dataset_digest"],
                "method": "rule_based", "method_version": row["method_version"], "coverage": coverage, "limitations": row["limitations"],
                "prepared_by": row["prepared_by"], "actor_kind": row["actor_kind"], "prepared_at": row["prepared_at"].isoformat(), "findings": output,
                "review_status": "provisional", "review_required": any(f["support_state"] != "available" for f in output)}
