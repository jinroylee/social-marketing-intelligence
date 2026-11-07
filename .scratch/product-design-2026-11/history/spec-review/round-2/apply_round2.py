"""Apply the accepted round-2 revision (round-2/validation.md section 4) to task4/plan_source.json.

Run once from the repository root after round 1 has been applied.
"""

import json
from pathlib import Path

SOURCE = Path(".scratch/product-design-2026-11/task4/plan_source.json")
src = json.loads(SOURCE.read_text())
specs = src["specs"]
assert len(specs) == 40 and "operator-commands" not in specs, "round 2 already applied or round 1 missing"


def edit(slug, **fields):
    for key, value in fields.items():
        assert key in specs[slug] or key in {"size", "ui_bearing", "milestone"}, (slug, key)
        specs[slug][key] = value


def replace(slug, key, old, new):
    text = specs[slug][key]
    assert text.count(old) == 1, (slug, key, old[:60])
    specs[slug][key] = text.replace(old, new)


def new(slug, **fields):
    assert slug not in specs
    base = dict(dependencies=[], rationale={}, decision_blockers=[], ui_bearing=False,
                config="None beyond the shared test prerequisites.")
    base.update(fields)
    for key in ("title", "lane", "size", "milestone", "owners", "evidence", "outcome", "scope", "interface",
                "migration", "integration", "authority", "recovery", "checks"):
        assert key in base, (slug, key)
    specs[slug] = base


def deps(slug, **rationale):
    """Set direct dependencies; value None keeps the existing rationale for that edge."""
    old = specs[slug]["rationale"]
    pairs = {}
    for key, reason in rationale.items():
        dep = key.replace("_", "-")
        assert dep in specs, (slug, dep)
        pairs[dep] = old[dep] if reason is None else reason
        assert pairs[dep], (slug, dep, "missing kept rationale")
    specs[slug]["dependencies"] = list(pairs)
    specs[slug]["rationale"] = pairs


# ------------------------------------------------------------------ M0

replace("pilot-configuration", "interface",
    "readiness(config) -> per-route classification, missing named prerequisites and configuration digest, never secret values or handles.",
    "readiness(config) -> per-route classification, missing named prerequisites (including a missing cost scope or route binding per route) and configuration digest, never secret values or handles.")
specs["pilot-configuration"]["checks"][1] = (
    "With a simulated model configured and its cost scope set up through the public UsageAccounting operation in the test, "
    "the shipped server runs ranked recommendation, criteria interpretation and a knowledge answer end to end. The shipped "
    "operator sequence is accepted in {{operator-commands}}.")

new("operator-commands",
    title="Give the operator recorded commands for cost controls and bounded X polling",
    lane="pilot-build", size="S", milestone="M0",
    owners="smi_costs and smi_monitoring.polling keep validation and SQL; the pilot composition module owns argument parsing and the trusted operator identity",
    evidence=["src/smi_costs/store.py", "src/smi_monitoring/polling/store.py", "src/smi_ingestion/cli.py", "src/smi_campaigns/responses/__init__.py"],
    outcome="An operator can configure spending controls and run bounded live X polling from the shipped tools, so live probes and recurring work have a recorded, attributable path.",
    scope="Subcommands on the composed operator CLI from {{pilot-configuration}}: configure-cost-scope (a CostScope from an explicitly named file section), bind-cost-route (adapter, scope and the owner's required max_units), set-cost-ceiling (amount, currency, period, pause), read-allowance, activate-x-topic (topic key, expected topic version, first window end, request ID), deactivate-x-topic and run-x-due --once (one bounded RecentPolling.run_due pass). Non-goals: browser forms ({{monitoring-workspace}}, {{spending-operations}}); reconciliation and meter recovery ({{spending-operations}}); any daemon or loop ({{local-runtime}}); new receipt tables; applying cost settings implicitly at start-up.",
    interface="Thin adapters over UsageAccounting.configure_scope/configure_route/configure_ceiling/allowance and RecentPolling.activate/deactivate/run_due with source-free JSON output. Errors are owner reason codes such as cost_scope_conflict, unsupported_cost_route_contract, monitoring_poll_already_active and monitoring_topic_version_conflict. A changed immutable scope requires a new scope ID. Actor and workspace are never taken from arguments.",
    migration="No schema change and no new receipt model; owners keep their existing request claims. Document the operator sequence in docs/user-guide.md, docs/costs.md and docs/monitoring.md.",
    integration="{{live-feasibility-probes}} and recurring work use these commands; {{spending-operations}} later calls the same command layer from its forms; {{local-runtime}} owns continuous polling.",
    authority="Each command is an explicit, attributable operator action. Configuration never applies cost settings or activation implicitly, and activation remains one recorded command per topic revision under ADR 0023.",
    recovery="Re-running an identical command reopens the original result. A conflicting change writes nothing and returns the owner's conflict reason. An unknown X response keeps its liability and is never re-dispatched by a retry.",
    checks=["On a fresh database, the documented sequence (scope, route binding, ceiling) through the shipped commands makes the simulated model route admissible from the shipped server and the {{pilot-configuration}} model journeys run; before the sequence, readiness() names the missing cost scope.",
            "Re-running the same scope or route command changes nothing. A changed rate under the same scope ID fails with the owner's conflict reason and writes nothing.",
            "With fake HTTP, activate, run-x-due --once N times and deactivate produce N windows and a recorded deactivation; a further run dispatches no request.",
            "Output and logs never contain secrets or provider handles, and a forged actor or workspace argument is rejected."])
