"""Public ranking after real source revocation while waiting on cost admission."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time
import uuid

import psycopg
from psycopg import sql
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceStore
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tests'))
from test_ranked_recommendations import configured_current, rank
from test_knowledge_queries import publish_account

DSN=os.environ.get('SMI_TEST_DATABASE_URL','postgresql://smi:local_only_change_me@127.0.0.1:6543/smi')
SCHEMA='standards_'+uuid.uuid4().hex
with psycopg.connect(DSN) as setup:
    setup.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(SCHEMA)))
try:
    with TemporaryDirectory() as path:
        db=Database(DSN,SCHEMA)
        db.migrate()
        evidence=EvidenceStore(db,Path(path))
        stack=(db,evidence,None,None)
        store,campaign,costs,transport=configured_current(stack)
        _,observation=publish_account(stack,'ranking-input')
        with db.connect() as gate,ThreadPoolExecutor(max_workers=1) as pool:
            gate.execute("SELECT scope_id FROM cost_scopes WHERE workspace_id='local' AND scope_id='synthetic-model' FOR NO KEY UPDATE")
            future=pool.submit(rank,store,campaign)
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                gate.execute('SELECT pg_stat_clear_snapshot()')
                if gate.execute('SELECT pid FROM pg_stat_activity WHERE %s = ANY(pg_blocking_pids(pid))',(gate.info.backend_pid,)).fetchone():
                    break
                time.sleep(.025)
            else:
                raise RuntimeError('ranking did not reach accounting admission')
            assert len(transport.calls)==0
            evidence.revoke(observation.id)
            gate.commit()
            result=future.result(timeout=10)
        print(json.dumps({'source_revoked_before_dispatch':True,'simulated_model_calls_after_revocation':len(transport.calls),
            'final_status':result['status'],'reason':result['reason'],'actual_cost':costs.read(result['operation_id'],__import__('test_publications').HUMAN)['actuals']},indent=2))
finally:
    with psycopg.connect(DSN) as cleanup:
        cleanup.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(SCHEMA)))
