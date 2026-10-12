from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from smi_ingestion.adapters.registry import default_registry
from smi_ingestion.canonical import CanonicalReader, CanonicalWriter
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceStore
from smi_ingestion.runner import IngestionRunner


DSN = os.environ.get(
    "SMI_TEST_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi"
)
EXAMPLES = Path(__file__).parents[1] / "examples" / "synthetic"


@pytest.fixture
def stack(tmp_path):
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(DSN) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    db = Database(DSN, schema)
    db.migrate()
    evidence = EvidenceStore(db, tmp_path / "evidence")
    registry = default_registry()
    runner = IngestionRunner(evidence, CanonicalWriter(db), registry)
    try:
        yield db, evidence, runner, registry
    finally:
        with psycopg.connect(DSN) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
