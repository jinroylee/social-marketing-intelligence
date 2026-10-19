"""Run the repository's local and CI verification with a single database preflight."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import psycopg


def database_ready() -> bool:
    """Check the test database once without revealing connection details."""
    dsn = os.environ.get("SMI_TEST_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi")
    try:
        with psycopg.connect(dsn, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except (psycopg.Error, ValueError):
        print("Test PostgreSQL is unavailable. Start it with 'docker compose up -d --wait postgres' "
              "or configure SMI_TEST_DATABASE_URL.", file=sys.stderr)
        return False
    return True


def main() -> int:
    """Run correctness lint, documentation checks, then isolated-schema tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true", help="Run checks that do not need PostgreSQL")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for command in ([sys.executable, "-m", "ruff", "check", "src", "tests", "tools"],
                    [sys.executable, str(root / "tools/check_docs.py")]):
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode:
            return result.returncode
    if args.static:
        return 0
    if not database_ready():
        return 1
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=short", "--maxfail=1"],
                          cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
