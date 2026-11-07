"""Render the reader's ordered entry point from plan.json.

Tables, milestones, depths, critical paths and parallel waves are computed from the
dependency graph so the narrative cannot drift from the executable plan. Prose that is
not computable uses {{slug}} tokens resolved to published S-numbers.
"""

import json
import os
import re
from pathlib import Path

src = Path(__file__).resolve().parent  # plan/source
out = src.parent                       # implementation-roadmap
inputs = os.path.relpath(out.parent / ".scratch/product-design-2026-11", out)  # approved inputs and history
plan = json.loads((out / "plan.json").read_text())
specs = plan["specs"]
byid = {s["id"]: s for s in specs}
byslug = {s["slug"]: s for s in specs}


def t(text):
    return re.sub(r"\{\{([a-z0-9-]+)\}\}", lambda m: byslug[m[1]]["id"], text)


def link(slug):
    s = byslug[slug]
    return f'[{s["id"]} {s["title"]}](specs/{s["file"]})'


depth = {}


def level(spec_id):
    if spec_id not in depth:
        depth[spec_id] = 1 + max((level(d) for d in byid[spec_id]["dependencies"]), default=0)
    return depth[spec_id]


def longest_path(spec_id):
    s = byid[spec_id]
    if not s["dependencies"]:
        return [spec_id]
    return longest_path(max(s["dependencies"], key=level)) + [spec_id]


for s in specs:
    level(s["id"])

rows = []
for s in specs:
    blockers = ", ".join(s["dependencies"]) or "None"
    if s["decision_blockers"]:
        blockers += "; decision " + ", ".join(s["decision_blockers"])
    rows.append(f'| {s["id"]} | [{s["title"]}](specs/{s["file"]}) | {s["lane"]} | {s["size"]} | {s["execution"]["mode"]} | {s["milestone"]} | {depth[s["id"]]} | {blockers} |')

MILESTONES = {
    "M0": "Baseline, configuration, operator commands, client foundation, live probes, automated interpretation and pilot-scale retrieval, ending at the early real-data marketer check {{early-marketer-checkpoint}} on pre-UI paths (legacy forms and CLI). The probes {{live-feasibility-probes}} run once the operator commands exist and the user grants bounded live authorization (U1).",
    "M1": "Runtime with lifecycle maintenance, workspace and inspector, source capabilities, brief-to-shortlist, task progress, exact approval, chat, and the D1 schedule plus runtime-health screen.",
    "M2": "Graph reads and the interactive graph, whose first deliverable is a time-boxed layout-library spike.",
    "M3": "Live-window comparability, topics and alerts, the current-highlighted chart, investigation and promotion, engagement and semantic-shift methods, ending at the browser checkpoint {{interaction-checkpoint}} for graph, chart, campaign and chat.",
    "M4": "Spending controls, the acquisition plan model and one named supplementary route, inbox plus single-recipient SMTP email, and planning with KR/JP quality packets.",
    "M5": "Four independently claimable readiness rows ({{provider-readiness}}–{{email-readiness}}) and the live-data release record {{human-pilot-acceptance}}.",
    "Later": "Evaluated retrieval, the richer-agent candidate, adjudication and decision-blocked enablement, hosted tenancy, projection governance, multimodal ontology, portfolios, outcomes/attribution and causal measurement. These preserve full FR and proposal coverage without blocking the local pilot.",
}
milestone_text = []
for key, text in MILESTONES.items():
    members = ", ".join(s["id"] for s in specs if s["milestone"] == key)
    milestone_text.append(f"- **{key}** ({members}). {t(text)}")

pilot = [s for s in specs if s["milestone"] != "Later"]
build = [s for s in pilot if s["lane"] == "pilot-build"]
deepest_build = max(build, key=lambda s: depth[s["id"]])
paths = [
    ("First live evidence", byslug["live-feasibility-probes"]["id"]),
    ("Early real-data marketer check", byslug["early-marketer-checkpoint"]["id"]),
    ("Deepest pilot build spec", deepest_build["id"]),
    ("Browser interaction checkpoint", byslug["interaction-checkpoint"]["id"]),
    ("Pilot release record", byslug["human-pilot-acceptance"]["id"]),
]
path_text = [f"- {label}: {' → '.join(longest_path(i))} (depth {depth[i]})." for label, i in paths]

# Size-weighted longest path, using illustrative weeks (S = 0.5, M = 1, L = 3) to compare orderings only.
WEIGHT = {"S": 0.5, "M": 1, "L": 3}
weighted = {}


def weighted_path(spec_id):
    if spec_id not in weighted:
        s = byid[spec_id]
        best = max((weighted_path(d) for d in s["dependencies"]), key=lambda x: x[0], default=(0, []))
        weighted[spec_id] = (best[0] + WEIGHT[s["size"]], best[1] + [spec_id])
    return weighted[spec_id]


