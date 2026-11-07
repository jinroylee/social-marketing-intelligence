"""Render the planning package from plan_source.json.

plan_source.json is the single editable source. Specs are keyed by stable slug;
`order` fixes the published S-number of each slug. Text fields reference other
specs as {{slug}} tokens, rendered to their published S-number, so specs can be
added, split or reordered without renumbering prose by hand. `rationale` maps
each direct dependency slug to the reason the edge exists.
"""

import json
import os
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent             # implementation-roadmap/source: editable inputs and generators
OUT = SRC.parent                                  # implementation-roadmap: rendered roadmap
ROOT = OUT.parent                                 # repository root
INPUTS = ROOT / ".scratch/product-design-2026-11"  # approved requirements, analysis, UI design and approval


def rel(target, start):
    """Return a POSIX relative link from directory `start` to `target`."""
    return Path(os.path.relpath(target, start)).as_posix()


SPEC_TO_ROOT = rel(ROOT, OUT / "specs")
TO_ROOT = rel(ROOT, OUT)
TO_INPUTS = rel(INPUTS, OUT)
SOURCE = json.loads((SRC / "plan_source.json").read_text())
ORDER = SOURCE["order"]
assert len(ORDER) == len(set(ORDER)) == len(SOURCE["specs"]), "order must list every spec slug exactly once"
NUMBER = {slug: n for n, slug in enumerate(ORDER, 1)}


def published(text):
    """Replace {{slug}} tokens with published S-numbers; unknown slugs fail loudly."""
    return re.sub(r"\{\{([a-z0-9-]+)\}\}", lambda m: f"S{NUMBER[m[1]]:02}", text)


# Shared rule for every spec that ships a screen; stated once instead of per spec.
UI_OBLIGATION = ("UI spec obligations: use the shared {{client-foundation}} freshness utility rather than a screen-specific "
    "revalidation scheme; add this screen's EN/KO catalog keys; retire the legacy English-only form routes and views this "
    "screen replaces once parity tests pass, migrating their tests; and deliver a short human browser checklist for this "
    "screen, executed at {{interaction-checkpoint}} or {{human-pilot-acceptance}}, not as a build-completion gate.")
UI_CHECK = ("Keep a source-dependent view of this screen open, revoke support and observe removal on the next successful "
    "revalidation through the shared freshness utility. The {{client-foundation}} catalog completeness check passes with "
    "this screen's EN/KO keys, and legacy form routes this screen replaces are removed after their parity tests pass.")
DECISIONS = SOURCE["decisions"]

SPECS = []
for slug in ORDER:
    src = SOURCE["specs"][slug]
    spec_id = f"S{NUMBER[slug]:02}"
    s = {"id": spec_id, "slug": slug, "file": f"{NUMBER[slug]:02}-{slug}.md"}
    for key, value in src.items():
        if isinstance(value, str):
            s[key] = published(value)
        elif key == "checks":
            s[key] = [published(v) for v in value]
        else:
            s[key] = value
    s["dependencies"] = [f"S{NUMBER[d]:02}" for d in src["dependencies"]]
    s["rationale"] = {f"S{NUMBER[d]:02}": published(r) for d, r in src.get("rationale", {}).items()}
    if src.get("ui_bearing"):
        s["integration"] += " " + published(UI_OBLIGATION)
        s["checks"] = s["checks"] + [published(UI_CHECK)]
    SPECS.append(s)

ASSIGNMENTS = {key: sorted(NUMBER[slug] for slug in slugs) for key, slugs in SOURCE["assignments"].items()}


def parse_rows(path):
    rows = {}
    for line in path.read_text().splitlines():
        match = re.match(r"\| ((?:FR|OFR|PROP|UD)-[A-Z0-9]+)(?:: ([^|]+))? \|", line)
        if match:
            rows[match[1]] = [part.strip() for part in line.strip("|").split("|")]
    return rows


def link_from_spec(path):
    return f"{SPEC_TO_ROOT}/{path}"


