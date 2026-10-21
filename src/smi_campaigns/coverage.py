"""One explicit coverage decision over an immutable current-KB comparison."""

from datetime import datetime, timedelta


PROFILE = {
    'version': 'supported-campaign-coverage-v1',
    'minimum_candidates': 3,
    'minimum_relevant_candidates': 3,
    'minimum_fresh_candidates': 3,
    'maximum_capture_age_seconds': 30 * 24 * 60 * 60,
    'relevance': 'at_least_one_satisfied_include_criterion_with_pinned_support',
    'freshness': 'all_candidate_support_captures_known_not_future_and_within_30_days',
    'scope': 'bounded_current_knowledge_not_market_coverage',
    'discovery': 'first_human_product_else_brand_catalog_name_30_days_intersect_human_window_v1',
}


def assess(candidates, comparison_id: str, assessed_at: datetime) -> dict:
    """Pin thresholds, clock and exact input references without copying source bodies.

    Eligible accounts count independently of literal relevance. Freshness uses
    every pinned source capture for an eligible account; missing/future captures
    remain unknown. Import/publication time never renews a source capture.
    """
    eligible = [c for c in candidates if c['body']['assessment'] == 'eligible_with_explicit_gaps']
    relevant, fresh, stale, unknown = 0, 0, 0, 0
    for candidate in eligible:
        body = candidate['body']
        relevant += any(j['state'] == 'satisfied' and j['support_ids'] for j in body['judgments'])
        dates = [datetime.fromisoformat(d['captured_at'].replace('Z', '+00:00')) if d['captured_at'] else None
                 for d in body['source_dates']]
        if not dates or any(d is None or d > assessed_at for d in dates):
            unknown += 1
        elif any(assessed_at - d > timedelta(seconds=PROFILE['maximum_capture_age_seconds']) for d in dates):
            stale += 1
        else:
            fresh += 1
    reasons = [reason for actual, required, reason in (
        (len(eligible), PROFILE['minimum_candidates'], 'insufficient_quantity'),
        (relevant, PROFILE['minimum_relevant_candidates'], 'insufficient_relevance'),
        (fresh, PROFILE['minimum_fresh_candidates'], 'insufficient_freshness'),
    ) if actual < required]
    return {'profile': dict(PROFILE), 'assessed_at': assessed_at.isoformat(), 'clock_basis': 'server_utc',
            'inputs': {'comparison_id': comparison_id, 'candidate_ids': [str(c['id']) for c in candidates]},
            'result': {'sufficient': not reasons, 'reasons': reasons, 'eligible_candidates': len(eligible),
                       'relevant_candidates': relevant, 'fresh_candidates': fresh,
                       'stale_candidates': stale, 'unknown_capture_candidates': unknown}}
