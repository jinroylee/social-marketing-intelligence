"""One explicit offline task execution, composed from public ingestion/publication APIs."""

import hashlib
from pathlib import Path
import uuid
from typing import Any

from psycopg.types.json import Jsonb

from smi_ingestion.adapters.json_fixture import JsonFixtureMapper
from smi_ingestion.adapters.local import LocalFileCollector
from smi_ingestion.adapters.registry import AdapterRegistry
from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import RunLimits
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError, EvidenceStore
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.runner import IngestionRunner
from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgePublications

from .store import AcquisitionTasks


class OfflineTaskWorker:
    """Run at most one queued task, with no registered network/model capability."""

    def __init__(self, db: Database, evidence_root: Path, workspace_id: str = 'local'):
        self.db, self.workspace_id = db, workspace_id
        self.tasks = AcquisitionTasks(db, workspace_id)
        self.evidence = EvidenceStore(db, evidence_root)
        registry = AdapterRegistry()
        registry.register('fixture-json', LocalFileCollector('fixture-json'), JsonFixtureMapper())
        self.runner = IngestionRunner(self.evidence, CanonicalWriter(db), registry)

    def _phase(self, task_id, attempt_id, phase):
        with self.db.connect() as connection:
            connection.execute('UPDATE acquisition_tasks SET status=%s WHERE id=%s', (phase, task_id))
            connection.execute('UPDATE acquisition_attempts SET phases=phases || %s::jsonb WHERE id=%s', (Jsonb([phase]), attempt_id))

    def _finish(self, task_id, attempt_id, coverage, *, outcome, failure_phase=None, failure_code=None, publication_id=None):
        with self.db.connect() as connection:
            connection.execute('UPDATE acquisition_tasks SET status=%s,outcome=%s,coverage=%s,failure_phase=%s,failure_code=%s,finished_at=now() WHERE id=%s',
                               ('failed' if outcome == 'failure' else 'completed', outcome, Jsonb(coverage), failure_phase, failure_code, task_id))
            connection.execute('UPDATE acquisition_attempts SET finished_at=now() WHERE id=%s', (attempt_id,))
            if publication_id:
                connection.execute('INSERT INTO acquisition_task_publications(task_id,publication_id) VALUES (%s,%s)', (task_id, publication_id))

    def run_one(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        """Execute one admitted task; terminal retries reopen its committed outcome.

        Interrupted active attempts remain explicit and require the later recovery
        operation; this entry point never silently reacquires their input.
        """
        actor.require_workspace(self.workspace_id)
        if actor.kind != 'automation':
            raise EvidenceError('task_worker_authority_required')
        view = self.tasks.read(task_id, actor)
        if view['outcome'] is not None:
            return view
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM acquisition_tasks WHERE id=%s AND workspace_id=%s FOR UPDATE', (task_id, self.workspace_id)).fetchone()
            if row['status'] != 'queued':
                raise EvidenceError('task_execution_incomplete')
            if row['origin'] != 'campaign' or row['scope']['route'] != 'fixture-json':
                raise EvidenceError('unsupported_task_origin_or_route')
            run_id = self.evidence.start_run(Path(row['manifest_path']), row['manifest_hash'], 'fixture-json', RunLimits(**row['limits']), connection=connection, workspace_id=self.workspace_id)
            attempt_id = str(uuid.uuid4())
            connection.execute('INSERT INTO acquisition_attempts(id,task_id,number,run_id,producer_id,producer_kind) VALUES (%s,%s,1,%s,%s,%s)', (attempt_id, task_id, run_id, actor.actor_id, actor.kind))
            connection.execute("UPDATE acquisition_tasks SET status='collecting' WHERE id=%s", (task_id,))
        phase = 'collection'
        coverage = {'collected_observations': 0, 'ingested_observations': 0, 'published_members': 0, 'scope': 'bounded_requested_input', 'market_coverage': 'unknown'}
        try:
            # Revalidate the nominated manifest before using the runner. It has only
            # the fixture registry even if a file is replaced after this check.
            with Path(row['manifest_path']).open('rb') as source:
                raw = source.read(1_048_577)
            if hashlib.sha256(raw).hexdigest() != row['manifest_hash']:
                raise EvidenceError('input_changed')
            report = self.runner.resume(run_id)
            coverage.update(collected_observations=report['observations'], ingested_observations=report['applied'],
                            quarantined_observations=report['quarantined'], input_coverage=report['coverage'],
                            requests_used=report['requests_used'], bytes_used=report['bytes_used'], issues=report['issues'])
            phase = 'ingestion'
            self._phase(task_id, attempt_id, 'ingesting')
            if report['issues'] or report['status'] != 'completed':
                code = report['issues'][0]['code'] if report['issues'] else 'incomplete_input'
                failed_phase = 'ingestion' if report['quarantined'] or code == 'processing_not_permitted' else 'collection'
                self._finish(task_id, attempt_id, coverage, outcome='failure', failure_phase=failed_phase, failure_code=code)
                return self.tasks.read(task_id, actor)
            support = IngestedEvidence(self.db, self.workspace_id).select_run(run_id, actor, include_synthetic=True)
            phase = 'publication'
            publications = KnowledgePublications(self.db, self.workspace_id)
            new_support = publications.unpublished(support, actor, include_synthetic=True)
            coverage['unchanged_members'] = len(support) - len(new_support)
            support = new_support
            if not support:
                self._finish(task_id, attempt_id, coverage, outcome='no_usable_update')
                return self.tasks.read(task_id, actor)
            phase = 'publication'
            self._phase(task_id, attempt_id, 'publishing')
            published = publications.publish(support, actor, request_id=f'task:{task_id}', include_synthetic=True)
            coverage['published_members'] = len(support)
            self._finish(task_id, attempt_id, coverage, outcome='usable_update', publication_id=published['publication_id'])
        except (EvidenceError, OSError, ValueError, KeyError, TypeError) as error:
            code = error.code if isinstance(error, EvidenceError) else 'offline_input_unavailable'
            self._finish(task_id, attempt_id, coverage, outcome='failure', failure_phase=phase, failure_code=code)
        return self.tasks.read(task_id, actor)
