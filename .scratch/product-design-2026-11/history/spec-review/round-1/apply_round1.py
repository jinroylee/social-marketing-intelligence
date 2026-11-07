"""Apply the accepted round-1 revision (validation.md section 4) to task4/plan_source.json.

Run once from the repository root. Old slugs keep their identity; splits keep the old slug
for the half named first in validation.md 4a and add a new slug for the other half.
"""

import json
from pathlib import Path

SOURCE = Path(".scratch/product-design-2026-11/task4/plan_source.json")
src = json.loads(SOURCE.read_text())
specs = src["specs"]
assert len(specs) == 30 and "pilot-configuration" not in specs, "round 1 already applied"

UI = ("{{client-foundation}}")


def edit(slug, **fields):
    for key, value in fields.items():
        assert key in specs[slug] or key in {"size", "ui_bearing", "milestone"}, (slug, key)
        specs[slug][key] = value


def new(slug, **fields):
    assert slug not in specs
    base = dict(dependencies=[], rationale={}, decision_blockers=[], ui_bearing=False,
                config="None beyond the shared test prerequisites.")
    base.update(fields)
    for key in ("title", "lane", "size", "milestone", "dependencies", "rationale", "owners", "evidence", "outcome",
                "scope", "interface", "migration", "integration", "authority", "recovery", "checks", "config"):
        assert key in base, (slug, key)
    specs[slug] = base


def deps(slug, **rationale):
    """Set direct dependencies with exactly one recorded reason per edge (keyword = slug with _ for -)."""
    pairs = {k.replace("_", "-"): v for k, v in rationale.items()}
    for d in pairs:
        assert d in specs, (slug, d)
    specs[slug]["dependencies"] = list(pairs)
    specs[slug]["rationale"] = pairs


# ---------------------------------------------------------------- new and rescoped pilot foundations

edit("stable-verification-clock",
    title="Restore a complete, time-stable verification baseline",
    owners="Test infrastructure maintainers; owning-module maintainers review fixture conversions in their suites",
    outcome="Every implementation worker starts from a complete, attributable test baseline in which no test depends on the real calendar date.",
    scope="Run the whole suite once without --maxfail against real PostgreSQL and classify every failure as clock-aging or other. Add one shared relative-date/controlled-clock test helper and convert freshness-, retention-, seven-day-window- and accounting-period-sensitive fixtures to it; use relative SQL intervals where the database clock decides. Non-goals: no product freshness, retention or window policy change; no time-travel tooling for the PostgreSQL server.",
    interface="Proposed tests/support clock helper exposing a fixture base instant and relative constructors (days_ago, within_retention) used by test fixtures only. Keep public KnowledgeAssistant/AssistantEnrichment, cost, polling and schedule test journeys; never patch private business outcomes.",
    migration="No schema migration. Record the full-suite inventory with exact failures. Update docs/development.md: remove the current fixture limitation only after a real passing run, and document the helper and the --maxfail inventory command.",
    integration="No UI or agent behavior changes. Every later spec's completion evidence relies on this baseline.",
    authority="Tests must not grant freshness, retention or window eligibility to old or unknown captures. The src/ diff for this spec contains no freshness, retention or window constant change.",
    recovery="A database preflight failure is a failed prerequisite with its exact cause. A non-clock failure found by the inventory is filed against its owning module instead of being masked here.",
    checks=["Record the full-suite inventory (no --maxfail) with every failing test and its classification.",
            "All clock-aging failures pass, and the src/ diff contains no freshness, retention or window constant change.",
            "The clock-sensitive subset passes with the helper base shifted +90 days.",
            "Stale-capture and unknown-capture cases still report explicit limitations.",
            "uv run --locked python tools/check.py passes against real PostgreSQL and docs/development.md reflects the actual result."],
    size="M", milestone="M0")

new("pilot-configuration",
    title="Compose the local pilot from one validated configuration",
    lane="pilot-build", size="M", milestone="M0",
    owners="smi_review composition root plus a small proposed configuration module; route owners keep their own validation",
    evidence=["src/smi_review/server.py", "src/smi_review/app.py", "src/smi_monitoring/polling/store.py", "src/smi_ingestion/cli.py", "docs/user-guide.md"],
    outcome="One operator starts the review server, runtime and CLIs against simulated or provider routes from one validated, versioned local configuration.",
    scope="A TOML or JSON file with secrets referenced only by environment-variable name; explicit simulated/provider classification for the model, X recent, Bright Data keyword/profile and email routes; process gates, thresholds, caps, cadence defaults and an interpretation catalog bound; a source-free readiness() read; and one compose(config) used by smi-review main, the runtime and the CLIs, wiring ResponsesRoute, LiveXConfig and the Bright Data routes. Name the exact secret variable per route with a named missing-secret diagnostic; an alias for the two documented Bright Data names is optional. Non-goals: hosted secrets management; any configuration that confers topic activation or live schedule authority.",
    interface="Proposed PilotConfig.load(path) -> validated, versioned config with digest; compose(config) -> ReviewApp plus runtime/CLI owners; readiness(config) -> per-route classification, missing named prerequisites and configuration digest, never secret values or handles. Existing CLI flags keep working or map one-to-one.",
    migration="No business tables. Document the file schema, every secret variable name and the readiness read in docs/development.md, docs/user-guide.md and docs/architecture.md. Add the configuration module's AGENTS.md with its sibling relative CLAUDE.md symlink.",
    integration="The runtime, live probes, notification transport and capability registry consume this one configuration. UI reads only the source-free readiness projection.",
    authority="Configuration routes, credentials, process gates, thresholds and caps. Topic activation and live schedule activation remain recorded operator commands under ADRs 0015 and 0023; no file or environment key confers them.",
    recovery="An invalid or unknown key, or a missing referenced secret, fails start-up with a sanitized named reason rather than a provider-looking failure. Changing the file never alters already admitted task, window or occurrence scope.",
    checks=["An invalid or unknown key, or a missing referenced secret, fails start-up with a sanitized named reason.",
            "With a simulated model configured, the shipped server runs ranked recommendation, criteria interpretation and a knowledge answer end to end.",
            "With live X configured but no recorded activation, no X request is dispatched.",
            "readiness() never exposes secret values or provider handles.",
            "Existing CLI flags keep working or map one-to-one, and the documentation names every secret variable."],
    config="A local configuration file and environment-held secrets supplied by the operator. Simulated routes are valid configuration.")

