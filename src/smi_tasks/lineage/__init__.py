"""Read-only task lineage assembled from public owner contracts."""

from typing import Any

from smi_costs import UsageAccounting
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgePublications

from ..store import AcquisitionTasks


# Collectors may supply arbitrary exception codes. Only installed operational
# reasons belong in this source-free view; exception text is never evidence.
_FAILURE_CODES = frozenset({'normalization_failed', 'source_unavailable', 'input_changed', 'offline_input_unavailable',
    'processing_not_permitted', 'record_limit_reached', 'request_limit_reached', 'byte_limit_reached',
    'incomplete_input', 'publication_support_unavailable', 'publication_request_conflict',
    'ingested_support_not_found', 'evidence_unavailable', 'replay_unavailable', 'unsupported_task_route',
    'discovery_selection_unassessable', 'supplementary_source_failure', 'provider_snapshot_failed',
    'provider_snapshot_canceled', 'provider_snapshot_pending_limit'})
_COVERAGE_KEYS = ('collected_observations', 'ingested_observations', 'published_members', 'quarantined_observations',
    'requested_inputs', 'remaining_inputs', 'requests_used', 'bytes_used', 'eligible_members', 'unchanged_members',
    'unpublished_members', 'ineligible_observations', 'returned_records', 'eligible_records', 'admitted_records',
    'failed_records', 'published_records', 'unchanged_records', 'retrieval_skipped')


class TaskLineage:
    """Reopen one task's bounded historical effects and current support/cost state.

    This projection stores nothing, executes no source/model work and needs no
    route configuration, payload files or credentials. Historical publication
    counts never assert current permission. Source wording stays with governed
    evidence pages; only content-free identity, methods and coverage appear here.
    Reads across owners are independent committed frontiers, not an atomic
    pipeline snapshot while a worker is running.
    """

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db, self.workspace_id = db, workspace_id

    def read(self, task_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict[str, Any]:
        """Read exact authority, attempts/runs, receipted publications and costs.

        Explicit synthetic visibility permits simulated source dates/support
        navigation; otherwise its historical linkage remains metadata only.
        Unknown costs retain unknown coverage and are never added across scopes.
        """
        actor.require_workspace(self.workspace_id)
        if type(include_synthetic) is not bool:
            raise EvidenceError('invalid_synthetic_visibility')
        task = AcquisitionTasks(self.db, self.workspace_id).read(task_id, actor)
        authority = {'origin': task['origin'], 'initiator': task['initiator'], 'scope_version': task['scope_version'],
                     **{key: task['scope'][key] for key in ('route', 'route_version', 'campaign_id', 'brief_id', 'brief_version', 'shortlist_id') if key in task['scope']},
                     'approval': task['proposal_approval']}
        if 'schedule' in task['scope']:
            authority['schedule'] = {key: task['scope']['schedule'][key] for key in ('occurrence_id', 'configuration_version', 'keyword_key', 'accounting_day', 'operator_id') if key in task['scope']['schedule']}
        attempts = []
        source = IngestedEvidence(self.db, self.workspace_id)
        for attempt in task['attempts']:
            attempts.append({key: attempt[key] for key in ('attempt_id', 'number', 'producer', 'resumed_by', 'recovery_count', 'phases', 'started_at', 'finished_at')})
            attempts[-1]['run'] = source.run_lineage(attempt['run_id'], actor, include_synthetic=include_synthetic)
            attempts[-1]['prepared_support'] = attempt['publication_support']
        publications = []
        for publication_id in task['publication_ids']:
            try:
                publication = KnowledgePublications(self.db, self.workspace_id).read(publication_id, actor, include_synthetic=include_synthetic)
            except EvidenceError as error:
                if error.code != 'synthetic_evidence_excluded':
                    raise
                publications.append({'publication_id': publication_id, 'availability': 'synthetic_evidence_excluded', 'href': None,
                                     'support': [], 'current_support': {'available_members': 0, 'unavailable_members': None}})
                continue
            support = []
            for member in publication['members']:
                available = (member['availability'] == 'available' and member['support_status'] == 'current'
                             and all(member['policy'][f'can_{p}'] for p in ('process', 'display', 'retain')))
                support.append({key: member[key] for key in ('observation_id', 'derivation_id', 'assertion_ids', 'metric_ids', 'support_status')})
                support[-1]['availability'] = 'available' if available else 'unavailable'
            available = sum(m['availability'] == 'available' for m in support)
            publications.append({key: publication[key] for key in ('publication_id', 'published_at', 'producer', 'method_version', 'coverage')})
            publications[-1].update(support=support, availability='available' if available else 'unavailable',
                current_support={'available_members': available, 'unavailable_members': len(support) - available},
                href=f'/knowledge/publications/{publication_id}' + ('?include_synthetic=yes' if include_synthetic else '') if available else None)
        coverage = {key: task['coverage'][key] for key in _COVERAGE_KEYS if key in task['coverage']}
        failure = task['failure']
        if failure:
            failure = {'phase': failure['phase'], 'code': failure['code'] if failure['code'] in _FAILURE_CODES else 'unclassified_failure'}
        progress = {key: task['progress'][key] for key in ('phase', 'resumable', 'operation_id', 'retry_not_before') if key in task['progress']}
        return {'task_id': task['task_id'], 'workspace_id': self.workspace_id, 'authority': authority,
                'status': task['status'], 'outcome': task['outcome'], 'submitted_at': task['submitted_at'], 'finished_at': task['finished_at'],
                'execution': task['execution'], 'progress': progress, 'failure': failure, 'historical_coverage': coverage,
                'limits': task['limits'], 'attempt_limit': task['attempt_limit'], 'attempts': attempts, 'publications': publications,
                'stages': self._stages(task, attempts),
                'costs': UsageAccounting(self.db, self.workspace_id).task_operations(task['task_id'], actor),
                'include_synthetic': include_synthetic, 'snapshot': 'independent_committed_owner_reads', 'market_coverage': 'unknown'}

    @staticmethod
    def _stages(task, attempts):
        source = ingestion = publication = 'not_started'
        if attempts:
            run = attempts[-1]['run']
            counts = run['counts']
            collected, applied = sum(counts.values()), counts.get('applied', 0)
            failure_phase = task['failure']['phase'] if task['failure'] else None
            source = ('partial' if collected else 'failed') if failure_phase == 'collection' else 'waiting' if run['waiting'] else 'completed' if run['input_complete'] else 'partial' if collected else 'pending'
            ingestion = ('partial' if applied else 'failed') if counts.get('quarantined') or failure_phase == 'ingestion' else 'partial' if applied and counts.get('pending') else 'pending' if counts.get('pending') else 'completed' if collected or run['input_complete'] else 'not_started'
            publication = ('published' if task['publication_ids'] else 'failed' if failure_phase == 'publication' else
                           'no_update' if task['outcome'] == 'no_usable_update' else 'not_reached' if task['outcome'] == 'failure' else 'pending')
        return {'queue': 'accepted', 'source': source, 'ingestion': ingestion, 'publication': publication,
                'completion': task['outcome'] or 'pending'}
