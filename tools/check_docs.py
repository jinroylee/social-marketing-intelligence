"""Check product documentation against repository files and physical schemas."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


def check_docs(root: Path) -> list[str]:
    """Return broken local links, undocumented tables and invalid instruction symlinks."""
    errors = []
    documents = [*root.joinpath("docs").rglob("*.md"), root / "README.md", root / "GLOSSARY.md", root / "AGENTS.md"]
    for document in documents:
        if not document.is_file():
            errors.append(f"Missing document: {document.relative_to(root)}")
            continue
        for link in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            target = link.strip("<>").split("#", 1)[0]
            if not target or re.match(r"[a-zA-Z][\w+.-]*:", target):
                continue
            target = re.sub(r":\d+$", "", unquote(target))
            if not (document.parent / target).exists():
                errors.append(f"Broken link in {document.relative_to(root)}: {link}")
    model = root / "docs/data-model.md"
    if model.is_file():
        diagram = model.read_text()
        for schema in root.joinpath("src").rglob("schema.sql"):
            for table in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", schema.read_text()):
                if not re.search(r"\b" + re.escape(table) + r"\s*\{", diagram):
                    errors.append(f"Missing physical ERD table: {table}")
    else:
        errors.append("Missing docs/data-model.md")
    instructions = [root / "AGENTS.md"]
    for directory in ("src", "tools", "docs", "tests"):
        instructions.extend(root.joinpath(directory).rglob("AGENTS.md"))
    for instruction in instructions:
        sibling = instruction.with_name("CLAUDE.md")
        if not sibling.is_symlink() or sibling.readlink() != Path("AGENTS.md"):
            errors.append(f"Expected relative CLAUDE.md -> AGENTS.md beside {instruction.relative_to(root)}")
    return errors


def main() -> int:
    """Validate the repository containing this script."""
    errors = check_docs(Path(__file__).resolve().parents[1])
    if errors:
        print("\n".join(errors))
        return 1
    print("Documentation links, physical ERD coverage and instruction symlinks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
