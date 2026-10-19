"""Shared scalar and record-reference parsing at the browser form boundary."""

import uuid

from smi_ingestion.evidence import EvidenceError


def one(form: dict[str, list[str]], key: str, default: str = "") -> str:
    values = form.get(key, [default])
    if len(values) != 1:
        raise EvidenceError("invalid_form")
    return values[0]


def identifier(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except ValueError as error:
        raise EvidenceError("record_not_found") from error