deps("operator-commands", pilot_configuration="Commands act on the owners, routes and trusted operator identity composed from the validated configuration.")

cf = specs["client-foundation"]
edit("client-foundation",
    scope="Plain ES modules served from smi_review/static with no build step. Deliver the API client (envelope parsing, CSRF, request-ID generation, retry kinds), the versioned same-origin /api/v1 adapter framework, the i18n catalog mechanism and completeness check (catalogs grow per spec), the shell, navigation, four-colour theme and EN/KO switch, the shared display_valid_until freshness utility and the node --test harness. Consumer logic belongs to its consumers: the graph library decision and branch reducer to {{interactive-graph}}, the chart-series reducer to {{monitoring-history}} and the composer reducer to {{conversations}}. Non-goals: framework rewrite, CDN dependencies, browser automation.",
    interface="Client modules: api (request(command|read) -> envelope with allowed_actions, display_valid_until and sanitized error), i18n (t(key, params), locale switch preserving inputs and IDs) and freshness (revalidate on focus, navigation, explicit read and a configured bounded timer; fail closed at the deadline; an older response never restores a newer tombstone). Server side: versioned /api/v1 routing that parses each command explicitly and derives RequestContext on the server, beside the existing forms.",
    migration="No business tables. Add node --test execution to tools/check.py and list Node in docs/development.md and CI. Update docs/local-review.md, docs/architecture.md and smi_review/AGENTS.md with the client structure rules.",
    checks=["tools/check.py runs the Node tests and fails on a broken client-module test.", cf["checks"][3], cf["checks"][4],
            "The API client parses envelopes, generates request IDs and classifies retry kinds; a sanitized error never renders raw server text."],
    size="M")

lp = specs["live-feasibility-probes"]
edit("live-feasibility-probes",
    outcome="The premises of {{monitoring-depth-and-timing}}, {{engagement-anomalies}}, {{supplementary-detail-route}} and {{inbox-email}} are settled by bounded real evidence, and a bounded real discovery corpus exists for {{early-marketer-checkpoint}}, before those specs finish.",
    scope="One independently completable capability row each: model (schema adherence, latency, cost basis); Bright Data keyword (fields, capture times, cost basis, KR/JP yield, and the bounded discovery corpus for {{early-marketer-checkpoint}}: up to 10 keywords and a few hundred posts); X recent (one topic activated through {{operator-commands}} for at most the authorized number of windows, recording the saturation rate as the share of windows with next_token, receipt-minus-publication ages, public_metrics fields and counts-endpoint availability for the account tier, ending with a U3 depth recommendation and W02 evidence); email (the chosen transport, by default SMTP submission through the operator mailbox: acceptance-reply semantics and Message-ID handling, with no product send). Non-goals: production readiness claims; fixture substitution.",
    authority="Only explicitly authorized, bounded calls with recorded caps. Probes create no unbounded or unrecorded activation: the X row activates one topic through {{operator-commands}} for at most the U1-authorized number of windows and records its deactivation. A successful HTTP response is not permission, final billing, usefulness or delivery.",
    checks=[lp["checks"][0],
            "The X row runs one bounded activation for the authorized number of windows, records its deactivation, saturation rate and measurement ages, and ends with a recorded U3 depth recommendation and W02 evidence.",
            lp["checks"][2], lp["checks"][3],
            "The email row names its transport and records acceptance-reply semantics, or a blocked reason."],
    config="Blocked until the user grants bounded live authorization, credentials, per-capability call counts, the bounded discovery corpus and one spending ceiling (U1). If not granted, the build continues on fixtures and premise-dependent specs stay provisional.")
deps("live-feasibility-probes", operator_commands="Every live route refuses until a cost scope and route binding exist, and X also needs a recorded activation; these commands are the only shipped path.")