new("client-foundation",
    title="Establish the bilingual client foundation, shell and client verification",
    lane="pilot-build", size="L", milestone="M0", ui_bearing=False,
    owners="smi_review owns the client foundation, shell and versioned adapter framework; domain owners retain decisions",
    evidence=["src/smi_review/static/review.js", "src/smi_review/static/review.css", "src/smi_review/server.py", "tools/check.py", ".scratch/product-design-2026-11/task3/r2/verify-prototype.cjs"],
    outcome="Every later UI spec builds on one tested client structure: shell, navigation, theme, EN/KO switch, API client and shared freshness behavior.",
    scope="Plain ES modules served from smi_review/static with no build step. Record one engineering decision on graph layout and rendering; recommended is a vendored, pinned, licence-recorded graph library (for example Cytoscape.js) with its SHA-256 in the repository, because a hand-built incremental layout with pinning is multi-week work; the chart is plain SVG. Deliver the API client (envelope parsing, CSRF, request-ID generation, retry kinds), the versioned same-origin /api/v1 adapter framework, the i18n catalog mechanism (catalogs grow per spec), the shell, navigation, four-colour theme and EN/KO switch, the shared display_valid_until freshness utility, and reducer modules for graph branch/generation, chart series and composer/draft/IME state. Non-goals: framework rewrite, CDN dependencies, browser automation.",
    interface="Client modules: api (request(command|read) -> envelope with allowed_actions, display_valid_until and sanitized error), i18n (t(key, params), locale switch preserving inputs and IDs), freshness (revalidate on focus, navigation, explicit read and a configured bounded timer; fail closed at the deadline; an older response never restores a newer tombstone), and pure reducers for graph branches, chart series and the composer. Server side: versioned /api/v1 routing that parses each command explicitly and derives RequestContext on the server, beside the existing forms.",
    migration="No business tables. Add node --test execution to tools/check.py and list Node in docs/development.md and CI. Record the vendored library, version, licence and digest. Update docs/local-review.md, docs/architecture.md and smi_review/AGENTS.md with the client structure rules.",
    integration="Every UI-bearing spec reuses these modules and adds its catalog keys; none re-implements freshness, envelopes or locale handling. Agent tools later read the same envelopes.",
    authority="Preserve loopback Host, same-origin writes, CSRF, HTML escaping, no-store responses and source URL validation. Locale and client state are presentation only, never evidence or authority. Client-held positions or drafts never contain source values.",
    recovery="A failed read keeps selected record IDs and drafts. Missing translations fail the completeness check rather than rendering raw keys. Expired freshness withholds content until a successful governed read.",
    checks=["tools/check.py runs the Node tests and fails on a broken reducer.",
            "The graph reducer discards a late page with a mismatched generation and keeps shared members when one of two overlapping branches collapses.",
            "The composer state never sends during IME composition, Shift+Enter inserts a newline and empty input adds no turn.",
            "The freshness utility withholds content at display_valid_until without a successful revalidation and ignores an older response.",
            "The catalog completeness check fails on a missing KO key, and the EN/KO switch preserves inputs and IDs over loopback HTTP; foreign Host, missing CSRF and forged actor/workspace fields are rejected."],
    config="Node available for the shared check. No CDN or network fetch at runtime.")

new("live-feasibility-probes",
    title="Probe bounded live model, discovery, X and email-provider feasibility early",
    lane="live-validation", size="M", milestone="M0",
    owners="Named local operator plus the model, ingestion, monitoring and notification maintainers",
    evidence=["src/smi_ingestion/cli.py", "src/smi_monitoring/polling/route.py", "src/smi_assistant/answers.py", "docs/source-integrations.md", "docs/costs.md"],
    outcome="The premises of {{monitoring-depth-and-timing}}, {{engagement-anomalies}}, {{supplementary-detail-route}} and {{inbox-email}} are settled by bounded real evidence before those specs finish.",
    scope="One independently completable capability row each: model (schema adherence, latency, cost basis); Bright Data keyword (fields, capture times, cost basis, KR/JP yield); X recent (posts per window, next_token frequency, public_metrics fields and timing, counts-endpoint availability for the account tier); email provider (acceptance and idempotency semantics, sender-domain readiness; no product send because no transport exists yet). Non-goals: production readiness claims; fixture substitution.",
    interface="Each row records operator, authorization, caps, configuration digest, request/response/evidence IDs, billing basis and unresolved portions in the same record format {{provider-readiness}} later reuses. Probes run through installed owners composed by {{pilot-configuration}}.",
    migration="No feature migration. Store probe records in owner-approved evidence locations with governed retention. Update docs/source-integrations.md and docs/monitoring.md only with demonstrated facts.",
    integration="Findings feed the cadence and saturation configuration of {{monitoring-depth-and-timing}}, the W02 decision, the detail fields of {{supplementary-detail-route}} and the retry design of {{inbox-email}}. Specs whose premises depend on a row keep those premises marked provisional until that row passes.",
    authority="Only explicitly authorized, bounded calls with recorded caps. A successful HTTP response is not permission, final billing, usefulness or delivery. Probes activate no recurring topic or schedule.",
    recovery="Unknown response or charge records liability and pauses reissue. A refused or blocked row is a valid recorded outcome and blocks only claims for that capability.",
    checks=["Each capability row has an actual authorized receipt or an explicit refused/blocked state with its reason.",
            "The X row records saturation and metric fields that feed the {{monitoring-depth-and-timing}} configuration and the W02 decision.",
            "The Bright Data row names candidate {{supplementary-detail-route}} detail fields and their observed coverage.",
            "Each billing basis reconciles against recorded commitments or is recorded as unknown."],
    config="Blocked until the user grants bounded live authorization, credentials, per-capability call counts and a spending ceiling (U1). If not granted, the build continues on fixtures and premise-dependent specs stay provisional.")

