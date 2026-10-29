"""Read-only software review reproduction: public rank and evidence revocation.

Only the external model transport is simulated. PostgreSQL and every domain
operation are real. The transport's classification read is a controlled pause
after comparison preparation and before any model dispatch.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tests'))

from conftest import stack as stack_fixture
from test_ranked_recommendations import configured_current, RankingTransport, rank
from test_knowledge_queries import publish_account
from test_publications import HUMAN
from smi_knowledge import KnowledgePublications


class PausedTransport(RankingTransport):
    def __init__(self):
        super().__init__()
        self.pre_dispatch = Event()
        self.release = Event()

    @property
    def execution_mode(self):
        self.pre_dispatch.set()
        assert self.release.wait(10)
        return 'simulated'


with TemporaryDirectory() as directory:
    stack_generator = stack_fixture.__wrapped__(Path(directory))
    stack = next(stack_generator)
    try:
        store, campaign, costs, _ = configured_current(stack)
        publication, observation = publish_account(stack, 'policy-race')
        transport = PausedTransport()
        store.model_transport = transport
        with ThreadPoolExecutor(max_workers=1) as pool:
            result_future = pool.submit(rank, store, campaign)
            assert transport.pre_dispatch.wait(10)
            assert len(transport.calls) == 0
            stack[1].revoke(observation.id)
            assert KnowledgePublications(store.db).read(publication['publication_id'], HUMAN)['members'][0]['availability'] == 'unavailable'
            transport.release.set()
            result = result_future.result(10)
        report = {
            'revoked_before_model_dispatch': True,
            'model_calls_after_revocation': len(transport.calls),
            'outcome': result['status'],
            'reason': result['reason'],
            'saved_shortlist': result['shortlist_id'],
            'charged_synthetic_amount': costs.read(result['operation_id'], HUMAN)['actuals']['amount'],
        }
        print(json.dumps(report, indent=2))
    finally:
        try:
            next(stack_generator)
        except StopIteration:
            pass