specs["pilot-scale-retrieval"]["scope"] += (
    " Record the index mechanism (own term table, pg_trgm or tsvector; PostgreSQL has no Korean or Japanese text-search parser) "
    "with benchmark results on the 1,000-post fixture, and a deterministic, versioned ranking rule among matches (recommended: "
    "exact subject-ID matches, then derived-term match count, then recency, with stable tie-breaking). Wire derive_scope into the "
    "installed question-to-answer and brief-to-comparison paths whenever the caller supplies no explicit terms, so the early "
    "real-data check exercises the new retrieval.")
specs["pilot-scale-retrieval"]["checks"].append(
    "The recorded index mechanism and ranking rule are documented with fixture benchmark results, and the installed answer and comparison paths (legacy form and CLI) pin the derived scope.")

edit("early-marketer-checkpoint",
    title="Check shortlist and answer usefulness with a marketer on real discovered data",
    owners="Actual pilot marketer and a KR/JP reader, supported by the campaign, knowledge and assistant maintainers",
    outcome="Early, on real discovered data, a marketer and a KR/JP reader judge whether shortlists, mention judgments and extractive answers are useful, so {{automated-interpretation}} and {{pilot-scale-retrieval}} can change before the campaign and chat UIs are built.",
    scope="Under U1 caps, the operator runs the bounded live keyword-discovery corpus through the installed live task path with automated interpretation. The reviewers grade about 10 briefs' shortlists and about 10 questions' supporting findings, including EN and KO questions over KR/JP captions, through whatever UI exists at that build (legacy forms and CLI expected; the new campaign and chat screens if they have landed). Record denominators, precision@k for supporting findings (no threshold claimed) and mention-judgment errors. Pre-declared outcomes: retrieval fails -> revise the {{pilot-scale-retrieval}} ranking rule or pull a named subset of {{evaluated-retrieval}} forward before {{conversations}} lands; mention judgments fail -> revise the {{automated-interpretation}} catalog rules. Non-goals: UI review ({{interaction-checkpoint}}, {{human-pilot-acceptance}}); release gating.",
    interface="Record reviewer, language, build and configuration digest and live provenance under the quality owner's attributable review contract, plus per-item grades and denominators.",
    integration="Each triggered pre-declared outcome is filed against its owning spec's execution issue. Results are inputs to {{human-pilot-acceptance}}.",
    checks=["Named reviewers, build and configuration identity, and live data provenance are recorded.",
            "Each brief and question is graded with its denominator, and failing examples are kept.",
            "Precision@k for supporting findings and mention-judgment error counts are recorded per language.",
            "Each triggered pre-declared outcome is filed against its owning spec's execution issue with the declared action."],
    config="Requires an actual marketer, a KR/JP reader, the model and Bright Data keyword rows of the live probes passed, and the bounded discovery corpus authorized under U1.",
    milestone="M0")
deps("early-marketer-checkpoint",
    live_feasibility_probes="Requires passed model and Bright Data keyword rows and the bounded discovery corpus under U1.",
    automated_interpretation="Discovered posts must carry published mention interpretations.",
    pilot_scale_retrieval="Shortlists and answers must use pilot-scale, question-scoped retrieval.")

# ------------------------------------------------------------------ M1

replace("local-runtime", "integration",
    "Operations screens show last tick, per-component health, next due and actual activation.",
    "health() exposes last tick, per-component health, next due and actual activation for {{discovery-operations-screen}}.")
specs["local-runtime"]["scope"] += (
    " Add one bounded lifecycle-maintenance component that calls the existing expire, reconcile and reconcile-knowledge "
    "operations on a configured cadence with a per-tick bound and reports in health(); no new lifecycle logic. Inbox "
    "reconciliation is registered by {{inbox-email}}.")
specs["local-runtime"]["checks"].append(
    "With an expired payload and a withdrawn source, a maintenance tick removes the payload and reconciles dependent copies within its bound, and health reports the run.")
edit("local-runtime", title="Run bounded local work continuously with restart, health and lifecycle maintenance")

sc = specs["source-capabilities"]
edit("source-capabilities",
    title="Describe usable source routes and bounded selection policy",
    scope=sc["scope"].split(" Own the D1 configuration screen")[0] + " Describe the oEmbed and tiktok-web adapters as existing for supplied references but not task-integrated. The D1 screen is {{discovery-operations-screen}}.",
    integration="The public readiness read exposes installed, access-unknown, permission-denied, configuration-blocked and activated states separately for {{discovery-operations-screen}}. Registered keyword count and day allowance remain owner-enforced. Selection results expose rank inputs and unknown trend evidence rather than a trending claim without a baseline. The agent planner consumes this contract, never adapter internals.",
    checks=sc["checks"][:4], ui_bearing=False, milestone="M1")
deps("source-capabilities", pilot_configuration=None)

replace("conversations", "interface", "Draft uses separate version, not thread-head mutation.",
    "Draft uses separate version, not thread-head mutation. This spec owns the composer/draft/IME reducer with Node tests.")

