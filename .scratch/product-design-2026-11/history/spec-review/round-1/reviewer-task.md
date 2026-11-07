ROLE: critical reviewer of an implementation-spec sequence (round 1). Read-only except your one output file.

TARGET
Repository: /Users/makinarocks/workspace/personal/social-marketing-intelligence
Planning package under review: .scratch/product-design-2026-11/task4/
- implementation-sequence.md (main entry: ordered list of specs S01..S30, lanes, blockers, milestones, critical path)
- specs/01-*.md .. specs/30-*.md (the individual specs)
- gap-analysis.md, architecture-target.md, traceability.md
- plan.json (machine form, incl. dependency edges); build_plan.py generates the spec markdown
- ../wayfinder/issues/000-product-map.md and 001-richer-agent-boundary.md (open decision W01)

ULTIMATE GOAL the specs must serve
Close the gap from the actual installed code to the approved product and UI. The user-confirmed first delivery is a campaign-first, single-workspace LOCAL PILOT with: real automated discovery, monitoring and background task processing; a familiar EN/KO-switchable chat assistant; a monitoring time-series chart highlighting current data; in-product inbox plus email notifications; and a genuinely interactive Neo4j-style knowledge graph. Every FR must have an implementation or explicit later path. Richer agent research/synthesis is target-roadmap scope. Hosted tenancy is later. The deliverable is an ordered set of individually implementable specs, starting from the real codebase, that a team of agents can execute.
Authoritative goal sources (read as needed):
- .scratch/product-design-2026-11/task4-brief.md (the brief the spec author received)
- .scratch/product-design-2026-11/task1-recovery/requirements-analysis.md and decisions.md (confirmed user decisions)
- .scratch/product-design-2026-11/task3/r2/design-spec.md and prototype.html (the approved UI; approved by the user with "I love it")
- FR.md, docs/functional-requirements.md, POPOSAL.md, docs/architecture.md, docs/adr/ (product requirements and accepted decisions)
- src/ and tests/ (the actual code; verify claims here)

CHANGE (what to produce)
Write a critical review to exactly this file:
.scratch/product-design-2026-11/spec-review/round-1/review.md

Judge two things separately:
1. VALIDITY: is each spec correct against the real code and the requirements; are gap claims true; is each spec actually implementable by one owner with clear acceptance; are there contradictions, missing requirements, or invented constraints?
2. OPTIMALITY toward the ultimate goal: is this the right SET and ORDER of specs? Consider risk ordering (are the highest-uncertainty items validated early or late?), dependency necessity (is each edge in plan.json real or artificial; does any artificial edge lengthen the critical path?), granularity (are specs comparably sized and individually implementable, or are some trivial and others multi-week bundles?), missing specs, redundant or over-engineered specs for a single-user local pilot, undecided technical choices hidden inside specs, and whether real users/data touch the product early enough.

Be critical and independent. Do not trust the package's own claims or its structural verifier (verification-results.txt); passing structure says nothing about quality. Verify material claims against src/ and tests/ yourself. Avoid nitpicks about wording; focus on findings that would change what gets built, in what order, or how risky it is.

REQUIRED review.md STRUCTURE
1. Verdict: one paragraph each on validity and optimality.
2. Findings, ranked most severe first. For each: ID (R1-F01...), title, severity (critical/major/minor), confidence (high/medium/low), affected specs, evidence with file:line references (code or spec), consequence if unchanged, and a concrete proposed change (split/merge/reorder/add/remove/edit edge/rewrite scope).
3. A proposed revised ordering or dependency set, if your findings imply one (a compact table is fine).
4. What should be kept as is (briefly), so a later reviser does not churn sound parts.

CONSTRAINTS
- Do not edit any file other than review.md. Do not modify specs, code, docs, git state, or the wayfinder issues.
- No browser automation, no external network calls, no paid provider calls, no email, no commits.
- You may run read-only commands (grep, reading files, `python .scratch/product-design-2026-11/task4/verify_plan.py`). Do not run the full test suite.
- Do not spawn sub-agents for facts that are inside this repo unless it materially speeds up reading; you own the final judgment.

OWNERSHIP
You own only .scratch/product-design-2026-11/spec-review/round-1/review.md.

OBSERVABLE ACCEPTANCE
- review.md exists with the four sections above and at least the material findings you can defend with evidence.
- Then send worker_done exactly once with --outcome succeeded (or failed if you could not complete), --files-modified and --report-path pointing to review.md.
