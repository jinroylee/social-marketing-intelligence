from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_database_preflight_fails_once_without_credentials_or_test_tracebacks():
    secret = "SENTINEL_CHECK_PASSWORD"
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/check.py")], cwd=ROOT,
        env={**os.environ, "SMI_TEST_DATABASE_URL": f"postgresql://smi:{secret}@127.0.0.1:1/smi"},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert result.stderr.count("Test PostgreSQL is unavailable") == 1
    assert "Traceback" not in result.stdout + result.stderr
    assert secret not in result.stdout + result.stderr


def test_document_checker_detects_broken_links_missing_tables_and_symlinks(tmp_path):
    spec = importlib.util.spec_from_file_location("repository_doc_checks", ROOT / "tools/check_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    for name in ("README.md", "GLOSSARY.md", "AGENTS.md"):
        (tmp_path / name).write_text("# Documentation\n")
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
    (tmp_path / "docs/data-model.md").write_text("```mermaid\nerDiagram\n sample {\n int id PK\n }\n```\n")
    (tmp_path / "src/schema.sql").write_text("CREATE TABLE IF NOT EXISTS sample (id INTEGER);\n")
    assert module.check_docs(tmp_path) == []
    (tmp_path / "README.md").write_text("[Missing](docs/missing.md)\n")
    (tmp_path / "src/schema.sql").write_text("CREATE TABLE IF NOT EXISTS missing_table (id INTEGER);\n")
    (tmp_path / "CLAUDE.md").unlink()
    errors = module.check_docs(tmp_path)
    assert len(errors) == 3
    assert any("Broken link" in error for error in errors)
    assert any("Missing physical ERD table: missing_table" in error for error in errors)
    assert any("Expected relative CLAUDE.md" in error for error in errors)
