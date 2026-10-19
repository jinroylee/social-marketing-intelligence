"""Human planning revisions with pinned campaign context and dependent note cleanup."""

import hashlib
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader
from smi_knowledge import KnowledgeStore

from ..contracts import require, text
from ..store import CampaignStore
from .contracts import DecisionNote, MeasurementPlan


def hashed(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


class CampaignPlanning:
    """Persist proposed plans and immutable human notes, never commercial outcomes."""

    def __init__(self, db: Database, workspace_id: str = "local"):
        self.db = db
        self.workspace_id = workspace_id
        self.campaigns = CampaignStore(db, workspace_id)
        self.evidence = EvidenceSetReader(db, workspace_id)
        self.knowledge = KnowledgeStore(db, workspace_id)

    def migrate(self):
        """Install planning records after campaign tables exist."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text())

    def _write_context(self, actor, expected_version, request_id):
        actor.require_workspace(self.workspace_id)
        require(actor.kind == "human", "human_action_required")
        require(type(expected_version) is int and expected_version >= 0, "invalid_planning_version")
        require(text(request_id) and len(request_id) <= 200, "invalid_planning_request_id")

    def _campaign(self, connection, campaign_id, *, lock=False):
        row = connection.execute("SELECT * FROM campaigns WHERE id=%s AND workspace_id=%s" + (" FOR UPDATE" if lock else ""),
                                 (campaign_id, self.workspace_id)).fetchone()
        require(row is not None, "campaign_not_found")
        return row

    @staticmethod
    def _head(connection, table, campaign_id):
        # Table names come only from fixed method constants, never submitted fields.
        return connection.execute(f"SELECT coalesce(max(version),0) AS version FROM {table} WHERE campaign_id=%s", (campaign_id,)).fetchone()["version"]

    def save_plan(self, campaign_id, brief_id, shortlist_id, plan: MeasurementPlan, actor: ActorContext, *, expected_version: int, request_id: str):
        """Append proposed intent for an exact current brief/relevant shortlist."""
        self._write_context(actor, expected_version, request_id)
        document = plan.document()
        reference = self.campaigns.shortlist_support(shortlist_id, actor)
        require(reference["campaign_id"] == campaign_id and reference["brief_id"] == brief_id, "planning_reference_mismatch")
        hashed_request = hashed({"brief_id": brief_id, "shortlist_id": shortlist_id, "plan": document, "expected_version": expected_version})
        with self.db.connect() as connection:
            campaign = self._campaign(connection, campaign_id, lock=True)
            prior = connection.execute("SELECT * FROM measurement_plan_revisions WHERE campaign_id=%s AND request_id=%s", (campaign_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == hashed_request and prior["recorded_by"] == actor.actor_id, "planning_request_conflict")
                return {"status": "duplicate", "plan_id": str(prior["id"]), "version": prior["version"]}
            require(self._head(connection, "measurement_plan_revisions", campaign_id) == expected_version, "measurement_plan_version_conflict")
            brief = connection.execute("SELECT * FROM campaign_briefs WHERE id=%s AND campaign_id=%s", (brief_id, campaign_id)).fetchone()
            require(brief is not None, "campaign_brief_not_found")
            require(brief["version"] == campaign["brief_version"], "brief_version_conflict")
            catalog = self.knowledge.catalog(brief["document"]["catalog_id"], actor).document
            allowed = {p["id"] for p in catalog["products"] if p["brand_id"] == brief["document"]["brand_id"]}
            require(set(plan.product_ids) <= allowed and (not brief["document"]["product_ids"] or set(plan.product_ids) <= set(brief["document"]["product_ids"])), "measurement_product_scope_invalid")
            plan_id, version = str(uuid.uuid4()), expected_version + 1
            connection.execute("INSERT INTO measurement_plan_revisions(id,campaign_id,brief_id,shortlist_id,version,document,request_id,request_digest,recorded_by) "
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (plan_id, campaign_id, brief_id, shortlist_id, version, Jsonb(document), request_id, hashed_request, actor.actor_id))
        return {"status": "proposed", "plan_id": plan_id, "version": version}

    def add_note(self, campaign_id, shortlist_id, note: DecisionNote, actor: ActorContext, *, expected_version: int, request_id: str):
        """Append feedback with cited selected-set support and conservative copied-text policy."""
        self._write_context(actor, expected_version, request_id)
        document = note.document()
        reference = self.campaigns.shortlist_support(shortlist_id, actor)
        require(reference["campaign_id"] == campaign_id, "planning_reference_mismatch")
        hashed_request = hashed({"shortlist_id": shortlist_id, "note": document, "expected_version": expected_version})
        with self.db.connect() as connection:
            self._campaign(connection, campaign_id, lock=True)
            prior = connection.execute("SELECT * FROM decision_note_revisions WHERE campaign_id=%s AND request_id=%s", (campaign_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == hashed_request and prior["recorded_by"] == actor.actor_id, "planning_request_conflict")
                return {"status": "duplicate", "note_id": str(prior["id"]), "version": prior["version"]}
            require(self._head(connection, "decision_note_revisions", campaign_id) == expected_version, "decision_note_version_conflict")
            statuses = self.evidence.statuses(reference["dataset_id"], actor, connection=connection)
            for dependency in reference["dependencies"]:
                state = statuses[dependency["observation_id"]]
                require(state["can_process"] and state["can_display"] and state["can_retain"] and state["current"], "decision_note_support_unavailable")
            shortlist = self.campaigns.read_shortlist(shortlist_id, actor)
            require(not shortlist["review_required"], "decision_note_support_unavailable")
            allowed = {claim["id"] for selected in shortlist["selected"] for claim in selected["evidence"]}
            require(set(note.support_ids) <= allowed, "invalid_decision_note_support")
            note_id, version = str(uuid.uuid4()), expected_version + 1
            connection.execute("INSERT INTO decision_note_revisions(id,campaign_id,shortlist_id,version,text,support_ids,request_id,request_digest,recorded_by) "
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (note_id, campaign_id, shortlist_id, version, note.text, list(document["support_ids"]), request_id, hashed_request, actor.actor_id))
            for d in reference["dependencies"]:
                connection.execute("INSERT INTO decision_note_support(note_id,observation_id,source_assertion_id,interpretation_id) VALUES (%s,%s,%s,%s)",
                                   (note_id, d["observation_id"], d["source_assertion_id"], d["interpretation_id"]))
        return {"status": "recorded", "note_id": note_id, "version": version}

    def read(self, campaign_id, actor: ActorContext):
        """Read immutable plan/note history with current-policy text overlays and cleanup."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            self._campaign(connection, campaign_id)
            plans = connection.execute("SELECT * FROM measurement_plan_revisions WHERE campaign_id=%s ORDER BY version", (campaign_id,)).fetchall()
            notes = connection.execute("SELECT * FROM decision_note_revisions WHERE campaign_id=%s ORDER BY version", (campaign_id,)).fetchall()
        output = []
        for note in notes:
            reference = self.campaigns.shortlist_support(str(note["shortlist_id"]), actor)
            shortlist = self.campaigns.read_shortlist(str(note["shortlist_id"]), actor)
            with self.db.connect() as connection:
                statuses = self.evidence.statuses(reference["dataset_id"], actor, connection=connection)
                dependencies = connection.execute("SELECT observation_id FROM decision_note_support WHERE note_id=%s", (note["id"],)).fetchall()
                states = [statuses[str(d["observation_id"])] for d in dependencies]
                if any(not state["can_retain"] for state in states):
                    connection.execute("UPDATE decision_note_revisions SET text=NULL WHERE id=%s", (note["id"],))
                    note["text"] = None
            state = "available"
            if note["text"] is None or any(not s["can_display"] for s in states):
                state = "unavailable"
            elif any(not s["current"] for s in states) or shortlist["review_required"]:
                state = "review_required"
            output.append({"note_id": str(note["id"]), "shortlist_id": str(note["shortlist_id"]), "version": note["version"], "basis": note["basis"],
                           "text": note["text"] if state == "available" else None, "support_state": state, "support_ids": [str(s) for s in note["support_ids"]],
                           "recorded_by": note["recorded_by"], "recorded_at": note["recorded_at"].isoformat()})
        return {"campaign_id": campaign_id, "plan_version": plans[-1]["version"] if plans else 0, "note_version": notes[-1]["version"] if notes else 0,
                "plans": [{"plan_id": str(p["id"]), "brief_id": str(p["brief_id"]), "shortlist_id": str(p["shortlist_id"]), "version": p["version"],
                           "document": p["document"], "status": p["status"], "outcome_access": "not_verified", "outcomes": None,
                           "recorded_by": p["recorded_by"], "recorded_at": p["recorded_at"].isoformat()} for p in plans], "notes": output}