new("automated-interpretation",
    title="Publish catalog-scoped caption interpretations from automated tasks",
    lane="pilot-build", size="M", milestone="M0",
    owners="smi_knowledge owns the support-based interpretation port; the smi_tasks worker composes it before publication",
    evidence=["src/smi_tasks/worker.py", "src/smi_knowledge/publications/store.py", "src/smi_knowledge/store.py", "src/smi_knowledge/queries/store.py", "src/smi_campaigns/comparison.py"],
    outcome="Task-discovered posts carry published brand/product interpretations, so campaign criteria and graph mention edges work on real data.",
    scope="Add a support-based interpretation port (the existing KnowledgeStore.prepare reads frozen datasets only). The worker interprets prepared support against the workspace's active catalogs inside its TaskExecution, before the publication transaction, and publishes members and claims together with interpretation_ids. On interpretation failure the members still publish with an explicit interpretation_failed coverage state. Non-goals: model-based interpretation; new catalog semantics.",
    interface="Proposed KnowledgeStore.prepare_support(support: tuple[SupportReference, ...], catalog_ids, actor, *, request_id, connection) -> interpretation IDs and coverage. Idempotent request identity is task + catalog + method version. An explicit re-interpretation creates a successor publication, and queries de-duplicate the same observation/derivation by preferring the newest current publication.",
    migration="Schema change only if interpretation status needs a column on task coverage. Update docs/knowledge.md, docs/tasks.md, the ERD and the knowledge/tasks owner instructions in the same change.",
    integration="Campaign comparison, graph mention edges and chat support read the published claims through existing public query operations. No UI change beyond coverage display.",
    authority="Interpretation is deterministic rule work with no external I/O inside the fenced worker. It never asserts Creator identity, endorsement or causation, and a withdrawn source purges its interpretation copies.",
    recovery="A crash between interpretation and publication resumes on the same request identity without duplicate claims. A forced failure never blocks member publication.",
    checks=["A keyword task over a corpus that mentions a registered brand yields supported claims in the query result, and the member is no longer flagged caption_interpretations_not_published.",
            "A forced interpretation failure still publishes the members and reports interpretation_failed.",
            "A re-interpretation never produces duplicate members in search.",
            "A crash between interpretation and publication recovers without duplicate claims.",
            "A withdrawn source purges its interpretation copies from new reads."])

new("pilot-scale-retrieval",
    title="Select question-, brief- and graph-scoped governed support at pilot scale",
    lane="pilot-build", size="L", milestone="M0",
    owners="smi_knowledge.queries owns selection; smi_ingestion owns the governed index columns and migration",
    evidence=["src/smi_knowledge/queries/store.py", "src/smi_assistant/store.py", "src/smi_campaigns/store.py", "src/smi_knowledge/graph/store.py", "src/smi_knowledge/queries/AGENTS.md"],
    outcome="Chat, campaign comparison and graph seeds select relevant permitted support from a KB much larger than 100 publications, with explicit, reported bounds.",
    scope="An indexed selection port owned by ingestion (governed text and normalized-term index on ingestion-owned columns, purged with the source) used by KnowledgeQueries; configurable member and scan bounds with keyset continuation reported in coverage; a deterministic per-turn scope derived from the question (NFKC normalization, literal terms, CJK n-grams, catalog alias to subject_ids) pinned in the answer/turn record; brief-driven, account-centric candidate selection for prepare_current_comparison; GraphScope seeds use the same port. Non-goals: embeddings and semantic ranking ({{evaluated-retrieval}}); model-proposed terms, which would add a second model influence not covered by ADR 0017.",
    interface="Proposed QueryScope gains derived_terms, subject_ids, scan_bound and continuation; KnowledgeQueries.search reports actual scanned publications, members, truncation and continuation. Proposed derive_scope(question|brief, catalogs) -> pinned, digest-stable scope. Retrieval never broadens authority or source scope.",
    migration="Ingestion migration for the governed index with purge-with-source semantics; no second source-value cache. Update docs/knowledge.md, smi_knowledge/queries/AGENTS.md and the ERD.",
    integration="{{conversations}} pins each turn's derived scope, {{campaign-decisions}} uses brief-driven selection and {{graph-reads}} uses the same seed selection. Coverage text in the UI reports the actual bounds.",
    authority="Current process/display/retention policy filters every selected member. Withdrawal removes index content with the source. Historical results reopen their pinned membership exactly.",
    recovery="A bound reached is reported as result_limit_reached with a continuation, never as completeness. An index rebuild is idempotent and never resurrects withdrawn values.",
    checks=["On a fixture KB of at least 1,000 published posts across at least 200 publications, a question about a brand published only in old publications returns that support with derived terms pinned.",
            "A comparison includes an eligible creator whose only support is older than the newest 100 members, and its coverage reports the actual scan bounds.",
            "Withdrawing a source removes it from the index and from new results; a historical result reopens exactly.",
            "Per-query work stays inside the configured bound, with a recorded latency budget on the reference fixture.",
            "Exact retries remain digest-stable."])

deps("pilot-configuration", stable_verification_clock="Configuration changes touch every composition root and need a trustworthy full-suite result.")
deps("client-foundation", stable_verification_clock="Adds Node checks to the shared check, which must be green first.")
deps("live-feasibility-probes", pilot_configuration="Model and live-X routes, credentials and caps are only constructible through the pilot configuration.")
deps("automated-interpretation", stable_verification_clock="Changes task publication behavior covered by the existing worker suites.")
deps("pilot-scale-retrieval", stable_verification_clock="Changes query bounds exercised across the campaign, assistant and graph suites.")

# ---------------------------------------------------------------- milestone M1: runtime, workspace, campaign, tasks, chat

edit("local-runtime", size="L", milestone="M1")
deps("local-runtime", pilot_configuration="The runtime reads routes, gates, budgets and cadence from the validated configuration.")

edit("workspace-and-evidence",
    title="Open saved campaigns and inspect governed evidence in the shared inspector",
    owners="smi_review owns the campaign index, detail reads and shared governed inspector; domain owners retain decisions",
    outcome="A marketer opens all saved campaigns and inspects exact permitted evidence through one shared inspector, in EN or KO.",
    scope="Deliver the campaign index and detail reads and the shared governed inspector (observed/derived/human bases, independent dates, conflicts, full-input membership, truncation and current availability), with the EN/KO keys for these screens. Shell, navigation, theme, i18n mechanism and adapter framework come from {{client-foundation}}. No hosted authentication or arbitrary source embedding.",
    interface="Proposed ReviewWorkspace.campaigns(context, cursor, limit) and evidence(selection_id, purpose='display') return the common response envelope in architecture-target.md through the {{client-foundation}} adapter framework.",
    migration="Presentation needs no new business tables. Persist only a locale preference if needed, scoped to the local actor. Update docs/local-review.md and the review owner instructions. Retain no source values in browser storage.",
    integration="Campaign index opens real CampaignStore.list_campaigns/read_campaign results. Inspector renders observed, derived and human bases, independent dates, conflicts, full-input membership, truncation and current availability. Agent read tools later use the same envelopes.",
    checks=["Start the actual loopback app with two saved campaigns and reopen each after process restart.",
            "The EN/KO switch preserves brief input and semantic IDs on the campaign and inspector screens.",
            "Withdraw selected support and observe no label, excerpt or aggregate leakage in the response or DOM.",
            "Reject foreign Host, missing CSRF and forged actor/workspace fields through public HTTP on these reads and commands."],
    size="M", milestone="M1", ui_bearing=True)
