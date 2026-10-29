"""Quantitative alerts through public collection, assessment, history and inbox seams."""

from datetime import datetime, timezone

from smi_monitoring.recent import RecentMonitoring
from test_recent_monitoring import OPERATOR, READER, RECORD, configured, fixture_route, no_external_io as recent_no_external_io
from test_campaigns import campaigns as campaigns_fixture


no_external_io = recent_no_external_io
campaigns = campaigns_fixture


def collect_pair(stack, tmp_path, baseline=1, detection=4):
    recent = configured(stack, tmp_path)
    recent.configure('cushion', {**recent.read_topic('cushion', READER)['revisions'][-1]['document'],
                               'window_minutes': 60}, OPERATOR, expected_version=1, request_id='hourly')
    ids = []
    for end, hour, count, first in [('2026-10-28T11:00:00Z', 10, baseline, 1),
                                    ('2026-10-28T12:00:00Z', 11, detection, 10)]:
        records = [{**RECORD, 'capture_id': f'post-{i}', 'native_id': str(i),
                    'published_at': f'2026-10-28T{hour}:10:00Z',
                    'captured_at': f'2026-10-28T{hour}:30:00Z',
                    'metric_measured_at': None, 'metrics': {}}
                   for i in range(first, first + count)]
        recent.route = fixture_route(tmp_path, records)
        ids.append(recent.poll('cushion', end, OPERATOR)['window_id'])
    return recent, ids[0], ids[1]


def alerts(recent):
    from smi_monitoring.alerts import QuantitativeAlerts, VolumeThreshold
    owner = QuantitativeAlerts(recent, threshold=VolumeThreshold(minimum_baseline_posts=1,
        minimum_increase_posts=3, minimum_ratio=3), clock=lambda: datetime(2026, 10, 28, 12, tzinfo=timezone.utc))
    owner.migrate()
    return owner


def test_supported_volume_change_retains_one_alert_and_local_notification_after_restart(stack, tmp_path):
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    result = owner.detect(detection, baseline, OPERATOR, request_id='volume-1')
    assert result['outcome'] == 'significant_change'
    assert result['comparison'] == {'baseline_posts': 1, 'detection_posts': 4, 'increase_posts': 3, 'ratio': 4.0}
    assert result['method']['version'] == 'distinct-post-volume-v1'
    assert result['method']['configuration']['minimum_ratio'] == 3
    assert result['windows']['baseline']['window_id'] == baseline
    assert result['windows']['detection']['window_id'] == detection
    assert result['windows']['detection']['coverage']['field_coverage'] == 'partial'
    restarted = alerts(RecentMonitoring(stack[0], clock=recent.clock))
    assert restarted.read_assessment(result['assessment_id'], READER) == result
    assert restarted.read_alert(result['alert_id'], READER)['assessment_id'] == result['assessment_id']
    notifications = restarted.notifications(READER)
    assert len(notifications) == 1
    assert notifications[0]['alert_id'] == result['alert_id']
    assert '1 → 4 distinct X posts' in notifications[0]['message']
    assert 'synthetic' in notifications[0]['message'].lower()
    assert 'market' in notifications[0]['message'].lower()


def test_repeated_captures_are_one_post_and_no_change_creates_no_notification(stack, tmp_path):
    recent, baseline, _ = collect_pair(stack, tmp_path, baseline=1, detection=1)
    recent.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    records = [{**RECORD, 'capture_id': f'capture-{minute}', 'native_id': '99',
                'published_at': '2026-10-28T12:10:00Z', 'captured_at': f'2026-10-28T12:{minute}:00Z',
                'metric_measured_at': None, 'metrics': {}} for minute in ('20', '30', '40', '50')]
    recent.route = fixture_route(tmp_path, records)
    window = recent.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id']
    owner = alerts(recent)
    result = owner.detect(window, baseline, OPERATOR, request_id='same-volume')
    assert result['outcome'] == 'no_change'
    assert result['comparison']['detection_posts'] == 1
    assert result['alert_id'] is None
    assert owner.notifications(READER) == []
    assert owner.history(READER)[0]['assessment_id'] == result['assessment_id']


