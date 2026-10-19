"""Knowledge-owned persistence with exact support and source-policy dependencies."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Literal

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader

from .catalog import Catalog
from .extraction import METHOD_VERSION, extract, validate_support


class KnowledgeStore:
    """Persist immutable references and provisional caption interpretations."""

    def __init__(self, db: Database, workspace_id: str = "local"):
        self.db = db
        self.workspace_id = workspace_id
        self.evidence = EvidenceSetReader(db, workspace_id)

    def migrate(self) -> None:
        """Install knowledge-owned tables after the ingestion schema exists."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text())

    def register_catalog(self, catalog: Catalog, actor: ActorContext) -> dict[str, Any]:
        """Register attributable human references; changed catalogs need a new ID."""
        actor.require_workspace(self.workspace_id, importing=True)
        validated = Catalog.from_document(catalog.document)
        if validated.digest != catalog.digest:
            raise EvidenceError("catalog_mutated")
        document = validated.document
        with self.db.connect() as connection:
            # Catalogs can share business IDs, so serialize reference registration per workspace.
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"knowledge-catalog:{self.workspace_id}",))
            existing = connection.execute(
                "SELECT digest FROM knowledge_catalogs WHERE workspace_id=%s AND catalog_id=%s",
                (self.workspace_id, document["catalog_id"]),
            ).fetchone()
            if existing:
                if existing["digest"] != catalog.digest:
                    raise EvidenceError("catalog_version_conflict")
                return {"status": "duplicate", "catalog_id": document["catalog_id"]}
            for group, table, key in (("brands", "knowledge_brands", "brand_id"),
                                      ("products", "knowledge_products", "product_id")):
                for entry in document[group]:
                    # Table/column names are fixed module constants, never catalog values.
                    row = connection.execute(
                        f"SELECT * FROM {table} WHERE workspace_id=%s AND {key}=%s",
                        (self.workspace_id, entry["id"]),
                    ).fetchone()
                    if row:
                        if row["preferred_name"] != entry["name"] or (group == "products" and row["brand_id"] != entry["brand_id"]):
                            raise EvidenceError("knowledge_reference_conflict")
                        continue
                    if group == "brands":
                        connection.execute(
                            "INSERT INTO knowledge_brands(workspace_id,brand_id,preferred_name,recorded_by) VALUES (%s,%s,%s,%s)",
                            (self.workspace_id, entry["id"], entry["name"], actor.actor_id),
                        )
                    else:
                        connection.execute(
                            "INSERT INTO knowledge_products(workspace_id,product_id,brand_id,preferred_name,recorded_by) VALUES (%s,%s,%s,%s,%s)",
                            (self.workspace_id, entry["id"], entry["brand_id"], entry["name"], actor.actor_id),
                        )
            connection.execute(
                "INSERT INTO knowledge_catalogs(workspace_id,catalog_id,digest,document,recorded_by) VALUES (%s,%s,%s,%s,%s)",
                (self.workspace_id, document["catalog_id"], catalog.digest, Jsonb(document), actor.actor_id),
            )
        return {"status": "registered", "catalog_id": document["catalog_id"], "digest": catalog.digest}

    def catalog(self, catalog_id: str, actor: ActorContext) -> Catalog:
        """Read the exact registered interpretation configuration in the actor's workspace."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT document FROM knowledge_catalogs WHERE workspace_id=%s AND catalog_id=%s",
                (self.workspace_id, catalog_id),
            ).fetchone()
        if row is None:
            raise EvidenceError("knowledge_catalog_not_found")
        return Catalog.from_document(row["document"])

    def list_catalogs(self, actor: ActorContext) -> list[dict[str, Any]]:
        """List registered human configuration metadata within the actor's workspace."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute("SELECT catalog_id,digest,recorded_by,recorded_at FROM knowledge_catalogs "
                                      "WHERE workspace_id=%s ORDER BY recorded_at,catalog_id", (self.workspace_id,)).fetchall()
        return [{**row, "recorded_at": row["recorded_at"].isoformat()} for row in rows]

    def reconcile(self, dataset_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> int:
        """Purge retained interpretation values/excerpts whose support no longer permits retention."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            statuses = self.evidence.statuses(dataset_id, actor, include_synthetic=include_synthetic, connection=connection)
            withdrawn = [obs for obs, state in statuses.items() if not state["can_retain"]]
            if not withdrawn:
                return 0
            result = connection.execute(
                "UPDATE knowledge_assertions a SET value=NULL,excerpt=NULL,support_state='withdrawn' "
                "FROM knowledge_runs r WHERE r.id=a.run_id AND r.workspace_id=%s AND r.dataset_id=%s "
                "AND a.observation_id=ANY(%s::uuid[]) AND a.support_state<>'withdrawn'",
                (self.workspace_id, dataset_id, withdrawn),
            )
            return result.rowcount

    def prepare(
        self, dataset_id: str, catalog_id: str, actor: ActorContext, *, include_synthetic: bool = False,
        request_id: str = "initial",
    ) -> dict[str, Any]:
        """Prepare one immutable request; use a new request ID for an explicit refresh."""
        actor.require_workspace(self.workspace_id)
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError("invalid_preparation_request_id")
        catalog = self.catalog(catalog_id, actor)
        source = self.evidence.read(dataset_id, actor, purpose="process", include_synthetic=include_synthetic)
        self.reconcile(dataset_id, actor, include_synthetic=include_synthetic)
        prepared = []
        coverage = {"dataset_digest": source["digest"], "members": source["coverage"]["total_members"],
                    "processed": 0, "unavailable": 0, "not_retained": 0, "superseded": 0}
        for member in source["members"]:
            if member["availability"] != "available":
                coverage["unavailable"] += 1
                continue
            if not member["policy"]["can_retain"]:
                coverage["not_retained"] += 1
                continue
            if member["support_status"] != "current":
                coverage["superseded"] += 1
                continue
            caption = next((a for a in member["assertions"] if a["field"] == "caption" and a["state"] == "observed"), None)
            if caption is None:
                coverage["unavailable"] += 1
                continue
            claims = extract(caption["value"], catalog)
            for claim in claims:
                validate_support(claim, caption["value"])
            prepared.append((member, caption, claims))
            coverage["processed"] += 1
        with self.db.connect() as connection:
            key = f"knowledge:{self.workspace_id}:{dataset_id}:{catalog_id}:{METHOD_VERSION}:{request_id}"
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (key,))
            existing = connection.execute(
                "SELECT id FROM knowledge_runs WHERE workspace_id=%s AND dataset_id=%s AND catalog_id=%s "
                "AND method_version=%s AND request_id=%s",
                (self.workspace_id, dataset_id, catalog_id, METHOD_VERSION, request_id),
            ).fetchone()
            if existing:
                return {"status": "duplicate", "run_id": str(existing["id"]), "request_id": request_id}
            statuses = self.evidence.statuses(dataset_id, actor, include_synthetic=include_synthetic, connection=connection)
            for member, _, _ in prepared:
                state = statuses[member["observation_id"]]
                if not (state["can_process"] and state["can_retain"] and state["current"]):
                    raise EvidenceError("knowledge_support_changed")
            run_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO knowledge_runs(id,workspace_id,dataset_id,catalog_id,method_version,request_id,recorded_by,coverage) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (run_id, self.workspace_id, dataset_id, catalog_id, METHOD_VERSION, request_id, actor.actor_id, Jsonb(coverage)),
            )
            for member, caption, claims in prepared:
                for claim in claims:
                    connection.execute(
                        "INSERT INTO knowledge_assertions(id,run_id,subject_id,source_assertion_id,observation_id,"
                        "predicate,value,basis,span_start,span_end,excerpt) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (str(uuid.uuid4()), run_id, caption["subject_id"], caption["assertion_id"], member["observation_id"],
                         claim.predicate, Jsonb(claim.value), "derived", claim.start, claim.end, claim.excerpt),
                    )
        return {"status": "prepared", "run_id": run_id, "method_version": METHOD_VERSION, "request_id": request_id,
                "interpretations": sum(len(claims) for _, _, claims in prepared), "coverage": coverage}

    def read(
        self, run_id: str, actor: ActorContext, *, purpose: Literal["display", "process"] = "display",
        include_synthetic: bool = False,
    ) -> dict[str, Any]:
        """Read supported interpretations or tombstones after policy cleanup; never substitute support."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            run = connection.execute("SELECT * FROM knowledge_runs WHERE id=%s AND workspace_id=%s",
                                     (run_id, self.workspace_id)).fetchone()
        if run is None:
            raise EvidenceError("knowledge_run_not_found")
        self.reconcile(run["dataset_id"], actor, include_synthetic=include_synthetic)
        source = self.evidence.read(run["dataset_id"], actor, purpose=purpose, include_synthetic=include_synthetic)
        members = {m["observation_id"]: m for m in source["members"]}
        with self.db.connect() as connection:
            rows = connection.execute("SELECT * FROM knowledge_assertions WHERE run_id=%s ORDER BY observation_id,span_start,predicate,id",
                                      (run_id,)).fetchall()
        output = []
        for row in rows:
            member = members[str(row["observation_id"])]
            item = {"id": str(row["id"]), "subject_id": str(row["subject_id"]),
                    "source_assertion_id": str(row["source_assertion_id"]), "observation_id": str(row["observation_id"])}
            if row["support_state"] == "withdrawn" or member["availability"] != "available":
                item.update(state="unavailable", reason="source_support_withdrawn_or_denied")
            elif member["support_status"] != "current":
                item.update(state="review_required", reason="source_support_superseded")
            else:
                item.update(state="supported", predicate=row["predicate"], value=row["value"], basis=row["basis"],
                            span={"start": row["span_start"], "end": row["span_end"], "text": row["excerpt"]},
                            review_status=row["review_status"], source_reference=member["source_reference"],
                            captured_at=member["captured_at"],
                            published_at=next((a["value"] for a in member["assertions"] if a["field"] == "published_at" and a["state"] == "observed"), None),
                            recorded_at=row["recorded_at"].isoformat())
            output.append(item)
        return {"run_id": run_id, "dataset_id": run["dataset_id"], "catalog_id": run["catalog_id"],
                "method_version": run["method_version"], "request_id": run["request_id"], "recorded_by": run["recorded_by"],
                "recorded_at": run["recorded_at"].isoformat(), "preparation_coverage": run["coverage"],
                "current_coverage": source["coverage"], "interpretations": output}

    def review_packet(self, run_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict[str, Any]:
        """Generate a policy-checked review packet; translations and human labels begin pending."""
        result = self.read(run_id, actor, include_synthetic=include_synthetic)
        source = self.evidence.read(result["dataset_id"], actor, include_synthetic=include_synthetic)
        items = []
        for member in source["members"]:
            supported = [a for a in result["interpretations"] if a["observation_id"] == member["observation_id"] and a["state"] == "supported"]
            if member["availability"] != "available" or not member["policy"]["can_retain"]:
                items.append({"observation_id": member["observation_id"], "state": "unavailable"})
                continue
            caption = next((a for a in member["assertions"] if a["field"] == "caption" and a["state"] == "observed"), None)
            if caption is None:
                continue
            items.append({"observation_id": member["observation_id"], "source_reference": member["source_reference"],
                          "source_assertion_id": caption["assertion_id"], "original_caption": caption["value"],
                          "support_status": member["support_status"],
                          "proposed_interpretations": supported, "translation": None, "translator_method": None,
                          "review": {"label": None, "material": None, "reviewer": None, "ambiguity": None}})
        return {"rubric": "caption-support-review-v1", "method_version": result["method_version"],
                "dataset_id": source["dataset_id"], "digest": source["digest"],
                "review_status": "pending_translation_assisted_review", "reference_provenance": "provisional_development_set",
                "labels": ["supported", "unsupported", "ambiguous", "not_assessable"], "items": items,
                "synthetic_challenges": [
                    {"caption": "ヒーロークッションは使っていません。", "case": "negation", "expected_limit": "Mention does not imply use or endorsement."},
                    {"caption": "ヒーロークッションとブラッククッションを比較。", "case": "comparison", "expected_limit": "Two mentions do not identify a winner."},
                    {"caption": "ヒーロークッションかもしれない。", "case": "uncertainty", "expected_limit": "Literal matching cannot resolve uncertain product identity."},
                ]}