for label, slug in (("Early real-data marketer check", "early-marketer-checkpoint"), ("Pilot release record", "human-pilot-acceptance")):
    weeks, chain = weighted_path(byslug[slug]["id"])
    path_text.append(f"- Size-weighted, {label.lower()}: {' → '.join(chain)} (about {weeks:g} illustrative weeks).")
journeys = [byslug[x]["id"] for x in ("campaign-decisions", "conversations", "interactive-graph", "monitoring-history")]
path_text.append("- Headline journeys complete at depth " + ", ".join(f"{i} {depth[i]}" for i in journeys) + " (campaign, chat, graph, chart).")

waves = {}
for s in pilot:
    waves.setdefault(depth[s["id"]], []).append(s["id"])
wave_text = [f"- Depth {d}: {', '.join(ids)}" for d, ids in sorted(waves.items())]

user_rows = []
for item in plan["user_decisions"]:
    affects = ", ".join(byslug[a]["id"] for a in item["affects"])
    user_rows.append(f'| {item["id"]} | {item["decision"]} | {item["default"]} | {affects} |')

decisions = "; ".join(
    f'[{d["title"]}]({d["file"]}) ({k}) blocks ' + (", ".join(s["id"] for s in specs if k in s["decision_blockers"]) or "no spec")
    for k, d in plan["decisions"].items())

