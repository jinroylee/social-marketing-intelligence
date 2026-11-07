"""Check planning links, exact coverage and the declared execution frontier."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent             # implementation-roadmap/source
PLAN = HERE.parent                                 # implementation-roadmap: rendered roadmap and decisions
ROOT = PLAN.parent                                 # repository root
BASE = ROOT / ".scratch/product-design-2026-11"    # approved requirements, analysis, UI design and approval


def heading_id(value):
    value = re.sub(r"[`*_]", "", value).lower().strip()
    value = re.sub(r"[^\w\- ]", "", value)
    return value.replace(" ", "-")


def check():
    plan = json.loads((PLAN / "plan.json").read_text())
    trace = json.loads((PLAN / "traceability.json").read_text())
    specs = plan["specs"]
    ids = [s["id"] for s in specs]
    assert len(set(ids)) == len(ids), "spec identities must be unique"
    assert ids == [f"S{n:02}" for n in range(1, len(ids) + 1)], "published order is numeric"
    byid = {s["id"]: s for s in specs}
    assert {path.name for path in (PLAN / "specs").glob("*.md")} == {s["file"] for s in specs}, "orphaned or duplicate spec file"
    expected = set(re.findall(r"^\| ((?:FR|OFR|PROP|UD)-[A-Z0-9]+) \|",
        (BASE / "task1-recovery/requirements-matrix.md").read_text(), re.M))
    approved = set(re.findall(r"^\| ((?:FR|OFR|PROP|UD)-[A-Z0-9]+):",
        (BASE / "task3/r2/fr-ui-traceability.md").read_text(), re.M))
    assert len(expected) == 99 and expected == approved
    all_ids = expected | {"R2-CHAT", "R2-STREAM", "R2-GRAPH"}
    assert {row["id"] for row in trace} == all_ids and len(trace) == 102
    assert set(plan["assignments"]) == all_ids
    for row in trace:
        assert row["specs"] == [f"S{n:02}" for n in plan["assignments"][row["id"]]]
        for field in ("target", "foundation", "capability_gap", "ui_gap", "readiness_gap", "contract", "owner"):
            assert row[field], (row["id"], field)
        if row["id"] == "UD-09":
            assert row["evidence_status"] == "satisfied-upstream" and not row["specs"]
        else:
            assert row["specs"] and row["checks"]
        for spec_id, acceptance in zip(row["specs"], row["checks"]):
            spec = byid[spec_id]
            assert row["id"] in spec["requirements"]
            content = (PLAN / "specs" / spec["file"]).read_text()
            assert f"### {acceptance}" in content

    visited = set()
    active = set()

    def visit(identity):
        assert identity in byid, f"unknown dependency {identity}"
        assert identity not in active, f"dependency cycle at {identity}"
        if identity in visited:
            return
        active.add(identity)
        s = byid[identity]
        for dep in s["dependencies"]:
            assert int(dep[1:]) < int(identity[1:]), f"nonsequential dependency {identity} -> {dep}"
            visit(dep)
        active.remove(identity)
        visited.add(identity)

    required_sections = ("User outcome", "Current evidence", "Scope and non-goals",
        "Owners, interfaces and data shapes", "Data migration and documentation",
        "UI reads, commands and agent integration", "Invariants and authorization",
        "Failure and recovery", "Acceptance", "Completion evidence")
    for s in specs:
        visit(s["id"])
        content = (PLAN / "specs" / s["file"]).read_text()
        assert content.startswith(f'# {s["id"]}. {s["title"]}')
        assert all(f"## {section}" in content for section in required_sections)
        assert s["owners"] and s["checks"] and s["evidence"]
        for path in s["evidence"]:
            assert (ROOT / path).exists(), f"missing evidence {path}"
        for decision in s["decision_blockers"]:
            assert decision in plan["decisions"]
    frontier = [s["id"] for s in specs if not s["dependencies"] and not s["decision_blockers"]]
    assert frontier == ["S01"], "S01 must be the only dependency-free executable spec"
    blocked = [s["id"] for s in specs if s["decision_blockers"]]
    for s in specs:
        assert set(s["rationale"]) == set(s["dependencies"]) and all(s["rationale"].values()), (s["id"], "every dependency edge needs exactly one non-empty rationale")
        assert s.get("size") in {"S", "M", "L"}, (s["id"], "size must be S, M or L")
        mode = s.get("execution", {})
        assert mode.get("mode") in {"single-pass", "wayfinder"} and mode.get("reason"), (s["id"], "execution mode and reason required")
        assert (mode["mode"] == "wayfinder") == bool(mode["decisions"]), (s["id"], "wayfinder specs, and only they, list decisions to chart")
        for decision in s["decision_blockers"]:
            blocks = re.search(r"^Blocks: (.+)$", (PLAN / plan["decisions"][decision]["file"]).read_text(), re.M)
            assert blocks and s["file"] in blocks[1], (s["id"], decision, "decision issue must name the spec it blocks")

    issues = list((PLAN / "decisions").glob("*.md"))
    maps = []
    for path in issues:
        body = path.read_text()
        labels = re.findall(r"^Labels: (.+)$", body, re.M)
        assert len(labels) == 1 and re.fullmatch(r"wayfinder:(map|grilling|task|prototype|research)", labels[0])
        for field in ("Issue", "Parent", "Assignee", "Status", "Blockers"):
            assert re.search(rf"^{field}: .+", body, re.M), (path, field)
        if labels[0] == "wayfinder:map":
            maps.append(path)
        else:
            assert "000-product-map.md" in body and "## Question" in body
            assert not re.search(r"^Status: (resolved|closed)", body, re.M), "charting must not fake a resolution"
    assert len(maps) == 1
    for decision in plan["decisions"].values():
        assert (PLAN / decision["file"]).exists()
        assert decision["status"] == "open" and not decision["blockers"]

    files = list(PLAN.rglob("*.md"))
    links = 0
    for path in files:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            target = target.split(' "', 1)[0].strip("<>")
            if re.match(r"[a-zA-Z]+://", target) or target.startswith("mailto:"):
                continue
            filename, _, fragment = unquote(target).partition("#")
            dest = (path.parent / filename).resolve() if filename else path
            assert dest.exists(), f"broken link {path.relative_to(ROOT)} -> {target}"
            if fragment and dest.suffix == ".md":
                anchors = {heading_id(h) for h in re.findall(r"^#{1,6} (.+)$", dest.read_text(), re.M)}
                assert fragment in anchors, f"missing anchor {dest}#{fragment}"
            links += 1

    sequence = (PLAN / "implementation-sequence.md").read_text()
    sequence_ids = re.findall(r"^\| (S\d{2}) \|", sequence, re.M)
    assert sequence_ids == ids, "reader-facing serial sequence differs from executable order"
    digest = hashlib.sha256((BASE / "task3/r2/artifact-manifest.json").read_bytes()).hexdigest()
    assert digest == "1c1875228eab75585e865b10f3d68003bc09b251d5ca72754a63beb0774d24b5"
    manifest = json.loads((BASE / "task3/r2/artifact-manifest.json").read_text())
    for filename, expected_digest in manifest["files"].items():
        actual_digest = hashlib.sha256((BASE / "task3/r2" / filename).read_bytes()).hexdigest()
        assert actual_digest == expected_digest, f"approved artifact changed: {filename}"
    approval = (BASE / "ui-review-status.md").read_text()
    assert "## Actual r2 approval" in approval and '> I love it' in approval
    print(f"PASS: {len(specs)} unique specs in dependency order; DAG has {sum(len(s['dependencies']) for s in specs)} direct edges.")
    print("PASS: 99 upstream IDs plus 3 r2 IDs have complete target/foundation/gap/UI/contract/spec/acceptance/owner paths.")
    print("PASS: UD-09 is satisfied upstream evidence and creates no new implementation or approval blocker.")
    print("PASS: all per-spec sections, code paths, acceptance anchors and decision blockers exist.")
    print(f"PASS: {links} local links/anchors across {len(files)} Markdown files resolve.")
    print(f"PASS: one canonical map with only wayfinder:map; {len(issues) - 1} open child decision issues with one wayfinder label each and explicit fallback relationships.")
    print(f"PASS: exact r2 manifest, {len(manifest['files'])} approved artifact hashes and actual human approval record match the planning input.")
    print(f"DEPENDENCY-READY FRONTIER: {', '.join(frontier)}. Each spec's environment/config prerequisites still apply.")
    print(f"DIRECT DECISION-BLOCKED: {', '.join(f'{i} ({"/".join(byid[i]["decision_blockers"])})' for i in blocked) or 'none'}. Each decision issue names the spec it blocks.")
    print("LIMIT: structure does not prove unbuilt behavior, provider readiness, semantic validation or actual human acceptance.")
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier", action="store_true")
    args = parser.parse_args()
    plan = check()
    if args.frontier:
        for key, decision in plan["decisions"].items():
            blocked_specs = [s["id"] for s in plan["specs"] if key in s["decision_blockers"]]
            print(f"DECISION FRONTIER: {decision['title']} ({key}); status {decision['status']}; assignee {decision['assignee']}; blocks {', '.join(blocked_specs) or 'no spec'}.")
        for item in plan.get("user_decisions", []):
            print(f"USER DECISION {item['id']}: default if unanswered: {item['default']}")
        print("No decision was resolved by planning.")
