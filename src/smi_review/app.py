"""Application routes composing public stores, without owning decision rules."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import psycopg

from smi_costs import UsageAccounting
from smi_campaigns import Brief, CampaignStore, Criterion, Selection
from smi_campaigns.interpretation import ResponsesRoute, ResponsesTransport
from smi_campaigns.planning import CampaignPlanning, DecisionNote, MeasurementPlan
from smi_ingestion.contracts import ExternalKey
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader
from smi_knowledge import KnowledgePublications, KnowledgeQueries, KnowledgeStore
from smi_monitoring import MonitoringStore
from smi_tasks import AcquisitionTasks, CompletionInbox, EnrichmentProposal, OfflineRoute, TaskAuthority

from . import cost_views, inbox_views, monitoring_views, planning_views, proposal_views, publication_views, query_views, task_views, views
from .forms import identifier, one


@dataclass(frozen=True)
class Response:
    """A rendered page, fixed asset or redirect for the HTTP boundary."""

    status: int
    body: bytes = b""
    content_type: str = "text/html; charset=utf-8"
    location: str | None = None


def brief_from_form(form: dict[str, list[str]]) -> Brief:
    """Parse explicit human fields; actor and confirmation fields are rejected."""
    count = int(one(form, "criterion_count"))
    if not 1 <= count <= 30:
        raise EvidenceError("invalid_brief.criteria")
    allowed = {"csrf", "request_id", "expected_version", "criterion_count", "catalog_id", "brand_id", "product_ids",
               "objective", "target_market", "platforms", "known_accounts", "publication_from", "publication_to",
               "campaign_dates", "budget", "currency", "audience_detail", "original_input"}
    columns = {"id", "label", "kind", "value", "required", "operator", "unknown_handling"}
    allowed.update(f"criterion_{i}_{column}" for i in range(count) for column in columns)
    if not form.keys() <= allowed:
        raise EvidenceError("invalid_form")
    criteria = tuple(Criterion(
        one(form, f"criterion_{i}_id"), one(form, f"criterion_{i}_label"), one(form, f"criterion_{i}_kind"),
        one(form, f"criterion_{i}_value").strip() or None, one(form, f"criterion_{i}_required") == "yes",
        one(form, f"criterion_{i}_operator"), one(form, f"criterion_{i}_unknown_handling"),
    ) for i in range(count))
    accounts = []
    for line in one(form, "known_accounts").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 3:
            raise EvidenceError("invalid_brief.known_account")
        accounts.append(ExternalKey(parts[0], parts[1], "account", parts[2]))
    return Brief(one(form, "catalog_id"), one(form, "brand_id"), tuple(form.get("product_ids", [])),
                 one(form, "objective"), one(form, "target_market"),
                 tuple(p.strip() for p in one(form, "platforms").split(",") if p.strip()), criteria, tuple(accounts),
                 {key: one(form, key).strip() or None for key in ("campaign_dates", "budget", "currency", "audience_detail")},
                 one(form, "publication_from").strip() or None, one(form, "publication_to").strip() or None,
                 one(form, "original_input") or None)


def selections_from_form(form: dict[str, list[str]]) -> tuple[Selection, ...]:
    """Parse selected candidates and their individually cited/acknowledged review inputs."""
    allowed = {"csrf", "request_id", "expected_version", "selected", "action", "reviewed", "source_shortlist_id"}
    for key in form:
        if key in allowed:
            continue
        prefix, separator, suffix = key.partition("_")
        if not separator or prefix not in {"reason", "support", "unknown", "position"}:
            raise EvidenceError("invalid_form")
        identifier(suffix)
    selected = form.get('selected', [])
    if one(form, 'source_shortlist_id'):
        positions = [int(one(form, 'position_' + cid)) for cid in selected]
        if any(p < 1 for p in positions) or len(set(positions)) != len(positions):
            raise EvidenceError('invalid_selection_order')
        selected = [cid for _, cid in sorted(zip(positions, selected))]
    return tuple(Selection(identifier(cid), one(form, f"reason_{cid}").strip() or None,
                           tuple(form.get(f"support_{cid}", [])), tuple(form.get(f"unknown_{cid}", [])))
                 for cid in selected)


class ReviewApp:
    """One trusted local marketer's browser application; all saves go through domain stores."""

    def __init__(self, db: Database, actor_id: str = "local-marketer", workspace_id: str = "local", *, offline_route: OfflineRoute | None = None,
                 model_route: ResponsesRoute | None = None, model_transport: ResponsesTransport | None = None, model_credential: str | None = None):
        self.actor = ActorContext(workspace_id, actor_id, "human")
        self.actor.require_workspace(workspace_id)
        self.worker = ActorContext(workspace_id, "local-rule-preparation", "automation")
        self.campaigns = CampaignStore(db, workspace_id, model_route=model_route, model_transport=model_transport, model_credential=model_credential)
        self.knowledge = KnowledgeStore(db, workspace_id)
        self.publications = KnowledgePublications(db, workspace_id)
        self.queries = KnowledgeQueries(db, workspace_id)
        self.evidence = EvidenceSetReader(db, workspace_id)
        self.monitoring = MonitoringStore(db, workspace_id)
        self.planning = CampaignPlanning(db, workspace_id)
        self.tasks = AcquisitionTasks(db, workspace_id, route=offline_route, authority=TaskAuthority.for_human(actor_id))
        self.inbox = CompletionInbox(db, workspace_id)
        self.costs = UsageAccounting(db, workspace_id, task_attribution=self.tasks.resolve_cost_attribution)
        self.csrf = secrets.token_urlsafe(32)

    def page(self, title: str, content: str, status: int = 200) -> Response:
        return Response(status, views.page(title, content, self.actor.actor_id).encode())

    def _campaign(self, campaign_id: str):
        campaign = self.campaigns.read_campaign(campaign_id, self.actor)
        return campaign, campaign["briefs"][-1]

    def _campaign_page(self, campaign_id, submitted=None, error=None, status=200):
        campaign, current = self._campaign(campaign_id)
        capability = self.campaigns.interpretation_capability(self.actor)
        return self.page("Campaign", views.campaign_page(campaign, current, self.evidence.list_sets(self.actor), self.csrf,
                                                         model_configured=capability['status'] == 'configured', model_mode=capability['execution_mode'], submitted=submitted, error=error), status)

    def _brief_page(self, campaign_id: str | None, query, submitted=None, error=None, status=200):
        campaign, current = self._campaign(campaign_id) if campaign_id else (None, None)
        catalogs = self.knowledge.list_catalogs(self.actor)
        catalog_id = one(submitted, "catalog_id") if submitted else one(query, "catalog_id", current["document"]["catalog_id"] if current else "")
        if not catalog_id and catalogs:
            catalog_id = catalogs[0]["catalog_id"]
        if not catalog_id:
            return self.page("Create a brief", views.empty_inputs(), status)
        catalog = self.knowledge.catalog(catalog_id, self.actor).document
        return self.page("Revise brief" if campaign else "Create a brief",
                         views.brief_form(catalog, catalogs, self.csrf, campaign, current, submitted, error), status)

    def _comparison_page(self, comparison_id, query, submitted=None, error=None, status=200):
        comparison = self.campaigns.read_comparison(comparison_id, self.actor)
        campaign, _ = self._campaign(comparison["campaign_id"])
        brief = next(b for b in campaign["briefs"] if b["id"] == comparison["brief_id"])
        source = comparison["knowledge_query"] or self.evidence.read(comparison["dataset_id"], self.actor)
        previous = None
        source_shortlist_id = one(submitted, 'source_shortlist_id') if submitted is not None else one(query, 'shortlist_id')
        if source_shortlist_id:
            previous = self.campaigns.read_shortlist(identifier(source_shortlist_id), self.actor)
            if previous["comparison_id"] != comparison_id:
                raise EvidenceError("selection_not_in_comparison")
        return self.page("Review comparison", views.comparison_page(comparison, campaign, brief, source, self.csrf,
                                                                    previous, submitted, error), status)

    def _scope_page(self, investigation_id, query, submitted=None, error=None, status=200):
        investigation = self.monitoring.read_investigation(investigation_id, self.actor) if investigation_id else None
        current = investigation["scopes"][-1] if investigation else None
        catalogs = self.knowledge.list_catalogs(self.actor)
        catalog_id = one(submitted, "catalog_id") if submitted else one(query, "catalog_id", current["document"]["catalog_id"] if current else "")
        if not catalog_id and catalogs:
            catalog_id = catalogs[0]["catalog_id"]
        if not catalog_id:
            return self.page("Create investigation", views.empty_inputs(), status)
        catalog = self.knowledge.catalog(catalog_id, self.actor).document
        return self.page("Investigation scope", monitoring_views.scope_form(catalog, catalogs, self.csrf, investigation, current, submitted, error), status)

    def _planning_page(self, campaign_id, submitted=None, kind=None, error=None, status=200):
        campaign, current = self._campaign(campaign_id)
        records = self.planning.read(campaign_id, self.actor)
        if submitted is not None and kind == "note":
            try:
                selected = self.campaigns.read_shortlist(identifier(one(submitted, "shortlist_id")), self.actor)
                if selected["campaign_id"] != campaign_id or selected["review_required"]:
                    submitted = {**submitted, "text": [""]}
            except (EvidenceError, ValueError):
                submitted = {**submitted, "text": [""]}
        return self.page("Measurement and learning", planning_views.planning_page(campaign, current, records, self.csrf, submitted, kind, error), status)

    def _task_page(self, campaign_id, submitted=None, error=None, status=200):
        campaign, brief = self._campaign(campaign_id)
        if submitted:
            brief = next((b for b in campaign['briefs'] if b['id'] == one(submitted, 'brief_id')), brief)
        return self.page("Submit offline acquisition", task_views.submit_form(campaign, brief, self.csrf, self.tasks.route, submitted, error), status)

    def handle(self, method: str, target: str, form: dict[str, list[str]] | None = None) -> Response:
        """Route validated requests; surface sanitized errors and preserve recoverable edits."""
        parsed = urlsplit(target)
        path, query = parsed.path, parse_qs(parsed.query, keep_blank_values=True)
        try:
            if method == "GET":
                return self._get(path, query)
            if method == "POST" and form is not None:
                return self._post(path, form)
            return self.page("Request unavailable", views.error_message("invalid_form"), 405)
        except (EvidenceError, ValueError, psycopg.Error) as error:
            code = error.code if isinstance(error, EvidenceError) else "database_unavailable" if isinstance(error, psycopg.Error) else "invalid_form"
            status = 503 if isinstance(error, psycopg.Error) else 404 if code.endswith("not_found") else 409 if "conflict" in code else 422
            if method == "POST" and form is not None and not isinstance(error, psycopg.Error):
                try:
                    if path == "/proposals":
                        return self.page("Supply enrichment proposal", proposal_views.supplied_form(self.csrf, self.tasks.route, form, code), status)
                    match = re.fullmatch(r"/proposals/([^/]+)/approve", path)
                    if match:
                        proposal = self.tasks.read_proposal(identifier(match[1]), self.actor)
                        return self.page("Review enrichment proposal", proposal_views.detail(proposal, self.csrf, form, code), status)
                    match = re.fullmatch(r"/campaigns/([^/]+)/tasks", path)
                    if match:
                        return self._task_page(identifier(match[1]), form, code, status)
                    if path == "/knowledge/search":
                        return self.page("Search current knowledge", query_views.search_form(self.csrf, form, code), status)
                    if path == "/campaigns":
                        return self._brief_page(None, {}, form, code, status)
                    match = re.fullmatch(r"/campaigns/([^/]+)/(?:interpretations|current-comparisons|recommendations|ranked-recommendations)", path)
                    if match:
                        return self._campaign_page(identifier(match[1]), form, code, status)
                    match = re.fullmatch(r"/campaigns/([^/]+)/briefs", path)
                    if match:
                        return self._brief_page(identifier(match[1]), {}, form, code, status)
                    match = re.fullmatch(r"/comparisons/([^/]+)/shortlists", path)
                    if match:
                        return self._comparison_page(identifier(match[1]), {}, form, code, status)
                    if path == "/investigations":
                        return self._scope_page(None, {}, form, code, status)
                    match = re.fullmatch(r"/investigations/([^/]+)/scopes", path)
                    if match:
                        return self._scope_page(identifier(match[1]), {}, form, code, status)
                    match = re.fullmatch(r"/campaigns/([^/]+)/(plans|notes)", path)
                    if match:
                        return self._planning_page(identifier(match[1]), form, "plan" if match[2] == "plans" else "note", code, status)
                except (EvidenceError, ValueError, psycopg.Error):
                    pass
            return self.page("Action needs attention", views.error_message(code), status)

    def _get(self, path, query):
        if path == "/costs":
            return self.page("Usage and costs", cost_views.index(self.costs.list(self.actor)))
        match = re.fullmatch(r"/costs/([^/]+)", path)
        if match:
            return self.page("Cost detail", cost_views.detail(self.costs.read(identifier(match[1]), self.actor)))
        match = re.fullmatch(r"/tasks/([^/]+)/costs", path)
        if match:
            task = self.tasks.read(identifier(match[1]), self.actor)
            return self.page("Task costs", cost_views.index(self.costs.list(self.actor, task_id=task['task_id'])))
        if path == "/inbox":
            return self.page("Completion inbox", inbox_views.index(self.inbox.list(self.actor)))
        match = re.fullmatch(r"/inbox/([^/]+)", path)
        if match:
            return self.page("Task completion", inbox_views.detail(self.inbox.read(identifier(match[1]), self.actor)))
        if path == "/proposals":
            return self.page("Enrichment proposals", proposal_views.index(self.tasks.list_proposals(self.actor)))
        if path == "/proposals/new":
            return self.page("Supply enrichment proposal", proposal_views.supplied_form(self.csrf, self.tasks.route))
        match = re.fullmatch(r"/proposals/([^/]+)", path)
        if match:
            return self.page("Review enrichment proposal", proposal_views.detail(self.tasks.read_proposal(identifier(match[1]), self.actor), self.csrf))
        if path == "/tasks":
            return self.page("Acquisition tasks", task_views.index(self.tasks.list(self.actor)))
        match = re.fullmatch(r"/tasks/([^/]+)", path)
        if match:
            task = self.tasks.read(identifier(match[1]), self.actor)
            return self.page("Offline acquisition task", task_views.detail(task)
                             + cost_views.task_summary(self.costs.list(self.actor, task_id=task['task_id'])))
        match = re.fullmatch(r"/campaigns/([^/]+)/tasks/new", path)
        if match:
            return self._task_page(identifier(match[1]))
        if path == "/knowledge/search":
            return self.page("Search current knowledge", query_views.search_form(self.csrf))
        match = re.fullmatch(r"/knowledge/results/([^/]+)", path)
        if match:
            include_synthetic = one(query, "include_synthetic") == "yes"
            return self.page("Saved knowledge search", query_views.detail(
                self.queries.read(identifier(match[1]), self.actor, include_synthetic=include_synthetic), include_synthetic=include_synthetic))
        if path == "/knowledge/publications":
            return self.page("Knowledge publications", publication_views.index(self.publications.list(self.actor)))
        match = re.fullmatch(r"/knowledge/publications/([^/]+)", path)
        if match:
            return self.page("Knowledge publication", publication_views.detail(self.publications.read(identifier(match[1]), self.actor, include_synthetic=one(query, "include_synthetic") == "yes")))
        if path == "/investigations":
            return self.page("Market investigations", monitoring_views.index(self.monitoring.list_investigations(self.actor)))
        if path == "/investigations/new":
            return self._scope_page(None, query)
        match = re.fullmatch(r"/investigations/([^/]+)(/edit)?", path)
        if match:
            investigation_id = identifier(match[1])
            if match[2]:
                return self._scope_page(investigation_id, query)
            investigation = self.monitoring.read_investigation(investigation_id, self.actor)
            return self.page("Investigation", monitoring_views.investigation_page(investigation, self.evidence.list_sets(self.actor), self.csrf))
        match = re.fullmatch(r"/insights/([^/]+)", path)
        if match:
            insight = self.monitoring.read_insight(identifier(match[1]), self.actor)
            investigation = self.monitoring.read_investigation(insight["investigation_id"], self.actor)
            scope = next(s for s in investigation["scopes"] if s["id"] == insight["scope_id"])
            source = self.evidence.read(insight["dataset_id"], self.actor)
            return self.page("Snapshot insight", monitoring_views.insight_page(insight, scope, source))
        match = re.fullmatch(r"/campaigns/([^/]+)/planning", path)
        if match:
            return self._planning_page(identifier(match[1]))
        if path in {"/static/review.css", "/static/review.js"}:
            asset = Path(__file__).with_name("static") / path.rsplit("/", 1)[1]
            return Response(200, asset.read_bytes(), "text/css; charset=utf-8" if path.endswith(".css") else "text/javascript; charset=utf-8")
        if path == "/":
            return self.page("Campaign workspace", views.home(self.campaigns.list_campaigns(self.actor),
                                                              self.evidence.list_sets(self.actor), self.knowledge.list_catalogs(self.actor)))
        if path == "/campaigns/new":
            return self._brief_page(None, query)
        match = re.fullmatch(r"/campaigns/([^/]+)(/edit)?", path)
        if match:
            campaign_id = identifier(match[1])
            if match[2]:
                return self._brief_page(campaign_id, query)
            return self._campaign_page(campaign_id)
        match = re.fullmatch(r"/comparisons/([^/]+)", path)
        if match:
            return self._comparison_page(identifier(match[1]), query)
        match = re.fullmatch(r"/shortlists/([^/]+)", path)
        if match:
            shortlist = self.campaigns.read_shortlist(identifier(match[1]), self.actor)
            campaign, _ = self._campaign(shortlist["campaign_id"])
            brief = next(b for b in campaign["briefs"] if b["id"] == shortlist["brief_id"])
            comparison = self.campaigns.read_comparison(shortlist["comparison_id"], self.actor)
            source = comparison["knowledge_query"] or self.evidence.read(comparison["dataset_id"], self.actor)
            return self.page("Saved shortlist", views.shortlist_page(shortlist, brief, comparison, source))
        raise EvidenceError("record_not_found")

    def _post(self, path, form):
        if not secrets.compare_digest(one(form, "csrf").encode(), self.csrf.encode()):
            raise EvidenceError("invalid_form")
        request_id = one(form, "request_id")
        if path == "/proposals":
            if not form.keys() <= {"csrf", "request_id", "purpose", "intent", "subject_ids", "search_queries"}:
                raise EvidenceError("invalid_form")
            proposal = EnrichmentProposal(one(form, "purpose"), one(form, "intent"),
                tuple(v.strip() for v in one(form, "subject_ids").splitlines() if v.strip()),
                tuple(v.strip() for v in one(form, "search_queries").splitlines() if v.strip()))
            saved = self.tasks.save_proposal(proposal, self.actor, request_id=request_id)
            return Response(303, location=f"/proposals/{saved['proposal_id']}")
        match = re.fullmatch(r"/proposals/([^/]+)/approve", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "scope_digest", "reviewed"}:
                raise EvidenceError("invalid_form")
            if one(form, "reviewed") != "yes":
                raise EvidenceError("proposal_human_approval_required")
            proposal_id = identifier(match[1])
            approval = self.tasks.approve_proposal(proposal_id, self.actor, scope_digest=one(form, "scope_digest"), request_id=request_id)
            submitted = self.tasks.submit_approved(proposal_id, self.actor, approval_id=approval['approval_id'],
                scope_digest=one(form, "scope_digest"), request_id=request_id)
            return Response(303, location=f"/tasks/{submitted['task_id']}")
        match = re.fullmatch(r"/campaigns/([^/]+)/tasks", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "brief_id", "purpose"}:
                raise EvidenceError("invalid_form")
            submitted = self.tasks.submit_campaign(identifier(match[1]), self.actor, brief_id=identifier(one(form, "brief_id")),
                                                    purpose=one(form, "purpose"), request_id=request_id)
            return Response(303, location=f"/tasks/{submitted['task_id']}")
        if path == "/knowledge/search":
            include_synthetic = one(form, "include_synthetic") == "yes"
            result = self.queries.search(query_views.scope_from_form(form), self.actor, request_id=request_id, include_synthetic=include_synthetic)
            suffix = "?include_synthetic=yes" if include_synthetic else ""
            return Response(303, location=f"/knowledge/results/{result['result_id']}{suffix}")
        if path == "/investigations" or re.fullmatch(r"/investigations/[^/]+/scopes", path):
            scope = monitoring_views.scope_from_form(form)
            if path == "/investigations":
                result = self.monitoring.start(scope, self.actor, request_id=request_id)
                investigation_id = result["investigation_id"]
            else:
                investigation_id = identifier(path.split("/")[2])
                self.monitoring.revise_scope(investigation_id, scope, self.actor, expected_version=int(one(form, "expected_version")), request_id=request_id)
            return Response(303, location=f"/investigations/{investigation_id}")
        match = re.fullmatch(r"/investigations/([^/]+)/insights", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "scope_id", "dataset_id", "expected_version"}:
                raise EvidenceError("invalid_form")
            investigation_id, scope_id = identifier(match[1]), identifier(one(form, "scope_id"))
            investigation = self.monitoring.read_investigation(investigation_id, self.actor)
            scope = next((s for s in investigation["scopes"] if s["id"] == scope_id), None)
            if scope is None:
                raise EvidenceError("investigation_scope_not_found")
            run = self.knowledge.prepare(one(form, "dataset_id"), scope["document"]["catalog_id"], self.worker, request_id=f"monitoring:{request_id}")
            prepared = self.monitoring.prepare_insight(investigation_id, scope_id, run["run_id"], self.worker,
                                                       expected_version=int(one(form, "expected_version")), request_id=request_id)
            return Response(303, location=f"/insights/{prepared['insight_id']}")
        match = re.fullmatch(r"/campaigns/([^/]+)/(plans|notes)", path)
        if match:
            campaign_id, shortlist_id = identifier(match[1]), identifier(one(form, "shortlist_id"))
            context = {"csrf", "request_id", "expected_version", "shortlist_id", "brief_id"}
            if match[2] == "plans":
                if not form.keys() <= context | MeasurementPlan.__dataclass_fields__.keys():
                    raise EvidenceError("invalid_form")
                fields = {key: one(form, key).strip() or None for key in MeasurementPlan.__dataclass_fields__ if key not in {"product_ids", "gaps"}}
                fields.update(product_ids=[s.strip() for s in one(form, "product_ids").split(",") if s.strip()],
                              gaps=[s.strip() for s in one(form, "gaps").splitlines() if s.strip()])
                self.planning.save_plan(campaign_id, identifier(one(form, "brief_id")), shortlist_id, MeasurementPlan.from_document(fields), self.actor,
                                        expected_version=int(one(form, "expected_version")), request_id=request_id)
            else:
                if not form.keys() <= context | {"text"}:
                    raise EvidenceError("invalid_form")
                self.planning.add_note(campaign_id, shortlist_id, DecisionNote(one(form, "text")), self.actor,
                                       expected_version=int(one(form, "expected_version")), request_id=request_id)
            return Response(303, location=f"/campaigns/{campaign_id}/planning")
        if path == "/campaigns":
            created = self.campaigns.start(brief_from_form(form), self.actor, request_id=request_id)
            return Response(303, location=f"/campaigns/{created['campaign_id']}")
        match = re.fullmatch(r"/campaigns/([^/]+)/briefs", path)
        if match:
            campaign_id = identifier(match[1])
            self.campaigns.revise_brief(campaign_id, brief_from_form(form), self.actor,
                                        expected_version=int(one(form, "expected_version")), request_id=request_id)
            return Response(303, location=f"/campaigns/{campaign_id}")
        match = re.fullmatch(r"/campaigns/([^/]+)/interpretations", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "brief_id", "expected_version"}:
                raise EvidenceError("invalid_form")
            campaign_id = identifier(match[1])
            self.campaigns.interpret_criteria(campaign_id, identifier(one(form, "brief_id")), self.actor,
                                              expected_version=int(one(form, "expected_version")), request_id=request_id)
            return Response(303, location=f"/campaigns/{campaign_id}")
        match = re.fullmatch(r"/campaigns/([^/]+)/(recommendations|ranked-recommendations)", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "brief_id", "interpretation_id", "expected_brief_version", "expected_shortlist_version"}:
                raise EvidenceError("invalid_form")
            recommend = self.campaigns.recommend_ranked if match[2] == "ranked-recommendations" else self.campaigns.recommend
            saved = recommend(identifier(match[1]), identifier(one(form, "brief_id")), self.worker,
                expected_brief_version=int(one(form, "expected_brief_version")),
                expected_shortlist_version=int(one(form, "expected_shortlist_version")), request_id=request_id,
                interpretation_id=identifier(one(form, "interpretation_id")) if one(form, "interpretation_id") else None)
            return Response(303, location=f"/shortlists/{saved['shortlist_id']}" if saved.get("shortlist_id") else f"/campaigns/{match[1]}")
        match = re.fullmatch(r"/campaigns/([^/]+)/current-comparisons", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "brief_id", "interpretation_id"}:
                raise EvidenceError("invalid_form")
            prepared = self.campaigns.prepare_current_comparison(identifier(match[1]), identifier(one(form, "brief_id")),
                                                                 self.worker, request_id=request_id,
                                                                 interpretation_id=identifier(one(form, "interpretation_id")) if one(form, "interpretation_id") else None)
            return Response(303, location=f"/comparisons/{prepared['comparison_id']}")
        match = re.fullmatch(r"/campaigns/([^/]+)/comparisons", path)
        if match:
            if not form.keys() <= {"csrf", "request_id", "brief_id", "dataset_id", "interpretation_id"}:
                raise EvidenceError("invalid_form")
            campaign_id = identifier(match[1])
            campaign, _ = self._campaign(campaign_id)
            brief_id = identifier(one(form, "brief_id"))
            brief = next((b for b in campaign["briefs"] if b["id"] == brief_id), None)
            if brief is None:
                raise EvidenceError("campaign_brief_not_found")
            run = self.knowledge.prepare(one(form, "dataset_id"), brief["document"]["catalog_id"], self.worker,
                                         request_id=f"review:{request_id}")
            prepared = self.campaigns.prepare_comparison(campaign_id, brief_id, run["run_id"], self.worker, request_id=request_id,
                                                         interpretation_id=identifier(one(form, "interpretation_id")) if one(form, "interpretation_id") else None)
            return Response(303, location=f"/comparisons/{prepared['comparison_id']}")
        match = re.fullmatch(r"/comparisons/([^/]+)/shortlists", path)
        if match:
            action = one(form, "action")
            if action not in {"draft", "confirm"}:
                raise EvidenceError("invalid_form")
            if action == "confirm" and one(form, "reviewed") != "yes":
                raise EvidenceError("human_review_acknowledgement_required")
            result = self.campaigns.save_shortlist(identifier(match[1]), selections_from_form(form), self.actor,
                                                    confirmed=action == "confirm", expected_version=int(one(form, "expected_version")),
                                                    request_id=request_id,
                                                    source_shortlist_id=identifier(one(form, 'source_shortlist_id')) if one(form, 'source_shortlist_id') else None)
            return Response(303, location=f"/shortlists/{result['shortlist_id']}")
        raise EvidenceError("record_not_found")