def render():
    upstream = parse_rows(INPUTS / "task1-recovery/requirements-matrix.md")
    ui = parse_rows(INPUTS / "task3/r2/fr-ui-traceability.md")
    assert set(upstream) == set(ui)
    assert set(ASSIGNMENTS) == set(upstream) | {"R2-CHAT", "R2-STREAM", "R2-GRAPH"}
    byid = {s["id"]: s for s in SPECS}
    for s in SPECS:
        s["requirements"] = [key for key, nums in ASSIGNMENTS.items() if int(s["id"][1:]) in nums]
        deps = [f'[{byid[d]["title"]}]({byid[d]["file"]})' + (f' ({s["rationale"][d]})' if s["rationale"].get(d) else '') for d in s["dependencies"]]
        decision_links = [f'[{DECISIONS[d]["title"]}](../{DECISIONS[d]["file"]}) ({d})' for d in s["decision_blockers"]]
        evidence = "\n".join(f"- [{p}]({link_from_spec(p)})" for p in s["evidence"])
        acceptance = "\n\n".join(f'### {s["id"]}-A{i:02}\n\n{check}' for i, check in enumerate(s["checks"], 1))
        text = f'''# {s["id"]}. {s["title"]}

Status: planned, no implementation or validation claimed.
Lane: {s["lane"]}
Size: {s["size"]} (S = up to a few days, M = about one week, L = multi-week)
Execution mode: {s["execution"]["mode"]}. {s["execution"]["reason"]}{(" Decisions to chart before implementation: " + "; ".join(s["execution"]["decisions"]) + ".") if s["execution"]["decisions"] else ""}
Assignee: unassigned. Claim the local implementation issue before execution.
Owner: {s["owners"]}
Direct spec blockers: {", ".join(deps) or "None. This is the first executable spec."}
Direct decision blockers: {", ".join(decision_links) or "None."}
Configuration or actual-evidence prerequisites: {s["config"]}

## User outcome

{s["outcome"]}

## Current evidence

Read the installed foundations and gap classifications in [the requirement trace](../traceability.md). These code and representative test paths were inspected, not executed for this plan:

{evidence}

## Scope and non-goals

{s["scope"]}

## Owners, interfaces and data shapes

{s["interface"]}

Apply [the shared adapter and evidence contract](../architecture-target.md#shared-contract). Proposed names in this spec are implementation contracts for review, not installed APIs or accepted successor ADRs.

## Data migration and documentation

{s["migration"]}

## UI reads, commands and agent integration

{s["integration"]}

## Invariants and authorization

{s["authority"]}

## Failure and recovery

{s["recovery"]}

## Acceptance

{acceptance}

## Completion evidence

For build work, retain the implementation commit, public-operation checks with real PostgreSQL and simulated external I/O, actual UI checks where authorized, and the shared check result. Separate live-provider and actual human evidence from code completion. For validation work, retain actual named/operator receipts and unresolved failures, not a fixture-based pass. Publish execution issues under the [local tracker]({SPEC_TO_ROOT}/docs/agents/issue-tracker.md); this planning file is not a claimed or resolved implementation ticket.

Requirement references: {", ".join(s["requirements"])}. Each has its approved UI mapping, evidence, gap and target check in [traceability](../traceability.md).
'''
        (OUT / "specs" / s["file"]).write_text(text)
    (OUT / "plan.json").write_text(json.dumps(dict(specs=SPECS, assignments=ASSIGNMENTS,
        decisions={k: dict(title=v["title"], file=v["file"], status="open", assignee="unassigned", blockers=[]) for k, v in DECISIONS.items()},
        user_decisions=SOURCE["user_decisions"]), indent=2) + "\n")
    rows = []
    for key, nums in ASSIGNMENTS.items():
        if key == "UD-09":
            rows.append(dict(id=key, target=upstream[key][2],
                foundation="Actual r2 human approval recorded; Task 4 gate satisfied.",
                capability_gap="None. This is a completed planning prerequisite.",
                ui_gap=published("None for the approved design gate. Implemented browser acceptance is a separate {{human-pilot-acceptance}} obligation."),
                readiness_gap="No unresolved Task 4 start gate.",
                contract="Actual human approval of the exact r2 manifest, recorded by coordinator.",
                specs=[], checks=[], owner="Actual user and coordinator", evidence_status="satisfied-upstream",
                markdown=f"| UD-09 | Actual human approval of exact UI before Task 4 | Actual r2 response recorded for manifest 1c1875228eab75585e865b10f3d68003bc09b251d5ca72754a63beb0774d24b5 | None; satisfied planning prerequisite | No remaining design gate. S20 separately validates the implemented product | Satisfied, no build blocker | [Actual r2 approval]({TO_INPUTS}/ui-review-status.md#actual-r2-approval) | Coordinator records exact actual human response | Actual user and coordinator | Satisfied upstream, no implementation task | [Actual approval evidence]({TO_INPUTS}/ui-review-status.md#actual-r2-approval), not a future review |"))
            continue
        targets = [SPECS[n - 1] for n in nums]
        first = targets[0]
        if key in upstream:
            source = upstream[key]
            target, installed = source[2], source[3]
            view = ui[key][2]
            needs = ui[key][4]
        else:
            target, installed, view, needs = {
                "R2-CHAT": ("Conventional persistent conversation with bounded per-turn context", "Single bounded question answer only; no thread/draft owner", "Assistant thread rail, turn log, multiline composer and sources/research disclosures", "K1 conversation IDs, turns/drafts/head/cursor/context and A1/T1 research status"),
                "R2-STREAM": ("Current-highlighted metric stream with exact selected-window support", "Recent timeline and volume/controversy reads; no metric history projection", "Monitoring time-series/chart/table/latest and selected-window evidence", "M1 bounded windows/status/native metrics/denominators/method/baseline/current policy"),
                "R2-GRAPH": ("Full interactive graph and bounded incremental read protocol", "Bounded whole-sample projection and traversal; no branch continuation/client", "Graph camera/drag/pin/layout/expand/collapse/filter/keyboard/list/inspector", "G1 scope/root/branch/generation/cursor/policy frontier/exact support/limits"),
            }[key]
        capability = first["outcome"]
        if key == "UD-09":
            installed = "Satisfied planning gate: actual r2 approval is recorded verbatim for manifest 1c1875228eab75585e865b10f3d68003bc09b251d5ca72754a63beb0774d24b5."
            capability = published("No remaining Task 4 start gate. {{human-pilot-acceptance}} is later implemented-product acceptance, not a repeated design approval.")
        readiness = "Actual live/provider or named human acceptance remains independent of build."
        if any(t["slug"] == "provider-readiness" for t in targets):
            readiness = published("{{provider-readiness}} requires actual permitted bounded provider/billing/send evidence, not simulated transport.")
        if key.startswith("PROP-") and all(t["lane"].startswith("later") for t in targets):
            readiness = "Later proposal path. Requires that spec's actual data/rights/evaluation prerequisites; not a first-pilot blocker."
        if key in {"UD-04", "PROP-05", "OFR-B02"}:
            readiness += published(" {{enable-richer-agent}} is blocked on W01 actual successor decision and {{agent-human-evidence}} named evidence.")
        spec_links = ", ".join(f'[{t["id"]}: {t["title"]}](specs/{t["file"]})' for t in targets)
        check_links = ", ".join(f'[{t["id"]}-A01](specs/{t["file"]}#{t["id"].lower()}-a01)' for t in targets)
        target_states = ui[key][3] if key in ui else "Normal, partial, empty, unavailable and stale-response behavior in the production contract"
        check_links += ". Required observable states: " + target_states
        evidence_links = ", ".join(f"[{p}]({TO_ROOT}/{p})" for p in first["evidence"][:3])
        # A row is a requirement-to-contract path; the full owning spec has all acceptance checks.
        rows.append(dict(id=key, target=target, foundation=installed, capability_gap=capability,
            ui_gap=view, readiness_gap=readiness, contract=needs, specs=[t["id"] for t in targets],
            checks=[f'{t["id"]}-A01' for t in targets], owner=first["owners"]))
        rows[-1]["markdown"] = f"| {key} | {target} | {installed} | {capability} | {view} | {readiness} | {evidence_links} | {needs} | {first['owners']} | {spec_links} | {check_links} |"
    (OUT / "traceability.json").write_text(json.dumps([{k:v for k,v in row.items() if k != "markdown"} for row in rows], indent=2) + "\n")
    header = '''# Requirement to implementation trace

This is a planning reference, not an implementation or readiness score. It covers all 99 stable upstream IDs and three r2 review IDs. Read each assigned spec's full acceptance section, not only its first linked check.

Approved UI authority is [actual r2 approval]({inputs}/ui-review-status.md#actual-r2-approval), which supersedes historical pending language inside the frozen [r2 UI mapping]({inputs}/task3/r2/fr-ui-traceability.md). Accepted target and installed-foundation text come from the [Task 1 recovery matrix]({inputs}/task1-recovery/requirements-matrix.md); code evidence and spec paths are added here. UI-gap text describes production work needed even when the fixture demonstrates it. Capability-gap cells name the concrete missing or adapted outcome, not an assertion that the installed foundation is absent.

For each row, the contract column is the approved UI's owner/read/command need. The linked spec supplies proposed signatures, fields, migrations, authority and every acceptance check. ''' + published("{{live-feasibility-probes}}, {{provider-readiness}}, {{early-marketer-checkpoint}}, {{interaction-checkpoint}}, {{human-pilot-acceptance}} and {{agent-human-evidence}} require actual operator/human evidence.") + ''' Later proposal paths preserve full destination coverage without making every ambition a pilot release gate. UD-09's design gate is already satisfied.

| ID | Accepted target | Installed foundation | Capability gap or remaining adaptation | Approved UI and UI gap | Readiness gap | Code and representative evidence | Backend/agent contract | Primary owner | Ordered spec paths | Target acceptance entry points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
'''
    (OUT / "traceability.md").write_text(header.replace("{inputs}", TO_INPUTS) + "\n".join(row["markdown"] for row in rows) + "\n")


if __name__ == "__main__":
    render()