deps("workspace-and-evidence", client_foundation="Needs the shell, API client and envelope, i18n mechanism and freshness utility.")

specs["campaign-decisions"]["checks"] += [
    "A shortlist over task-discovered support shows real supported or unknown brand/product judgments from published interpretations.",
    "A comparison over a KB of more than 100 publications reports its scan bounds and includes an older eligible creator."]
edit("campaign-decisions", size="L", milestone="M1", ui_bearing=True)
deps("campaign-decisions",
    workspace_and_evidence="C1 renders evidence through the shared inspector and campaign index.",
    pilot_scale_retrieval="The candidate pool must reach eligible creators beyond the newest 100 members.",
    automated_interpretation="Brand/product criteria need published interpretations on discovered support.",
    pilot_configuration="Model ranking and criteria interpretation must be operable from the shipped server.")

edit("task-events-lineage",
    interface="Proposed AcquisitionTasks.events(task_id, actor, after_sequence, limit) -> events/cursor/head; TaskLineage.read remains the evidence source. Each progress event has task/attempt/execution identity, sequence, phase, timestamp where recorded, sanitized code and publication receipt ID where committed. The owner may implement events() over the existing acquisition_attempts.phases and adds a table only where cursor or timestamp requirements are unmet. Polling is sufficient; an event stream must resume by cursor and use the same checks.",
    migration="Prefer derivation from existing attempt phases. If a task-owned task_progress_events table is needed, give it unique task/sequence and effect identity, write it on TaskExecution's ownership connection with each phase commit, and backfill only source-free snapshot markers for legacy tasks, never invented historical phases. Update tasks, architecture, ERD and lineage/review contracts for any actual change.",
    size="S", milestone="M1", ui_bearing=True)
deps("task-events-lineage", workspace_and_evidence="The T1 timeline opens lineage evidence in the shared inspector.")

edit("exact-approval-tools",
    interface=specs["exact-approval-tools"]["interface"] + " campaign.recommend wraps the installed CampaignStore.recommend/CampaignRecommendations.regenerate operations, so this spec does not wait for the C1 UI.",
    size="M", milestone="M1", ui_bearing=True)
deps("exact-approval-tools",
    task_events_lineage="Approve/submit receipts and the task.status/events tools read the progress feed.",
    workspace_and_evidence="A1 scope review shows exact evidence and limits in the shared inspector.")

c = specs["conversations"]
edit("conversations",
    title="Save conventional chat threads with question-scoped extractive turns",
    scope="Implement R2-CHAT rail, log, composer, per-thread draft and bounded history. Pilot answers remain labelled extractive selections under ADR 0017. Each turn pins the {{pilot-scale-retrieval}} scope derived from its question, and carries bounded prior human questions and answer IDs as context references with explicit context selection/omission. Fluent synthesis and inferred executable scope await later specs.",
    integration=c["integration"].split(" Open source-dependent views use the shared display_valid_until contract")[0] + " The research-status disclosure is a conditional check, verified once {{exact-approval-tools}} exists.",
    checks=[x for x in c["checks"] if not x.startswith("Keep a source-dependent view open")] + [
        "Two different questions over the same KB of more than 100 publications select different, relevant support, and the pinned scope reopens exactly."],
    size="L", milestone="M1", ui_bearing=True)
deps("conversations",
    workspace_and_evidence="Per-turn sources open in the shared inspector.",
    pilot_scale_retrieval="Each turn's pinned retrieval scope is derived from the question.",
    pilot_configuration="The shipped server needs the configured model route.")

new("early-marketer-checkpoint",
    title="Check brief-to-shortlist and chat with a marketer on real discovered data",
    lane="human-validation", size="S", milestone="M1",
    owners="Actual pilot marketer and a KR/JP reader, supported by the campaign, assistant and quality maintainers",
    evidence=["docs/evaluation.md", "src/smi_review/quality/", ".scratch/product-design-2026-11/ui-review-status.md"],
    outcome="Real-data usefulness defects in the two headline journeys surface while they are cheap to fix.",
    scope="One marketer completes brief-to-shortlist and three chat questions on automatically discovered live data, in EN and KO, using the browser checklists delivered by {{campaign-decisions}} and {{conversations}}. The session records exact build/config identity, outputs, failures and corrections. Not a release gate; {{human-pilot-acceptance}} remains the release record.",
    interface="Record reviewer, language, build and configuration digest, data provenance (live, not fixture), exact inputs/outputs and per-journey pass/fail under the quality owner's attributable review contract.",
    migration="No production schema change beyond quality-owner records. Update docs/evaluation.md with the actual checkpoint outcome and unresolved gaps.",
    integration="Defects are filed against their owning spec's execution issue. Results are inputs to {{human-pilot-acceptance}} at the same or a newer build identity.",
    authority="A model, fixture or coordinator cannot stand in for the marketer. Design approval and agent checks are not this checkpoint.",
    recovery="A failed journey keeps its failing examples and owner; fixes re-run the affected journey rather than rewriting the record.",
    checks=["A named reviewer, build identity and live data provenance are recorded.",
            "Each journey has a pass/fail with failing examples kept.",
            "Each defect is filed against its owning spec."],
    config="Requires an actual marketer, a KR/JP reader, the model and Bright Data keyword rows of the live probes passed, and permitted browser use by that human.")
deps("early-marketer-checkpoint",
    live_feasibility_probes="Requires passed Bright Data keyword and model probe rows, so the session runs on real data and a real model.",
    local_runtime="Discovery must run automatically, not by hand.",
    campaign_decisions="The brief-to-shortlist journey under test.",
    conversations="The chat journey under test.")

# ---------------------------------------------------------------- milestone M2: graph

edit("graph-reads",
    scope=specs["graph-reads"]["scope"] + " Graph seeds and continuation use the {{pilot-scale-retrieval}} selection port instead of the newest 100 members.",
    size="M", milestone="M2")
deps("graph-reads", pilot_scale_retrieval="Graph seeds and continuation must use pilot-scale selection, not the newest 100 members.")

