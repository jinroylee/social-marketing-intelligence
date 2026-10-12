from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from smi_ingestion.canonical import CanonicalReader
from smi_ingestion.contracts import ExternalKey


EXAMPLES = Path(__file__).parents[1] / "examples" / "synthetic"


def _cli(db, evidence_dir: Path, *args: str):
    return subprocess.run(
        [sys.executable, "-m", "smi_ingestion", "--dsn", db.dsn, "--schema", db.schema,
         "--evidence-dir", str(evidence_dir), *args],
        capture_output=True, text=True, check=False,
    )


def test_cli_two_source_demo_and_default_synthetic_filter(stack, tmp_path):
    db, _, _, _ = stack
    evidence_dir = tmp_path / "evidence-cli"
    first = _cli(db, evidence_dir, "ingest", str(EXAMPLES / "json-manifest.json"))
    second = _cli(db, evidence_dir, "ingest", str(EXAMPLES / "html-manifest.json"))
    assert first.returncode == second.returncode == 0
    first_report = json.loads(first.stdout)
    assert first_report["status"] == "completed"
    assert first_report["latest_captured_at"] == "2026-09-10T12:00:00+00:00"
    hidden = _cli(db, evidence_dir, "inspect", "tiktok", "fixture:public", "content", "fixture-post-1")
    assert json.loads(hidden.stdout) == {"entity": None, "metrics": []}
    shown = _cli(db, evidence_dir, "inspect", "tiktok", "fixture:public", "content", "fixture-post-1", "--include-synthetic")
    body = json.loads(shown.stdout)
    assert body["entity"]["synthetic"] is True
    assert [metric["value"] for metric in body["metrics"]] == [1000, 1050]
    observation_id = body["metrics"][0]["observation_id"]
    replay = _cli(db, evidence_dir, "replay", observation_id)
    assert json.loads(replay.stdout)["status"] == "duplicate"


def test_cli_partial_exit_code_and_sanitized_connection_error(stack, tmp_path):
    db, _, _, _ = stack
    limited = _cli(db, tmp_path / "evidence-cli", "ingest", str(EXAMPLES / "json-manifest.json"), "--max-bytes", "1")
    assert limited.returncode == 2
    assert json.loads(limited.stdout)["issues"][0]["code"] == "byte_limit_reached"
    secret = "SENTINEL_PASSWORD_DO_NOT_PRINT"
    bad_dsn = f"postgresql://smi:{secret}@127.0.0.1:6543/smi"
    failed = subprocess.run(
        [sys.executable, "-m", "smi_ingestion", "--dsn", bad_dsn, "migrate"],
        capture_output=True, text=True, check=False,
    )
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["code"] == "database_error"
    assert secret not in failed.stdout + failed.stderr
