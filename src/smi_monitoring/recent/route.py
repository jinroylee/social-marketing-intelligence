"""One bounded local JSON route; original source times are never local import times."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from smi_ingestion.evidence import EvidenceError
from smi_monitoring.contracts import require


MAX_FILE_BYTES = 262144
MAX_FILE_RECORDS = 200
METRICS = {
    'like_count': 'X public likes at metric_measured_at; missing is unknown, not zero.',
    'repost_count': 'X public reposts at metric_measured_at; excludes any assumed unique audience.',
    'reply_count': 'X public replies at metric_measured_at; not sentiment or controversy.',
    'view_count': 'X reported views at metric_measured_at; not unique viewers or impressions on another source.',
}


def instant(value):
    """Normalize an explicit timezone-aware timestamp to UTC."""
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.utcoffset() is not None, 'recent_x_timezone_required')
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError, TypeError) as error:
        raise EvidenceError('invalid_recent_x_time') from error


def fingerprint(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def capture_identity(record, response_id=None):
    """Pin native post and original capture; an import label grants no new identity."""
    if response_id is not None:
        return fingerprint({'source': 'x-api-v2', 'response_id': response_id, 'native_id': record['native_id']})
    basis = {'native_id': record['native_id'], 'captured_at': record['captured_at']}
    if record['captured_at'] is None:
        # Unknown captures cannot establish a refresh; retain the available source times.
        basis.update(published_at=record['published_at'], metric_measured_at=record['metric_measured_at'])
    return fingerprint(basis)


def capture_fingerprint(record):
    return fingerprint({k: v for k, v in record.items() if k != 'capture_id'})


class OfflineXRoute:
    """Read at most one 256 KiB local fixture per poll, with no network capability."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def collect(self):
        """Return validated bounded source captures and declared fixture coverage."""
        try:
            require(self.path.is_file(), 'recent_x_fixture_unavailable')
            with self.path.open('rb') as source:
                raw = source.read(MAX_FILE_BYTES + 1)
            require(len(raw) <= MAX_FILE_BYTES, 'recent_x_file_limit')
            document = json.loads(raw)
        except (OSError, ValueError, UnicodeError) as error:
            raise EvidenceError('recent_x_fixture_unavailable') from error
        require(isinstance(document, dict) and set(document) == {'coverage', 'records'}, 'invalid_recent_x_fixture')
        require(isinstance(document['coverage'], str) and document['coverage'] in {'complete', 'partial', 'missing'}, 'invalid_recent_x_coverage')
        records = document['records']
        require(isinstance(records, list) and len(records) <= MAX_FILE_RECORDS, 'recent_x_file_record_limit')
        require(document['coverage'] != 'missing' or not records, 'invalid_recent_x_coverage')
        validated = validate_records(records)
        return validated, {'route': 'offline-x-json', 'version': 'offline-x-v1', 'synthetic': True,
                           'fixture_sha256': hashlib.sha256(raw).hexdigest(), 'bytes_read': len(raw), 'requests': 1,
                           'declared_coverage': document['coverage']}


def validate_records(records):
    """Normalize bounded recent captures; source times retain their original meaning."""
    validated = []
    for record in records:
        require(isinstance(record, dict) and set(record) == {'capture_id', 'native_id', 'text', 'published_at', 'captured_at', 'metric_measured_at', 'metrics'}, 'invalid_recent_x_record')
        require(isinstance(record['capture_id'], str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', record['capture_id']), 'invalid_recent_x_capture_id')
        require(isinstance(record['native_id'], str) and re.fullmatch(r'[0-9]{1,24}', record['native_id']), 'invalid_recent_x_native_id')
        require(record['text'] is None or isinstance(record['text'], str) and len(record['text']) <= 4096 and '\x00' not in record['text'], 'invalid_recent_x_text')
        normalized = dict(record)
        for key in ('published_at', 'captured_at', 'metric_measured_at'):
            normalized[key] = instant(record[key]).isoformat() if record[key] is not None else None
        metrics = record['metrics']
        require(isinstance(metrics, dict) and metrics.keys() <= METRICS.keys(), 'invalid_recent_x_metrics')
        require(all(type(v) is int and 0 <= v <= 10**15 for v in metrics.values()), 'invalid_recent_x_metrics')
        validated.append(normalized)
    return validated
