"""Bounded review records composed through source-owning public operations."""

import hashlib
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_assistant import KnowledgeAssistant
from smi_campaigns import CampaignStore
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgeQueries
from smi_monitoring.recent import RecentMonitoring
from smi_monitoring.semantic import SemanticAlerts

from .sources import answer_findings, permitted, query_sources, require
from .records import assessment, template, validate

BOUNDS = {'record_limit': 50, 'workspace_packet_limit': 5000, 'review_byte_limit': 262144}


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def identity(value):
    try:
        return str(uuid.UUID(value))
    except (TypeError, ValueError, AttributeError):
        require(False, 'invalid_review_identity')


class OperationalReviews:
    """Export and reopen one exact result without making automatic quality judgments.

    Actors are trusted local attribution, not hosted identity verification. Pass a
    configured recent reader to preserve its retention clock. No transport, model
    credential, source route or acquisition authority is accepted by this owner.
    """

    def __init__(self, db, workspace_id='local', *, recent: RecentMonitoring | None = None):
        self.db, self.workspace_id = db, workspace_id
        self.campaigns = CampaignStore(db, workspace_id)
        self.assistant = KnowledgeAssistant(db, workspace_id)
        self.queries = KnowledgeQueries(db, workspace_id)
        require(recent is None or (recent.db is db and recent.workspace_id == workspace_id), 'review_reader_context_mismatch')
        self.semantic = SemanticAlerts(recent if recent is not None else RecentMonitoring(db, workspace_id))

    def migrate(self):
        """Install review-only storage after result owners have been migrated."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _view(self, connection, kind, result_id, actor, synthetic):
        if kind == 'answer':
            result = self.assistant.read(result_id, actor, include_synthetic=synthetic, connection=connection)
            query = result['knowledge_query']
            statuses = self.queries.statuses(query['result_id'], actor, include_synthetic=synthetic, connection=connection)
            return {'membership': result['selected_support_ids'], 'input_support_ids': result['input_support_ids'],
                'dependencies': query['manifest'], 'versions': result['configuration'],
                'result_context': {'query_result_id': query['result_id'], 'recorded_at': result['recorded_at'],
                    'method_version': result['configuration']['method_version'], 'requested_by': result['requested_by'],
                    'generated_by': result['generated_by']},
                'result': {'findings': answer_findings(result), 'limits': result['limits']},
                'sources': query_sources(query, statuses), 'available': result['usable'] and permitted(statuses),
                'can_retain': all(s['can_retain'] for s in statuses.values())}
        if kind == 'recommendation':
            result = self.campaigns.read_shortlist(result_id, actor, include_synthetic=synthetic, connection=connection)
            comparison = self.campaigns.read_comparison(result['comparison_id'], actor, include_synthetic=synthetic, connection=connection)
            require(result['status'] == 'generated' and comparison['source_mode'] == 'current_knowledge', 'review_requires_current_kb_recommendation')
            query = comparison['knowledge_query']
            statuses = self.queries.statuses(query['result_id'], actor, include_synthetic=synthetic, connection=connection)
            ranking = result['ranking_assessment']
            return {'membership': [s['candidate_id'] for s in result['selected']],
                'input_support_ids': list(dict.fromkeys(i for m in query['manifest']
                    for key in ('assertion_ids', 'metric_ids', 'interpretation_ids') for i in m[key])),
                'dependencies': query['manifest'], 'versions': ranking['configuration'] if ranking else result['execution_profile'],
                'result_context': {key: result[key] for key in ('campaign_id', 'brief_id', 'comparison_id', 'method_version', 'recorded_at', 'recorded_by', 'actor_kind')},
                'result': {'selected': result['selected'], 'ranking': ranking, 'coverage': result['coverage']},
                'sources': query_sources(query, statuses),
                'available': permitted(statuses) and not result['review_required'] and not (ranking and ranking['review_required']),
                'can_retain': all(s['can_retain'] for s in statuses.values())}
        require(kind == 'semantic_alert', 'invalid_operational_review_kind')
        result = self.semantic.read_alert(result_id, actor, connection=connection)
        window = result['window']
        sources = []
        for observation in window['observations']:
            item = {key: observation.get(key) for key in ('observation_id', 'native_id', 'captured_at', 'published_at', 'imported_at')}
            available = all(window['current_permissions'].values()) and observation['body'] is not None
            item.update(available=available, texts=[], spans=[])
            if available:
                item.update(source_reference=observation['source_reference'],
                    texts=[{'support_id': observation['observation_id'], 'field': 'text', 'original_text': observation['body']['text']}],
                    spans=[{key: j[key] for key in ('start', 'end', 'excerpt')} for j in result['judgments']
                           if j['observation_id'] == observation['observation_id']])
            sources.append(item)
        return {'membership': [j['observation_id'] for j in result['judgments']],
            'input_support_ids': result['input_observation_ids'],
            'dependencies': [{'window_id': window['window_id'], 'observation_ids': result['input_observation_ids']}],
            'versions': {**result['configuration'], 'semantic_method': result['method']},
            'result_context': {'assessment_id': result['assessment_id'], 'window_id': window['window_id'],
                'input_digest': result['input_digest'], 'recorded_at': result['recorded_at'],
                'recorded_by': result['recorded_by'], 'actor_kind': result['actor_kind'], 'generated_by': result['generated_by']},
            'result': {'judgments': result['judgments'], 'comparison': result['comparison'], 'limitations': result['limitations'],
                'coverage': window['coverage'], 'window_start': window['window_start'], 'window_end': window['window_end']},
            'sources': sources, 'available': result['usable'],
            'can_retain': window['current_permissions']['retain'] and all(o['body'] is not None for o in window['observations'])}

    def export(self, kind, result_id, actor: ActorContext, *, request_id, include_synthetic=False):
        """Pin one result's exact membership; fresh original text and unanswered human fields.

        Exact request retries reopen the same packet. This local export does not
        manage external copies; retain them only within the source-permitted review
        environment and reopen before use. Missing support grants no quality pass.
        """
        actor.require_workspace(self.workspace_id)
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200 and '\x00' not in request_id, 'invalid_review_request')
        require(type(include_synthetic) is bool, 'invalid_synthetic_selection')
        require(kind in {'answer', 'recommendation', 'semantic_alert'}, 'invalid_operational_review_kind')
        result_id = identity(result_id)
        request_digest = digest({'kind': kind, 'result_id': result_id, 'actor': actor.actor_id,
            'actor_kind': actor.kind, 'synthetic': include_synthetic})
        with self.db.connect() as connection:
            view = self._view(connection, kind, result_id, actor, include_synthetic)
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'operational-review:{self.workspace_id}',))
            row = connection.execute('SELECT * FROM operational_review_packets WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if row:
                require(row['request_digest'] == request_digest, 'review_request_conflict')
            else:
                if not view['available']:
                    if not view['can_retain']:
                        connection.execute('UPDATE operational_review_records SET body=NULL,purged=TRUE WHERE packet_id IN '
                            '(SELECT id FROM operational_review_packets WHERE workspace_id=%s AND result_kind=%s AND result_id=%s)',
                            (self.workspace_id, kind, result_id))
                    return {'packet_id': None, 'result_kind': kind, 'result_id': result_id,
                        'recording_status': 'support_unavailable', 'available': False, 'sources': [], 'result': None,
                        'bounds': dict(BOUNDS), 'quality': assessment(None, 0)[0]}
                require(bool(view['membership']), 'review_result_support_unavailable_or_empty')
                count = connection.execute('SELECT count(*) AS n FROM operational_review_packets WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
                require(count < BOUNDS['workspace_packet_limit'], 'operational_review_packet_limit')
                manifest = {key: view[key] for key in ('membership', 'input_support_ids', 'dependencies', 'versions', 'result_context')}
                packet_id = str(uuid.uuid4())
                connection.execute('INSERT INTO operational_review_packets(id,workspace_id,request_id,request_digest,result_kind,result_id,include_synthetic,manifest,exported_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (packet_id, self.workspace_id, request_id, request_digest, kind, result_id, include_synthetic, Jsonb(manifest), actor.actor_id))
                row = connection.execute('SELECT * FROM operational_review_packets WHERE id=%s', (packet_id,)).fetchone()
            return self._read(connection, row, view)

    def _read(self, connection, row, view):
        # Source locks acquired by the owning reader precede packet/record locks.
        # Re-read rows under those locks so a concurrent purge cannot leak a copy.
        connection.execute('SELECT id FROM operational_review_packets WHERE id=%s FOR UPDATE', (row['id'],))
        if not view['can_retain']:
            connection.execute('UPDATE operational_review_records SET body=NULL,purged=TRUE WHERE packet_id=%s', (row['id'],))
        records = connection.execute('SELECT * FROM operational_review_records WHERE packet_id=%s ORDER BY version', (row['id'],)).fetchall()
        latest = records[-1] if records else None
        body = latest['body'] if latest and view['available'] and not latest['purged'] else None
        quality, counts = assessment(body, len(row['manifest']['membership']))
        return {'packet_id': str(row['id']), 'rubric': 'operational-result-review-v1',
            'bounds': dict(BOUNDS),
            'result_kind': row['result_kind'], 'result_id': str(row['result_id']), **row['manifest'],
            'exported_by': row['exported_by'], 'exported_at': row['exported_at'].isoformat(),
            'available': view['available'], 'sources': view['sources'],
            'recording_status': 'recorded' if body else 'pending' if view['available'] else 'support_unavailable',
            'result': view['result'] if view['available'] else None, 'review': body,
            'review_template': template(row['manifest']['membership']),
            'records': [{'record_id': str(r['id']), 'version': r['version'], 'attribution': r['attribution'],
                'recorded_at': r['recorded_at'].isoformat(), 'purged': r['purged']} for r in records],
            'pending_fields': {'translation': None, 'translator': None, 'reviewer': None, 'reviewed_at': None,
                'label': None, 'material_error': None, 'correction': None, 'marketer_usefulness': None},
            'quality': quality, 'label_counts': counts,
            'denominators': {'selected': len(row['manifest']['membership']),
                'submitted': len(latest['attribution']['reviewed_item_ids']) if latest else 0,
                'countable': len(body['items']) if body else 0,
                'unavailable': 0 if view['available'] else len(row['manifest']['membership'])}}

    def record(self, packet_id, review, actor: ActorContext, *, request_id, include_synthetic=False):
        """Append an explicitly attributed translation-assisted review under current policy.

        Supply actual reviewer time, translations and translator/method versions;
        no automatic human input or truth validation is supplied. New requests
        append corrections without rewriting earlier receipts. Retention loss
        purges all source-dependent copies on export/record/read; safe attribution
        and exact reviewed membership remain. External exports are operator-owned.
        """
        actor.require_workspace(self.workspace_id)
        require(actor.kind == 'human', 'human_action_required')
        require(type(include_synthetic) is bool, 'invalid_synthetic_selection')
        packet_id = identity(packet_id)
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200 and '\x00' not in request_id, 'invalid_review_request')
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM operational_review_packets WHERE id=%s AND workspace_id=%s', (packet_id, self.workspace_id)).fetchone()
            require(row is not None, 'operational_review_not_found')
            require(not row['include_synthetic'] or include_synthetic, 'synthetic_evidence_excluded')
            view = self._view(connection, row['result_kind'], str(row['result_id']), actor, include_synthetic)
            current = self._read(connection, row, view)
            if not view['available']:
                return current
            attribution = validate(review, row['manifest']['membership'], actor)
            require(len(json.dumps(review, ensure_ascii=False, allow_nan=False).encode()) <= BOUNDS['review_byte_limit'], 'invalid_review_size')
            request_digest = digest(review)
            prior = connection.execute('SELECT request_digest FROM operational_review_records WHERE packet_id=%s AND request_id=%s', (packet_id, request_id)).fetchone()
            if prior:
                require(prior['request_digest'] == request_digest, 'review_record_request_conflict')
            else:
                require(len(current['records']) < BOUNDS['record_limit'], 'operational_review_record_limit')
                connection.execute('INSERT INTO operational_review_records(id,packet_id,version,request_id,request_digest,attribution,body) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    (uuid.uuid4(), packet_id, len(current['records']) + 1, request_id, request_digest, Jsonb(attribution), Jsonb(review)))
                current = self._read(connection, row, view)
            return current

    def read(self, packet_id, actor: ActorContext, *, include_synthetic=False):
        """Recheck every original result input before reopening text or annotations."""
        actor.require_workspace(self.workspace_id)
        require(type(include_synthetic) is bool, 'invalid_synthetic_selection')
        packet_id = identity(packet_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM operational_review_packets WHERE id=%s AND workspace_id=%s', (packet_id, self.workspace_id)).fetchone()
            require(row is not None, 'operational_review_not_found')
            require(not row['include_synthetic'] or include_synthetic, 'synthetic_evidence_excluded')
            view = self._view(connection, row['result_kind'], str(row['result_id']), actor, include_synthetic)
            return self._read(connection, row, view)
