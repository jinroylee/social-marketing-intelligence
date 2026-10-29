"""Read-only review reproduction; isolated PostgreSQL schema, public owner calls only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time
import uuid

import psycopg
from psycopg import sql
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceStore
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgePublications
from smi_monitoring.recent import RecentMonitoring
from smi_monitoring.alerts import QuantitativeAlerts, VolumeThreshold
from smi_monitoring.context import AlertInvestigations
from smi_monitoring.promotion import MonitoringPromotion

DSN = os.environ.get('SMI_TEST_DATABASE_URL', 'postgresql://smi:local_only_change_me@127.0.0.1:6543/smi')
SCHEMA = 'standards_' + uuid.uuid4().hex
OPERATOR = ActorContext('local', 'monitoring-operator', 'human')
READER = ActorContext('local', 'reader', 'human')

def wait_blocked(gate, blocker_pid):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        gate.execute('SELECT pg_stat_clear_snapshot()')
        row = gate.execute('SELECT pid FROM pg_stat_activity WHERE %s = ANY(pg_blocking_pids(pid))', (blocker_pid,)).fetchone()
        if row:
            return row['pid']
        time.sleep(.025)
    raise RuntimeError('expected blocked public operation was not observed')

with psycopg.connect(DSN) as setup:
    setup.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(SCHEMA)))
try:
    db = Database(DSN, SCHEMA)
    db.migrate()
    evidence = EvidenceStore(db, None)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    recent = RecentMonitoring(db, operators=frozenset({OPERATOR.actor_id}), clock=lambda: now)
    recent.migrate()
    policy = {'context_id': 'review', 'can_process': True, 'can_display': True, 'can_retain': True, 'expires_at': None, 'revoked': False}
    recent.set_policy(policy, OPERATOR, expected_version=0)
    recent.configure('review', {'query': 'review', 'cadence_minutes': 60, 'window_minutes': 60, 'max_records': 10, 'retention_hours': 24, 'source_policy_id': 'review'}, OPERATOR, expected_version=0, request_id='topic')
    windows=[]
    for hours, count, first in ((1,1,1),(0,4,10)):
        end=now-timedelta(hours=hours)
        records=[{'capture_id': f'record-{i}', 'native_id':str(i), 'text':'review sample', 'published_at':(end-timedelta(minutes=30)).isoformat(), 'captured_at':(end-timedelta(minutes=20)).isoformat(), 'metric_measured_at':None, 'metrics':{}} for i in range(first,first+count)]
        acquisition={'route':'offline-x-json','version':'review-v1','synthetic':True,'declared_coverage':'complete','sampling':{'method':'review-fixture'},'max_records':10}
        with db.connect() as c:
            prepared=recent.prepare_collection_in_transaction(c,'review',end.isoformat(),OPERATOR)
            windows.append(recent.save_collection_in_transaction(c,'review',end.isoformat(),OPERATOR,revision_id=prepared['revision_id'],records=records,acquisition=acquisition)['window_id'])
    alerts=QuantitativeAlerts(recent,threshold=VolumeThreshold(1,3,3),clock=lambda:now)
    alerts.migrate()
    alert=alerts.detect(windows[1],windows[0],OPERATOR,request_id='alert')
    assert alert['alert_id']
    context=AlertInvestigations(recent)
    context.migrate()
    promotion=MonitoringPromotion(recent,evidence)
    promotion.migrate()
    obs=recent.read_window(windows[1],READER)['observations'][0]['observation_id']
    result={}
    with db.connect() as gate, ThreadPoolExecutor(max_workers=2) as pool:
        gate.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('alert-context:local',))
        context_future=pool.submit(context.investigate,'quantitative',alert['alert_id'],READER,request_id='deadlock')
        context_pid=wait_blocked(gate,gate.info.backend_pid)
        promotion_future=pool.submit(promotion.promote,windows[1],(obs,),OPERATOR,request_id='promotion')
        promotion_pid=wait_blocked(gate,context_pid)
        result['coordination']={'context_waited_at_context_lock':True,'promotion_waited_on_context_recent_lock':True}
        gate.commit()
        for name,future in (('context',context_future),('promotion',promotion_future)):
            try:
                value=future.result(timeout=12)
                result[name]={'status':value.get('status','succeeded')}
            except Exception as error:
                result[name]={'exception_type':type(error).__name__,'sqlstate':getattr(error,'sqlstate',None),'message':str(error).splitlines()[0]}
    # Independently examine the documented full-permission alert projection.
    recent.set_policy({**policy,'can_process':False},OPERATOR,expected_version=1)
    denied=alerts.read_alert(alert['alert_id'],READER)
    result['process_denial']={'current_support':denied['current_support'],'comparison':denied['comparison'],'returned_source_bodies':sum(o['body'] is not None for w in denied['windows'].values() for o in w['observations'])}
    print(json.dumps(result,indent=2))
finally:
    with psycopg.connect(DSN) as cleanup:
        cleanup.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(SCHEMA)))
