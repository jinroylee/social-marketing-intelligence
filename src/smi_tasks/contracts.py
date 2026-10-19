"""Trusted offline route configuration; browser/model text never selects a collector."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from smi_ingestion.contracts import RunLimits
from smi_ingestion.evidence import EvidenceError


@dataclass(frozen=True)
class OfflineRoute:
    """Operator-selected synthetic fixture input and hard execution bounds."""

    manifest_path: Path
    version: str = 'offline-fixture-v1'
    limits: RunLimits = RunLimits(max_requests=10, max_pages=10, max_records=10)

    def snapshot(self) -> tuple[Path, str, dict[str, Any]]:
        """Validate configuration without reading payloads or performing collection."""
        if (not isinstance(self.version, str) or not self.version.strip() or len(self.version) > 100
                or not isinstance(self.limits, RunLimits)):
            raise EvidenceError('invalid_offline_route')
        if any(type(v) is not int or not 1 <= v <= bound for v, bound in (
            (self.limits.max_requests, 100), (self.limits.max_pages, 100),
            (self.limits.max_records, 100), (self.limits.max_bytes, 10_485_760),
        )):
            raise EvidenceError('invalid_task_limits')
        path = self.manifest_path.resolve()
        try:
            if path.stat().st_size > 1_048_576:
                raise EvidenceError('invalid_offline_route')
            raw = path.read_bytes()
            manifest = json.loads(raw)
            if (not isinstance(manifest, dict) or manifest.get('adapter') != 'fixture-json'
                    or manifest.get('synthetic') is not True):
                raise EvidenceError('unsupported_task_route')
            items = manifest.get('items')
            if (not isinstance(items, list) or len(items) > 100
                    or any(not isinstance(item, dict) or not isinstance(item.get('path'), str)
                           or not isinstance(item.get('reference', ''), str) for item in items)):
                raise EvidenceError('invalid_offline_route')
        except (OSError, ValueError, TypeError) as error:
            raise EvidenceError('invalid_offline_route') from error
        return path, hashlib.sha256(raw).hexdigest(), manifest