new("discovery-operations-screen",
    title="Configure scheduled discovery and see route and runtime health",
    lane="pilot-build", size="S", milestone="M1", ui_bearing=True,
    owners="smi_review owns the D1 screen; ScheduledDiscovery, SourceCapabilities and LocalRuntime keep their logic behind public ports",
    evidence=["src/smi_tasks/schedules/__init__.py", "src/smi_review/app.py", ".scratch/product-design-2026-11/task3/r2/design-spec.md"],
    outcome="In one D1 screen, an operator configures up to ten scheduled keywords and the shared daily allowance, activates schedules as recorded commands, and sees route capability, readiness, selection basis and runtime health.",
    scope="The r2 D1 screen (ten-keyword limit, recorded activation, day allowance, route health, selection basis) plus runtime health (last tick, per-component health, next due, actual activation). Retire the legacy /schedules form after parity. Non-goals: new scheduling or selection logic; topic activation ({{monitoring-workspace}}); spending forms ({{spending-operations}}).",
    interface="/api/v1 reads for schedule settings, occurrences and allowance, per-route capability and readiness, and runtime health; commands to configure or activate a schedule with an expected version and request ID. Installed, access-unknown, permission-denied, configuration-blocked and activated states stay separate.",
    migration="No business tables. Update docs/local-review.md and the review owner instructions; remove the legacy schedule views and migrate their tests after parity.",
    integration="Reads {{source-capabilities}} readiness and {{local-runtime}} health through public ports; schedule activation stays a recorded command under ADR 0015.",
    authority="Saving settings grants no live authority; activation is an explicit recorded operator command. Configuration edits never alter an existing occurrence's scope or accounting day.",
    recovery="Stale edits conflict and preserve input. A stopped runtime shows stale health rather than last-known-good as current.",
    checks=["An eleventh scheduled keyword is refused, the daily cap and occurrence authority are shown truthfully, and configuration edits never alter an existing occurrence's scope.",
            "Route states display separately from the readiness read, including access-unknown and configuration-blocked.",
            "When the runtime stops, health turns stale within the configured bound; after restart, the new last tick and next due appear.",
            "The legacy /schedules routes are removed after their parity tests pass."])
deps("discovery-operations-screen",
    workspace_and_evidence="D1 renders in the shell with the shared inspector.",
    source_capabilities="Route capability, readiness and selection basis come from the registry.",
    local_runtime="Last tick, per-component health and next due come from the runtime health read.")

# ------------------------------------------------------------------ M2

ig = specs["interactive-graph"]
edit("interactive-graph",
    scope="First deliverable: a time-boxed spike (at most 3 working days) that renders {{graph-reads}} fixture branch pages with the candidate library and records the engineering decision. Recommended: a vendored, pinned, licence-recorded library such as Cytoscape.js with its SHA-256 in the repository; a hand-built layout only if the spike fails. Offer an optional, non-gating 30-minute human look. " + ig["scope"],
    interface=ig["interface"].replace(" Use the {{client-foundation}} vendored layout library and graph branch/generation reducer.", " This spec owns the graph branch/generation reducer and the layout library decision."))
specs["interactive-graph"]["rationale"]["workspace-and-evidence"] = "Selection opens the shared inspector."

# ------------------------------------------------------------------ M3 monitoring

