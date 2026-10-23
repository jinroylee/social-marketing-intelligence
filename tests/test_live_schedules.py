"""Recorded scheduled live authority and bounded execution at public/HTTP seams."""

import pytest

from smi_tasks import AcquisitionTasks, TaskAuthority, OfflineTaskWorker
from smi_tasks.schedules import ScheduledDiscovery
from test_live_discovery import live_setup, live_costs, enabled, http_boundary, post
from test_schedules import Clock, config
from test_tasks import HUMAN, WORKER


def live_schedule(stack, tmp_path, *, clock=None):
    tasks, evidence = live_setup(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=tasks.route, live_discovery_enabled=True,
        authority=TaskAuthority(schedule_operators=frozenset({HUMAN.actor_id}),
                                schedule_automations=frozenset({WORKER.actor_id})))
    return ScheduledDiscovery(tasks, clock=clock or Clock()), tasks, evidence


def test_explicit_activation_records_exact_authority_and_publishes_with_shared_daily_counts(stack, tmp_path, monkeypatch):
    owner, tasks, evidence = live_schedule(stack, tmp_path)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()])])
    saved = owner.configure(config(), HUMAN, expected_version=0, live=True)
    assert saved['live_activation'] is True
    assert saved['configurations'][0]['operator_id'] == HUMAN.actor_id
    authority = saved['configurations'][0]['route_authority']
    assert authority['route'] == 'brightdata-tiktok-keyword'
    assert authority['route_version'] == tasks.route.version
    occurrence = owner.tick(WORKER)['created_occurrences'][0]
    queued = tasks.read(occurrence['task_id'], HUMAN)
    assert queued['scope']['schedule']['route_authority'] == authority
    assert queued['scope_version'] == 'schedule-live-v1'
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(queued['task_id'], WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['daily_allowance']['used'] == 1
    assert completed['daily_allowance']['occurrence_counts']['new_posts'] == 1
    assert completed['coverage']['returned_records'] == 1
    assert completed['coverage']['published_records'] == 1
    assert len(requests) == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'


def test_exhausted_shared_day_stops_new_paid_posts_until_explicit_cap_edit_without_reset(stack, tmp_path, monkeypatch):
    owner, tasks, evidence = live_schedule(stack, tmp_path)
    live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()]), (200, [post()])])
    keywords = config()['keywords'] + [{'key': 'review', 'query': 'review', 'subject_ids': ['product:sunscreen']}]
    owner.configure(config(daily_allowance=1, keywords=keywords), HUMAN, expected_version=0, live=True)
    first, second = owner.tick(WORKER)['created_occurrences']
    worker = lambda task: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task, WORKER)
    assert worker(first['task_id'])['daily_allowance']['used'] == 1
    stopped = worker(second['task_id'])
    assert stopped['outcome'] is None
    assert stopped['progress']['reason'] == 'scheduled_daily_new_post_allowance_exhausted'
    assert stopped['daily_allowance']['remaining'] == 0
    assert len(requests) == 1
    owner.configure(config(daily_allowance=2, keywords=keywords), HUMAN, expected_version=1, live=True)
    assert ScheduledDiscovery(tasks, clock=Clock()).tick(WORKER)['created_occurrences'] == []
    refreshed = worker(second['task_id'])
    assert refreshed['outcome'] == 'no_usable_update'
    assert refreshed['daily_allowance']['used'] == 1
    assert refreshed['daily_allowance']['occurrence_counts']['deduplicated_posts'] == 1
    assert refreshed['coverage']['unchanged_records'] == 1
    assert len(requests) == 2


def test_http_activation_is_explicit_operator_save_and_never_dispatches_on_configuration_or_tick(stack, tmp_path, monkeypatch):
    import json
    from smi_review import ReviewApp
    from test_review import form, request, running

    owner, tasks, _ = live_schedule(stack, tmp_path)
    requests = http_boundary(monkeypatch, [])
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route,
                           schedule_operator=True, schedule_clock=Clock(), live_discovery_enabled=True)) as url:
        page = request(url, path='/schedules')[2]
        fields = form(page, '/schedules')
        assert fields['execution_mode'] == ['offline']
        fields.update(timezone=['Asia/Seoul'], daily_at=['09:00'], lookback_days=['7'], daily_allowance=['1'],
                      keywords=[json.dumps(config()['keywords'])], execution_mode=['live'])
        assert request(url, 'POST', '/schedules', {**fields, 'origin': ['schedule']})[0] == 422
        assert owner.read(HUMAN)['version'] == 0
        assert request(url, 'POST', '/schedules', fields)[0] == 303
        page = request(url, path='/schedules')[2]
        assert 'Recorded live activation' in page
        assert 'brightdata-tiktok-keyword' in page
        assert request(url, 'POST', '/schedules/tick', form(page, '/schedules/tick'))[0] == 303
        assert len(tasks.list(HUMAN)) == 1
    assert requests == []
    app = ReviewApp(tasks.db, actor_id=HUMAN.actor_id, schedule_clock=Clock())
    with running(app) as url:
        page = request(url, path='/schedules')[2]
        assert 'Recorded live activation' in page
        assert request(url, 'POST', '/schedules', {**fields, 'csrf': [app.csrf]})[0] == 422