g = specs["interactive-graph"]
edit("interactive-graph",
    interface=g["interface"] + " Use the {{client-foundation}} vendored layout library and graph branch/generation reducer.",
    integration=g["integration"].split(" Open source-dependent views use the shared display_valid_until contract")[0],
    checks=["Node reducer tests: expand two overlapping branches, collapse one and retain shared members, selection and pinned positions.",
            "Node reducer tests: change filters during a slow page and deliver the stale response late; observe no stale merge. A governed withdrawal response removes affected nodes immediately.",
            "Explicit Load more/truncation drives bounded server work through the public API with no unbounded recursive fetch.",
            "Deliver the {{interaction-checkpoint}} checklist covering pointer drag/pin, pointer-anchored zoom, Fit, reduced motion and keyboard/list-only search, selection, traversal, evidence, pin and fit."],
    size="L", milestone="M2", ui_bearing=True)
deps("interactive-graph",
    graph_reads="Consumes branch pages, cursors and generations.",
    workspace_and_evidence="Selection opens the shared inspector; the client foundation's layout and reducers arrive through it.")

# ---------------------------------------------------------------- milestone M3: monitoring

new("monitoring-depth-and-timing",
    title="Make monitoring saturation, cadence and metric retrieval time explicit",
    lane="pilot-build", size="M", milestone="M3",
    owners="smi_monitoring.polling and smi_monitoring.recent own collection limits and metric support fields",
    evidence=["src/smi_monitoring/polling/route.py", "docs/monitoring.md", "docs/adr/0023-bounded-recent-x-poll-authority.md", "src/smi_monitoring/alerts/store.py"],
    outcome="Live monitoring states truthfully how complete each window is and when metrics were retrieved, inside ADR 0023.",
    scope="A collection_saturated limitation whenever next_token is present, carried into volume, chart and semantic method limitations; configurable cadence with probe-informed values and cost bounds; metrics_retrieved_at recorded on recent metric support as the successful-response receipt time, documented as retrieval time and not a source or measurement timestamp; and proposed W02 ADR text for {{engagement-anomalies}}. Non-goals: pagination beyond one page (U3); recomputing old windows.",
    interface="Recent window coverage gains collection_saturated with the observed next_token presence; recent metric support gains metrics_retrieved_at per attempt. Cadence is read from {{pilot-configuration}} and pinned per activation.",
    migration="Add the saturation and metrics_retrieved_at fields with explicit legacy-unrecorded values. Update docs/monitoring.md, the ERD and the monitoring owner instructions.",
    integration="{{monitoring-workspace}} and {{monitoring-history}} display saturation; {{engagement-anomalies}} consumes metrics_retrieved_at only under W02.",
    authority="One page per window stays the ADR 0023 rule; a remaining page is a coverage limitation, never a pagination loop. Cadence changes need fresh activation and keep finite cost bounds.",
    recovery="Unknown poll responses keep liability without repetition. Legacy windows report metrics_retrieved_at as unrecorded rather than inventing a time.",
    checks=["A simulated response with next_token yields collection_saturated on the window and on dependent volume and chart reads.",
            "A shorter configured cadence produces non-overlapping, equal-duration windows without catch-up loops.",
            "metrics_retrieved_at persists exactly once per attempt and is never shown as capture time.",
            "Legacy windows report metrics_retrieved_at as unrecorded."],
    config="Cadence values informed by the X row of the live probes; validated cost bounds.")
deps("monitoring-depth-and-timing", pilot_configuration="Cadence, saturation and cost bounds are validated configuration.")

m = specs["monitoring-workspace"]
m_checks = list(m["checks"])
edit("monitoring-workspace",
    title="Operate independent topics, activation and alert history",
    owners="smi_monitoring recent/polling/alerts/semantic retain their separate contracts; smi_review renders M1",
    outcome="A marketer configures and explicitly activates an independent topic and inspects its windows, alert history and original alert evidence.",
    scope="Deliver topic revision/activation/pause, method/cadence/bounds/retention controls, actual last collection and health, alert history and snapshots. Start with installed volume and provisional controversy; register {{engagement-anomalies}}/{{semantic-shift}} methods when available. Investigation and promotion are {{alert-investigation-promotion}}.",
    interface="M1 composes RecentMonitoring.configure/read_topic/read_window/timeline, RecentPolling.activate/deactivate/read, quantitative/semantic readers and snapshot MonitoringStore. New adapters require exact topic version, window/alert selections, request IDs and trusted operator context. Preserve source publication, capture, metric measurement and import times independently.",
    integration="Monitoring is accessible with no campaign or populated KB. Saturated windows from {{monitoring-depth-and-timing}} are shown when that spec exists.",
    authority="Saving topic settings grants no recurring live authority. Configuration edits require fresh activation.",
    recovery="Unknown poll response stays waiting with liability. Pause leaves in-flight history intact. A withheld alert keeps source-free historical identity.",
    checks=[m_checks[0], m_checks[3], "When {{monitoring-depth-and-timing}} exists, a saturated window displays its collection limitation in M1."],
    size="M", milestone="M3", ui_bearing=True)
deps("monitoring-workspace", workspace_and_evidence="M1 renders windows and alerts through the shell and inspector.")

h = specs["monitoring-history"]
edit("monitoring-history",
    integration=h["integration"].split(" Open source-dependent views use the shared display_valid_until contract")[0] + " Saturated windows are labelled as bounded counts when {{monitoring-depth-and-timing}} exists.",
    checks=[x for x in h["checks"] if not x.startswith("Keep a source-dependent view open")][:3] + [
        "Withdraw an input and observe policy-safe history, summary and evidence. Deliver the {{interaction-checkpoint}} checklist for keyboard selection, latest/selected/gap behavior and EN/KO metric-state stability."],
    size="M", milestone="M3", ui_bearing=True)
deps("monitoring-history", monitoring_workspace="The chart is a view of topic windows and alert history composed in M1.")