edit("monitoring-depth-and-timing",
    title="Make live X windows comparable: saturation, receipt-time bounds and live-page method eligibility",
    owners="smi_monitoring.recent owns window projections; smi_monitoring.alerts and smi_monitoring.semantic own the new live-page method versions",
    evidence=["src/smi_monitoring/polling/route.py", "src/smi_monitoring/recent/store.py", "src/smi_monitoring/alerts/store.py", "src/smi_monitoring/semantic/method.py", "docs/adr/0019-source-free-quantitative-alert-history.md", "docs/adr/0023-bounded-recent-x-poll-authority.md", "tests/test_live_recent.py"],
    outcome="Live X windows state their saturation and receipt-time bounds truthfully and, under an accepted W02, produce honest live volume and controversy outcomes inside ADR 0023's one-page rule.",
    scope="(1) Project the stored acquisition.pagination_remaining as a typed collection_saturated limitation on window, volume and semantic reads. (2) Project the stored acquisition.retrieved_at (receipt time) as metrics_retrieved_at with its elapsed_seconds bound on live windows; offline and fixture windows report it as unrecorded; no column and no backfill write. (3) Add a separately versioned live-page eligibility rule to the volume and controversy owners: an unsaturated live page is a complete sample of the provider's recent-search results for the literal query, with market coverage unknown; receipt time bounds unknown capture and measurement times from above; a saturated window supports only a lower-bound crossing claim; a non-crossing result on a saturated window, and any saturated baseline, is not_assessable with collection_saturated. (4) Provide a shared live-shaped fixture builder that reproduces XRecentRoute.collect's receipt (declared_coverage partial, unknown capture time, pagination_remaining true or false). (5) Draft the W02 amendment text for ADR 0019, ADR 0023 and docs/monitoring.md. Non-goals: pagination or the counts endpoint (U3); global cadence configuration (cadence stays a topic-revision setting); rewriting stored coverage; recomputing existing assessments.",
    interface="Window reads gain collection_saturated: bool | null and metrics_retrieved_at plus retrieval_bound_seconds, where null means unrecorded. The method version is pinned on each assessment. The live-page versions are registered only when W02 is accepted; installed v1 behavior is unchanged.",
    migration="No schema column and no backfill. Version the new method rules alongside the installed ones. Update docs/monitoring.md, the monitoring owner instructions and, once W02 is accepted, the ADR 0019/0023 amendments.",
    integration="{{monitoring-workspace}}, {{monitoring-history}}, {{engagement-anomalies}} and {{semantic-shift}} consume the projections, the live-page eligibility rule and the shared live-shaped fixture builder.",
    authority="One page per window stays the ADR 0023 rule; a remaining page is a limitation, never a pagination loop. Receipt time is never presented as a capture or source timestamp.",
    recovery="Unknown poll responses keep their liability. A legacy window without a receipt stays unrecorded and is never assigned a time.",
    checks=["A live-shaped unsaturated window and a comparable live-shaped baseline yield significant_change or no_change under the live-page volume version, and still not_assessable (collection_incomplete) under installed v1.",
            "A saturated detection window over an unsaturated baseline yields an increase only when its lower bound meets the threshold, labelled as a lower bound; a saturated baseline or a saturated non-crossing result is not_assessable with collection_saturated. The same rule holds for the controversy method's thresholds.",
            "Live windows expose metrics_retrieved_at from the stored receipt and offline windows report it as unrecorded; it is never presented as capture time, and no schema column is added.",
            "Regression: cadence alignment, revision pinning and forced reactivation behave exactly as installed."],
    config="Live-page method versions are enabled only under an accepted W02. Saturation semantics follow the U3 choice.",
    size="M", milestone="M3")
deps("monitoring-depth-and-timing", stable_verification_clock="Changes the recent, alerts and semantic owners whose suites must be green; cadence stays a topic-revision setting, so there is no configuration edge.")

mw = specs["monitoring-workspace"]
mw["checks"][2] = "A live-shaped window from the {{monitoring-depth-and-timing}} builder shows its saturation and receipt-time limitation and the live-page method outcome in M1."
replace("monitoring-workspace", "integration",
    " Saturated windows from {{monitoring-depth-and-timing}} are shown when that spec exists.",
    " Saturation, receipt-time bounds and live-page method outcomes from {{monitoring-depth-and-timing}} are shown unconditionally; {{engagement-anomalies}} and {{semantic-shift}} method registration follows the integration rule.")
deps("monitoring-workspace", workspace_and_evidence=None,
    monitoring_depth_and_timing="M1 shows saturation, receipt-time bounds and live-page method outcomes unconditionally.")

mh = specs["monitoring-history"]
replace("monitoring-history", "integration",
    " Saturated windows are labelled as bounded counts when {{monitoring-depth-and-timing}} exists.",
    " Saturated windows render as lower bounds (>=N) with a distinct marker in chart and table.")
replace("monitoring-history", "interface", "Values reopen current policy and method validity on every read.",
    "Values reopen current policy and method validity on every read. This spec owns the chart-series reducer and defines a method-series registration contract register(method_key, version, read_points(topic, from, to, cursor)), where each point carries a value or null, unit, denominator, support IDs and comparability.")
mh["checks"].append("A stub method registered through the contract appears in the selector and table with its own denominators, with no chart-code change. Live-shaped saturated windows render as lower bounds in both chart and table.")
deps("monitoring-history", monitoring_workspace=None,
    monitoring_depth_and_timing="The chart renders saturated windows as lower bounds from the window projection.")

ea = specs["engagement-anomalies"]
ea["scope"] = ea["scope"].split(" Consume metrics_retrieved_at from")[0] + (
    " For live X, measurement age is metrics_retrieved_at minus published_at (an upper bound), comparable within a configured "
    "tolerance bounded by cadence and indexing delay; the result is labelled young-age engagement. This method version is "
    "registered only under an accepted W02; otherwise live engagement reports measurement_time_unknown. Six-hour "
    "re-measurement is a later path that needs a separately authorized operation and is not in the pilot. Chart and M1 "
    "integration follow the integration rule.")
