"""Record each final spec's execution mode (single-pass or wayfinder) in task4/plan_source.json.

single-pass: one owner or a thin layer over installed operations, design pinned by the spec, size S/M;
             one agent can claim and finish it. Human/operator validation specs are single-pass procedures.
wayfinder:   large or foundational; several open internal decisions that shape other specs. Chart the
             decisions (wayfinder map + child issues) and slice before implementation.
"""

import json
from pathlib import Path

SOURCE = Path(".scratch/product-design-2026-11/task4/plan_source.json")
src = json.loads(SOURCE.read_text())

SINGLE = {
    "stable-verification-clock": "Mechanical, pinned scope: inventory the suite, add one clock helper and convert fixtures; no product decisions.",
    "pilot-configuration": "One composition module with a pinned contract (load, compose, readiness); the file format is a small local choice.",
    "operator-commands": "Thin CLI adapters over installed UsageAccounting and RecentPolling operations.",
    "live-feasibility-probes": "Operator-run procedure with a fixed record format; needs U1 authorization, not design decisions.",
    "automated-interpretation": "Port signature, ordering before publication and failure state are pinned; one worker/knowledge change.",
    "early-marketer-checkpoint": "Human-run procedure with pre-declared outcomes and a fixed record format.",
    "workspace-and-evidence": "Two reads and the shared inspector on top of the client foundation; states are fixed by r2.",
    "task-events-lineage": "Small read model, preferably derived from existing attempt phases; T1 states are fixed.",
    "exact-approval-tools": "A1 UI and a listed tool set over installed proposal/approval operations; authority rules are explicit.",
    "discovery-operations-screen": "One screen over public reads from the registry, schedules and runtime health.",
    "monitoring-depth-and-timing": "Projections of stored receipt fields plus a live-page rule whose semantics and acceptance are fully specified.",
    "monitoring-workspace": "M1 UI composing installed recent, polling and alert owners.",
    "monitoring-history": "On-read projection and SVG chart with precise missing/zero/latest/lower-bound semantics and a given registration signature.",
    "alert-investigation-promotion": "M2 UI over installed context and promotion owners.",
    "interaction-checkpoint": "Human-run browser checklist with a fixed record format.",
    "spending-operations": "Operator forms over installed UsageAccounting operations and the operator command layer.",
    "supplementary-detail-route": "One named route integrated as plan steps; fields come from the probe and U4.",
    "plans-and-quality": "Forms and packets over installed planning and quality owners.",
    "provider-readiness": "Operator readiness row with a fixed record format.",
    "monitoring-readiness": "Operator readiness row with a fixed record format.",
    "detail-route-readiness": "Operator readiness row with a fixed record format.",
    "email-readiness": "Operator readiness row with a fixed record format.",
    "human-pilot-acceptance": "Human-run release record aggregating checkpoints and readiness rows.",
    "agent-human-evidence": "Human adjudication procedure; the decisions it informs belong to W01, not to this spec.",
}

