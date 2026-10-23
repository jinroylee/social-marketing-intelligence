"""Escaped server-rendered forms and source-health-aware evidence panels."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from html import escape
from urllib.parse import quote, urlsplit


KINDS = {"product_mention": "Product mention", "brand_mention": "Brand mention", "topic_mention": "Topic wording",
         "script_evidence": "Script evidence", "literal_marker": "Literal marker", "caption_language": "Caption language",
         "audience_geography": "Audience geography", "fee": "Fee", "availability": "Availability", "sales": "Sales",
         "recent_history": "Recent history", "custom": "Other criterion"}
ERRORS = {
    "scope_version_conflict": "This investigation scope changed. Reopen it and prepare an answer for the current question.",
    "insight_version_conflict": "Another insight revision was saved. Reopen the investigation before preparing a successor.",
    "measurement_plan_version_conflict": "Another plan revision was saved. Your edits remain below; reopen the current history before saving again.",
    "decision_note_version_conflict": "Another decision note was recorded. Your edits remain below; reopen current history before appending a new note.",
    "decision_note_support_unavailable": "The pinned shortlist support is unavailable or requires review. Source-dependent note text is withheld.",
    "planning_reference_mismatch": "Choose a shortlist from this campaign and, for plans, the current brief.",
    "measurement_plan_requires_gaps": "Record known missing measurement prerequisites; outcome access has not been verified.",
    "brief_version_conflict": "The brief changed while this page was open. Open the current campaign and prepare a comparison for the new brief.",
    "shortlist_version_conflict": "Another shortlist revision was saved while this page was open. Your edits remain below. Reopen the latest revision before saving again.",
    "shortlist_request_conflict": "This request was already used for a different save. Open the latest revision to begin another edit.",
    "campaign_regeneration_unavailable": "This completion has no currently usable published support. Reopen its task outcome or current campaign context before requesting another assessment.",
    "campaign_regeneration_request_conflict": "This request already belongs to different context or actors. Reopen the saved action, or reload current context for a new request.",
    "campaign_request_conflict": "This request was already used for a different brief. Open the campaign or start a new form.",
    "selection_reason_or_support_unavailable": "Each confirmed account needs an inclusion reason and currently available evidence.",
    "selection_requires_relevance_support": "Cite at least one positive relevance interpretation for every confirmed account.",
    "selection_unknowns_not_acknowledged": "Acknowledge every listed unknown for each selected account before confirming.",
    "selection_requirement_not_met": "A selected account contradicts a required exclusion, or a required unknown is set to defer.",
    "selection_support_not_permitted": "Source support no longer permits this decision. Review the current evidence before saving.",
    "invalid_selection_support": "Some cited evidence no longer belongs to an available candidate. Review the source panels.",
    "invalid_selection_unknowns": "Acknowledge only the unknowns listed for the available comparison candidate.",
    "comparison_support_changed": "Source support changed during preparation. Review the current dataset and try a new preparation.",
    "human_review_acknowledgement_required": "Confirm that this is your reviewed selection, or save an unconfirmed draft.",
    "invalid_brief.known_account": "Enter each known account as platform, namespace and native ID, separated by spaces.",
    "invalid_brief_window": "Use a full publication timestamp with a timezone, such as 2026-01-01T00:00:00+00:00.",
    "brief_window_requires_timezone": "Publication timestamps need an explicit timezone.",
    "database_unavailable": "The local database is unavailable or needs setup. Start PostgreSQL and run smi-ingest migrate, then reload.",
    "invalid_form": "The submitted form is invalid. Check the fields below or reopen the page.",
}


def e(value) -> str:
    return escape(str(value), quote=True)


def hidden(name, value) -> str:
    return f'<input type="hidden" name="{e(name)}" value="{e(value)}">'


def value(form, name, default=""):
    return form.get(name, [default])[0] if form else default


def selected(value, expected) -> str:
    return " selected" if value == expected else ""


def checked(condition) -> str:
    return " checked" if condition else ""


def options(items, current) -> str:
    return "".join(f'<option value="{e(key)}"{selected(key, current)}>{e(label)}</option>' for key, label in items)


def page(title, content, actor_id) -> str:
    """Render the common shell without inline executable code or external resources."""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Social Marketing Intelligence</title><link rel="stylesheet" href="/static/review.css"><script defer src="/static/review.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a><header><a class="wordmark" href="/">SMI<span>Social Marketing Intelligence</span></a>
<nav aria-label="Main"><a href="/">Campaigns</a><a href="/investigations">Investigations</a><a href="/knowledge/search">Knowledge search</a><a href="/knowledge/publications">Knowledge</a><a href="/proposals">Proposals</a><a href="/tasks">Tasks</a><a href="/schedules">Keyword schedule</a><a href="/inbox">Inbox</a><a href="/costs">Costs</a></nav><div class="operator">Local workspace<br><strong>Reviewer: {e(actor_id)}</strong></div></header>
<main id="main">{content}</main><footer>Evidence supports internal planning. Caption interpretations and original-language nuance remain provisional.</footer></body></html>'''


def request_error(message: str, local_url: str) -> str:
    """Render HTTP rejection recovery using the trusted server URL, never request headers."""
    return f'''<section class="panel"><h1>{e(message)}</h1>
<p>This request was not saved. Open the local workspace or a fresh brief form before trying again.</p>
<div class="actions"><a class="button" href="{e(local_url)}/">Open campaign workspace</a>
<a class="button secondary" href="{e(local_url)}/campaigns/new">Create a brief</a></div></section>'''


def error_message(code) -> str:
    message = ERRORS.get(code)
    if message is None:
        if code.endswith("not_found"):
            message = "This record or reference was not found."
        elif code.startswith(("invalid_brief.", "invalid_investigation.", "invalid_measurement_plan.")):
            message = "Check the required field: " + code.split(".", 1)[1].replace("_", " ")
        else:
            message = "The action could not be completed. Review the current inputs and try again."
    return f'<div class="notice error" role="alert"><strong>Action needs attention</strong><p>{e(message)}</p><small>{e(code)}</small></div><p><a href="/">Open campaign workspace</a></p>'


def empty_inputs() -> str:
    return '''<p class="eyebrow">Local setup</p><h1>Load your evidence first</h1><p class="lede">A registered product catalog and frozen dataset provide the inputs for a campaign comparison.</p>
<section class="panel"><h2>Offline sample setup</h2><pre>uv run smi-ingest migrate
uv run smi-ingest import-snapshot examples/curated/jp-kbeauty-tiktok-2026-10-05/snapshot-manifest.json
uv run smi-ingest register-catalog examples/catalogs/beauty-v1.json</pre><p>Reload this workspace after setup. Preparation uses the loaded captions without source or model calls.</p></section>'''


def home(campaigns, datasets, catalogs) -> str:
    content = '<div class="heading"><div><p class="eyebrow">Campaign decisions</p><h1>Evidence into a considered shortlist.</h1><p class="lede">Set the question, inspect the source support, and save your decision with its unknowns.</p></div><a class="button" href="/campaigns/new">Create a brief</a></div>'
    if not catalogs or not datasets:
        content += empty_inputs()
    cards = ""
    for campaign in campaigns:
        cards += f'''<a class="campaign-card" href="/campaigns/{e(campaign['campaign_id'])}"><span class="badge">{e(campaign['target_market'])}</span>
<h3>{e(campaign['objective'])}</h3><p>{e(campaign['brand_id'])} · Brief {campaign['brief_version']} · {campaign['shortlist_version']} saved shortlist revisions</p>
<small>Created by {e(campaign['owner_id'])} · {e(campaign['created_at'])}</small></a>'''
    content += f'<section><h2>Your campaigns <span class="count">{len(campaigns)}</span></h2><div class="campaign-grid">{cards or "<p>No campaigns yet. Start with a brief.</p>"}</div></section>'
    content += '<section class="panel"><h2>Loaded evidence</h2><p>Fixed selected observations; this coverage does not establish complete account histories or market representativeness.</p>'
    for dataset in datasets:
        content += f'<p><strong>{e(dataset["dataset_id"])}</strong><br>{dataset["posts"]} posts · {dataset["accounts"]} accounts · policy rechecked when used</p>'
    return content + '</section>'


def criterion_row(index, criterion=None, submitted=None) -> str:
    criterion = criterion or {"id": f"criterion-{index}", "label": "", "kind": "custom", "value": "", "required": True, "operator": "include", "unknown_handling": "acknowledge"}
    prefix = f"criterion_{index}_"
    get = lambda key: value(submitted, prefix + key, criterion.get(key) or "")
    required = prefix + "required" in submitted if submitted is not None else criterion["required"]
    return f'''<div class="criterion-row">{hidden(prefix + "id", get("id"))}<div class="row-title"><strong>Selection criterion</strong><button class="text-button" type="button" data-remove-criterion>Remove</button></div>
<div class="form-grid"><label>Criterion label<input name="{prefix}label" value="{e(get('label'))}" required placeholder="Product content worth investigating"></label>
<label>Evidence type<select name="{prefix}kind">{options(KINDS.items(), get('kind'))}</select></label>
<label>Expected reference or value<input name="{prefix}value" value="{e(get('value'))}" list="catalog-values" placeholder="Choose a catalog reference, or state a need"></label>
<label>Rule<select name="{prefix}operator">{options([('include','Include matching evidence'),('exclude','Exclude matching evidence')], get('operator'))}</select></label>
<label>When unknown<select name="{prefix}unknown_handling">{options([('acknowledge','Allow with acknowledgement'),('defer','Defer until supported')], get('unknown_handling'))}</select></label>
<label class="check"><input type="checkbox" name="{prefix}required" value="yes"{checked(required)}>Required criterion</label></div></div>'''


def brief_form(catalog, catalogs, csrf, campaign=None, current=None, submitted=None, error=None) -> str:
    first_brand = catalog["brands"][0]["id"]
    first_product = next((p["id"] for p in catalog["products"] if p["brand_id"] == first_brand), "")
    document = current["document"] if current else {"brand_id": first_brand, "product_ids": [first_product] if first_product else [],
        "objective": "", "target_market": "", "platforms": ["tiktok"], "known_accounts": [], "context": {},
        "criteria": [{"id": "relevance", "label": "Relevant product mention" if first_product else "Relevant brand mention",
                      "kind": "product_mention" if first_product else "brand_mention", "value": first_product or first_brand,
                      "required": True, "operator": "include", "unknown_handling": "acknowledge"}]}
    get = lambda key, default="": value(submitted, key, document.get(key) or default)
    content = '<p class="eyebrow">1 / Define the question</p><h1>' + ('Revise your brief' if campaign else 'Create a campaign brief') + '</h1><p class="lede">Choose what matters for this decision. Dates and commercial details can remain unknown.</p>'
    if not campaign:
        content += f'<form method="get" action="/campaigns/new" class="catalog-switch"><label>Reference catalog<select name="catalog_id">{options([(c["catalog_id"],c["catalog_id"]) for c in catalogs], catalog["catalog_id"])}</select></label><button type="submit" class="secondary">Use catalog</button></form>'
    if error:
        content += error_message(error)
    action = f'/campaigns/{campaign["campaign_id"]}/briefs' if campaign else '/campaigns'
    content += f'<form method="post" action="{e(action)}" id="brief-form">{hidden("csrf",csrf)}{hidden("request_id",value(submitted,"request_id",str(uuid.uuid4())))}{hidden("catalog_id",catalog["catalog_id"])}'
    if campaign:
        content += hidden("expected_version", value(submitted, "expected_version", campaign["brief_version"]))
    content += f'<section class="panel"><h2>Original marketer input</h2><label>Campaign needs in your own words<textarea name="original_input" rows="3">{e(get("original_input"))}</textarea></label><p>Saved alongside your structured choices. This text is human context; no language model interprets it. The structured fields below determine the installed caption comparison.</p></section>'
    content += f'<section class="panel"><h2>Campaign scope</h2><div class="form-grid"><label>Brand<select name="brand_id" id="brand">{options([(b["id"],b["name"]) for b in catalog["brands"]],get("brand_id"))}</select></label><label>Target market<input name="target_market" value="{e(get("target_market"))}" placeholder="JP" required></label></div><fieldset><legend>Products <span class="muted">Optional for a brand-level brief</span></legend><div class="choice-grid">'
    chosen_products = submitted.get("product_ids", []) if submitted is not None else document["product_ids"]
    for product in catalog["products"]:
        content += f'<label class="check product-choice" data-brand="{e(product["brand_id"])}"><input type="checkbox" name="product_ids" value="{e(product["id"])}"{checked(product["id"] in chosen_products)}>{e(product["name"])} <small>{e(product["specificity"])}</small></label>'
    content += f'</div></fieldset><label>Objective<textarea name="objective" required rows="2" placeholder="What will this campaign decision help you investigate?">{e(get("objective"))}</textarea></label><label>Platforms<input name="platforms" value="{e(value(submitted,"platforms",", ".join(document["platforms"])))}" required placeholder="tiktok, instagram"></label></section>'
    criteria = document["criteria"]
    try:
        count = min(30, max(1, int(value(submitted, "criterion_count", len(criteria)))))
    except ValueError:
        count = len(criteria)
    content += '<section class="panel"><h2>Visible selection criteria</h2><p>Literal matches support mentions only. Language, audience, sales, fees and availability remain unknown under this caption method.</p>'
    content += hidden("criterion_count", count) + '<div id="criteria">'
    content += "".join(criterion_row(i, criteria[i] if i < len(criteria) else None, submitted) for i in range(count))
    references = [(b["id"], b["name"]) for b in catalog["brands"]] + [(p["id"], p["name"]) for p in catalog["products"]] + [(t["id"], t["name"]) for t in catalog["topics"]] + [("kana", "Kana script"), ("pr_marker", "Literal PR marker"), ("qoo10_reference", "Qoo10 reference")]
    content += '</div><button type="button" class="secondary" id="add-criterion">Add criterion</button><datalist id="catalog-values">' + "".join(f'<option value="{e(key)}">{e(label)}</option>' for key, label in references) + '</datalist></section>'
    content += '<template id="criterion-template">' + criterion_row("__index__") + '</template>'
    known = "\n".join(f'{a["platform"]} {a["namespace"]} {a["native_id"]}' for a in document["known_accounts"])
    content += f'<details class="panel"><summary>Known accounts and optional context</summary><label>Marketer-known accounts<textarea name="known_accounts" rows="3" placeholder="tiktok web:public 6819904612390634498">{e(value(submitted,"known_accounts",known))}</textarea><small>One platform, namespace and native account ID per line. Handles do not establish identity.</small></label><div class="form-grid">'
    for key, label in [("campaign_dates","Campaign dates"),("budget","Budget"),("currency","Currency"),("audience_detail","Audience needs")]:
        content += f'<label>{label}<input name="{key}" value="{e(value(submitted,key,document["context"].get(key) or ""))}" placeholder="Unknown"></label>'
    for key, label in [("publication_from","Posts published from"),("publication_to","Posts published through")]:
        content += f'<label>{label}<input name="{key}" value="{e(get(key))}" placeholder="2026-01-01T00:00:00+00:00"></label>'
    content += '</div><p>Publication filters use timezone-aware timestamps. An empty result describes this dataset only.</p></details><div class="actions"><button type="submit">'
    content += 'Save brief revision' if campaign else 'Create campaign'
    return content + '</button><a href="/">Back to campaigns</a></div></form>'


def brief_summary(brief) -> str:
    document = brief["document"]
    content = f'<section class="panel"><div class="row-title"><h2>Brief {brief["version"]}</h2><span class="badge">Human input</span></div><p class="lede">{e(document["objective"])}</p><dl class="facts"><div><dt>Brand / products</dt><dd>{e(document["brand_id"])} / {e(", ".join(document["product_ids"]) or "Brand-level scope")}</dd></div><div><dt>Target market</dt><dd>{e(document["target_market"])}</dd></div><div><dt>Platforms</dt><dd>{e(", ".join(document["platforms"]))}</dd></div></dl><ul>'
    for criterion in document["criteria"]:
        content += f'<li>{e(criterion["label"])} · {e(KINDS[criterion["kind"]])} · {e(criterion["value"] or "Unspecified value")} · {"required" if criterion["required"] else "preference"} · {e(criterion["operator"])} · unknown: {e(criterion["unknown_handling"])}</li>'
    content += f'</ul><h3>Original marketer input</h3><p class="preserve">{e(document.get("original_input") or "No separate prose input recorded; structured fields above are the original input.")}</p>'
    content += profile_summary(brief.get("executable_profile"))
    return content + f'<small>Recorded by {e(brief["recorded_by"])} · {e(brief["recorded_at"])}</small><details><summary>Exact brief reference and optional context</summary><p>Brief ID: {e(brief["id"])}</p><p>Catalog: {e(document["catalog_id"])}</p><p>{e(document["context"])}</p><p>Publication window: {e(document.get("publication_from") or "Open")} → {e(document.get("publication_to") or "Open")}</p></details></section>'


def profile_summary(profile) -> str:
    """Show the saved executable snapshot; never reconstruct a legacy profile."""
    content = '<h3>Saved executable profile</h3>'
    if profile is None:
        return content + '<p>No executable profile was recorded for this historical brief. Save a successor brief to record the installed structured profile.</p>'
    content += f'<p>Brief {e(profile["brief_version"])} · {e(profile["brief_id"])}<br>Basis: {e(profile["basis"])} · {e(profile["criteria_profile_version"])}<br>Caption method: {e(profile["comparison_method_version"])}</p><ul>'
    for criterion in profile["criteria"]:
        content += f'<li>{e(criterion.get("basis", "human_structured_input"))} · {e(criterion["id"])}: {e(criterion["label"])} · {e(criterion["kind"])} = {e(criterion["value"] or "Unspecified")} · {e(criterion["importance"])} · {e(criterion["operator"])} · unknown: {e(criterion["unknown_handling"])}</li>'
    ranking, coverage = profile["ranking_profile"], profile["coverage_profile"]
    return content + f'</ul><p>Ranking profile: {e(ranking["version"])} · {e(ranking["status"])}<br>Order: {e(ranking["ordering"])}</p><p>Coverage profile: {e(coverage["version"])} · {e(coverage["status"])}<br>Scope: {e(coverage["scope"])} · sufficiency assessment: {e(coverage["sufficiency_assessment"])}</p><p>Baseline unknowns: {e(", ".join(profile["baseline_unknowns"]))}. Structured needs and labels do not establish source facts.</p>'


def campaign_page(campaign, current, datasets, csrf, *, model_configured=False, model_mode=None, submitted=None, error=None) -> str:
    content = f'<div class="heading"><div><p class="eyebrow">Campaign workspace</p><h1>{e(current["document"]["objective"])}</h1><p>Created by {e(campaign["owner_id"])} · {e(campaign["created_at"])}</p></div><a class="button secondary" href="/campaigns/{e(campaign["campaign_id"])}/edit">Revise brief</a></div>' + brief_summary(current)
    content += f'<p><a href="/campaigns/{e(campaign["campaign_id"])}/planning">Measurement plans and decision notes →</a></p>'
    content += '<section class="panel"><h2>Interpret natural-language criteria</h2>'
    if model_configured:
        content += ('<p>Explicitly enabled OpenAI Responses provider route. Usage is valued at configured rates; final invoices and account readiness are separate.</p>' if model_mode == 'provider' else
                    '<p>Configured simulated OpenAI Responses route. No live model execution or commercial charge.</p>')
    else:
        content += '<p>Model route unavailable: explicit server model, credential, rate classification, verified bounds and enablement are required.</p>'
    if error:
        content += error_message(error)
    retry = lambda key, default: submitted.get(key, [default])[0] if submitted else default
    content += f'<form method="post" action="/campaigns/{e(campaign["campaign_id"])}/interpretations">{hidden("csrf",csrf)}{hidden("request_id",retry("request_id",str(uuid.uuid4())))}{hidden("brief_id",retry("brief_id",current["id"]))}{hidden("expected_version",retry("expected_version",current["version"]))}<p>Interpret the saved original prose for this exact brief. Structured human constraints are retained. Inspect the result below before selecting it for comparison.</p><button type="submit">Interpret saved prose</button></form>'
    for interpretation in campaign.get('interpretations', []):
        content += f'<article><h3>Model-generated interpretation · {e(interpretation["status"])}</h3><p>{e(interpretation["interpretation_id"])} · Brief {e(interpretation["brief_version"])} / {e(interpretation["brief_id"])}<br>Requested by {e(interpretation["requested_by"])} · Generated by automation<br>{e(interpretation["reason"] or "Validated generated data; not verified source facts.")}</p>'
        configuration = interpretation['configuration']
        if configuration:
            content += f'<p>Model: {e(configuration["model"])} / {e(configuration["model_version"])}<br>Method: {e(configuration["method_version"])} · schema: {e(configuration["schema_version"])} · {e(configuration["execution"])}</p>'
        if interpretation['executable_profile']:
            content += profile_summary(interpretation['executable_profile'])
        if interpretation['operation_id']:
            content += f'<p><a href="/costs/{e(interpretation["operation_id"])}">Attributable usage and cost</a></p>'
        if interpretation['usage']:
            basis = 'Provider-reported usage' if configuration and configuration['execution'] == 'provider_enabled' else 'Simulated provider usage'
            content += f'<p>{basis} (includes nonvisible generated tokens): {e(interpretation["usage"])}</p>'
        if interpretation['status'] == 'in_progress':
            content += '<p>In flight or interrupted with unknown outcome. This request will not dispatch again.</p>'
        content += '</article>'
    content += '</section>'
    profiles = [('', 'Human structured profile')] + [(i['interpretation_id'], f"Model interpretation {i['interpretation_id']}")
                 for i in campaign.get('interpretations', []) if i['status'] == 'succeeded' and i['brief_id'] == current['id']]
    profile_select = f'<label>Executable profile<select name="interpretation_id">{options(profiles, "")}</select></label>'
    selected_profile = value(submitted, 'interpretation_id', '')
    current_profiles = profiles + ([(selected_profile, 'Submitted saved interpretation (stale or unavailable)')]
                                   if selected_profile and selected_profile not in {identity for identity, _ in profiles} else [])
    current_profile_select = f'<label>Executable profile<select name="interpretation_id">{options(current_profiles, selected_profile)}</select></label>'
    content += '<section class="panel"><h2>Recommend and save automatically</h2><p>Save supported current-knowledge accounts in deterministic comparison order with rationale and explicit gaps. Required exclusions and deferred unknown requirements remain unselected. This unranked automated result requires no human review.</p>'
    content += f'<form method="post" action="/campaigns/{e(campaign["campaign_id"])}/recommendations">{hidden("csrf",csrf)}{hidden("request_id",retry("request_id",str(uuid.uuid4())))}{hidden("brief_id",retry("brief_id",current["id"]))}{hidden("expected_brief_version",retry("expected_brief_version",current["version"]))}{hidden("expected_shortlist_version",retry("expected_shortlist_version",campaign["shortlist_version"]))}{current_profile_select}<button type="submit">Recommend and save automatically</button></form></section>'
    content += '<section class="panel"><h2>Rank supported candidates with a model</h2><p>Deterministic requirements run first, then one bounded model assessment orders eligible accounts. Generated judgments preserve explicit gaps. Valid results save automatically; failed or unavailable assessments remain visible.</p>'
    content += f'<form method="post" action="/campaigns/{e(campaign["campaign_id"])}/ranked-recommendations">{hidden("csrf",csrf)}{hidden("request_id",retry("request_id",str(uuid.uuid4())))}{hidden("brief_id",retry("brief_id",current["id"]))}{hidden("expected_brief_version",retry("expected_brief_version",current["version"]))}{hidden("expected_shortlist_version",retry("expected_shortlist_version",campaign["shortlist_version"]))}{current_profile_select}<button type="submit">Rank and save automatically</button></form>'
    for assessment in campaign.get('ranking_assessments', []):
        content += f'<article><h3>Model ranking assessment · {e(assessment["status"])}</h3><p>{e(assessment["assessment_id"])} · {e(assessment["reason"] or "Generated judgment; no human endorsement.")}</p><pre>{e(assessment["configuration"])}</pre>'
        if assessment['status'] == 'in_progress':
            content += '<p>In flight or interrupted with unknown outcome. This request will not dispatch again.</p>'
        if assessment['shortlist_id']:
            content += f'<p><a href="/shortlists/{e(assessment["shortlist_id"])}">Saved ranked outcome</a></p>'
        if assessment['operation_id']:
            content += f'<p><a href="/costs/{e(assessment["operation_id"])}">Attributable usage and cost</a></p>'
        content += '</article>'
    content += '</section>'
    content += '<section class="panel"><h2>Compare current knowledge</h2><p>Compare up to 100 published support bundles with deterministic caption rules. Incomplete supported accounts remain eligible; unsupported references remain discovery gaps. Ordering follows publication encounter order, without ranking.</p>'
    content += f'<form method="post" action="/campaigns/{e(campaign["campaign_id"])}/current-comparisons">{hidden("csrf",csrf)}{hidden("request_id",retry("request_id",str(uuid.uuid4())))}{hidden("brief_id",retry("brief_id",current["id"]))}{current_profile_select}<button type="submit">Compare current knowledge</button></form></section>'
    content += '<section class="panel"><p class="eyebrow">2 / Prepare an evidence comparison</p><h2>Compare accounts within a frozen dataset</h2><p>Preparation uses caption rules. Results remain provisional, with audience and commercial outcomes unknown.</p>'
    if datasets:
        content += f'<form method="post" action="/campaigns/{e(campaign["campaign_id"])}/comparisons">{hidden("csrf",csrf)}{hidden("request_id",str(uuid.uuid4()))}{hidden("brief_id",current["id"])}{profile_select}<label>Evidence dataset<select name="dataset_id">{options([(d["dataset_id"],f"{d['dataset_id']} · {d['posts']} selected posts") for d in datasets], datasets[0]["dataset_id"])}</select></label><button type="submit">Prepare rule-based comparison</button></form>'
    else:
        content += '<p>No dataset is loaded. Import a frozen snapshot before preparation.</p>'
    content += '</section><div class="history-grid"><section class="panel"><h2>Comparisons</h2>'
    for comparison in reversed(campaign["comparisons"]):
        content += f'<p><a href="/comparisons/{e(comparison["id"])}">Review comparison · {e(comparison["prepared_at"])}</a><br><small>Prepared by {e(comparison["prepared_by"])}</small></p>'
    content += ('<p>No comparisons prepared.</p>' if not campaign["comparisons"] else '') + '</section><section class="panel"><h2>Saved shortlist revisions</h2>'
    for revision in reversed(campaign["shortlists"]):
        content += f'<p><a href="/shortlists/{e(revision["id"])}">Revision {revision["version"]} · {e(revision["status"])}</a><br><small>{e(revision["recorded_by"])} · {e(revision["recorded_at"])}</small></p>'
    content += ('<p>No selection saved.</p>' if not campaign["shortlists"] else '') + '</section></div>'
    if len(campaign["briefs"]) > 1:
        content += '<details class="panel"><summary>Previous brief revisions</summary>' + ''.join(brief_summary(b) for b in reversed(campaign["briefs"][:-1])) + '</details>'
    content += f'<p><a href="/campaigns/{e(campaign["campaign_id"])}/tasks/new">Submit offline acquisition</a></p>'
    return content


def members_for(candidate, source):
    if candidate["body"] is None:
        return []
    return evidence_members(candidate["body"]["observations"], source)


def evidence_members(observation_ids, source):
    """Return only a complete, currently permitted set for one copied explanation."""
    ids = set(observation_ids)
    members = [m for m in source["members"] if m["observation_id"] in ids]
    if len(members) != len(ids) or any(m["availability"] != "available" or m["support_status"] != "current" or not m["policy"]["can_retain"] for m in members):
        return []
    return members


def account_name(candidate, members):
    handle = next((a["value"] for m in members for a in m["assertions"] if a["field"] == "handle" and a["state"] == "observed"), None)
    return f'@{handle}' if handle else candidate["account_key"]["native_id"]


def source_link(reference):
    url = reference if isinstance(reference, str) else ""
    parsed = urlsplit(url)
    if parsed.scheme in {"https", "http"} and parsed.netloc and not parsed.username and not parsed.password:
        return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">Open original source ↗</a>'
    return '<span>Source link unavailable</span>'


def marked_caption(caption, claims):
    spans = sorted((c["span"]["start"], c["span"]["end"]) for c in claims if c["span"]["text"] == caption[c["span"]["start"]:c["span"]["end"]])
    merged = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    result, position = "", 0
    for start, end in merged:
        result += e(caption[position:start]) + '<mark>' + e(caption[start:end]) + '</mark>'
        position = end
    return result + e(caption[position:])


def evidence_panel(members, claims):
    content = '<details class="evidence"><summary>Original captions and provenance <span class="count">' + str(len(members)) + '</span></summary>'
    for member in members:
        caption = next((a for a in member["assertions"] if a["field"] == "caption" and a["state"] == "observed"), None)
        supported = [c for c in claims if caption is not None and c["source_assertion_id"] == caption["assertion_id"]]
        published = next((a["value"] for a in member["assertions"] if a["field"] == "published_at" and a["state"] == "observed"), "Unknown")
        captured = datetime.fromisoformat(member["captured_at"].replace("Z", "+00:00")) if member["captured_at"] else None
        age = f'{max(0, (datetime.now(timezone.utc) - captured).days)} days ago' if captured else 'Unknown capture time'
        caption_content = f'<p class="caption">{marked_caption(caption["value"], supported)}</p><p class="muted">Translation pending. Original-language interpretation remains provisional.</p>' if caption else '<p>Caption not available in this supporting observation.</p>'
        content += f'<article class="post"><div class="row-title">{source_link(member["source_reference"])}<span class="badge">Observed text</span></div>{caption_content}<dl class="facts"><div><dt>Published</dt><dd>{e(published)}</dd></div><div><dt>Captured</dt><dd>{e(member["captured_at"])} · {age}</dd></div><div><dt>Acquisition</dt><dd>{e(member["provider"])} / {e(member["adapter"])}</dd></div></dl><details><summary>Support references</summary><p>Observation: {e(member["observation_id"])}<br>Assertion IDs: {e([a["assertion_id"] for a in member["assertions"]])}<br>Metric IDs: {e([m["metric_id"] for m in member["metrics"]])}<br>Original observation: {e(member.get("origin_observation_id", member["observation_id"]))}</p></details></article>'
    return content + '</details>'


def unknown_label(key, body):
    labels = {"audience_geography": "Audience geography", "fees": "Fees", "availability": "Availability",
              "sales_effectiveness": "Sales effectiveness", "recent_post_history": "Complete recent-post history"}
    if key.startswith("criterion:"):
        label = next((j["label"] for j in body["judgments"] if key == 'criterion:' + j["criterion_id"]), key)
        return "Criterion: " + label
    return labels.get(key, key)


def comparison_page(comparison, campaign, brief, source, csrf, previous=None, submitted=None, error=None):
    content = f'<p><a href="/campaigns/{e(campaign["campaign_id"])}">← Campaign and revision history</a></p><p class="eyebrow">3 / Review the support</p><h1>Account comparison</h1><p class="lede">Within these selected captions, which accounts merit further investigation for your brief?</p><div class="notice"><strong>Rule-based draft · provisional</strong><p>No audience or sales inference. Semantic and original-language review remain pending.</p></div>'
    if error:
        content += error_message(error)
    content += brief_summary(brief)
    if comparison.get('criteria_interpretation_id'):
        content += '<section class="panel"><h2>Selected model-generated executable profile</h2>' + profile_summary(comparison['executable_profile']) + '</section>'
    content += f'<p>{len(comparison["candidates"])} candidates · {len(comparison["coverage"]["actual_observation_ids"])} scoped observations · {source.get("current_coverage", source["coverage"])["unavailable_members"]} currently unavailable source observations</p>'
    source_description = 'Current committed knowledge · bounded, unranked' if comparison.get('knowledge_query') else f'Frozen dataset: {e(comparison["dataset_id"])}<br>Digest: {e(comparison["digest"])}<br>Knowledge run: {e(comparison["knowledge_run_id"])}'
    content += f'<details class="panel"><summary>Exact evidence and method</summary><p>{source_description}<br>Method: {e(comparison["method_version"])}<br>Prepared: {e(comparison["prepared_at"])} by {e(comparison["prepared_by"])}</p></details>'
    if comparison.get('knowledge_query'):
        query = comparison['knowledge_query']
        content += f'<details class="panel"><summary>Actual retrieved support manifest</summary><p>Query: {e(query["result_id"])} · {e(query["method_version"])} · ordering: unranked publication encounter order</p><pre>{e(query["manifest"])}</pre><p>Coverage: {e(comparison["coverage"])}<br>Freshness without a threshold: not_assessed</p></details>'
    stale = brief["version"] != campaign["brief_version"]
    if stale:
        content += error_message("brief_version_conflict")
    previous_choices = {s["candidate_id"]: s for s in previous["selected"]} if previous else {}
    content += f'<form method="post" action="/comparisons/{e(comparison["comparison_id"])}/shortlists" id="shortlist-form">{hidden("csrf",csrf)}{hidden("request_id",value(submitted,"request_id",str(uuid.uuid4())))}{hidden("expected_version",value(submitted,"expected_version",previous["version"] if previous else campaign["shortlist_version"]))}'
    if previous:
        content += hidden('source_shortlist_id', previous['shortlist_id'])
        content += f'<section class="panel"><h2>Optional human curation</h2><p>Starting from <a href="/shortlists/{e(previous["shortlist_id"])}">revision {e(previous["version"])}</a>. Select accounts and give each selected account a distinct position. Saving a draft records your curation without confirming review. Starting reasons retain their original automated or human basis until you save your human input.</p></section>'
        if previous['version'] != campaign['shortlist_version']:
            content += error_message('shortlist_version_conflict')
    if not comparison["candidates"]:
        content += '<section class="panel"><h2>No eligible supported accounts in this scope</h2><p>You can save an empty shortlist to record deliberate deferral.</p></section>'
    candidates = comparison['candidates']
    if previous and previous['ordering'] is not None:
        order = {s['candidate_id']: i for i, s in enumerate(previous['selected'])}
        candidates = sorted(candidates, key=lambda c: order.get(c['candidate_id'], len(order)))
    for index, candidate in enumerate(candidates):
        cid, body = candidate["candidate_id"], candidate["body"]
        members = members_for(candidate, source)
        available = body is not None and (not body["observations"] or bool(members))
        choice = previous_choices.get(cid, {})
        is_selected = cid in submitted.get("selected", []) if submitted is not None else cid in previous_choices
        content += f'<article class="panel candidate" data-candidate="{e(cid)}"><div class="row-title"><div><h2>{e(account_name(candidate,members))}</h2><small>{e(candidate["account_key"]["platform"])} · {e(candidate["account_key"]["namespace"])} · {e(candidate["account_key"]["native_id"])}</small></div><span class="badge">{e(candidate["origin"].replace("_"," "))}</span></div><label class="check select-candidate"><input type="checkbox" name="selected" value="{e(cid)}"{checked(is_selected)}>Include this account</label>'
        if previous:
            content += f'<label>Position in your selected order<input type="number" min="1" name="position_{e(cid)}" value="{e(value(submitted,"position_" + cid,str(index + 1)))}"></label>'
        if not available:
            content += '<div class="notice"><strong>Support unavailable or requires review</strong><p>Source-dependent explanations are withheld. This account can remain in an unconfirmed draft.</p></div></article>'
            continue
        if 'assessment' in body:
            content += f'<p>Assessment: {e(body["assessment"])} · provisional, unranked</p><details><summary>Source dates, freshness and gaps</summary><p>{e(body["source_dates"])}</p><p>{e(body["support_manifest"])}</p><p>{e(body["unknowns"])}</p></details>'
        content += '<div class="judgments">'
        for judgment in body["judgments"]:
            content += f'<div class="judgment {e(judgment["state"])}"><strong>{e(judgment["label"])}</strong><span>{e(judgment["state"].replace("_"," "))}</span><p>{e(judgment["reason"])}</p><small>{"Required" if judgment["required"] else "Preference"} · unknown: {e(judgment["unknown_handling"])} · {e(judgment["review_status"])}</small></div>'
        content += '</div>' + evidence_panel(members, candidate["evidence"])
        reason = value(submitted, 'reason_' + cid, choice.get("reason") or "")
        if choice.get('reason'):
            content += f'<p>Starting reason basis: {e(choice["reason_basis"])}, from the linked source revision. Your saved reason will be human supplied.</p>'
        content += f'<label>Human inclusion reason<textarea name="reason_{e(cid)}" rows="2" placeholder="Explain why the cited evidence merits further investigation.">{e(reason)}</textarea><small>Human input; its wording is not independently verified.</small></label><fieldset><legend>Cite relevance support</legend>'
        cited = submitted.get('support_' + cid, []) if submitted is not None else choice.get("support_ids", [])
        seen = set()
        for claim in candidate["evidence"]:
            if claim["id"] in seen:
                continue
            seen.add(claim["id"])
            content += f'<label class="check"><input type="checkbox" name="support_{e(cid)}" value="{e(claim["id"])}"{checked(claim["id"] in cited)}><span>{e(KINDS.get(claim["predicate"],claim["predicate"]))}: “{e(claim["span"]["text"])}” <small>Provisional interpretation</small></span></label>'
        if not seen:
            content += '<p>No positive relevance support is available. Save a draft or defer this account.</p>'
        content += '</fieldset><fieldset class="unknowns"><legend>Acknowledge unknowns for this account</legend>'
        acknowledged = submitted.get('unknown_' + cid, []) if submitted is not None else choice.get("acknowledged_unknowns", [])
        for key in body["unknowns"]:
            content += f'<label class="check"><input type="checkbox" name="unknown_{e(cid)}" value="{e(key)}"{checked(key in acknowledged)}>{e(unknown_label(key,body))}</label>'
        content += '</fieldset></article>'
    content += '<section class="panel save-panel"><p class="eyebrow">4 / Save your decision</p><h2>Keep the review draft, or confirm your selection</h2><p>Confirmation records an exploratory internal shortlist. Empty selections can record deferral.</p><label class="check"><input type="checkbox" name="reviewed" value="yes"' + checked(value(submitted,"reviewed") == "yes") + '>I reviewed the selected accounts, cited support and unknowns. This is my selection.</label>'
    disabled = ' disabled' if stale else ''
    return content + f'<div class="actions"><button type="submit" name="action" value="draft" class="secondary" formnovalidate{disabled}>Save draft</button><button type="submit" name="action" value="confirm"{disabled}>Confirm shortlist</button></div><small>Expected prior shortlist version: {e(value(submitted,"expected_version",campaign["shortlist_version"]))}. Saving creates a new immutable revision.</small></section></form>'


def shortlist_page(shortlist, brief, comparison, source, enrichment=None):
    content = f'<p><a href="/campaigns/{e(shortlist["campaign_id"])}">← Campaign and revision history</a></p><div class="heading"><div><p class="eyebrow">Saved decision</p><h1>Shortlist revision {shortlist["version"]}</h1><p><span class="badge">{e(shortlist["status"])}</span> Recorded by {e(shortlist["recorded_by"])} · {e(shortlist["recorded_at"])}</p></div><a class="button secondary" href="/comparisons/{e(shortlist["comparison_id"])}?shortlist_id={quote(shortlist["shortlist_id"])}">Create successor revision</a></div>'
    generated = shortlist["actor_kind"] == "automation"
    content += '<p class="lede">This saved account set and producer attribution are pinned. Source health below reflects current permissions.</p>' + brief_summary(brief)
    if generated:
        ranking = shortlist.get('ranking_assessment')
        description = ('Validated LLM assessment order. Generated judgment; saving records no human endorsement or acknowledgement.'
                       if ranking and ranking['candidates'] else 'Empty eligible batch; model not called.' if ranking
                       else 'Deterministic and unranked. Saving records no human endorsement or acknowledgement.')
        content += f'<section class="panel"><h2>Automation provenance</h2><p>Producer: {e(shortlist["actor_kind"])} · {e(shortlist["recorded_by"])}<br>Method: {e(shortlist["method_version"])}<br>Order: {e(shortlist["ordering"])}<br>Execution: {e(shortlist["execution_profile"])}</p><p>{e(description)}</p><p>Saved selection outcome: {e(shortlist["selection_summary"])}</p><details><summary>Coverage and gaps</summary><pre>{e(shortlist["coverage"])}</pre></details></section>'

        if ranking:
            content += f'<details class="panel"><summary>Exact assessed inputs and validated model judgments</summary><pre>{e(ranking)}</pre></details>'
    elif shortlist.get('source_shortlist_id'):
        content += f'<section class="panel"><h2>Human curation</h2><p>Source: <a href="/shortlists/{e(shortlist["source_shortlist_id"])}">original revision</a><br>Method: {e(shortlist["method_version"])}<br>Order: {e(shortlist["ordering"])}</p><p>{"Separate human confirmation recorded." if shortlist["status"] == "confirmed" else "Unconfirmed human curation; no human review is asserted."}</p></section>'
    coverage = shortlist.get('coverage_assessment')
    if coverage is not None:
        profile, result = coverage['profile'], coverage['result']
        content += f'<section class="panel"><h2>Campaign coverage</h2><p>Assessed at {e(coverage["assessed_at"])}. This bounded KB assessment does not establish market completeness.</p>'
        if result is None:
            content += '<p>Coverage explanations unavailable under current support policy.</p>'
        else:
            content += '<p>' + ('Sufficient under the recorded policy.' if result['sufficient'] else 'More evidence is needed under the recorded policy.') + '</p><dl>'
            for label, actual, minimum in (
                ('Supported candidates', 'eligible_candidates', 'minimum_candidates'),
                ('Candidates with supported literal relevance', 'relevant_candidates', 'minimum_relevant_candidates'),
                ('Candidates with recent known captures', 'fresh_candidates', 'minimum_fresh_candidates'),
            ):
                content += f'<dt>{label}</dt><dd>{result[actual]} / {profile[minimum]} required</dd>'
            content += f'</dl><p>Captures must be no more than {profile["maximum_capture_age_seconds"] // 86400} days old. Stale: {result["stale_candidates"]}; unknown or future capture time: {result["unknown_capture_candidates"]}.</p>'
            labels = {'insufficient_quantity': 'Too few supported eligible candidates.',
                      'insufficient_relevance': 'Too few candidates with supported literal relevance.',
                      'insufficient_freshness': 'Too few candidates with recent known capture times.'}
            content += '<ul>' + ''.join(f'<li>{e(labels[reason])}</li>' for reason in result['reasons']) + '</ul>'
        if enrichment:
            content += f'<p>Enrichment: {e(enrichment["status"])}'
            if enrichment['reason']:
                content += f' · {e(enrichment["reason"])}'
            content += '</p>'
            if enrichment['task_id']:
                task = enrichment['task']
                reason = task['progress'].get('reason') or (task['failure'] or {}).get('code')
                content += f'<p><a href="/tasks/{e(enrichment["task_id"])}">Discovery task</a> · {e(task["execution"]["state"])} · {e(task["outcome"] or "pending")}'
                if reason:
                    content += f' · {e(reason)}'
                content += '</p>'
        else:
            content += '<p>Automatic discovery disposition has not been recorded.</p>'
        content += f'<details><summary>Exact coverage profile and input references</summary><pre>{e(coverage)}</pre></details></section>'
    if shortlist["version"] != shortlist["current_shortlist_version"]:
        content += '<div class="notice">This is a historical revision. A newer shortlist revision exists in the campaign history.</div>'
    if not shortlist["selected"]:
        explanation = ('This generated revision has no supported candidates meeting the required criteria; the saved selection outcome records why.' if generated
                       else 'This revision records an empty selection or deliberate deferral.')
        content += f'<section class="panel"><h2>No accounts selected</h2><p>{explanation}</p></section>'
    candidates = {c["candidate_id"]: c for c in comparison["candidates"]}
    for selection in shortlist["selected"]:
        candidate = candidates[selection["candidate_id"]]
        members = members_for(candidate, source)
        safe = selection["reason_state"] == "available" and candidate["body"] is not None and (not candidate["body"]["observations"] or bool(members))
        content += f'<article class="panel"><div class="row-title"><h2>{e(account_name(candidate,members if safe else []))}</h2><span class="badge">Selected account</span></div><p>{e(selection["account_key"]["platform"])} · {e(selection["account_key"]["namespace"])} · {e(selection["account_key"]["native_id"])}</p>'
        if safe:
            if generated:
                content += f'<h3>{"Generated relative-fit rationale" if ranking else "Deterministic inclusion rationale"}</h3><p>{e(selection["reason"])}</p><p>Position: {e(selection["position"])} · {e(selection["reason_basis"])}</p><details><summary>Pinned support manifest</summary><pre>{e(selection["support_manifest"])}</pre></details>' + evidence_panel(members, selection["evidence"])
            else:
                position = f'<p>Position: {e(selection["position"])}</p>' if selection['position'] is not None else ''
                content += f'<h3>Human inclusion reason</h3><p>{e(selection["reason"] or "No reason recorded in this draft.")}</p>{position}<small>Human supplied; semantic review remains provisional.</small>' + evidence_panel(members, selection["evidence"])
        else:
            content += '<div class="notice"><strong>Review required</strong><p>Reason and evidence are unavailable under current support health. The saved membership and producer remain recorded.</p></div>'
        gaps = selection["acknowledged_unknowns"]
        if generated:
            gaps = (selection["gaps"] or []) if safe else []
        content += '<h3>' + ('Explicit gaps' if generated else 'Acknowledged unknowns') + '</h3><ul>' + ''.join('<li>' + e(unknown_label(key,candidate["body"] or {"judgments": []})) + '</li>' for key in gaps) + '</ul></article>'
    return content + f'<details class="panel"><summary>Exact saved references</summary><p>Shortlist: {e(shortlist["shortlist_id"])}<br>Comparison: {e(shortlist["comparison_id"])}<br>Brief: {e(shortlist["brief_id"])}<br>Dataset: {e(comparison["dataset_id"])}<br>Digest: {e(comparison["digest"])}</p></details>'