ea["checks"].append("A live-shaped window pair yields a matched-age comparison under the live version and measurement_time_unknown under the rejected-decision configuration.")
edit("engagement-anomalies", decision_blockers=[])
deps("engagement-anomalies",
    monitoring_depth_and_timing="Consumes the metrics_retrieved_at and saturation projections and the live-page eligibility rule.",
    source_capabilities=None)

ss = specs["semantic-shift"]
ss["integration"] = "Runtime registers exact-window/method assessment. M1 shows provisional codes, ambiguous/unresolved cases, language mix, both samples and missing baseline. Chart, M1 and inbox integration follow the integration rule."
ss["checks"].append("A live-shaped window pair is assessed under the live-page eligibility rule, and a saturated baseline is not assessable.")
deps("semantic-shift", monitoring_depth_and_timing="Baseline-aware comparison reuses the live-page eligibility rule and saturation limitation rather than a second definition.")

ic = specs["interaction-checkpoint"]
edit("interaction-checkpoint",
    title="Check graph, chart, campaign and chat interaction in a real browser",
    scope=ic["scope"] + " Also execute the {{campaign-decisions}} and {{conversations}} browser checklists in EN and KO; the marketer is preferred for those two journeys, otherwise a named human reviewer.")
ic["checks"].append("Campaign and chat checklists are recorded with per-item pass/fail in EN and KO, with failing examples filed against their owning specs.")
deps("interaction-checkpoint", interactive_graph=None, monitoring_history=None,
    campaign_decisions="The campaign browser checklist under test.",
    conversations="The chat browser checklist (EN/KO, IME, drafts) under test.")

# ------------------------------------------------------------------ M4

specs["spending-operations"]["interface"] += " The configure forms call the {{operator-commands}} command layer; reconciliation and meter recovery stay here, with the receipts this spec already owns."
deps("spending-operations",
    client_foundation="S1 forms render in the shell with governed reads.",
    operator_commands="Forms reuse the operator command layer for scope, route and ceiling instead of a second path.")

replace("progressive-acquisition", "integration",
    "Pipeline renders broad/detail choices, field support, estimated value assumptions, remaining bounds, reused support and terminal stop reasons.",
    "Under the integration rule, the {{task-events-lineage}} pipeline view renders broad/detail choices, field support, estimated value assumptions, remaining bounds, reused support and terminal stop reasons, using the AcquisitionPlan.read model this spec provides.")

specs["inbox-email"]["scope"] += (
    " The transport is SMTP submission through the configured operator mailbox by default (U7); an HTTP email API is used "
    "behind the same delivery-identity model only if that is what the operator has. Every email carries a Message-ID derived "
    "from the logical delivery key. An ambiguous accepted response stays uncertain and appears prominently in the channel "
    "status with a one-action attributable reissue that uses a new Message-ID linked to the original.")
specs["inbox-email"]["checks"].append("Each email's Message-ID derives from its logical delivery key; a reissue carries a new linked ID.")
specs["inbox-email"]["rationale"]["workspace-and-evidence"] = "Inbox items open governed task, alert and evidence links in the shared inspector."

# ------------------------------------------------------------------ M5 readiness rows

pr = specs["provider-readiness"]
ROW_FMT = "Keep the {{live-feasibility-probes}} record format, owner and invariants, link the matching probe row and state what changed since the probe."
edit("provider-readiness",
    title="Record live discovery, model and recurring-work readiness",
    outcome="The pilot can truthfully state whether live keyword discovery, the model and recurring keyword work are permitted, usable and metered, with actual bounded receipts.",
    scope="The final signed-off readiness row for keyword discovery, the model and recurring keyword work. " + ROW_FMT + " Other capabilities have their own rows: {{monitoring-readiness}}, {{detail-route-readiness}} and {{email-readiness}}. No prices or readiness are inferred from test fixtures.",
    checks=["Actual authorized keyword discovery and model receipts reopen usable permitted publications and answers through public owners.",
            "Recurring keyword discovery runs with finite bounds and refuses on source policy or ceiling, with no fifty-post throughput claim.",
            "Actual provider-basis charges reconcile against exact operations, or remain recorded as unknown."],
    size="S")
deps("provider-readiness",
    live_feasibility_probes="Reuses the probe authorizations and record format.",
    local_runtime="Recurring keyword discovery needs the runtime.",
    spending_operations="Reconciles this capability's actual charges through operator controls.")

READINESS_COMMON = dict(lane="live-validation", size="S", milestone="M5",
    owners=pr["owners"], migration=pr["migration"], authority=pr["authority"], recovery=pr["recovery"],
    interface=pr["interface"], integration=pr["integration"])

