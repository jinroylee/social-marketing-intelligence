"""Bounded task composition for one explicit missing nickname and one existing route."""

from dataclasses import asdict, replace
from datetime import datetime
import hashlib
import json

from psycopg.types.json import Jsonb

from smi_costs import DeferredProviderOperationAdapter, DeferredProviderResult
from smi_ingestion.adapters.bright_data import BrightDataProfileFieldCollector
from smi_ingestion.contracts import CollectedBatch
from smi_ingestion.evidence import policy_allows, policy_from_json
from smi_ingestion.support import IngestedEvidence, SupportReference
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope

from .policy import ProfileSupplement, SupplementationPolicy

__all__ = ['ProfileSupplement', 'SupplementationPolicy']


class ProfileSupplementation:
    """Join the original run, fenced task session and shared provider allowance.

    Primary evidence must identify the exact explicitly approved target. Source
    namespaces stay independent: matching native numbers confer scope only, not
    account equivalence or permission to merge fields/metrics across providers.
    """

    def __init__(self, primary, row, attempt, execution, evidence, costs, config, clock):
        self.primary, self.row, self.attempt, self.execution = primary, row, attempt, execution
        self.evidence, self.costs, self.config, self.clock = evidence, costs, config, clock
        self.policy = row['scope']['supplementation_policy']
        self.target = row['scope'].get('profile_supplement')
        self.support = IngestedEvidence(evidence.db, execution.actor.workspace_id)
        self.publications = KnowledgePublications(evidence.db, execution.actor.workspace_id)

    def _read(self, connection):
        return connection.execute('SELECT supplementation FROM acquisition_tasks WHERE id=%s',
                                  (self.execution.task_id,)).fetchone()['supplementation']

    def _save(self, document):
        with self.execution.transaction('supplementation_decision') as connection:
            connection.execute('UPDATE acquisition_tasks SET supplementation=%s WHERE id=%s',
                               (Jsonb(document), self.execution.task_id))
        return document

    def _stop(self, reason, checks=None, **extra):
        with self.execution.transaction('supplementation_read') as connection:
            prior = self._read(connection)
        document = prior or {'policy': self.policy, 'checks': checks or {}, 'decision': 'stop',
                             'decided_at': self.clock().isoformat()}
        return self._save({**document, 'state': 'stopped', 'reason': reason, **extra})

    def _knowledge(self, connection):
        # Literal search is bounded by the KB owner; exact source identity and
        # field filtering below never treat a text match as account equivalence.
        return KnowledgeQueries(self.evidence.db, self.execution.actor.workspace_id).search(
            QueryScope(text=self.target['native_id']), self.execution.actor, purpose='process',
            request_id=f'profile-field:{self.execution.task_id}:{self.execution.execution_id}', connection=connection)

    def _known_fields(self, members):
        return [(m, a) for m in members if m['availability'] == 'available' and m['support_status'] == 'current'
                for a in m['assertions'] if a['namespace'] == 'tiktok:public' and a['kind'] == 'account'
                and a['native_id'] == self.target['native_id'] and a['field'] == 'nickname' and a['state'] == 'observed']

    def _select(self, manifest, limits):
        checks = {'missingness': 'unknown', 'freshness': 'unknown', 'permission': 'unknown',
                  'capability': self.policy['route'],
                  'expected_information_value': self.policy['expected_information_value'],
                  'minimum_information_value': self.policy['minimum_information_value'],
                  'cost': 'not_admitted', 'limits': {'basis': 'original_run_remaining', **asdict(limits)}}
        if not self.target:
            return self._stop('profile_target_not_approved', checks)
        with self.execution.transaction('supplementation_selection') as connection:
            prior = self._read(connection)
            if prior:
                return prior
            refs = self.support.select_run(str(self.attempt['run_id']), self.execution.actor)
            members = self.support.read(refs, self.execution.actor, purpose='process', connection=connection) if refs else []
            in_scope = any(a['kind'] == 'account' and a['namespace'] == 'brightdata:tiktok-posts'
                and a['native_id'] == self.target['native_id'] and a['field'] == 'handle'
                and a['state'] == 'observed' and a['value'] == self.target['profile_url'].split('@')[1]
                for m in members if m['availability'] == 'available' for a in m['assertions'])
            permitted = members and all(m['availability'] == 'available' for m in members)
            unchanged = refs and not self.publications.unpublished(refs, self.execution.actor, connection=connection)
            # Prior task-owned support is reopened under current policy. A source
            # withdrawal cannot be repaired by fetching another copy of it.
            earlier = connection.execute("SELECT a.run_id FROM acquisition_tasks t JOIN acquisition_attempts a ON a.task_id=t.id "
                "WHERE t.workspace_id=%s AND t.id<>%s AND t.scope->'profile_supplement'=%s "
                "ORDER BY t.submitted_at DESC LIMIT 101", (self.execution.actor.workspace_id,
                    self.execution.task_id, Jsonb(self.target))).fetchall()
            knowledge = self._knowledge(connection)
            old = list(knowledge['members'])
            for task in earlier[:100]:
                old_refs = self.support.select_run(str(task['run_id']), self.execution.actor)
                old.extend(self.support.read(old_refs, self.execution.actor, purpose='process', connection=connection))
        checks['permission'] = 'permitted' if permitted and policy_allows(policy_from_json(manifest['policy']), 'process') and policy_allows(policy_from_json(manifest['policy']), 'retain') else 'denied'
        if not permitted or checks['permission'] != 'permitted' or any(m['availability'] != 'available' for m in old):
            return self._stop('source_support_unavailable', checks)
        if not in_scope:
            return self._stop('approved_profile_not_discovered', checks)
        fields = self._known_fields(old + members)
        checks['missingness'] = 'present' if fields else 'missing'
        if fields:
            captures = [datetime.fromisoformat(m['captured_at']) for m, _ in fields if m['captured_at']]
            ages = [(self.clock() - c).total_seconds() for c in captures if c <= self.clock()]
            checks['freshness'] = 'fresh' if any(age <= self.policy['max_capture_age_seconds'] for age in ages) else 'stale' if ages else 'unknown'
            return self._stop('field_already_supported', checks)
        if knowledge['coverage']['process_denied_members'] or knowledge['coverage']['unavailable_members']:
            return self._stop('knowledge_support_unavailable', checks)
        if knowledge['coverage']['publication_limit_reached'] or knowledge['coverage']['result_limit_reached']:
            return self._stop('knowledge_scan_limit', checks)
        if unchanged:
            return self._stop('unchanged_evidence', checks)
        if len(earlier) > 100:
            return self._stop('prior_support_scan_limit', checks)
        if self.policy['route'] != 'brightdata-tiktok-profile':
            return self._stop('capability_unavailable', checks)
        if self.policy['expected_information_value'] < self.policy['minimum_information_value'] or self.policy['expected_information_value'] == 0:
            return self._stop('insufficient_information_value', checks)
        reason = self.config.unavailable_reason()
        if reason or self.config.profile_supplementation_authorized is not True:
            return self._stop(reason or 'profile_supplementation_authorization_required', checks)
        control = self.costs.route_control('brightdata-tiktok-profile', self.execution.actor)
        primary_control = self.costs.route_control(self.row['scope']['route'], self.execution.actor)
        if not control or not primary_control or control['scope_id'] != primary_control['scope_id']:
            return self._stop('shared_cost_configuration_required', checks)
        checks['cost'] = {'scope_id': control['scope_id'], 'declared_max_units': control['max_units'],
                          'basis': 'operator_declared_commitment_final_charge_unknown'}
        return self._save({'policy': self.policy, 'checks': checks, 'decision': 'retrieve', 'state': 'selected',
            'reason': 'valuable_missing_field', 'decided_at': self.clock().isoformat(),
            'basis': [asdict(r) for r in refs]})

    def record_unapproved_target(self):
        """Record that operator capability alone grants no profile acquisition authority."""
        self._stop('profile_target_not_approved')

    def collect(self, manifest, checkpoint, limits):
        """Append one secondary operation only after primary canonical evidence commits."""
        if checkpoint.get('supplementation_phase') != 'select':
            batch = self.primary.collect(manifest, checkpoint, limits)
            if batch.complete:
                return replace(batch, complete=False, next_checkpoint={
                    'primary': batch.next_checkpoint, 'supplementation_phase': 'select'})
            return batch
        decision = self._select(manifest, limits)
        if decision['state'] == 'stopped':
            return CollectedBatch((), checkpoint, True)
        # A persisted choice pins scope, never future dispatch permission. Reopen
        # its exact basis and all live gates after any execution interruption.
        reason = self.config.unavailable_reason()
        if reason or self.config.profile_supplementation_authorized is not True:
            self._stop(reason or 'profile_supplementation_authorization_required')
            return CollectedBatch((), checkpoint, True)
        basis = tuple(SupportReference(r['observation_id'], r['derivation_id'], tuple(r['assertion_ids']), tuple(r['metric_ids'])) for r in decision['basis'])
        with self.execution.transaction('supplementation_permission') as connection:
            members = self.support.read(basis, self.execution.actor, purpose='process', connection=connection)
            knowledge = self._knowledge(connection)
        if (not members or any(m['availability'] != 'available' for m in members)
                or not policy_allows(policy_from_json(manifest['policy']), 'process')
                or not policy_allows(policy_from_json(manifest['policy']), 'retain')):
            self._stop('source_support_unavailable')
            return CollectedBatch((), checkpoint, True)
        if self._known_fields(knowledge['members']):
            self._stop('field_already_supported')
            return CollectedBatch((), checkpoint, True)
        if knowledge['coverage']['process_denied_members'] or knowledge['coverage']['unavailable_members']:
            self._stop('knowledge_support_unavailable')
            return CollectedBatch((), checkpoint, True)
        if knowledge['coverage']['publication_limit_reached'] or knowledge['coverage']['result_limit_reached']:
            self._stop('knowledge_scan_limit')
            return CollectedBatch((), checkpoint, True)
        control = self.costs.route_control('brightdata-tiktok-profile', self.execution.actor)
        primary_control = self.costs.route_control(self.row['scope']['route'], self.execution.actor)
        if not control or not primary_control or control['scope_id'] != primary_control['scope_id']:
            self._stop('shared_cost_configuration_required')
            return CollectedBatch((), checkpoint, True)
        identity = hashlib.sha256(json.dumps(checkpoint, sort_keys=True).encode()).hexdigest()
        collector = BrightDataProfileFieldCollector(self.target, self.config.api_key, clock=self.clock)
        adapter = DeferredProviderOperationAdapter(self.costs, control['scope_id'], max_units=control['max_units'])
        result = adapter.execute(self.execution.actor,
            request_id=f'task:{self.execution.task_id}:profile:{identity}', method='brightdata-profile-nickname-http-v1',
            call=lambda bound: DeferredProviderResult(collector.collect(manifest, {}, limits)),
            task_id=self.execution.task_id, attempt_id=str(self.attempt['id']), transaction=self.execution.transaction,
            operation_actor=ActorContext(self.execution.actor.workspace_id, self.attempt['producer_id'], self.attempt['producer_kind']))
        if result['status'] != 'executed':
            self._stop(result['reason'], operation_id=result['operation_id'], allowance=result['allowance'])
            return CollectedBatch((), checkpoint, True)
        batch = result['value']
        if not batch.items:
            self._stop('source_failure', operation_id=result['operation_id'],
                       source_outcome=batch.next_checkpoint['profile_result'], resumable=False)
        else:
            self._save({**decision, 'state': 'returned', 'reason': 'awaiting_mapping', 'operation_id': result['operation_id'], 'http_attempts': 1})
        return batch

    def complete(self, report):
        """Record the actual result, including runner-enforced limits before selection."""
        with self.execution.transaction('supplementation_read') as connection:
            decision = self._read(connection)
        if decision is None:
            limit = next((i['code'] for i in report['issues'] if i['code'].endswith('_limit_reached')), None)
            self._stop(limit or 'primary_source_failure')
        elif decision['state'] == 'returned':
            refs = self.support.select_run(str(self.attempt['run_id']), self.execution.actor)
            members = self.support.read(refs, self.execution.actor, purpose='process')
            extra = [m for m in members if m.get('adapter') == 'brightdata-tiktok-profile']
            if not extra:
                self._stop('source_failure')
                return
            observed = any(a['field'] == 'nickname' and a['state'] == 'observed'
                           for m in extra for a in m['assertions'])
            self._save({**decision, 'state': 'completed', 'reason': 'field_observed' if observed else 'field_still_unknown',
                        'support': [asdict(r) for r in refs if any(m['observation_id'] == r.observation_id for m in extra)]})