def test_missing_baseline_is_retained_without_a_spike_claim(stack, tmp_path):
    recent, _, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    result = owner.detect(detection, None, OPERATOR, request_id='missing')
    assert result['outcome'] == 'not_assessable'
    assert result['limitations'] == ['baseline_missing']
    assert result['comparison'] is None and result['alert_id'] is None
    assert owner.notifications(READER) == []
    assert owner.history(READER)[0] == result


def test_empty_window_denied_policy_cannot_be_claimed_as_zero_activity(stack, tmp_path):
    from test_recent_monitoring import POLICY
    recent, baseline, detection = collect_pair(stack, tmp_path, detection=0)
    owner = alerts(recent)
    recent.set_policy({**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
    result = owner.detect(detection, baseline, OPERATOR, request_id='denied-empty')
    assert result['outcome'] == 'not_assessable'
    assert result['current_support'] == 'unavailable'
    assert result['windows']['detection']['current_permissions']['process'] is False
    assert result['comparison'] is None


def test_process_denial_withholds_nested_alert_evidence_and_http_but_preserves_standalone_display(stack, tmp_path, campaigns):
    from smi_review import ReviewApp
    from test_recent_monitoring import POLICY
    from test_review import request, running

    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    saved = owner.detect(detection, baseline, OPERATOR, request_id='process-denial')
    recent.set_policy({**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
    for reopened in (owner.read_alert(saved['alert_id'], READER),
                     owner.read_assessment(saved['assessment_id'], READER), owner.history(READER)[0]):
        assert reopened['outcome'] == 'significant_change'
        assert reopened['alert_id'] == saved['alert_id'] and reopened['notification_id'] == saved['notification_id']
        assert reopened['current_support'] == 'unavailable' and reopened['comparison'] is None
        assert all(o['body'] is None and o['state'] == 'permission_denied'
            for w in reopened['windows'].values() for o in w['observations'])
        assert all(not w['support_permitted'] for w in reopened['windows'].values())
    assert owner.notifications(READER)[0]['current_support'] == 'unavailable'
    assert recent.read_window(detection, READER)['observations'][0]['body']['text'] == 'A cushion <sample>'
    with running(ReviewApp(stack[0], READER.actor_id, monitoring_clock=recent.clock)) as url:
        for path in ('/monitoring/assessments/' + saved['assessment_id'], '/monitoring/alerts/' + saved['alert_id']):
            status, _, page = request(url, path=path)
            assert status == 200 and 'unavailable' in page.lower()
            assert 'A cushion' not in page and '1 → 4' not in page
        assert 'A cushion &lt;sample&gt;' in request(url, path='/monitoring/windows/' + detection)[2]


def test_http_detection_inbox_restart_and_withdrawal_keep_current_evidence_governed(stack, tmp_path, campaigns):
    from smi_review import ReviewApp
    from test_review import form, request, running
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    app = ReviewApp(stack[0], OPERATOR.actor_id, monitoring_operator=True,
        monitoring_clock=recent.clock, monitoring_threshold=owner.threshold)
    with running(app) as url:
        status, _, page = request(url, path='/monitoring/assessments')
        assert status == 200
        action = '/monitoring/assessments'
        fields = form(page, action)
        fields.update(baseline_window_id=[baseline], detection_window_id=[detection], request_id=['browser-volume'])
        status, headers, page = request(url, 'POST', action, fields)
        assert status == 303, page
        assessment_path = headers['Location']
        status, _, page = request(url, path=assessment_path)
        assert status == 200 and '1 → 4' in page
        assert 'A cushion &lt;sample&gt;' in page
        _, _, page = request(url, path='/inbox')
        assert '1 → 4 distinct X posts' in page
        assert 'A cushion' not in page
    alert_id = owner.notifications(READER)[0]['alert_id']
    recent.withdraw('10', OPERATOR)
    restarted = ReviewApp(stack[0], OPERATOR.actor_id, monitoring_clock=recent.clock)
    with running(restarted) as url:
        for path in ('/inbox', assessment_path, '/monitoring/alerts/' + alert_id):
            status, _, page = request(url, path=path)
            assert status == 200
            assert '1 → 4' not in page
            assert 'unavailable' in page.lower()
    assert owner.read_alert(alert_id, READER)['comparison'] is None
    assert len(owner.notifications(READER)) == 1


def test_sampling_changes_and_incomplete_windows_record_limitations_without_alert(stack, tmp_path):
    recent, baseline, _ = collect_pair(stack, tmp_path)
    settings = recent.read_topic('cushion', READER)['revisions'][-1]['document']
    recent.configure('cushion', {**settings, 'max_records': 9}, OPERATOR, expected_version=2, request_id='sampling-change')
    recent.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    records = [{**RECORD, 'capture_id': str(i), 'native_id': str(i), 'published_at': '2026-10-28T12:10:00Z',
                'captured_at': '2026-10-28T12:30:00Z'} for i in range(30, 34)]
    recent.route = fixture_route(tmp_path, records)
    changed = recent.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id']
    owner = alerts(recent)
    result = owner.detect(changed, baseline, OPERATOR, request_id='sampling')
    assert result['outcome'] == 'not_assessable'
    assert 'max_records_incomparable' in result['limitations']
    assert result['comparison'] is None
    recent.configure('cushion', settings, OPERATOR, expected_version=3, request_id='restore')
    recent.clock = lambda: datetime(2026, 10, 28, 14, tzinfo=timezone.utc)
    recent.route = fixture_route(tmp_path, [], 'missing')
    missing = recent.poll('cushion', '2026-10-28T14:00:00Z', OPERATOR)['window_id']
    result = owner.detect(missing, baseline, OPERATOR, request_id='missing-coverage')
    assert result['limitations'] == ['collection_incomplete']
    assert result['windows']['detection']['coverage']['collection_status'] == 'missing'
    assert result['comparison'] is None and owner.notifications(READER) == []


def test_retry_and_concurrent_pair_detection_deliver_one_notification_and_protect_actor(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda i: owner.detect(detection, baseline, OPERATOR, request_id=f'concurrent-{i}'), range(2)))
    assert results[0] == results[1]
    saved = results[0]
    assert owner.detect(detection, baseline, OPERATOR, request_id='concurrent-0') == saved
    assert len(owner.history(READER)) == len(owner.notifications(READER)) == 1
    with pytest.raises(EvidenceError, match='request_conflict'):
        owner.detect(detection, None, OPERATOR, request_id='concurrent-0')
    other = ActorContext('local', 'other-operator', 'human')
    competing = alerts(RecentMonitoring(stack[0], operators=frozenset({other.actor_id}), clock=recent.clock))
    with pytest.raises(EvidenceError, match='request_conflict'):
        competing.detect(detection, baseline, other, request_id='concurrent-0')
    with pytest.raises(EvidenceError, match='operator_required'):
        owner.detect(detection, baseline, READER, request_id='unauthorized')
    foreign = ActorContext('foreign', 'reader', 'human')
    with pytest.raises(EvidenceError, match='workspace'):
        owner.read_alert(saved['alert_id'], foreign)


def test_zero_baseline_never_divides_and_complete_zero_detection_is_scoped_no_change(stack, tmp_path):
    recent, baseline, detection = collect_pair(stack, tmp_path, baseline=0)
    owner = alerts(recent)
    result = owner.detect(detection, baseline, OPERATOR, request_id='zero-baseline')
    assert result['outcome'] == 'not_assessable'
    assert result['limitations'] == ['baseline_below_minimum']
    assert result['comparison'] is None and result['alert_id'] is None
    recent.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    recent.route = fixture_route(tmp_path, [])
    empty = recent.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id']
    result = owner.detect(empty, detection, OPERATOR, request_id='zero-detection')
    assert result['outcome'] == 'no_change'
    assert result['comparison'] == {'baseline_posts': 4, 'detection_posts': 0, 'increase_posts': -4, 'ratio': 0.0}
    assert owner.notifications(READER) == []


def test_policy_withdrawal_and_expiry_never_reconstruct_alert_counts_or_wording(stack, tmp_path):
    from test_recent_monitoring import POLICY
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    saved = owner.detect(detection, baseline, OPERATOR, request_id='original')
    recent.set_policy({**POLICY, 'can_display': False}, OPERATOR, expected_version=1)
    denied = owner.read_alert(saved['alert_id'], READER)
    assert denied['comparison'] is None and denied['current_support'] == 'unavailable'
    assert 'A cushion' not in str(denied)
    assert '1 → 4' not in owner.notifications(READER)[0]['message']
    recent.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=2)
    recent.set_policy(POLICY, OPERATOR, expected_version=3)
    assert owner.detect(detection, baseline, OPERATOR, request_id='original')['comparison'] is None
    assert owner.read_alert(saved['alert_id'], READER)['outcome'] == 'significant_change'
    assert len(owner.notifications(READER)) == 1
    recent.clock = lambda: datetime(2026, 10, 30, 12, tzinfo=timezone.utc)
    reopened = owner.read_assessment(saved['assessment_id'], READER)
    assert reopened['comparison'] is None
    assert all(o['body'] is None for w in reopened['windows'].values() for o in w['observations'])


def test_failed_alert_commit_rolls_back_assessment_and_notification_together(stack, tmp_path):
    import psycopg
    import pytest
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    with stack[0].connect() as connection:
        connection.execute("CREATE FUNCTION fail_alert() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'simulated alert commit failure'; END $$")
        connection.execute('CREATE TRIGGER fail_alert BEFORE INSERT ON monitoring_alerts FOR EACH ROW EXECUTE FUNCTION fail_alert()')
    with pytest.raises(psycopg.Error):
        owner.detect(detection, baseline, OPERATOR, request_id='atomic-alert')
    assert owner.history(READER) == [] and owner.notifications(READER) == []
    with stack[0].connect() as connection:
        connection.execute('DROP TRIGGER fail_alert ON monitoring_alerts')
    saved = owner.detect(detection, baseline, OPERATOR, request_id='atomic-alert')
    assert owner.notifications(READER)[0]['alert_id'] == saved['alert_id']


def test_native_publication_time_conflict_between_windows_cannot_establish_new_volume(stack, tmp_path):
    recent, baseline, _ = collect_pair(stack, tmp_path)
    recent.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    records = [{**RECORD, 'capture_id': 'later-1', 'native_id': '1',
                'published_at': '2026-10-28T12:10:00Z', 'captured_at': '2026-10-28T12:30:00Z'}]
    recent.route = fixture_route(tmp_path, records)
    detection = recent.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id']
    result = alerts(recent).detect(detection, baseline, OPERATOR, request_id='time-conflict')
    assert result['outcome'] == 'not_assessable'
    assert result['limitations'] == ['native_publication_incomparable']
    assert result['comparison'] is None


def test_policy_mutation_waits_until_atomic_alert_commit_then_hides_the_claim(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from test_recent_monitoring import POLICY
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    with stack[0].connect() as connection:
        connection.execute("CREATE FUNCTION pause_alert() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(937430); RETURN NEW; END $$")
        connection.execute('CREATE TRIGGER pause_alert BEFORE INSERT ON monitoring_alerts FOR EACH ROW EXECUTE FUNCTION pause_alert()')
    with stack[0].connect() as gate, ThreadPoolExecutor(max_workers=2) as pool:
        gate.execute('SELECT pg_advisory_xact_lock(937430)')
        detection_future = pool.submit(owner.detect, detection, baseline, OPERATOR, request_id='policy-race')
        deadline = time.monotonic() + 5
        detection_pid = None
        while time.monotonic() < deadline:
            with stack[0].connect() as diagnostic:
                row = diagnostic.execute("SELECT pid FROM pg_locks WHERE locktype='advisory' AND objid=937430 AND NOT granted").fetchone()
            if row:
                detection_pid = row['pid']
                break
            time.sleep(0.01)
        if detection_pid is None:
            gate.commit()
        assert detection_pid is not None, 'detector did not reach injected commit pause'
        policy_future = pool.submit(recent.set_policy, {**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
        blocked = False
        while time.monotonic() < deadline:
            with stack[0].connect() as diagnostic:
                blocked = diagnostic.execute('SELECT EXISTS (SELECT 1 FROM pg_stat_activity WHERE %s=ANY(pg_blocking_pids(pid))) AS blocked', (detection_pid,)).fetchone()['blocked']
            if blocked:
                break
            time.sleep(0.01)
        # Release the injected pause even if the assertion fails, so cleanup can finish.
        gate.commit()
        saved = detection_future.result(timeout=5)
        policy_future.result(timeout=5)
        assert blocked, 'policy mutation escaped the detector commit transaction'
    assert saved['outcome'] == 'significant_change'
    assert owner.read_alert(saved['alert_id'], READER)['comparison'] is None
    assert owner.notifications(READER)[0]['current_support'] == 'unavailable'


def test_protected_http_detection_preserves_retry_and_rejects_scope_or_actor_authority(stack, tmp_path, campaigns):
    from smi_review import ReviewApp
    from test_review import form, request, running
    from smi_tasks import AcquisitionTasks
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    app = ReviewApp(stack[0], OPERATOR.actor_id, monitoring_operator=True,
        monitoring_clock=recent.clock, monitoring_threshold=owner.threshold)
    with running(app) as url:
        _, _, page = request(url, path='/monitoring/assessments')
        fields = form(page, '/monitoring/assessments')
        fields.update(baseline_window_id=[baseline], detection_window_id=[detection], request_id=['protected-volume'])
        for authority in ('actor_id', 'query', 'campaign_id', 'source_policy', 'threshold', 'search_query'):
            status, _, page = request(url, 'POST', '/monitoring/assessments', {**fields, authority: ['forged']})
            assert status == 422 and 'invalid_form' in page
            assert baseline in page and detection in page and 'protected-volume' in page
        assert owner.history(READER) == []
        status, headers, _ = request(url, 'POST', '/monitoring/assessments', fields)
        assert status == 303
        status, retry_headers, _ = request(url, 'POST', '/monitoring/assessments', fields)
        assert status == 303 and retry_headers['Location'] == headers['Location']
        status, _, page = request(url, 'POST', '/monitoring/assessments', {**fields, 'baseline_window_id': ['']})
        assert status == 409 and 'detection_request_conflict' in page
        assert 'protected-volume' in page
    assert campaigns[0].list_campaigns(READER) == []
    assert AcquisitionTasks(stack[0]).list(READER) == []


def test_overlap_and_changed_query_are_incomparable_even_with_complete_fixture_coverage(stack, tmp_path):
    recent, baseline, _ = collect_pair(stack, tmp_path)
    settings = recent.read_topic('cushion', READER)['revisions'][-1]['document']
    recent.configure('cushion', {**settings, 'query': 'sample', 'window_minutes': 120}, OPERATOR,
                     expected_version=2, request_id='different-scope')
    recent.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    recent.route = fixture_route(tmp_path, [])
    changed = recent.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id']
    result = alerts(recent).detect(changed, baseline, OPERATOR, request_id='different-scope')
    assert result['outcome'] == 'not_assessable'
    assert result['limitations'] == ['query_incomparable', 'windows_incomparable']
    assert result['comparison'] is None and result['alert_id'] is None


def test_local_expiry_withholds_retained_alert_and_clock_recovery_cannot_restore_it(stack, tmp_path):
    recent, baseline, detection = collect_pair(stack, tmp_path)
    owner = alerts(recent)
    saved = owner.detect(detection, baseline, OPERATOR, request_id='local-expiry')
    recent.clock = lambda: datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
    expired = owner.read_alert(saved['alert_id'], READER)
    assert expired['comparison'] is None and expired['current_support'] == 'unavailable'
    assert all(o['state'] == 'retention_expired' for w in expired['windows'].values() for o in w['observations'])
    recent.clock = lambda: datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
    assert owner.detect(detection, baseline, OPERATOR, request_id='local-expiry')['comparison'] is None
    assert '1 → 4' not in owner.notifications(READER)[0]['message']


def test_partial_fixture_coverage_never_creates_alert_even_with_large_raw_count_change(stack, tmp_path):
    recent, baseline, _ = collect_pair(stack, tmp_path)
    recent.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    records = [{**RECORD, 'capture_id': str(i), 'native_id': str(i), 'published_at': '2026-10-28T12:10:00Z',
                'captured_at': '2026-10-28T12:30:00Z'} for i in range(30, 38)]
    recent.route = fixture_route(tmp_path, records, 'partial')
    detection = recent.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id']
    owner = alerts(recent)
    result = owner.detect(detection, baseline, OPERATOR, request_id='partial-eight')
    assert result['outcome'] == 'not_assessable' and result['comparison'] is None
    assert result['limitations'] == ['collection_incomplete']
    assert owner.notifications(READER) == []