new("monitoring-readiness",
    title="Record live X monitoring and alert-method readiness",
    evidence=["src/smi_monitoring/polling/route.py", "docs/monitoring.md", "docs/costs.md"],
    outcome="Live X polling and each alert method have a signed-off readiness record or an explicit blocked record with its reason, without market-completeness or significance claims.",
    scope="The readiness row for recurring live X polling and the volume, controversy, engagement and semantic-shift methods. " + ROW_FMT + " Record the states of W02 and U3.",
    checks=["Recurring X windows are observed with finite bounds, and activation and deactivation are recorded.",
            "Each method (volume, controversy, engagement, semantic shift) has a live outcome or a recorded not_assessable/blocked reason; live alert readiness is claimed only under an accepted W02, otherwise the row records blocked_by_decision.",
            "X and model charges reconcile, or remain unknown.",
            "The saturation rate over the readiness period is recorded against the U3 choice."],
    config="Requires actual X account permission, credentials, live-run authorization and the recorded W02 and U3 states.",
    **READINESS_COMMON)
deps("monitoring-readiness",
    live_feasibility_probes="Reuses the X row.",
    local_runtime="Recurring polling needs the runtime.",
    monitoring_depth_and_timing="Live windows need saturation and live-page eligibility.",
    engagement_anomalies="The engagement method under test.",
    semantic_shift="The semantic-shift method under test.",
    spending_operations="Reconciles X and model charges.")

new("detail-route-readiness",
    title="Record supplementary detail-route readiness",
    evidence=["src/smi_ingestion/adapters/bright_data.py", "docs/source-integrations.md", "docs/costs.md"],
    outcome="The named supplementary detail route has a signed-off readiness record per field or an explicit blocked record.",
    scope="The readiness row for the {{supplementary-detail-route}} route. " + ROW_FMT,
    checks=["Authorized detail receipts for each field reopen through public owners.",
            "Unsupported fields are explicitly unavailable.",
            "Charges reconcile, or remain unknown."],
    config="Requires actual account permission, credentials and live-run authorization; U4 for any web route.",
    **READINESS_COMMON)
deps("detail-route-readiness",
    live_feasibility_probes="Reuses the Bright Data row's field findings.",
    supplementary_detail_route="The route under test.",
    spending_operations="Reconciles its charges.")

new("email-readiness",
    title="Record email send readiness",
    evidence=["src/smi_tasks/notifications/store.py", "docs/user-guide.md"],
    outcome="The pilot can truthfully state whether notification email reaches the configured recipient through the configured transport.",
    scope="The readiness row for the {{inbox-email}} transport. " + ROW_FMT,
    checks=["One explicitly authorized test email goes to the configured recipient.",
            "Provider acceptance and actual recipient receipt are recorded separately.",
            "The governed link is verified from the intended access context.",
            "Uncertain-delivery handling is exercised with a simulated failure only, with no extra live sends."],
    config="Requires the operator mailbox account (U7) and explicit send authorization.",
    **READINESS_COMMON)
deps("email-readiness",
    live_feasibility_probes="Reuses the email-provider row.",
    inbox_email="The transport, delivery identity and inbox under test.")

hp = specs["human-pilot-acceptance"]
hp["scope"] += " Incorporates the four readiness rows; a recorded blocked row is a valid input, and the affected journey is recorded as blocked rather than passed."
deps("human-pilot-acceptance",
    exact_approval_tools=None, early_marketer_checkpoint=None, alert_investigation_promotion=None,
    interaction_checkpoint=None, plans_and_quality=None,
    provider_readiness="Usefulness must be judged on live discovery and model capabilities; a recorded blocked row is a valid input.",
    monitoring_readiness="Alert journeys are judged on live monitoring readiness; a recorded blocked row is a valid input.",
    detail_route_readiness="Acquisition journeys are judged on the live detail route; a recorded blocked row is a valid input.",
    email_readiness="Notification journeys are judged on live email; a recorded blocked row is a valid input.")

# ------------------------------------------------------------------ order, decisions, coverage

src["order"] = """stable-verification-clock pilot-configuration operator-commands client-foundation live-feasibility-probes
automated-interpretation pilot-scale-retrieval early-marketer-checkpoint local-runtime workspace-and-evidence
source-capabilities campaign-decisions task-events-lineage exact-approval-tools conversations
discovery-operations-screen graph-reads interactive-graph monitoring-depth-and-timing monitoring-workspace
monitoring-history alert-investigation-promotion engagement-anomalies semantic-shift interaction-checkpoint
spending-operations progressive-acquisition supplementary-detail-route inbox-email plans-and-quality
provider-readiness monitoring-readiness detail-route-readiness email-readiness human-pilot-acceptance
evaluated-retrieval agent-candidate agent-human-evidence enable-richer-agent hosted-actors-tenancy
projection-governance multimodal-ontology objective-portfolios outcomes-attribution causal-measurement""".split()
assert sorted(src["order"]) == sorted(specs), set(specs) ^ set(src["order"])

