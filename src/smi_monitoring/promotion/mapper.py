"""Deterministic source-shaped X mapping with no account inference."""

import json
from datetime import datetime

from smi_ingestion.contracts import ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch


class ExistingCaptureOnly:
    """Reject collection: this route only maps a capture already owned by recent."""

    def collect(self, manifest, checkpoint, limits):
        raise ValueError('monitoring_promotion_cannot_collect')


class RecentXMapper:
    """Map retained X content, preserving native metric meanings and unknown author."""

    version = 'recent-x-content-v1'

    def normalize(self, observation, payload):
        record = json.loads(payload)
        key = ExternalKey('x', 'public', 'content', record['native_id'])
        fields = (FieldCandidate(key, 'caption', 'observed', record['body']['text'], '$.body.text'),
                  FieldCandidate(key, 'published_at', 'observed' if record['published_at'] else 'not_returned', record['published_at'], '$.published_at'),
                  FieldCandidate(key, 'author_account', 'not_returned', None, '$.author_account', 'source_did_not_return_author'))
        measured = datetime.fromisoformat(record['metric_measured_at']) if record['metric_measured_at'] else None
        metrics = tuple(MetricCandidate(key, 'x_public_' + name, name, value, None, 'exact', 'count', measured, '$.body.metrics.' + name)
                        for name, value in record['body']['metrics'].items())
        return NormalizedBatch((key,), fields, metrics)