WAYFINDER = {
    "client-foundation": ("Every UI spec inherits its conventions; the choices are hard to change later.",
        ["client module, routing and state conventions", "/api/v1 adapter framework and envelope shape", "i18n catalog format and completeness check", "freshness utility bounds and fail-closed UX"]),
    "pilot-scale-retrieval": ("L-sized; its index and ranking choices decide chat and campaign usefulness on KR/JP data.",
        ["index mechanism for Korean/Japanese (term table, pg_trgm or tsvector)", "normalization and CJK n-gram rules", "ranking rule among matches", "scan bounds and keyset continuation", "purge-with-source index ownership"]),
    "local-runtime": ("New smi_runtime module; L-sized process and scheduling design.",
        ["process, supervision and service packaging model", "fairness and tick budgets across components", "safe-retry classification", "multi-runtime safety", "maintenance cadence and bounds"]),
    "source-capabilities": ("Its registry contract is consumed by four specs and its selection policy is product-semantic.",
        ["capability registry schema and versioning", "recency/engagement/trend selection semantics and unknown disposition", "which capability changes are material to approved scope"]),
    "campaign-decisions": ("L-sized headline journey spanning about nine owner operations and many UI states.",
        ["read models for brief/shortlist version history and comparison", "conflict and interrupted-admission recovery UX", "presentation of unknowns, coverage and method", "regeneration successor flow"]),
    "conversations": ("New owner with four tables and retention rules; L-sized.",
        ["context selection and omission rules", "retention, deletion and expiry policy", "thread-head concurrency and exact retry", "composer/draft reducer design"]),
    "graph-reads": ("Cursor and policy-frontier protocol with an explicitly open mechanism choice.",
        ["cursor token versus page manifest", "policy frontier: revision port versus pinned dependency digest", "branch membership model", "per-call work bounds"]),
    "interactive-graph": ("L-sized client whose first deliverable is itself a library decision.",
        ["layout library (spike) and licence", "relationship/compact layouts and pinning", "camera and branch state model", "keyboard/list alternative design"]),
    "engagement-anomalies": ("New quantitative method whose statistical design is open and depends on W02 and probe data.",
        ["statistic and comparability rule", "age tolerance and minimum sample", "metric evidence fields through the source owner", "young-age labelling under W02"]),
    "semantic-shift": ("L-sized LLM method with an independent validator and baseline rules.",
        ["coding vocabulary, prompt and output schema", "independent validator design", "baseline comparability (language mix, sample)", "evaluation case design"]),
    "progressive-acquisition": ("L-sized plan/step engine replacing the legacy nickname planner.",
        ["plan and step schema", "information-value estimate and stop rules", "cross-route avoidance identity comparison", "migration of legacy plan methods"]),
    "inbox-email": ("New smi_notifications module with four or more tables and transport semantics.",
        ["event sync and reconcile ports per owner", "retry, backoff and uncertain-state policy", "template and governed-link design", "activation frontier and historical backfill"]),
    "evaluated-retrieval": ("Research-led retrieval depth with evaluation design.",
        ["held-out bilingual evaluation set", "semantic retrieval candidates and stores", "index rebuild and pinning"]),
    "agent-candidate": ("Disabled research/synthesis candidate with open validator and planner design.",
        ["research draft model", "claim validator method", "tool allowlist and prompt-attack handling"]),
    "enable-richer-agent": ("Implements whatever W01 decides; scope is undefined until then.",
        ["production contracts chosen by W01", "error and abstention policy", "runtime and provider readiness for new models"]),
    "hosted-actors-tenancy": ("Hosted identity and tenancy design.",
        ["identity provider and session model", "membership and role model", "query and file audit for tenant isolation", "service identities and multi-recipient preferences"]),
    "projection-governance": ("Operational governance for retained copies and projections.",
        ["outbox/revision model", "projection lag and rebuild", "managed storage, backup and restore"]),
    "multimodal-ontology": ("Per-slice ontology and modality extensions.",
        ["which modality and concept first", "reversible association decisions", "evaluation per slice"]),
    "objective-portfolios": ("Creator factor and portfolio modelling.",
        ["factor evidence contracts", "portfolio feasibility model", "overlap and uncertainty handling"]),
    "outcomes-attribution": ("Outcome ingestion and attribution design.",
        ["outcome source and permission model", "matching and deduplication", "attribution rules and windows"]),
    "causal-measurement": ("Causal study design.",
        ["study design per decision", "estimand and identification strategy", "diagnostics and withholding rules"]),
}

assert set(SINGLE) | set(WAYFINDER) == set(src["specs"]) and not set(SINGLE) & set(WAYFINDER)
for slug, reason in SINGLE.items():
    src["specs"][slug]["execution"] = {"mode": "single-pass", "reason": reason, "decisions": []}
for slug, (reason, decisions) in WAYFINDER.items():
    src["specs"][slug]["execution"] = {"mode": "wayfinder", "reason": reason, "decisions": decisions}
SOURCE.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n")
print(len(SINGLE), "single-pass;", len(WAYFINDER), "wayfinder")