src["decisions"]["W02"]["title"] = "Decide live X window comparability and receipt-time semantics"
UD = {u["id"]: u for u in src["user_decisions"]}
UD["U1"].update(decision="Grant bounded live authorization and credentials early: model; Bright Data keyword, including a bounded discovery corpus for the early marketer check (up to 10 keywords, a few hundred posts); X recent for one topic over a bounded number of windows; the email mailbox's semantics. Per-capability call counts and one spending ceiling.",
    default="Request at plan start with the smallest useful caps. If not granted, the probes and the early marketer check stay blocked, the build continues on fixtures and premise-dependent specs stay provisional.",
    affects=["live-feasibility-probes", "early-marketer-checkpoint", "provider-readiness", "monitoring-readiness", "detail-route-readiness", "email-readiness"])
UD["W02"].update(decision="Ask at plan start. For live X: (a) may the recorded receipt time bound capture and metric measurement time from above; (b) may an unsaturated single page count as a complete sample of the provider's recent-search results for the literal query; (c) may a saturated window support only lower-bound crossing claims? This amends ADR 0019, ADR 0023 and docs/monitoring.md through new method versions.",
    default="Accept all three as a narrowly scoped amendment, with market coverage still unknown and installed v1 unchanged. If rejected, live windows stay not assessable, there are no live alerts and no live engagement, and monitoring readiness records blocked_by_decision. Blocks no spec.",
    affects=["monitoring-depth-and-timing", "engagement-anomalies", "semantic-shift", "monitoring-readiness"])
UD["U3"].update(decision="Pilot X monitoring depth, revisited after the probe's X row: (a) counts endpoint as the volume series; (b) bounded multi-page collection; (c) shorter cadence within configured cost; (d) accept a saturated lower-bound display. (a) and (b) need an ADR 0023 successor and more recurring paid authority.",
    default="(c)+(d). The probe's X row records the saturation rate and a recommendation, and the coordinator re-asks. Choosing (a) or (b) adds one M spec before monitoring readiness.",
    affects=["live-feasibility-probes", "monitoring-depth-and-timing", "monitoring-history", "monitoring-readiness"])
UD["U4"]["affects"] = ["supplementary-detail-route", "detail-route-readiness"]
UD["U5"].update(decision="Permit scoped headless-browser tests against the loopback app, either (i) in CI only with no agent browsing, or (ii) also by agents?",
    default="Keep declining. Stated cost: graph and chart interaction stay human-verified only, at the browser checkpoint and release record, with Node state tests in between.",
    affects=["client-foundation", "interactive-graph", "monitoring-history", "interaction-checkpoint"])
UD["U7"].update(decision="Pilot email goes to one configured recipient through SMTP submission from an operator-supplied mailbox account; multi-recipient preferences come later.",
    default="Yes, with SMTP submission. If the operator has only an HTTP email API account, inbox-email uses it behind the same delivery-identity model.",
    affects=["live-feasibility-probes", "inbox-email", "email-readiness", "hosted-actors-tenancy"])

A = src["assignments"]


def add(ids, slug):
    for i in ids:
        if slug not in A[i]:
            A[i].append(slug)


def drop(ids, slug):
    for i in ids:
        A[i] = [s for s in A[i] if s != slug]


add(["FR-C01", "FR-S01", "OFR-E03", "OFR-S03", "UD-02"], "operator-commands")
add(["PROP-03"], "early-marketer-checkpoint")
drop(["UD-01", "UD-03"], "early-marketer-checkpoint")
add(["FR-A01", "FR-B01", "UD-01", "UD-03", "R2-CHAT"], "interaction-checkpoint")
add(["PROP-27"], "local-runtime")
drop(["FR-P01"], "source-capabilities")
add(["FR-P01", "FR-P02", "FR-L01", "OFR-E03", "PROP-34", "UD-03"], "discovery-operations-screen")
add(["FR-C03"], "monitoring-depth-and-timing")
drop(["FR-C01", "FR-C02", "FR-P04", "FR-P09", "PROP-23", "UD-05"], "provider-readiness")
add(["FR-C01", "FR-C02", "FR-C03", "FR-P09", "FR-S01", "OFR-S01"], "monitoring-readiness")
add(["FR-P04", "PROP-23", "FR-S01", "OFR-S01"], "detail-route-readiness")
add(["UD-05", "FR-C05"], "email-readiness")
for key, slugs in A.items():
    assert slugs or key == "UD-09", key

SOURCE.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n")
print("applied round 2:", len(specs), "specs,", sum(len(s["dependencies"]) for s in specs.values()), "edges")
