"""Export, record and reopen one governed operational quality-review packet."""

import argparse
import json
import os
from pathlib import Path
import sys

import psycopg

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_review.quality import OperationalReviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema', default=os.environ.get('SMI_DATABASE_SCHEMA'))
    parser.add_argument('--workspace', default='local')
    parser.add_argument('--actor', required=True, help='Actual trusted local human operating this command')
    parser.add_argument('--include-synthetic', action='store_true')
    commands = parser.add_subparsers(dest='action', required=True)
    export = commands.add_parser('export')
    export.add_argument('kind', choices=['recommendation', 'answer', 'semantic_alert'])
    export.add_argument('result_id')
    export.add_argument('--request-id', required=True)
    read = commands.add_parser('read')
    read.add_argument('packet_id')
    record = commands.add_parser('record')
    record.add_argument('packet_id')
    record.add_argument('review', type=Path)
    record.add_argument('--request-id', required=True)
    args = parser.parse_args()
    try:
        db = Database(os.environ.get('SMI_DATABASE_URL', 'postgresql://smi:local_only_change_me@127.0.0.1:6543/smi'), args.schema)
        actor = ActorContext(args.workspace, args.actor, 'human')
        owner = OperationalReviews(db, args.workspace)
        owner.migrate()
        if args.action == 'export':
            result = owner.export(args.kind, args.result_id, actor, request_id=args.request_id, include_synthetic=args.include_synthetic)
        elif args.action == 'read':
            result = owner.read(args.packet_id, actor, include_synthetic=args.include_synthetic)
        else:
            if args.review.stat().st_size > 262144:
                raise ValueError('review file too large')
            result = owner.record(args.packet_id, json.loads(args.review.read_text()), actor,
                request_id=args.request_id, include_synthetic=args.include_synthetic)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result['recording_status'] == 'support_unavailable' else 0
    except (OSError, ValueError, TypeError, KeyError, EvidenceError, psycopg.Error):
        print('Could not verify the operational review. Check attribution, exact fields, current support and local database setup.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
