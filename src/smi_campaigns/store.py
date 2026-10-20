"""Transactional campaign revisions with pinned support and human selection."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .interpretation import ResponsesRoute, ResponsesTransport

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader
from smi_knowledge import KnowledgeStore

from .comparison import METHOD_VERSION, build_comparison, structured_profile
from .contracts import Brief, Selection, require, text


def _digest(document: Any) -> str:
    return hashlib.sha256(json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _request(request_id: str) -> None:
    require(text(request_id) and len(request_id) <= 200, "invalid_campaign_request_id")


class CampaignStore:
    """Own briefs, automated comparisons and immutable human shortlist revisions."""

    def __init__(self, db: Database, workspace_id: str = "local", *, model_route: ResponsesRoute | None = None, model_transport: ResponsesTransport | None = None, model_credential: str | None = None):
        self.db = db
        self.model_route, self.model_transport, self.model_credential = model_route, model_transport, model_credential
        self.workspace_id = workspace_id
        self.knowledge = KnowledgeStore(db, workspace_id)
        self.evidence = EvidenceSetReader(db, workspace_id)

    def migrate(self) -> None:
        """Install campaign tables after ingestion and knowledge migrations."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text())
            connection.execute(Path(__file__).parent.joinpath("planning/schema.sql").read_text())

    def _human(self, actor: ActorContext) -> None:
        actor.require_workspace(self.workspace_id)
        require(actor.kind == "human", "human_action_required")

    def _brief_document(self, brief: Brief, actor: ActorContext) -> dict[str, Any]:
        document = brief.document()
        catalog = self.knowledge.catalog(brief.catalog_id, actor).document
        require(brief.brand_id in {b["id"] for b in catalog["brands"]}, "brief_brand_not_found")
        products = {p["id"]: p for p in catalog["products"]}
        require(all(p in products and products[p]["brand_id"] == brief.brand_id for p in brief.product_ids), "brief_product_scope_invalid")
        return document

    def _campaign(self, connection, campaign_id: str, *, lock: bool = False):
        row = connection.execute("SELECT * FROM campaigns WHERE id=%s AND workspace_id=%s" + (" FOR UPDATE" if lock else ""),
                                 (campaign_id, self.workspace_id)).fetchone()
        if row is None:
            raise EvidenceError("campaign_not_found")
        return row

    def start(self, brief: Brief, actor: ActorContext, *, request_id: str) -> dict[str, Any]:
        """Start one human-authored campaign; the same request/body is retry-safe."""
        self._human(actor)
        _request(request_id)
        document = self._brief_document(brief, actor)
        digest = _digest(document)
        with self.db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"campaign-start:{self.workspace_id}:{request_id}",))
            existing = connection.execute("SELECT * FROM campaigns WHERE workspace_id=%s AND request_id=%s",
                                          (self.workspace_id, request_id)).fetchone()
            if existing:
                require(existing["request_digest"] == digest and existing["owner_id"] == actor.actor_id, "campaign_request_conflict")
                first = connection.execute("SELECT id FROM campaign_briefs WHERE campaign_id=%s AND version=1", (existing["id"],)).fetchone()
                return {"status": "duplicate", "campaign_id": str(existing["id"]), "brief_id": str(first["id"]), "brief_version": 1}
            campaign_id, brief_id = str(uuid.uuid4()), str(uuid.uuid4())
            connection.execute("INSERT INTO campaigns(id,workspace_id,owner_id,request_id,request_digest) VALUES (%s,%s,%s,%s,%s)",
                               (campaign_id, self.workspace_id, actor.actor_id, request_id, digest))
            connection.execute("INSERT INTO campaign_briefs(id,campaign_id,version,document,request_id,request_digest,recorded_by,executable_profile) "
                               "VALUES (%s,%s,1,%s,%s,%s,%s,%s)",
                               (brief_id, campaign_id, Jsonb(document), request_id, digest, actor.actor_id,
                                Jsonb(structured_profile(document, brief_id, 1))))
        return {"status": "created", "campaign_id": campaign_id, "brief_id": brief_id, "brief_version": 1}

    def revise_brief(self, campaign_id: str, brief: Brief, actor: ActorContext, *, expected_version: int, request_id: str) -> dict[str, Any]:
        """Append a brief revision; stale versions and altered retries fail explicitly."""
        self._human(actor)
        _request(request_id)
        require(type(expected_version) is int and expected_version >= 1, "invalid_expected_brief_version")
        document = self._brief_document(brief, actor)
        digest = _digest({"brief": document, "expected_version": expected_version})
        with self.db.connect() as connection:
            campaign = self._campaign(connection, campaign_id, lock=True)
            prior = connection.execute("SELECT * FROM campaign_briefs WHERE campaign_id=%s AND request_id=%s", (campaign_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == digest and prior["recorded_by"] == actor.actor_id, "campaign_request_conflict")
                return {"status": "duplicate", "brief_id": str(prior["id"]), "brief_version": prior["version"]}
            require(campaign["brief_version"] == expected_version, "brief_version_conflict")
            brief_id, version = str(uuid.uuid4()), expected_version + 1
            connection.execute("INSERT INTO campaign_briefs(id,campaign_id,version,document,request_id,request_digest,recorded_by,executable_profile) "
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                               (brief_id, campaign_id, version, Jsonb(document), request_id, digest, actor.actor_id,
                                Jsonb(structured_profile(document, brief_id, version))))
            connection.execute("UPDATE campaigns SET brief_version=%s WHERE id=%s", (version, campaign_id))
        return {"status": "revised", "brief_id": brief_id, "brief_version": version}

    def read_campaign(self, campaign_id: str, actor: ActorContext) -> dict[str, Any]:
        """Reopen current heads and immutable brief history with human attribution."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            campaign = self._campaign(connection, campaign_id)
            briefs = connection.execute("SELECT * FROM campaign_briefs WHERE campaign_id=%s ORDER BY version", (campaign_id,)).fetchall()
            comparisons = connection.execute("SELECT id,brief_id,prepared_at,prepared_by FROM comparison_drafts "
                                             "WHERE campaign_id=%s ORDER BY prepared_at,id", (campaign_id,)).fetchall()
            interpretations = connection.execute("SELECT id FROM campaign_criteria_interpretations WHERE campaign_id=%s ORDER BY recorded_at,id", (campaign_id,)).fetchall()
            shortlists = connection.execute("SELECT id,comparison_id,brief_id,version,status,recorded_by,recorded_at "
                                            "FROM shortlist_revisions WHERE campaign_id=%s ORDER BY version", (campaign_id,)).fetchall()
        return {"campaign_id": campaign_id, "owner_id": campaign["owner_id"], "created_at": campaign["created_at"].isoformat(),
                "brief_version": campaign["brief_version"], "shortlist_version": campaign["shortlist_version"],
                "briefs": [{"id": str(b["id"]), "version": b["version"], "document": b["document"], "executable_profile": b["executable_profile"],
                            "recorded_by": b["recorded_by"], "recorded_at": b["recorded_at"].isoformat()} for b in briefs],
                "interpretations": [self.read_interpretation(str(row["id"]), actor) for row in interpretations],
                "comparisons": [{**row, "id": str(row["id"]), "brief_id": str(row["brief_id"]),
                                 "prepared_at": row["prepared_at"].isoformat()} for row in comparisons],
                "shortlists": [{**row, "id": str(row["id"]), "brief_id": str(row["brief_id"]),
                                "comparison_id": str(row["comparison_id"]), "recorded_at": row["recorded_at"].isoformat()} for row in shortlists]}

    def interpretation_capability(self, actor: ActorContext) -> dict:
        """Inspect explicit server enablement without credentials, I/O or admission."""
        actor.require_workspace(self.workspace_id)
        try:
            require(self.model_route is not None and self.model_transport is not None, 'model_route_unavailable')
            require(text(self.model_credential), 'model_credential_unavailable')
            self.model_route.document()
            require(getattr(self.model_transport, 'execution_mode', 'simulated') == self.model_route.execution_mode,
                    'model_transport_classification_mismatch')
            if self.model_route.execution_mode == 'provider':
                require(getattr(self.model_transport, 'enabled', False) is True, 'model_live_disabled')
            return {'status': 'configured', 'execution_mode': self.model_route.execution_mode, 'reason': None}
        except EvidenceError as error:
            return {'status': 'unavailable', 'execution_mode': None, 'reason': str(error)}

    def read_interpretation(self, interpretation_id: str, actor: ActorContext) -> dict:
        """Reopen exact immutable input, generated profile and sanitized model outcome."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT i.*,b.version,b.document FROM campaign_criteria_interpretations i "
                "JOIN campaigns c ON c.id=i.campaign_id JOIN campaign_briefs b ON b.id=i.brief_id "
                "WHERE i.id=%s AND c.workspace_id=%s", (interpretation_id, self.workspace_id)).fetchone()
        require(row is not None, 'criteria_interpretation_not_found')
        return {'interpretation_id': str(row['id']), 'campaign_id': str(row['campaign_id']),
                'brief_id': str(row['brief_id']), 'brief_version': row['version'], 'status': row['status'], 'reason': row['reason'],
                'request_id': row['request_id'], 'requested_by': row['requested_by'],
                'generated_by': {'actor_id': 'campaign-criteria-model', 'kind': 'automation'},
                'original_input': row['document'].get('original_input'), 'configuration': row['configuration'],
                'operation_id': str(row['operation_id']) if row['operation_id'] else None,
                'usage': row['usage'], 'executable_profile': row['executable_profile'],
                'recorded_at': row['recorded_at'].isoformat(),
                'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None}

    def interpret_criteria(self, campaign_id: str, brief_id: str, actor: ActorContext, *, expected_version: int, request_id: str) -> dict:
        """Save one visible generated addition for an exact human brief; retries never redispatch.

        Claims commit before simulated service I/O. Interrupted claims remain visibly
        in progress with unknown outcome; a new identity is an explicit new operation.
        """
        from smi_costs import UsageAccounting
        from .interpretation import execute, METHOD_VERSION
        self._human(actor)
        _request(request_id)
        digest = _digest({'brief_id': brief_id, 'expected_version': expected_version, 'method': METHOD_VERSION})
        with self.db.connect() as connection:
            self._campaign(connection, campaign_id, lock=True)
            prior = connection.execute('SELECT * FROM campaign_criteria_interpretations WHERE campaign_id=%s AND request_id=%s',
                                       (campaign_id, request_id)).fetchone()
            if prior:
                require(prior['request_digest'] == digest and prior['requested_by'] == actor.actor_id, 'criteria_interpretation_request_conflict')
                return self.read_interpretation(str(prior['id']), actor)
            self.require_current_brief(campaign_id, brief_id, actor, expected_version=expected_version, connection=connection)
            brief = connection.execute('SELECT document FROM campaign_briefs WHERE id=%s', (brief_id,)).fetchone()['document']
            identity = {'interpretation_id': str(uuid.uuid4()), 'brief_id': brief_id, 'brief_version': expected_version}
            connection.execute('INSERT INTO campaign_criteria_interpretations(id,campaign_id,brief_id,request_id,request_digest,requested_by,status) '
                               "VALUES (%s,%s,%s,%s,%s,%s,'in_progress')",
                               (identity['interpretation_id'], campaign_id, brief_id, request_id, digest, actor.actor_id))
        configuration = None
        try:
            require(self.model_route is not None and self.model_transport is not None, 'model_route_unavailable')
            require(text(self.model_credential), 'model_credential_unavailable')
            configuration = self.model_route.document()
            require(getattr(self.model_transport, 'execution_mode', 'simulated') == self.model_route.execution_mode,
                    'model_transport_classification_mismatch')
            if self.model_route.execution_mode == 'provider':
                require(getattr(self.model_transport, 'enabled', False) is True, 'model_live_disabled')
            require(text(brief.get('original_input')), 'model_original_input_missing')
            with self.db.connect() as connection:
                connection.execute('UPDATE campaign_criteria_interpretations SET configuration=%s WHERE id=%s',
                                   (Jsonb(configuration), identity['interpretation_id']))
            def attach_operation(operation_id):
                with self.db.connect() as connection:
                    connection.execute('UPDATE campaign_criteria_interpretations SET operation_id=%s WHERE id=%s',
                                       (operation_id, identity['interpretation_id']))
            worker = ActorContext(self.workspace_id, 'campaign-criteria-model', 'automation')
            outcome = execute(self.model_route, self.model_transport, self.model_credential,
                              UsageAccounting(self.db, self.workspace_id), worker, identity, brief, attach_operation)
        except EvidenceError as error:
            reason = str(error)
            outcome = {'status': 'meter_failure' if reason in {'synthetic_service_bound_violated', 'provider_service_bound_or_meter_violated'} else 'blocked', 'reason': reason}
        except Exception:
            # Provider exception messages may contain prompts/credentials. Retain only a fixed code.
            outcome = {'status': 'transport_uncertain', 'reason': 'model_transport_outcome_unknown'}
        with self.db.connect() as connection:
            campaign = self._campaign(connection, campaign_id, lock=True)
            if outcome['status'] == 'succeeded' and campaign['brief_version'] != expected_version:
                outcome = {**outcome, 'status': 'stale', 'reason': 'brief_version_conflict', 'executable_profile': None}
            connection.execute('UPDATE campaign_criteria_interpretations SET status=%s,reason=%s,configuration=%s,usage=%s,executable_profile=%s,finished_at=now() WHERE id=%s',
                               (outcome['status'], outcome.get('reason'), Jsonb(configuration), Jsonb(outcome.get('usage')),
                                Jsonb(outcome.get('executable_profile')), identity['interpretation_id']))
        return self.read_interpretation(identity['interpretation_id'], actor)

    def require_current_brief(self, campaign_id: str, brief_id: str, actor: ActorContext, *, expected_version: int, connection) -> None:
        """Validate an exact current brief, locking its campaign until the caller commits.

        Dependent admission must use this same transaction. A successor brief
        cannot commit between validation and the dependent write; stale or
        foreign brief identities raise ``brief_version_conflict``.
        """
        actor.require_workspace(self.workspace_id)
        require(type(expected_version) is int and expected_version >= 1, 'invalid_expected_brief_version')
        row = connection.execute(
            'SELECT c.brief_version,b.version FROM campaigns c JOIN campaign_briefs b ON b.campaign_id=c.id '
            'WHERE c.id=%s AND c.workspace_id=%s AND b.id=%s FOR SHARE OF c',
            (campaign_id, self.workspace_id, brief_id),
        ).fetchone()
        require(row is not None and row['brief_version'] == row['version'] == expected_version, 'brief_version_conflict')

    def list_campaigns(self, actor: ActorContext) -> list[dict[str, Any]]:
        """List campaign heads and human brief context, without source-derived explanations."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute("SELECT c.id,c.created_at,c.owner_id,c.brief_version,c.shortlist_version,b.document "
                                      "FROM campaigns c JOIN campaign_briefs b ON b.campaign_id=c.id AND b.version=c.brief_version "
                                      "WHERE c.workspace_id=%s ORDER BY c.created_at DESC,c.id", (self.workspace_id,)).fetchall()
        return [{"campaign_id": str(row["id"]), "created_at": row["created_at"].isoformat(), "owner_id": row["owner_id"],
                 "brief_version": row["brief_version"], "shortlist_version": row["shortlist_version"],
                 "objective": row["document"]["objective"], "brand_id": row["document"]["brand_id"],
                 "target_market": row["document"]["target_market"]} for row in rows]

    def prepare_comparison(
        self, campaign_id: str, brief_id: str, knowledge_run_id: str, actor: ActorContext, *, request_id: str,
        include_synthetic: bool = False, interpretation_id: str | None = None,
    ) -> dict[str, Any]:
        """Prepare a rule-based draft for an exact current brief and knowledge/evidence run."""
        actor.require_workspace(self.workspace_id)
        _request(request_id)
        request = {"brief_id": brief_id, "knowledge_run_id": knowledge_run_id, "method": METHOD_VERSION}
        if interpretation_id is not None:
            request['interpretation_id'] = interpretation_id
        digest = _digest(request)
        with self.db.connect() as connection:
            self._campaign(connection, campaign_id)
            brief_row = connection.execute("SELECT * FROM campaign_briefs WHERE id=%s AND campaign_id=%s", (brief_id, campaign_id)).fetchone()
        require(brief_row is not None, "campaign_brief_not_found")
        document = brief_row['document']
        if interpretation_id is not None:
            interpretation = self.read_interpretation(interpretation_id, actor)
            require(interpretation['campaign_id'] == campaign_id and interpretation['brief_id'] == brief_id
                    and interpretation['status'] == 'succeeded', 'criteria_interpretation_not_executable')
            document = {**document, 'criteria': [{key: value for key, value in criterion.items() if key not in {'importance', 'basis'}}
                                                 for criterion in interpretation['executable_profile']['criteria']]}
        brief = Brief.from_document(document)
        knowledge = self.knowledge.read(knowledge_run_id, actor, purpose="process", include_synthetic=include_synthetic)
        require(knowledge["catalog_id"] == brief.catalog_id, "comparison_catalog_mismatch")
        source = self.evidence.read(knowledge["dataset_id"], actor, purpose="process", include_synthetic=include_synthetic)
        candidates, coverage = build_comparison(brief, source, knowledge)
        with self.db.connect() as connection:
            campaign = self._campaign(connection, campaign_id, lock=True)
            prior = connection.execute("SELECT * FROM comparison_drafts WHERE campaign_id=%s AND request_id=%s", (campaign_id, request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == digest and prior["prepared_by"] == actor.actor_id
                        and prior["actor_kind"] == actor.kind, "comparison_request_conflict")
                return {"status": "duplicate", "comparison_id": str(prior["id"])}
            require(campaign["brief_version"] == brief_row["version"], "brief_version_conflict")
            statuses = self.evidence.statuses(source["dataset_id"], actor, include_synthetic=include_synthetic, connection=connection)
            for candidate in candidates:
                for dependency in candidate["dependencies"]:
                    state = statuses[dependency["observation_id"]]
                    require(state["can_process"] and state["can_retain"] and state["current"], "comparison_support_changed")
            current = self.knowledge.read(knowledge_run_id, actor, purpose="process", include_synthetic=include_synthetic)
            valid_ids = {c["id"] for c in current["interpretations"] if c["state"] == "supported"}
            require(all(d["interpretation_id"] is None or d["interpretation_id"] in valid_ids
                        for c in candidates for d in c["dependencies"]), "comparison_support_changed")
            comparison_id = str(uuid.uuid4())
            connection.execute("INSERT INTO comparison_drafts(id,campaign_id,brief_id,knowledge_run_id,dataset_id,dataset_digest,"
                               "method_version,request_id,request_digest,coverage,prepared_by,actor_kind,criteria_interpretation_id) "
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (comparison_id, campaign_id, brief_id, knowledge_run_id, source["dataset_id"], source["digest"],
                                METHOD_VERSION, request_id, digest, Jsonb(coverage), actor.actor_id, actor.kind, interpretation_id))
            for position, candidate in enumerate(candidates):
                candidate_id = str(uuid.uuid4())
                connection.execute("INSERT INTO comparison_candidates(id,comparison_id,position,account_key,account_id,origin,body) "
                                   "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                   (candidate_id, comparison_id, position, Jsonb(candidate["account_key"]), candidate["account_id"],
                                    candidate["origin"], Jsonb(candidate["body"])))
                for dependency in candidate["dependencies"]:
                    connection.execute("INSERT INTO comparison_support(candidate_id,observation_id,source_assertion_id,interpretation_id) "
                                       "VALUES (%s,%s,%s,%s)",
                                       (candidate_id, dependency["observation_id"], dependency["source_assertion_id"], dependency["interpretation_id"]))
        return {"status": "prepared", "comparison_id": comparison_id, "method": "rule_based", "coverage": coverage}

    def _comparison(self, connection, comparison_id: str):
        row = connection.execute("SELECT d.*,COALESCE(i.executable_profile,b.executable_profile) AS executable_profile FROM comparison_drafts d JOIN campaigns c ON c.id=d.campaign_id "
                                 "JOIN campaign_briefs b ON b.id=d.brief_id LEFT JOIN campaign_criteria_interpretations i ON i.id=d.criteria_interpretation_id "
                                 "WHERE d.id=%s AND c.workspace_id=%s", (comparison_id, self.workspace_id)).fetchone()
        require(row is not None, "comparison_not_found")
        return row

    @staticmethod
    def _support(connection, comparison_id: str):
        return connection.execute("SELECT s.* FROM comparison_support s JOIN comparison_candidates c ON c.id=s.candidate_id "
                                  "WHERE c.comparison_id=%s ORDER BY s.id", (comparison_id,)).fetchall()

    @staticmethod
    def _purge(connection, supports, statuses) -> None:
        affected = {str(s["candidate_id"]) for s in supports if not statuses[str(s["observation_id"])]["can_retain"]}
        if affected:
            connection.execute("UPDATE comparison_candidates SET body=NULL WHERE id=ANY(%s::uuid[])", (list(affected),))
            connection.execute("UPDATE shortlist_selections SET reason=NULL,reason_withdrawn=TRUE WHERE candidate_id=ANY(%s::uuid[])",
                               (list(affected),))

    def read_comparison(self, comparison_id: str, actor: ActorContext, *, purpose: str = "display", include_synthetic: bool = False) -> dict[str, Any]:
        """Read the pinned draft with current source health; denied bodies never reappear from copied reasons."""
        actor.require_workspace(self.workspace_id)
        require(purpose in {"display", "process"}, "invalid_evidence_purpose")
        with self.db.connect() as connection:
            draft = self._comparison(connection, comparison_id)
        knowledge = self.knowledge.read(str(draft["knowledge_run_id"]), actor, purpose=purpose, include_synthetic=include_synthetic)
        claims = {c["id"]: c for c in knowledge["interpretations"] if c["state"] == "supported"}
        with self.db.connect() as connection:
            statuses = self.evidence.statuses(draft["dataset_id"], actor, include_synthetic=include_synthetic, connection=connection)
            supports = self._support(connection, comparison_id)
            self._purge(connection, supports, statuses)
            candidates = connection.execute("SELECT * FROM comparison_candidates WHERE comparison_id=%s ORDER BY position", (comparison_id,)).fetchall()
        output = []
        for candidate in candidates:
            cid = str(candidate["id"])
            dependencies = [s for s in supports if str(s["candidate_id"]) == cid]
            states = [statuses[str(s["observation_id"])] for s in dependencies]
            body = candidate["body"]
            state = "available"
            if body is None or any(not s[f"can_{purpose}"] for s in states):
                state, body = "unavailable", None
            elif any(not s["current"] for s in states):
                state, body = "review_required", None
            elif any(s["interpretation_id"] is not None and str(s["interpretation_id"]) not in claims for s in dependencies):
                state, body = "unavailable", None
            output.append({"candidate_id": cid, "account_key": candidate["account_key"],
                           "account_id": str(candidate["account_id"]) if candidate["account_id"] else None,
                           "origin": candidate["origin"], "support_state": state, "body": body,
                           "evidence": [claims[str(s["interpretation_id"])] for s in dependencies
                                        if state == "available" and s["interpretation_id"] is not None]})
        return {"comparison_id": comparison_id, "campaign_id": str(draft["campaign_id"]), "brief_id": str(draft["brief_id"]),
                "knowledge_run_id": str(draft["knowledge_run_id"]), "dataset_id": draft["dataset_id"], "digest": draft["dataset_digest"],
                "method": "rule_based", "method_version": draft["method_version"], "coverage": draft["coverage"],
                "executable_profile": draft["executable_profile"],
                "criteria_interpretation_id": str(draft["criteria_interpretation_id"]) if draft["criteria_interpretation_id"] else None,
                "prepared_by": draft["prepared_by"], "actor_kind": draft["actor_kind"], "prepared_at": draft["prepared_at"].isoformat(),
                "candidates": output}

    def save_shortlist(
        self, comparison_id: str, selections: tuple[Selection, ...], actor: ActorContext, *,
        confirmed: bool, expected_version: int, request_id: str, include_synthetic: bool = False,
    ) -> dict[str, Any]:
        """Append a human draft/confirmation with retry-safe, expected-version checked persistence."""
        self._human(actor)
        _request(request_id)
        require(type(confirmed) is bool and type(expected_version) is int and expected_version >= 0, "invalid_shortlist_version")
        require(isinstance(selections, tuple) and all(isinstance(s, Selection) for s in selections), "invalid_selection")
        for selection in selections:
            require(text(selection.candidate_id) and (selection.reason is None or text(selection.reason))
                    and isinstance(selection.support_ids, tuple) and all(text(s) for s in selection.support_ids)
                    and isinstance(selection.acknowledged_unknowns, tuple) and all(text(s) for s in selection.acknowledged_unknowns), "invalid_selection")
        require(len({s.candidate_id for s in selections}) == len(selections), "duplicate_selected_account")
        request = {"comparison_id": comparison_id, "confirmed": confirmed, "expected_version": expected_version,
                   "selections": [{"candidate_id": s.candidate_id, "reason": s.reason, "support_ids": sorted(set(s.support_ids)),
                                   "acknowledged_unknowns": sorted(set(s.acknowledged_unknowns))} for s in selections]}
        digest = _digest(request)
        with self.db.connect() as connection:
            draft = self._comparison(connection, comparison_id)
            campaign = self._campaign(connection, str(draft["campaign_id"]), lock=True)
            prior = connection.execute("SELECT * FROM shortlist_revisions WHERE campaign_id=%s AND request_id=%s",
                                       (draft["campaign_id"], request_id)).fetchone()
            if prior:
                require(prior["request_digest"] == digest and prior["recorded_by"] == actor.actor_id, "shortlist_request_conflict")
                return {"status": "duplicate", "shortlist_id": str(prior["id"]), "version": prior["version"]}
            require(campaign["shortlist_version"] == expected_version, "shortlist_version_conflict")
            brief = connection.execute("SELECT version FROM campaign_briefs WHERE id=%s", (draft["brief_id"],)).fetchone()
            require(brief["version"] == campaign["brief_version"], "brief_version_conflict")
            statuses = self.evidence.statuses(draft["dataset_id"], actor, include_synthetic=include_synthetic, connection=connection)
            supports = self._support(connection, comparison_id)
            view = self.read_comparison(comparison_id, actor, include_synthetic=include_synthetic)
            candidates = {c["candidate_id"]: c for c in view["candidates"]}
            for selection in selections:
                require(selection.candidate_id in candidates, "selection_not_in_comparison")
                candidate = candidates[selection.candidate_id]
                body = candidate["body"]
                allowed_ids = {c["id"] for c in candidate["evidence"]}
                require(set(selection.support_ids) <= allowed_ids, "invalid_selection_support")
                require(set(selection.acknowledged_unknowns) <= set(body["unknowns"] if body else []), "invalid_selection_unknowns")
                if confirmed:
                    require(candidate["support_state"] == "available" and body is not None and text(selection.reason), "selection_reason_or_support_unavailable")
                    positive = {sid for j in body["judgments"] if j["state"] == "satisfied" for sid in j["support_ids"]}
                    require(bool(set(selection.support_ids) & positive), "selection_requires_relevance_support")
                    require(set(body["unknowns"]) <= set(selection.acknowledged_unknowns), "selection_unknowns_not_acknowledged")
                    require(not any(j["required"] and (j["state"] == "not_satisfied_on_evidence"
                                or j["state"] == "unknown" and j["unknown_handling"] == "defer") for j in body["judgments"]),
                            "selection_requirement_not_met")
                    require(all(statuses[str(s["observation_id"])]["can_process"] and statuses[str(s["observation_id"])]["can_display"]
                                for s in supports if str(s["candidate_id"]) == selection.candidate_id), "selection_support_not_permitted")
            revision_id, version = str(uuid.uuid4()), expected_version + 1
            connection.execute("INSERT INTO shortlist_revisions(id,campaign_id,brief_id,comparison_id,version,status,request_id,request_digest,recorded_by) "
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (revision_id, draft["campaign_id"], draft["brief_id"], comparison_id, version,
                                "confirmed" if confirmed else "draft", request_id, digest, actor.actor_id))
            for selection in selections:
                retained = all(statuses[str(s["observation_id"])]["can_retain"] for s in supports
                               if str(s["candidate_id"]) == selection.candidate_id)
                connection.execute("INSERT INTO shortlist_selections(id,revision_id,candidate_id,reason,support_ids,acknowledged_unknowns,reason_withdrawn) "
                                   "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                   (str(uuid.uuid4()), revision_id, selection.candidate_id, selection.reason if retained else None,
                                    list(selection.support_ids), Jsonb(list(selection.acknowledged_unknowns)), not retained))
            connection.execute("UPDATE campaigns SET shortlist_version=%s WHERE id=%s", (version, draft["campaign_id"]))
        return {"status": "confirmed" if confirmed else "draft", "shortlist_id": revision_id, "version": version}

    def read_shortlist(self, shortlist_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict[str, Any]:
        """Reopen exact historical membership/reviewer with a current support-health overlay."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            revision = connection.execute("SELECT r.* FROM shortlist_revisions r JOIN campaigns c ON c.id=r.campaign_id "
                                          "WHERE r.id=%s AND c.workspace_id=%s", (shortlist_id, self.workspace_id)).fetchone()
            require(revision is not None, "shortlist_not_found")
        comparison = self.read_comparison(str(revision["comparison_id"]), actor, include_synthetic=include_synthetic)
        candidates = {c["candidate_id"]: c for c in comparison["candidates"]}
        with self.db.connect() as connection:
            rows = connection.execute("SELECT * FROM shortlist_selections WHERE revision_id=%s ORDER BY id", (shortlist_id,)).fetchall()
            campaign = self._campaign(connection, str(revision["campaign_id"]))
        selected = []
        for row in rows:
            candidate = candidates[str(row["candidate_id"])]
            state = "unavailable" if row["reason_withdrawn"] else candidate["support_state"]
            selected.append({"candidate_id": str(row["candidate_id"]), "account_key": candidate["account_key"],
                             "account_id": candidate["account_id"], "reason": row["reason"] if state == "available" else None,
                             "reason_basis": row["reason_basis"], "reason_state": state,
                             "support_ids": [str(s) for s in row["support_ids"]], "acknowledged_unknowns": row["acknowledged_unknowns"],
                             "evidence": [c for c in candidate["evidence"] if c["id"] in {str(s) for s in row["support_ids"]} and state == "available"],
                             "review_required": state != "available"})
        return {"shortlist_id": shortlist_id, "campaign_id": str(revision["campaign_id"]), "brief_id": str(revision["brief_id"]),
                "comparison_id": str(revision["comparison_id"]), "version": revision["version"], "status": revision["status"],
                "recorded_by": revision["recorded_by"], "recorded_at": revision["recorded_at"].isoformat(),
                "current_shortlist_version": campaign["shortlist_version"], "selected": selected,
                "exploratory": True, "review_required": any(s["review_required"] for s in selected)}

    def shortlist_support(self, shortlist_id: str, actor: ActorContext) -> dict[str, Any]:
        """Return content-free pinned dependencies for policy-aware campaign feedback."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            revision = connection.execute("SELECT r.*,d.dataset_id FROM shortlist_revisions r JOIN campaigns c ON c.id=r.campaign_id "
                                          "JOIN comparison_drafts d ON d.id=r.comparison_id WHERE r.id=%s AND c.workspace_id=%s",
                                          (shortlist_id, self.workspace_id)).fetchone()
            require(revision is not None, "shortlist_not_found")
            rows = connection.execute("SELECT DISTINCT s.observation_id,s.source_assertion_id,s.interpretation_id FROM comparison_support s "
                                      "JOIN shortlist_selections selected ON selected.candidate_id=s.candidate_id WHERE selected.revision_id=%s",
                                      (shortlist_id,)).fetchall()
        return {"campaign_id": str(revision["campaign_id"]), "brief_id": str(revision["brief_id"]), "dataset_id": revision["dataset_id"],
                "dependencies": [{key: str(v) if v is not None else None for key, v in row.items()} for row in rows]}