@pytest.mark.parametrize('change', ['version', 'limits', 'freshness', 'manifest'])
def test_live_activation_needs_operator_and_trusted_mutation_gate_while_default_never_changes_route(stack, tmp_path, monkeypatch, change):
    import json
    from smi_ingestion.contracts import RunLimits
    from smi_tasks.discovery import DiscoveryPolicy
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import OfflineRoute

    owner, tasks, _ = live_schedule(stack, tmp_path)
    requests = http_boundary(monkeypatch, [])
    with pytest.raises(EvidenceError, match='schedule_operator_authority_required'):
        owner.configure(config(), WORKER, expected_version=0, live=True)
    disabled = ScheduledDiscovery(AcquisitionTasks(tasks.db, route=tasks.route, authority=tasks.authority), clock=Clock())
    with pytest.raises(EvidenceError, match='live_discovery_disabled'):
        disabled.configure(config(), HUMAN, expected_version=0, live=True)
    owner.configure(config(), HUMAN, expected_version=0)
    assert owner.read(HUMAN)['live_activation'] is False
    refused = owner.tick(WORKER)['created_occurrences'][0]
    assert refused['status'] == 'refused'
    assert tasks.list(HUMAN) == []
    owner.configure(config(), HUMAN, expected_version=1, live=True)
    assert owner.tick(WORKER)['created_occurrences'] == []
    # A new keyword is a distinct occurrence, still under the same day/account.
    edited = config(keywords=[{'key': 'new', 'query': 'review', 'subject_ids': ['product:sunscreen']}])
    owner.configure(edited, HUMAN, expected_version=2, live=True)
    changed_route = OfflineRoute(tasks.route.manifest_path, 'changed-version')
    if change == 'limits':
        changed_route = OfflineRoute(tasks.route.manifest_path, tasks.route.version, limits=RunLimits(9, 10, 10))
    elif change == 'freshness':
        changed_route = OfflineRoute(tasks.route.manifest_path, tasks.route.version, discovery_policy=DiscoveryPolicy(86400, 'canonical-v1'))
    elif change == 'manifest':
        manifest = json.loads(tasks.route.manifest_path.read_text())
        manifest['policy']['context_id'] = 'changed-policy-context'
        tasks.route.manifest_path.write_text(json.dumps(manifest))
        changed_route = tasks.route
    changed_tasks = AcquisitionTasks(tasks.db, route=changed_route, authority=tasks.authority, live_discovery_enabled=True)
    changed = ScheduledDiscovery(changed_tasks, clock=Clock()).tick(WORKER)['created_occurrences'][0]
    assert changed['reason'] == 'live_schedule_route_configuration_changed'
    assert changed['context']['route_authority']['route_version'] == tasks.route.version
    assert tasks.list(HUMAN) == []
    assert requests == []


def test_pending_snapshot_get_recovery_survives_cap_exhaustion_restart_and_schedule_deactivation(stack, tmp_path, monkeypatch):
    from datetime import timedelta

    clock = Clock()
    owner, tasks, evidence = live_schedule(stack, tmp_path, clock=clock)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [(202, {'snapshot_id': 'sd_scheduled'}), (200, [post()]),
        (200, {'snapshot_id': 'sd_scheduled', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'ready'}),
        (200, [post(post_id='2222', url='https://www.tiktok.com/@example/video/2222')])])
    keywords = config()['keywords'] + [{'key': 'review', 'query': 'review', 'subject_ids': ['product:sunscreen']}]
    owner.configure(config(daily_allowance=1, keywords=keywords), HUMAN, expected_version=0, live=True)
    pending, immediate = owner.tick(WORKER)['created_occurrences']
    worker = lambda task: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), clock=clock).run_one(task, WORKER)
    waiting = worker(pending['task_id'])
    assert waiting['progress']['code'] == 'provider_pending'
    assert worker(immediate['task_id'])['daily_allowance']['used'] == 1
    owner.configure(config(daily_allowance=1, keywords=keywords), HUMAN, expected_version=1)
    assert owner.read(HUMAN)['live_activation'] is False
    assert ScheduledDiscovery(tasks, clock=clock).tick(WORKER)['created_occurrences'] == []
    not_due = worker(pending['task_id'])
    assert not_due['progress']['reason'] == 'provider_retry_not_due'
    assert len(requests) == 2
    clock.at += timedelta(seconds=10)
    assert worker(pending['task_id'])['progress']['code'] == 'provider_pending'
    completed = worker(pending['task_id'])
    assert completed['outcome'] == 'no_usable_update'
    assert completed['coverage']['returned_records'] == 1
    assert completed['coverage']['admitted_records'] == 0
    assert completed['coverage']['published_records'] == 0
    assert completed['daily_allowance']['used'] == 1
    assert completed['daily_allowance']['occurrence_counts']['limit_excluded_posts'] == 1
    assert completed['scope']['schedule']['configuration_version'] == 1
    assert [r.get_method() for r in requests] == ['POST', 'POST', 'GET', 'GET']
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '4'
    assert worker(pending['task_id']) == completed
    assert len(requests) == 4


