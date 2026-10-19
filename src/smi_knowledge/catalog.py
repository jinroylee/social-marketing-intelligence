"""Validated immutable human configuration for caption interpretation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smi_ingestion.evidence import EvidenceError


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceError(code)


@dataclass(frozen=True)
class Catalog:
    """Brand/Product references and literal aliases; configuration is human-supplied."""

    document: dict[str, Any]
    digest: str

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> Catalog:
        """Validate typed references and freeze a JSON copy with a canonical digest."""
        _require(isinstance(document, dict) and set(document) == {"catalog_id", "version", "brands", "products", "topics"},
                 "invalid_catalog")
        _require(document.get("version") == "v1", "unsupported_catalog_version")
        _require(isinstance(document.get("catalog_id"), str) and bool(document["catalog_id"].strip()), "invalid_catalog_id")
        for group in ("brands", "products", "topics"):
            entries = document[group]
            _require(isinstance(entries, list), "invalid_catalog_entries")
            ids = []
            for entry in entries:
                _require(isinstance(entry, dict), "invalid_catalog_entry")
                expected = {"id", "name", "aliases"}
                if group == "products":
                    expected |= {"brand_id", "specificity"}
                _require(set(entry) == expected, "invalid_catalog_entry")
                for key in ("id", "name"):
                    _require(isinstance(entry.get(key), str) and bool(entry[key].strip()), "invalid_catalog_reference")
                aliases = entry["aliases"]
                _require(isinstance(aliases, list) and all(isinstance(a, str) and a.strip() for a in aliases), "invalid_catalog_alias")
                ids.append(entry["id"])
            _require(len(ids) == len(set(ids)), "duplicate_catalog_reference")
        brands = {b["id"] for b in document["brands"]}
        for product in document["products"]:
            _require(isinstance(product["brand_id"], str) and product["brand_id"] in brands, "catalog_brand_not_found")
            _require(isinstance(product["specificity"], str) and product["specificity"] in {"family", "variant"}, "invalid_product_specificity")
        try:
            payload = json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
        except (TypeError, ValueError) as error:
            raise EvidenceError("invalid_catalog") from error
        return cls(json.loads(payload), hashlib.sha256(payload).hexdigest())

    @classmethod
    def load(cls, path: Path) -> Catalog:
        """Load local catalog configuration; no source or model requests are made."""
        if path.stat().st_size > 1024 * 1024:
            raise EvidenceError("catalog_too_large")
        try:
            return cls.from_document(json.loads(path.read_bytes()))
        except (ValueError, UnicodeError) as error:
            raise EvidenceError("invalid_catalog_json") from error