new("alert-investigation-promotion",
    title="Investigate alerts with existing KB context and promote selected evidence",
    lane="pilot-build", size="S", milestone="M3", ui_bearing=True,
    owners="smi_monitoring context and promotion retain their contracts; smi_review renders M2",
    evidence=["src/smi_monitoring/context/", "src/smi_monitoring/promotion/", "tests/test_monitoring_promotion.py"],
    outcome="A marketer investigates an alert using only existing KB context and selectively promotes useful observations through normal ingestion.",
    scope="Deliver KB-only investigation and exact promotion review over installed context and promotion owners. Rich contextual prose stays later work.",
    interface="M2 composes context.investigate/read and promotion.promote/read with exact alert, window and observation selections, request IDs and trusted operator context.",
    migration="Reuse monitoring owner tables. Add public bounded list/history adapters rather than querying another owner's SQL. Update monitoring and local-review contracts.",
    integration="Context explanation pins the original recent alert plus the existing published KB selection; an empty KB is an explicit context gap. Promotion selects exact members, then normal ingestion/publication with inherited source identity and deadline.",
    authority="Investigate makes zero external calls and creates no campaign. Promotion creates no unsupported Creator/product identity association or renewed age.",
    recovery="Expired or withdrawn promotion cannot reconstruct copied evidence after permission restoration. Withheld context keeps source-free historical identity.",
    checks=[m_checks[1], m_checks[2]],
    config="None beyond the shared test prerequisites.")
deps("alert-investigation-promotion", monitoring_workspace="Investigation and promotion start from an alert and window selected in M1.")

sc = specs["source-capabilities"]
edit("source-capabilities",
    title="Describe usable source routes, bounded selection and D1 schedule configuration",
    scope=sc["scope"] + " Own the D1 configuration screen: at most ten keywords, activation as a recorded command, the shared day allowance, route health and selection basis. Describe the oEmbed and tiktok-web adapters as existing for supplied references but not task-integrated.",
    config="Provider/account, quotas, field support, rates and source-use authorization come from the {{live-feasibility-probes}} rows and the final {{provider-readiness}} record. No commercial price or readiness is assumed.",
    checks=sc["checks"] + ["An eleventh scheduled keyword is refused, the daily cap and occurrence authority are shown truthfully, and configuration edits never alter an existing occurrence's scope."],
    size="M", milestone="M3", ui_bearing=True)
deps("source-capabilities",
    workspace_and_evidence="D1 and capability screens use the shell and inspector.",
    pilot_configuration="The readiness read extends the configuration's source-free readiness.")

e = specs["engagement-anomalies"]
edit("engagement-anomalies",
    scope=e["scope"] + " Consume metrics_retrieved_at from {{monitoring-depth-and-timing}} only under an accepted W02; without it, live X engagement reports measurement_time_unknown as unassessable, which is honest but leaves live engagement fixture-only in the pilot. Chart integration with {{monitoring-history}} is a conditional check.",
    decision_blockers=["W02"], size="M", milestone="M3")
deps("engagement-anomalies",
    monitoring_depth_and_timing="Matched-age comparison consumes the recorded metrics_retrieved_at and saturation fields.",
    source_capabilities="Metric capability per route comes from the registry.")

sh = specs["semantic-shift"]
sh_packet_check = sh["checks"][3]
edit("semantic-shift",
    integration="Runtime registers exact-window/method assessment. M1 shows provisional codes, ambiguous/unresolved cases, language mix, both samples and missing baseline. Chart rendering in {{monitoring-history}} and source-free alert delivery in {{inbox-email}} are conditional checks once those specs exist.",
    checks=sh["checks"][:3], size="L", milestone="M3")
deps("semantic-shift", stable_verification_clock="Extends the installed semantic owner whose suites must be green; chart and alert integration are conditional checks.")

new("interaction-checkpoint",
    title="Check graph and history-chart interaction in a real browser",
    lane="human-validation", size="S", milestone="M3",
    owners="A named human tester, supported by the graph client and monitoring chart maintainers",
    evidence=[".scratch/product-design-2026-11/task3/r2/review-guide.md", ".scratch/product-design-2026-11/ui-review-status.md", "docs/evaluation.md"],
    outcome="The two client behaviors agents cannot verify while browser access stays declined are checked by a human on the implemented build.",
    scope="A human executes the {{interactive-graph}} and {{monitoring-history}} checklists: drag/pin, overlapping branches, stale-page discard, keyboard/list equivalence, reduced motion, chart latest/selected/gap behavior and narrow CJK layouts.",
    interface="Record build identity, browser and platform, and each checklist item as pass/fail with evidence under the quality owner's attributable review contract.",
    migration="No production schema change beyond quality-owner records. Update docs/evaluation.md with the actual outcome.",
    integration="Failures are filed against their owning spec. Results feed {{human-pilot-acceptance}} at the same build identity.",
    authority="Agent source checks and Node tests are not this checkpoint. A model cannot be the human tester.",
    recovery="A failed item keeps its evidence and owner; fixes re-run the affected items at the new build identity.",
    checks=["The build identity and each checklist item are recorded as pass/fail with evidence.",
            "Each failure is filed against its owning spec.",
            "Accessibility observations are recorded separately from functional results."],
    config="Requires a named human tester with permitted browser use. Agent browser access remains declined unless the user changes U5.")
deps("interaction-checkpoint",
    interactive_graph="Graph drag/pin/branch/stale-page behavior under test.",
    monitoring_history="Chart latest/selected/gap behavior under test.")

# ---------------------------------------------------------------- milestone M4: spending, acquisition, notifications, planning

edit("spending-operations", size="M", milestone="M4", ui_bearing=True)
deps("spending-operations", workspace_and_evidence="S1 forms render in the shell with governed reads.")

pa = specs["progressive-acquisition"]
edit("progressive-acquisition",
    title="Plan finite field-capability acquisition steps and stop honestly",
    outcome="A task plans finite broad-plus-detail steps over declared route capability, reuses eligible evidence and stops with a visible reason.",
    scope="Generalize the installed one-nickname fill into an AcquisitionPlan/step model with value-based stopping and cross-route avoidance over the existing keyword and nickname routes. The successor-approval path uses installed proposal operations; A1 UI linkage is a conditional check. A new supplementary route is {{supplementary-detail-route}}.",
    checks=["Run a broad-plus-detail task over the keyword and nickname routes through public worker operations and inspect exact step scope, decision support, one supplementary observation and final publication."] + pa["checks"][1:],
    size="L", milestone="M4")
deps("progressive-acquisition", source_capabilities="Steps are planned only over declared route/field capability and selection policy.")