def test_concurrent_live_workers_share_atomic_day_even_when_both_paid_requests_started_before_exhaustion(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from urllib.request import OpenerDirector

    owner, tasks, evidence = live_schedule(stack, tmp_path)
    live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()]),
        (200, [post(post_id='2222', url='https://www.tiktok.com/@example/video/2222')])])
    simulated_http = OpenerDirector.open
    barrier = Barrier(2)

    def send(opener, request, data=None, timeout=None):
        if request.full_url.startswith('https://api.brightdata.com/'):
            barrier.wait(timeout=15)
        return simulated_http(opener, request, data, timeout)

    monkeypatch.setattr(OpenerDirector, 'open', send)
    keywords = config()['keywords'] + [{'key': 'review', 'query': 'review', 'subject_ids': ['product:sunscreen']}]
    owner.configure(config(daily_allowance=1, keywords=keywords), HUMAN, expected_version=0, live=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        ticks = list(executor.map(lambda _: ScheduledDiscovery(tasks, clock=Clock()).tick(WORKER), range(2)))
    task_ids = [o['task_id'] for tick in ticks for o in tick['created_occurrences']]
    assert len(task_ids) == 2
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda task: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task, WORKER), task_ids))
    assert len(requests) == 2
    assert sum(r['daily_allowance']['occurrence_counts']['new_posts'] for r in results) == 1
    assert sum(r['daily_allowance']['occurrence_counts']['limit_excluded_posts'] for r in results) == 1
    assert sorted(r['outcome'] for r in results) == ['no_usable_update', 'usable_update']
    assert owner.read(HUMAN)['daily_allowance']['used'] == 1
    assert ScheduledDiscovery(tasks, clock=Clock()).tick(WORKER)['created_occurrences'] == []


def test_scheduled_live_work_uses_shared_money_ceiling_before_every_snapshot_get(stack, tmp_path, monkeypatch):
    from datetime import timedelta

    clock = Clock()
    owner, tasks, evidence = live_schedule(stack, tmp_path, clock=clock)
    costs = live_costs(tasks, ceiling_amount='1')
    requests = http_boundary(monkeypatch, [(202, {'snapshot_id': 'sd_money'})])
    owner.configure(config(), HUMAN, expected_version=0, live=True)
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), clock=clock).run_one(task_id, WORKER)
    assert worker()['progress']['code'] == 'provider_pending'
    clock.at += timedelta(seconds=10)
    stopped = worker()
    assert stopped['outcome'] is None
    assert stopped['progress']['reason'] == 'cost_allowance_exhausted'
    assert stopped['daily_allowance']['used'] == 0
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'
    assert len(requests) == 1



def test_scheduled_retrieval_keeps_unknown_capture_freshness_and_reports_unchanged_support(stack, tmp_path, monkeypatch):
    from smi_tasks import OfflineRoute
    from smi_tasks.discovery import DiscoveryPolicy

    owner, tasks, evidence = live_schedule(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(tasks.route.manifest_path, tasks.route.version,
        discovery_policy=DiscoveryPolicy(86400, 'canonical-v1')), authority=tasks.authority, live_discovery_enabled=True)
    owner = ScheduledDiscovery(tasks, clock=Clock())
    live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()]), (200, [post()])])
    owner.configure(config(), HUMAN, expected_version=0, live=True)
    first = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    assert OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(first, WORKER)['outcome'] == 'usable_update'
    owner.configure(config(keywords=[{'key': 'replacement', 'query': 'sunscreen review', 'subject_ids': ['product:sunscreen']}]),
                    HUMAN, expected_version=1, live=True)
    second = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(second, WORKER)
    assert completed['discovery_history']['decision'] == 'retrieve'
    assert completed['discovery_history']['reason'] == 'capture_time_unknown'
    assert completed['outcome'] == 'no_usable_update'
    assert completed['coverage']['returned_records'] == 1
    assert completed['coverage']['unchanged_records'] == 1
    assert completed['publication_ids'] == []
    assert completed['daily_allowance']['used'] == 1
    assert len(requests) == 2