text = t(f'''# Proposed implementation sequence for the approved product

Status: revised plan for review. These are proposed implementation contracts for an approved product/UI, not implemented features or accepted successor ADRs. Both review rounds' findings, validations and applied changes are in [the design history]({inputs}/history/spec-review/).

Start with [{{{{stable-verification-clock}}}} Restore a complete, time-stable verification baseline](specs/01-stable-verification-clock.md). It is the only dependency-free spec. Every direct dependency precedes its consumer, every edge records its reason in the spec's "Direct spec blockers" line, and each spec is independently claimable once its direct blockers and configuration prerequisites pass. None is implemented by this planning package.

The first delivery is the approved campaign-first, single-workspace local pilot: automated work, EN/KO chat with question-scoped retrieval, a current-highlighted monitoring stream, a fully interactive graph, independent spending controls, inbox and email. Live feasibility is probed early in {{{{live-feasibility-probes}}}} once the operator commands {{{{operator-commands}}}} exist, and recorded finally in four independently claimable readiness rows ({{{{provider-readiness}}}}–{{{{email-readiness}}}}). Human evidence comes early at {{{{early-marketer-checkpoint}}}} (real discovered data on pre-UI paths) and {{{{interaction-checkpoint}}}} (browser check of graph, chart, campaign and chat), before the release record {{{{human-pilot-acceptance}}}}. Code or fixture completion does not complete any validation spec.

The r2 UI approval is already satisfied by [the actual user response]({inputs}/ui-review-status.md#actual-r2-approval). Current ADRs, including 0017, 0018 and 0023, remain in force for the pilot. Open decisions: {decisions}. The map is [the wayfinder product map](decisions/000-product-map.md).

Use [gap analysis](gap-analysis.md) for installed foundations, [target architecture](architecture-target.md) for proposed ownership/contracts, and [traceability](traceability.md) for all 99 upstream IDs plus three r2 IDs. Publish a spec as a local execution issue under the repository tracker when starting implementation, with a real assignee, direct blockers and acceptance evidence.

## Ordered specifications

Depth is the longest dependency chain ending at the spec, counting the spec itself. Size: S = up to a few days, M = about one week, L = multi-week. Validation rows need actual people, access and authorization in addition to their build blockers.

| Order | Specification | Lane | Size | Mode | Milestone | Depth | Direct blockers |
| --- | --- | --- | --- | --- | --- | --- | --- |
''')
text += "\n".join(rows)
single = [s for s in specs if s["execution"]["mode"] == "single-pass"]
wayfinder = [s for s in specs if s["execution"]["mode"] == "wayfinder"]
text += t(f"""

## Execution modes

Each spec is classified for execution. **Single-pass** ({len(single)}): one owner or a thin layer over installed operations, with its design pinned by the spec and size S or M, so one agent can claim and finish it; human- and operator-run validation specs are single-pass procedures. **Wayfinder** ({len(wayfinder)}): large or foundational, with several open internal decisions that shape other specs; chart those decisions as a wayfinder map with child issues and slice the work before implementation. Each spec's header names its reason and, for wayfinder specs, the decisions to chart.

- Single-pass build: {", ".join(s["id"] for s in single if s["lane"] == "pilot-build")}
- Single-pass human/operator procedures: {", ".join(s["id"] for s in single if s["lane"] != "pilot-build")}
- Wayfinder, pilot: {", ".join(s["id"] for s in wayfinder if s["milestone"] != "Later")}
- Wayfinder, later: {", ".join(s["id"] for s in wayfinder if s["milestone"] == "Later")}""")
text += "\n\n## Milestones\n\n" + "\n".join(milestone_text)
text += "\n\n## Critical paths (computed from plan.json)\n\n" + "\n".join(path_text)
text += t('''

Depth chains are precedence, not duration; the size-weighted chains use illustrative weights only to compare orderings. Provider access and actual reviewer availability can dominate elapsed time, which is why the bounded live authorization (U1) is requested at plan start.

## Safe parallel execution

Pilot specs grouped by dependency depth; every spec in one group can run in parallel once the earlier groups it depends on are done:

''') + "\n".join(wave_text)
text += t('''

Coordinate shared smi_review catalogs and adapters through one integration owner, with distinct feature modules per spec. Do not have workers write one shared spec, schema migration or browser state object concurrently. Integration with a spec that has not landed is a conditional check, never a hidden blocker; each conditional check is mirrored in its partner spec, and when both exist the spec that lands second makes the check pass unconditionally.

## User decisions with recommended defaults

None of these blocks the start of the pilot build or any pilot spec; W01 blocks only {{enable-richer-agent}}. Each has a default the plan proceeds on until the user answers. Ask U1, W02, U3, U5 and U7 at plan start.

| ID | Decision | Default if unanswered | Affects |
| --- | --- | --- | --- |
''') + "\n".join(user_rows)
text += t('''

Engineering choices recorded inside specs, not user decisions: graph library versus hand-built layout ({{interactive-graph}}, first deliverable), configuration file format ({{pilot-configuration}}), retrieval index mechanism and ranking rule ({{pilot-scale-retrieval}}), event table versus derived phases ({{task-events-lineage}}), interpretation before publication ({{automated-interpretation}}), live-page method versioning ({{monitoring-depth-and-timing}}) and notification Message-ID derivation ({{inbox-email}}). External prerequisites, not decisions: a named marketer and a KR/JP reader for {{early-marketer-checkpoint}}, {{interaction-checkpoint}} and {{human-pilot-acceptance}}; an operator mailbox account (U7); live accounts under U1.

## Prerequisites and honest blocked states

{{stable-verification-clock}} requires real PostgreSQL and the locked development environment, and first inventories the whole suite without --maxfail; no green baseline is claimed before that run. Retention, thresholds, models, provider accounts, rate versions, currencies and ceilings are validated operator configuration in {{pilot-configuration}}, not fabricated product constants; cadence stays a topic-revision setting. Cost configuration and X activation are recorded operator commands ({{operator-commands}}); keyword schedules use the legacy /schedules form until {{discovery-operations-screen}}, and topic forms arrive in {{monitoring-workspace}}.

Specs whose premises depend on probe results ({{monitoring-depth-and-timing}} live-page premises, {{engagement-anomalies}}, {{supplementary-detail-route}} fields, {{inbox-email}} transport) record those premises as provisional until the matching {{live-feasibility-probes}} row passes. Contingency: if U3 is answered (a) or (b), add one M spec "Extend live X monitoring depth" after {{monitoring-depth-and-timing}} and {{operator-commands}} that blocks {{monitoring-readiness}}. {{conversations}} requires a finite configured retention policy for user text and drafts. {{inbox-email}} requires validated recipient/sender/link policy before transport activation. Agent browser access remains declined (U5); human browser checks run at the checkpoints. Failure of one live capability blocks claims for that capability only.

{{evaluated-retrieval}}–{{enable-richer-agent}} deepen retrieval and richer research; {{enable-richer-agent}} stays blocked until W01 is resolved and the accepted method/error policy is concrete. {{hosted-actors-tenancy}}–{{causal-measurement}} keep the broader proposal with explicit prerequisites. No graph database, multiple agents, microservices, queue vendor, vector store or analytics stack is preselected by the UI's appearance.

## Verify this plan

From the repository root, run:

```bash
python implementation-roadmap/source/build_plan.py
python implementation-roadmap/source/write_sequence.py
python implementation-roadmap/source/verify_plan.py --frontier
uv run --locked python tools/check.py --static
```

[`source/plan_source.json`](source/plan_source.json) is the single editable source; `source/build_plan.py` renders the specs, `plan.json` and traceability from it. [Verification output](verification/verification-results.txt) records structural checks only. A passing planning verifier cannot prove semantic completeness, provider readiness or human acceptance. The implementation checks in each spec remain required.
''')
(out / "implementation-sequence.md").write_text(text)
for name in ("gap-analysis.md", "architecture-target.md"):
    (out / name).write_text(t((src / (name + ".tmpl")).read_text()))
