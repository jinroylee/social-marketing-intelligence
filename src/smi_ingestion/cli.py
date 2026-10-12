"""Local command-line entry point for bounded collection and inspection."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from .adapters.registry import default_registry
from .canonical import CanonicalReader, CanonicalWriter
from .contracts import ExternalKey, RunLimits
from .db import Database
from .evidence import EvidenceError, EvidenceStore
from .runner import IngestionRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smi-ingest")
    parser.add_argument("--dsn", default=os.environ.get("SMI_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi"))
    parser.add_argument("--schema", default=os.environ.get("SMI_DATABASE_SCHEMA"))
    parser.add_argument("--evidence-dir", type=Path, default=Path(os.environ.get("SMI_EVIDENCE_DIR", ".evidence")))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("manifest", type=Path)
    ingest.add_argument("--max-records", type=int, default=100)
    ingest.add_argument("--max-requests", type=int, default=10)
    ingest.add_argument("--max-bytes", type=int, default=1_048_576)
    resume = commands.add_parser("resume")
    resume.add_argument("run_id")
    replay = commands.add_parser("replay")
    replay.add_argument("observation_id")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("platform")
    inspect.add_argument("namespace")
    inspect.add_argument("kind", choices=["account", "content"])
    inspect.add_argument("native_id")
    inspect.add_argument("--include-synthetic", action="store_true")
    revoke = commands.add_parser("revoke")
    revoke.add_argument("observation_id")
    commands.add_parser("expire")
    commands.add_parser("reconcile")
    args = parser.parse_args(argv)
    try:
        db = Database(args.dsn, args.schema)
        if args.command == "migrate":
            db.migrate()
            result = {"status": "migrated"}
        else:
            evidence = EvidenceStore(db, args.evidence_dir)
            runner = IngestionRunner(evidence, CanonicalWriter(db), default_registry())
            if args.command == "ingest":
                result = runner.ingest(args.manifest, RunLimits(
                    max_requests=args.max_requests, max_records=args.max_records, max_bytes=args.max_bytes
                ))
            elif args.command == "resume":
                result = runner.resume(args.run_id)
            elif args.command == "replay":
                result = runner.replay(args.observation_id)
            elif args.command == "inspect":
                key = ExternalKey(args.platform, args.namespace, args.kind, args.native_id)
                reader = CanonicalReader(db)
                result = {
                    "entity": reader.entity(key, args.include_synthetic),
                    "metrics": reader.metrics(key, args.include_synthetic),
                }
            elif args.command == "revoke":
                evidence.revoke(args.observation_id)
                result = {"status": "revoked", "observation_id": args.observation_id}
            elif args.command == "reconcile":
                result = {"status": "reconciled", "removed_orphan_files": evidence.reconcile_orphans()}
            else:
                result = {"status": "expired", "count": evidence.expire()}
        print(json.dumps(result, ensure_ascii=False, default=str))
        return 2 if result.get("status") == "partial" else 0
    except (EvidenceError, ValueError, OSError, KeyError, psycopg.Error) as error:
        code = error.code if isinstance(error, EvidenceError) else "database_error" if isinstance(error, psycopg.Error) else "invalid_input"
        print(json.dumps({"status": "failed", "code": code}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