new("supplementary-detail-route",
    title="Task-integrate one named supplementary detail route",
    lane="pilot-build", size="M", milestone="M4",
    owners="smi_ingestion adapters own the route and evidence; smi_tasks plan steps own execution",
    evidence=["src/smi_ingestion/adapters/bright_data.py", "src/smi_ingestion/adapters/registry.py", "src/smi_tasks/supplementation/policy.py"],
    outcome="A plan step can collect one named kind of supplementary detail evidence for an approved subject within finite cost and request bounds.",
    scope="Task-integrate one named route. The default is Bright Data profile/post detail fields (follower count, post metrics, post history window), with exact fields fixed by the Bright Data row of {{live-feasibility-probes}}. tiktok-web only if the user grants source use (U4); oEmbed is limited to identity and title. Non-goal: a multi-provider route catalog.",
    interface="Proposed capability entry with exact field/subject/billing and allowed parent scope, registered in the {{source-capabilities}} registry, executed as an AcquisitionPlan step with request/record/byte/charge bounds.",
    migration="Add route-specific evidence fields only with explicit legacy-unrecorded migration. Update source integrations, costs and adapter instructions.",
    integration="The pipeline renders the detail step, its field support and stop reason. New support follows ingestion/publication before any answer or ranking.",
    authority="Each step stays inside the approved parent scope and independent spending/novelty admission. Namespaces from this route stay separate from keyword captures.",
    recovery="Pending, ambiguous or failed responses are never blindly retried. An unsupported field is explicitly unavailable.",
    checks=["A broad-plus-detail task records one supplementary observation per step within cost and request bounds.",
            "Pending, ambiguous or failed responses are never blindly retried.",
            "Namespaces stay separate from keyword captures and no capture age is refreshed by matching.",
            "An unsupported field is explicitly unavailable."],
    config="Live use requires the Bright Data probe row and the final readiness record; U4 for any web route.")
deps("supplementary-detail-route", progressive_acquisition="The route executes as plan steps under the plan model's scope and stop rules.")

ie = specs["inbox-email"]
edit("inbox-email",
    scope="Implement inbox composition/read-unread, the single configured recipient and sender, durable email attempts, bounded retries and visible final/uncertain failure. Email is required for the first pilot. Multi-recipient preferences are later ({{hosted-actors-tenancy}}). Provider credentials and actual sending are authorized readiness work.",
    checks=[x.replace("per configured recipient/channel", "for the configured recipient and each channel") for x in ie["checks"]],
    size="L", milestone="M4", ui_bearing=True)
deps("inbox-email",
    local_runtime="Delivery.run_due is registered as a runtime component.",
    pilot_configuration="Recipient, sender, link and transport configuration come from the validated configuration.",
    workspace_and_evidence="The inbox renders in the shell with governed links.")

pq = specs["plans-and-quality"]
edit("plans-and-quality",
    title="Preserve measurement planning and prepare attributable KR/JP quality packets",
    checks=pq["checks"] + [sh_packet_check],
    size="M", milestone="M4", ui_bearing=True)
deps("plans-and-quality", campaign_decisions="Plans and notes bind to exact brief/shortlist revisions produced by C1.")

# ---------------------------------------------------------------- milestone M5: release records

pr = specs["provider-readiness"]
edit("provider-readiness",
    title="Record actual per-capability provider, billing, recurrence and send readiness",
    scope="The final signed-off record per capability, reusing the {{live-feasibility-probes}} authorizations and record format. Each row can be completed when its own capability spec is done; no row waits on unrelated build work. Validate each required route/model/method/notification separately. No prices or readiness are inferred from test fixtures.",
    checks=pr["checks"] + ["Each readiness row links its {{live-feasibility-probes}} row and states what changed since the probe."],
    size="M", milestone="M5")
deps("provider-readiness",
    live_feasibility_probes="Reuses the probe authorizations and findings.",
    local_runtime="The recurring-work row needs the runtime.",
    engagement_anomalies="The X engagement row.",
    semantic_shift="The semantic model row.",
    spending_operations="The billing reconciliation row needs operator controls.",
    supplementary_detail_route="The supplementary route row.",
    inbox_email="The email send row.")

hp = specs["human-pilot-acceptance"]
edit("human-pilot-acceptance",
    title="Record pilot release acceptance on live data",
    scope="The release record that incorporates {{early-marketer-checkpoint}} and {{interaction-checkpoint}} results and covers the remaining journeys: approved research to later question, alert to KB context, spending, inbox/email and lineage, plus KR/JP adjudication on live data. Include empty/partial/stale/conflict/withdrawn/meter/unknown-response states, accessibility and narrow CJK layouts. Keep failures and reviewer disagreement visible.",
    checks=["Record actual browser runs for r2 review scenarios not already passed in {{interaction-checkpoint}} at the same build identity, or re-run them if the build changed."] + hp["checks"][1:],
    size="M", milestone="M5")
deps("human-pilot-acceptance",
    exact_approval_tools="The approved-research to later-question journey.",
    early_marketer_checkpoint="Incorporates H1 findings and fixes.",
    alert_investigation_promotion="The alert to KB-context journey.",
    interaction_checkpoint="Incorporates H2 findings and fixes.",
    plans_and_quality="KR/JP adjudication packets.",
    provider_readiness="Usefulness must be judged on live, ready capabilities.")

# ---------------------------------------------------------------- later lanes

edit("evaluated-retrieval",
    scope=specs["evaluated-retrieval"]["scope"] + " Compare against the deterministic {{pilot-scale-retrieval}} baseline.",
    size="L", milestone="Later")
deps("evaluated-retrieval",
    pilot_scale_retrieval="The deterministic baseline to beat.",
    plans_and_quality="Held-out bilingual evaluation packets.")
edit("agent-candidate", size="L", milestone="Later",
    config="Informing, non-blocking prerequisite: W01 initial direction (U6). Recommended 'yes' branches are non-binding working assumptions until answered.")
deps("agent-candidate",
    exact_approval_tools="Draft research compiles to exact proposal/approval operations and tools.",
    conversations="Candidate turns live in conversation records.")
edit("agent-human-evidence", size="M", milestone="Later")
deps("agent-human-evidence", agent_candidate="Adjudicates the candidate's outputs.")
edit("enable-richer-agent", size="L", milestone="Later")
deps("enable-richer-agent", agent_human_evidence="Acceptance needs actual adjudication evidence.")
edit("hosted-actors-tenancy",
    scope=specs["hosted-actors-tenancy"]["scope"] + " Add multi-recipient notification preferences here, beyond the pilot's single configured recipient.",
    size="L", milestone="Later")
deps("hosted-actors-tenancy", human_pilot_acceptance="Hosting follows an accepted local pilot.")
edit("projection-governance", size="L", milestone="Later")
deps("projection-governance",
    evaluated_retrieval="Governs the retrieval index and projections it introduces.",
    hosted_actors_tenancy="Managed storage, secrets and restore are hosted concerns.")
