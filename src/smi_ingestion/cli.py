"""Local command-line entry point for bounded collection and inspection."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from smi_knowledge import Catalog, KnowledgePublications, KnowledgeQueries, KnowledgeStore, QueryScope
from smi_campaigns import Brief, CampaignStore, Selection
from smi_monitoring import MonitoringStore
from smi_tasks import AcquisitionTasks, CompletionInbox, EnrichmentProposal, OfflineRoute, OfflineTaskWorker, TaskAuthority, TaskExecutionLost

from .adapters.registry import default_registry
from .canonical import CanonicalReader, CanonicalWriter
from .contracts import ExternalKey, RunLimits, SourcePolicy
from .db import Database
from .evidence import EvidenceError, EvidenceStore
from .evidence_sets import ActorContext, EvidenceSetReader, SnapshotImporter
from .runner import IngestionRunner
from .support import IngestedEvidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smi-ingest")
    parser.add_argument("--dsn", default=os.environ.get("SMI_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi"))
    parser.add_argument("--schema", default=os.environ.get("SMI_DATABASE_SCHEMA"))
    parser.add_argument("--evidence-dir", type=Path, default=Path(os.environ.get("SMI_EVIDENCE_DIR", ".evidence")))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("manifest", type=Path)
    ingest.add_argument("--max-records", type=int, default=100)
    ingest.add_argument("--max-requests", type=int, default=10)
    ingest.add_argument("--max-bytes", type=int, default=1_048_576)
    resume = commands.add_parser("resume")
    resume.add_argument("run_id")
    replay = commands.add_parser("replay")
    replay.add_argument("observation_id")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("platform")
    inspect.add_argument("namespace")
    inspect.add_argument("kind", choices=["account", "content"])
    inspect.add_argument("native_id")
    inspect.add_argument("--include-synthetic", action="store_true")
    revoke = commands.add_parser("revoke")
    revoke.add_argument("observation_id")
    commands.add_parser("expire")
    commands.add_parser("reconcile")
    snapshot = commands.add_parser("import-snapshot", help="Import a complete local snapshot without source calls")
    snapshot.add_argument("manifest", type=Path)
    snapshot.add_argument("--actor", default="local-builder")
    dataset = commands.add_parser("inspect-set", help="Read pinned evidence with current source policy")
    dataset.add_argument("dataset_id")
    dataset.add_argument("--actor", default="local-builder")
    dataset.add_argument("--purpose", choices=["display", "process"], default="display")
    dataset.add_argument("--include-synthetic", action="store_true")
    catalog = commands.add_parser("register-catalog", help="Register human-supplied Brand/Product references and aliases")
    catalog.add_argument("path", type=Path)
    catalog.add_argument("--actor", default="local-builder")
    preparation = commands.add_parser("prepare-knowledge", help="Prepare provisional rule-based caption interpretations")
    preparation.add_argument("dataset_id")
    preparation.add_argument("catalog_id")
    preparation.add_argument("--actor", default="local-builder")
    preparation.add_argument("--include-synthetic", action="store_true")
    preparation.add_argument("--request-id", default="initial", help="Reuse for retries; choose a new ID for a fresh preparation")
    for command in ("inspect-knowledge", "review-packet"):
        knowledge = commands.add_parser(command)
        knowledge.add_argument("run_id")
        knowledge.add_argument("--actor", default="local-builder")
        knowledge.add_argument("--include-synthetic", action="store_true")
    publication = commands.add_parser("publish-knowledge", help="Publish a bounded selection of ingested run support")
    publication.add_argument("run_id")
    publication.add_argument("--request-id", required=True)
    publication.add_argument("--observation-id", action="append", default=[])
    publication.add_argument("--interpretation-id", action="append", default=[])
    publication.add_argument("--actor", default="local-builder")
    publication.add_argument("--include-synthetic", action="store_true")
    inspect_publication = commands.add_parser("inspect-publication")
    inspect_publication.add_argument("publication_id")
    inspect_publication.add_argument("--actor", default="local-builder")
    inspect_publication.add_argument("--include-synthetic", action="store_true")
    search = commands.add_parser("search-knowledge", help="Search committed permitted knowledge and preserve exact support")
    search.add_argument("--text", default="")
    search.add_argument("--platform", action="append", default=[])
    search.add_argument("--subject-id", action="append", default=[])
    search.add_argument("--captured-from")
    search.add_argument("--captured-to")
    search.add_argument("--max-age-seconds", type=int)
    search.add_argument("--limit", type=int, default=100)
    search.add_argument("--request-id", required=True)
    inspect_query = commands.add_parser("inspect-query", help="Reopen an exact knowledge query result under current policy")
    inspect_query.add_argument("result_id")
    for query_command in (search, inspect_query):
        query_command.add_argument("--actor", default="local-builder")
        query_command.add_argument("--purpose", choices=["display", "process"], default="display")
        query_command.add_argument("--include-synthetic", action="store_true")
    cleanup = commands.add_parser("reconcile-knowledge", help="Purge retained knowledge copies after source policy withdrawal")
    cleanup.add_argument("dataset_id")
    cleanup.add_argument("--actor", default="local-builder")
    cleanup.add_argument("--include-synthetic", action="store_true")
    start_campaign = commands.add_parser("start-campaign", help="Create a human-authored campaign from a brief JSON file")
    start_campaign.add_argument("brief", type=Path)
    revise = commands.add_parser("revise-brief")
    revise.add_argument("campaign_id")
    revise.add_argument("brief", type=Path)
    revise.add_argument("--expected-version", type=int, required=True)
    compare = commands.add_parser("prepare-comparison", help="Prepare a rule-based comparison for an exact brief and knowledge run")
    compare.add_argument("campaign_id")
    compare.add_argument("brief_id")
    compare.add_argument("knowledge_run_id")
    compare.add_argument("--include-synthetic", action="store_true")
    save = commands.add_parser("save-shortlist")
    save.add_argument("comparison_id")
    save.add_argument("selections", type=Path)
    save.add_argument("--confirm", action="store_true")
    save.add_argument("--expected-version", type=int, required=True)
    save.add_argument("--include-synthetic", action="store_true")
    for action in (start_campaign, revise, compare, save):
        action.add_argument("--actor", default="local-marketer")
        action.add_argument("--request-id", required=True)
    for name, field in (("inspect-campaign", "campaign_id"), ("inspect-comparison", "comparison_id"), ("inspect-shortlist", "shortlist_id")):
        inspect_action = commands.add_parser(name)
        inspect_action.add_argument(field)
        inspect_action.add_argument("--actor", default="local-marketer")
        inspect_action.add_argument("--include-synthetic", action="store_true")
    task_submit = commands.add_parser("submit-campaign-task", help="Acknowledge campaign-authorized synthetic offline acquisition")
    task_submit.add_argument("campaign_id")
    task_submit.add_argument("--brief-id", required=True)
    task_submit.add_argument("--purpose", required=True)
    task_submit.add_argument("--request-id", required=True)
    task_submit.add_argument("--offline-manifest", type=Path, required=True)
    task_submit.add_argument("--offline-route-version", default="offline-fixture-v1")
    task_submit.add_argument("--actor", default="local-marketer")
    task_run = commands.add_parser("run-offline-task", help="Execute or resume one fixture-json task; live collectors are unavailable")
    task_run.add_argument("task_id")
    task_run.add_argument("--worker-id", default="local-offline-task-worker")
    task_inspect = commands.add_parser("inspect-task", help="Reopen durable phase/outcome, exact runs and publication links")
    task_inspect.add_argument("task_id")
    task_inspect.add_argument("--actor", default="local-marketer")
    for command in ("list-inbox", "inspect-completion", "reconcile-completions"):
        inbox_action = commands.add_parser(command, help="Reopen or reconcile durable local completion events")
        inbox_action.add_argument("--actor", default="local-marketer")
        inbox_action.add_argument("--workspace-id", default="local")
        if command == "inspect-completion":
            inbox_action.add_argument("event_id")
    proposal_save = commands.add_parser("save-proposal", help="Save a supplied immutable proposal without approving or submitting work")
    proposal_save.add_argument("proposal", type=Path)
    proposal_save.add_argument("--offline-manifest", type=Path, required=True)
    proposal_save.add_argument("--offline-route-version", default="offline-fixture-v1")
    proposal_save.add_argument("--request-id", required=True)
    proposal_save.add_argument("--actor", default="local-assistant")
    proposal_inspect = commands.add_parser("inspect-proposal", help="Review exact proposal scope, limits and human approval")
    proposal_inspect.add_argument("proposal_id")
    proposal_inspect.add_argument("--actor", default="local-marketer")
    proposal_approve = commands.add_parser("approve-proposal", help="Record an explicit operator human approval of the reviewed scope digest")
    proposal_approve.add_argument("proposal_id")
    proposal_approve.add_argument("--scope-digest", required=True)
    proposal_approve.add_argument("--request-id", required=True)
    proposal_approve.add_argument("--approve-exact-scope", action="store_true", required=True)
    proposal_approve.add_argument("--actor", default="local-marketer")
    proposal_submit = commands.add_parser("submit-approved-task", help="Acknowledge only exact saved human-approved scope")
    proposal_submit.add_argument("proposal_id")
    proposal_submit.add_argument("--approval-id", required=True)
    proposal_submit.add_argument("--scope-digest", required=True)
    proposal_submit.add_argument("--request-id", required=True)
    proposal_submit.add_argument("--actor", default="local-assistant")
    args = parser.parse_args(argv)
    try:
        db = Database(args.dsn, args.schema)
        if args.command == "migrate":
            db.migrate()
            KnowledgeStore(db).migrate()
            CampaignStore(db).migrate()
            MonitoringStore(db).migrate()
            AcquisitionTasks(db).migrate()
            result = {"status": "migrated"}
        elif args.command in {"save-proposal", "inspect-proposal", "approve-proposal", "submit-approved-task"}:
            route = OfflineRoute(args.offline_manifest, args.offline_route_version) if args.command == "save-proposal" else None
            authority = TaskAuthority.for_human(args.actor) if args.command == "approve-proposal" else TaskAuthority()
            tasks = AcquisitionTasks(db, route=route, authority=authority)
            kind = "automation" if args.command in {"save-proposal", "submit-approved-task"} else "human"
            actor = ActorContext("local", args.actor, kind)
            if args.command == "save-proposal":
                proposal = EnrichmentProposal.from_document(json.loads(args.proposal.read_text()))
                result = tasks.save_proposal(proposal, actor, request_id=args.request_id)
            elif args.command == "inspect-proposal":
                result = tasks.read_proposal(args.proposal_id, actor)
            elif args.command == "approve-proposal":
                result = tasks.approve_proposal(args.proposal_id, actor, scope_digest=args.scope_digest, request_id=args.request_id)
            else:
                result = tasks.submit_approved(args.proposal_id, actor, approval_id=args.approval_id,
                                               scope_digest=args.scope_digest, request_id=args.request_id)
        elif args.command in {"submit-campaign-task", "run-offline-task", "inspect-task"}:
            if args.command == "run-offline-task":
                result = OfflineTaskWorker(db, args.evidence_dir).run_one(args.task_id, ActorContext("local", args.worker_id, "automation"))
            elif args.command == "submit-campaign-task":
                tasks = AcquisitionTasks(db, route=OfflineRoute(args.offline_manifest, args.offline_route_version), authority=TaskAuthority.for_human(args.actor))
                result = tasks.submit_campaign(args.campaign_id, ActorContext("local", args.actor, "human"),
                                               brief_id=args.brief_id, purpose=args.purpose, request_id=args.request_id)
            else:
                result = AcquisitionTasks(db).read(args.task_id, ActorContext("local", args.actor, "human"))
        elif args.command in {"list-inbox", "inspect-completion", "reconcile-completions"}:
            inbox = CompletionInbox(db, args.workspace_id)
            actor = ActorContext(args.workspace_id, args.actor, "human")
            if args.command == "list-inbox":
                result = inbox.list(actor)
            elif args.command == "inspect-completion":
                result = inbox.read(args.event_id, actor)
            else:
                result = inbox.reconcile(actor)
        elif args.command in {"search-knowledge", "inspect-query"}:
            queries = KnowledgeQueries(db)
            actor = ActorContext("local", args.actor, "human")
            if args.command == "search-knowledge":
                scope = QueryScope(text=args.text, platforms=tuple(args.platform), subject_ids=tuple(args.subject_id),
                                   captured_from=args.captured_from, captured_to=args.captured_to,
                                   max_age_seconds=args.max_age_seconds, limit=args.limit)
                result = queries.search(scope, actor, request_id=args.request_id, purpose=args.purpose, include_synthetic=args.include_synthetic)
            else:
                result = queries.read(args.result_id, actor, purpose=args.purpose, include_synthetic=args.include_synthetic)
        elif args.command in {"publish-knowledge", "inspect-publication"}:
            publications = KnowledgePublications(db)
            actor = ActorContext("local", args.actor, "human")
            if args.command == "publish-knowledge":
                support = IngestedEvidence(db).select_run(args.run_id, actor, include_synthetic=args.include_synthetic)
                if args.observation_id:
                    requested = set(args.observation_id)
                    if not requested <= {r.observation_id for r in support}:
                        raise EvidenceError("publication_observation_not_in_run")
                    support = tuple(r for r in support if r.observation_id in requested)
                result = publications.publish(support, actor, request_id=args.request_id,
                                              interpretation_ids=tuple(args.interpretation_id), include_synthetic=args.include_synthetic)
            else:
                result = publications.read(args.publication_id, actor, include_synthetic=args.include_synthetic)
        elif args.command in {"start-campaign", "revise-brief", "prepare-comparison", "save-shortlist",
                              "inspect-campaign", "inspect-comparison", "inspect-shortlist"}:
            campaigns = CampaignStore(db)
            actor = ActorContext("local", args.actor, "human")
            if args.command == "start-campaign":
                result = campaigns.start(Brief.from_document(json.loads(args.brief.read_text())), actor, request_id=args.request_id)
            elif args.command == "revise-brief":
                result = campaigns.revise_brief(args.campaign_id, Brief.from_document(json.loads(args.brief.read_text())), actor,
                                               expected_version=args.expected_version, request_id=args.request_id)
            elif args.command == "prepare-comparison":
                result = campaigns.prepare_comparison(args.campaign_id, args.brief_id, args.knowledge_run_id, actor,
                                                     request_id=args.request_id, include_synthetic=args.include_synthetic)
            elif args.command == "save-shortlist":
                selection_data = json.loads(args.selections.read_text())
                if not isinstance(selection_data, list):
                    raise EvidenceError("invalid_selection")
                result = campaigns.save_shortlist(args.comparison_id, tuple(Selection.from_document(s) for s in selection_data), actor,
                                                 confirmed=args.confirm, expected_version=args.expected_version, request_id=args.request_id,
                                                 include_synthetic=args.include_synthetic)
            elif args.command == "inspect-campaign":
                result = campaigns.read_campaign(args.campaign_id, actor)
            elif args.command == "inspect-comparison":
                result = campaigns.read_comparison(args.comparison_id, actor, include_synthetic=args.include_synthetic)
            else:
                result = campaigns.read_shortlist(args.shortlist_id, actor, include_synthetic=args.include_synthetic)
        elif args.command in {"register-catalog", "prepare-knowledge", "inspect-knowledge", "review-packet", "reconcile-knowledge"}:
            knowledge = KnowledgeStore(db)
            actor = ActorContext("local", args.actor, "human")
            if args.command == "register-catalog":
                result = knowledge.register_catalog(Catalog.load(args.path), actor)
            elif args.command == "prepare-knowledge":
                result = knowledge.prepare(args.dataset_id, args.catalog_id, actor,
                                           include_synthetic=args.include_synthetic, request_id=args.request_id)
            elif args.command == "inspect-knowledge":
                result = knowledge.read(args.run_id, actor, include_synthetic=args.include_synthetic)
            elif args.command == "review-packet":
                result = knowledge.review_packet(args.run_id, actor, include_synthetic=args.include_synthetic)
            else:
                result = {"status": "reconciled", "purged_interpretations": knowledge.reconcile(
                    args.dataset_id, actor, include_synthetic=args.include_synthetic)}
        else:
            evidence = EvidenceStore(db, args.evidence_dir)
            runner = IngestionRunner(evidence, CanonicalWriter(db), default_registry())
            if args.command == "import-snapshot":
                result = SnapshotImporter(evidence).import_snapshot(
                    args.manifest, ActorContext("local", args.actor, "human"),
                    SourcePolicy("local-development-snapshot", True, True, True),
                )
            elif args.command == "inspect-set":
                result = EvidenceSetReader(db).read(
                    args.dataset_id, ActorContext("local", args.actor, "human"),
                    purpose=args.purpose, include_synthetic=args.include_synthetic,
                )
            elif args.command == "ingest":
                result = runner.ingest(args.manifest, RunLimits(
                    max_requests=args.max_requests, max_records=args.max_records, max_bytes=args.max_bytes
                ))
            elif args.command == "resume":
                result = runner.resume(args.run_id)
            elif args.command == "replay":
                result = runner.replay(args.observation_id)
            elif args.command == "inspect":
                key = ExternalKey(args.platform, args.namespace, args.kind, args.native_id)
                reader = CanonicalReader(db)
                result = {
                    "entity": reader.entity(key, args.include_synthetic),
                    "metrics": reader.metrics(key, args.include_synthetic),
                }
            elif args.command == "revoke":
                evidence.revoke(args.observation_id)
                result = {"status": "revoked", "observation_id": args.observation_id}
            elif args.command == "reconcile":
                result = {"status": "reconciled", "removed_orphan_files": evidence.reconcile_orphans()}
            else:
                result = {"status": "expired", "count": evidence.expire()}
        print(json.dumps(result, ensure_ascii=False, default=str))
        if not isinstance(result, dict):
            return 0
        return 1 if result.get("outcome") == "failure" else 2 if result.get("status") == "partial" else 0
    except (EvidenceError, TaskExecutionLost, ValueError, OSError, KeyError, psycopg.Error) as error:
        code = error.code if isinstance(error, EvidenceError) else 'task_execution_lost' if isinstance(error, TaskExecutionLost) else "database_error" if isinstance(error, psycopg.Error) else "invalid_input"
        print(json.dumps({"status": "failed", "code": code}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