edit("multimodal-ontology", size="L", milestone="Later")
deps("multimodal-ontology",
    evaluated_retrieval="New concepts need evaluated retrieval.",
    projection_governance="Retained copies must already reconcile.")
edit("objective-portfolios", size="L", milestone="Later")
deps("objective-portfolios",
    evaluated_retrieval="Factor retrieval depth.",
    multimodal_ontology="Richer creator concepts.")
edit("outcomes-attribution", size="L", milestone="Later")
deps("outcomes-attribution",
    plans_and_quality="Proposed measurement plans to observe against.",
    hosted_actors_tenancy="Outcome data needs tenant access.",
    projection_governance="Governed retention of outcome copies.")
edit("causal-measurement", size="L", milestone="Later")
deps("causal-measurement", outcomes_attribution="Needs observed outcomes and attribution.")

# ---------------------------------------------------------------- order, decisions, coverage

src["order"] = [
    "stable-verification-clock", "pilot-configuration", "client-foundation", "live-feasibility-probes",
    "automated-interpretation", "pilot-scale-retrieval", "local-runtime", "workspace-and-evidence",
    "campaign-decisions", "task-events-lineage", "exact-approval-tools", "conversations",
    "early-marketer-checkpoint", "graph-reads", "interactive-graph", "monitoring-depth-and-timing",
    "monitoring-workspace", "monitoring-history", "alert-investigation-promotion", "source-capabilities",
    "engagement-anomalies", "semantic-shift", "interaction-checkpoint", "spending-operations",
    "progressive-acquisition", "supplementary-detail-route", "inbox-email", "plans-and-quality",
    "provider-readiness", "human-pilot-acceptance", "evaluated-retrieval", "agent-candidate",
    "agent-human-evidence", "enable-richer-agent", "hosted-actors-tenancy", "projection-governance",
    "multimodal-ontology", "objective-portfolios", "outcomes-attribution", "causal-measurement"]
assert sorted(src["order"]) == sorted(specs), set(specs) ^ set(src["order"])

src["decisions"] = {
    "W01": {"title": "Set the richer research and synthesis boundary", "file": "../wayfinder/issues/001-richer-agent-boundary.md"},
    "W02": {"title": "Decide live X metric measurement-time semantics", "file": "../wayfinder/issues/002-x-metric-measurement-time.md"},
}
src["user_decisions"] = [
    {"id": "U1", "decision": "Grant bounded live authorization and credentials early for the probes: model, Bright Data keyword, X recent and the email provider's semantics, with per-capability call counts and a spending ceiling.", "default": "Request at plan start with the smallest useful caps. If not granted, the probes stay blocked, the build continues on fixtures and premise-dependent specs stay provisional.", "affects": ["live-feasibility-probes", "early-marketer-checkpoint", "provider-readiness"]},
    {"id": "W02", "decision": "May a successful X response's receipt time serve as the metric measurement time (an upper bound, with configured tolerance) for matched-age engagement?", "default": "Accept as a narrowly scoped ADR amendment labelled metrics_retrieved_at, never a capture time, validated against the X probe row. If rejected, live engagement is reported as unassessable.", "affects": ["engagement-anomalies"]},
    {"id": "U3", "decision": "Allow more than one X page per window (a successor to ADR 0023 with more recurring paid authority)?", "default": "No at pilot start. Use cadence and saturation reporting, and revisit with X probe data.", "affects": ["monitoring-depth-and-timing", "provider-readiness"]},
    {"id": "U4", "decision": "Which supplementary detail route, and is tiktok-web source use permitted?", "default": "Bright Data profile/post detail fields; tiktok-web stays unavailable.", "affects": ["supplementary-detail-route"]},
    {"id": "U5", "decision": "Permit scoped headless-browser tests against the loopback app in CI or by agents (currently declined)?", "default": "Keep declining. Rely on Node state tests plus the human checkpoints.", "affects": ["client-foundation", "interactive-graph", "monitoring-history", "interaction-checkpoint"]},
    {"id": "U6", "decision": "W01 initial direction: agent-drafted scope for human approval, and validated fluent synthesis.", "default": "Proceed with the disabled candidate under the recommended 'yes' branches as non-binding working assumptions; enabling stays decision-blocked.", "affects": ["agent-candidate", "enable-richer-agent"]},
    {"id": "U7", "decision": "Pilot email goes to one configured recipient, with multi-recipient preferences later.", "default": "Yes.", "affects": ["inbox-email", "hosted-actors-tenancy"]},
]

A = src["assignments"]


def add(ids, slug):
    for i in ids:
        if slug not in A[i]:
            A[i].append(slug)


def drop(ids, slug):
    for i in ids:
        A[i] = [s for s in A[i] if s != slug]


add(["OFR-E03", "UD-02", "PROP-34"], "pilot-configuration")
add(["UD-03", "UD-07", "PROP-03", "OFR-E02", "PROP-15"], "client-foundation")
drop(["UD-07", "PROP-03"], "workspace-and-evidence")
add(["FR-C01", "FR-P04", "FR-P09", "FR-S01", "OFR-S03", "PROP-23", "PROP-28", "UD-05"], "live-feasibility-probes")
add(["FR-A02", "FR-A03", "FR-G02", "PROP-17"], "automated-interpretation")
add(["FR-A02", "FR-B01", "FR-B02", "FR-G01", "PROP-32", "PROP-35"], "pilot-scale-retrieval")
add(["FR-A01", "FR-B01", "OFR-E01", "UD-01", "UD-03", "PROP-16"], "early-marketer-checkpoint")
add(["FR-C01", "FR-C02", "FR-P09", "OFR-C01", "R2-STREAM"], "monitoring-depth-and-timing")
m2 = ["FR-C04", "FR-C07", "PROP-04", "PROP-07", "UD-08"]
drop(m2, "monitoring-workspace")
add(m2, "alert-investigation-promotion")
add(["FR-P01", "FR-P02"], "source-capabilities")
add(["UD-06", "UD-07", "R2-GRAPH", "R2-STREAM", "FR-G01"], "interaction-checkpoint")
drop(["FR-P04"], "progressive-acquisition")
add(["FR-P04", "FR-P06", "PROP-23"], "supplementary-detail-route")
add(["PROP-16", "OFR-E01"], "plans-and-quality")
for key, slugs in A.items():
    assert slugs or key == "UD-09", key

SOURCE.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n")
print("applied round 1:", len(specs), "specs,", sum(len(s["dependencies"]) for s in specs.values()), "edges")
