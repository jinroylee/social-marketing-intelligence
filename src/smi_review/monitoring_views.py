"""Independent investigation forms and permitted snapshot finding panels."""

import uuid

from smi_ingestion.evidence import EvidenceError
from smi_monitoring import InvestigationScope

from .forms import one
from .views import checked, e, error_message, evidence_members, evidence_panel, hidden, options, value


def scope_from_form(form):
    allowed = {"csrf", "request_id", "expected_version"} | InvestigationScope.__dataclass_fields__.keys()
    if not form.keys() <= allowed:
        raise EvidenceError("invalid_form")
    return InvestigationScope(one(form, "catalog_id"), one(form, "question"), one(form, "market_context"),
        tuple(p.strip() for p in one(form, "platforms").split(",") if p.strip()),
        tuple(form.get("brand_ids", [])), tuple(form.get("product_ids", [])), tuple(form.get("topic_ids", [])),
        one(form, "caption_language").strip() or None, one(form, "publication_from").strip() or None, one(form, "publication_to").strip() or None)


def index(investigations):
    content = '<div class="heading"><div><p class="eyebrow">Independent market monitoring</p><h1>Investigate what the sample supports.</h1><p class="lede">Save a product or topic question without starting a campaign. Snapshot findings retain their sources and limits.</p></div><a class="button" href="/investigations/new">Create investigation</a></div><div class="campaign-grid">'
    for investigation in investigations:
        content += f'<a class="campaign-card" href="/investigations/{e(investigation["investigation_id"])}"><span class="badge">{e(investigation["market_context"])}</span><h2>{e(investigation["question"])}</h2><p>Scope {investigation["scope_version"]} · {investigation["insight_version"]} insight revisions</p><small>Saved by {e(investigation["owner_id"])}</small></a>'
    return content + ('<p>No investigations saved yet.</p>' if not investigations else '') + '</div>'


def scope_form(catalog, catalogs, csrf, investigation=None, current=None, submitted=None, error=None):
    document = current["document"] if current else {"question": "", "market_context": "", "platforms": ["tiktok"], "brand_ids": [], "product_ids": [], "topic_ids": []}
    get = lambda name: value(submitted, name, document.get(name) or "")
    content = '<p class="eyebrow">Independent investigation</p><h1>' + ('Revise the question' if investigation else 'Create an investigation') + '</h1><p class="lede">Choose product or topic references. Findings will describe their literal support in the selected observations.</p>'
    if not investigation:
        content += f'<form method="get" action="/investigations/new" class="catalog-switch"><label>Reference catalog<select name="catalog_id">{options([(c["catalog_id"],c["catalog_id"]) for c in catalogs],catalog["catalog_id"])}</select></label><button class="secondary">Use catalog</button></form>'
    if error:
        content += error_message(error)
    action = f'/investigations/{investigation["investigation_id"]}/scopes' if investigation else '/investigations'
    content += f'<form method="post" action="{e(action)}">{hidden("csrf",csrf)}{hidden("request_id",value(submitted,"request_id",str(uuid.uuid4())))}{hidden("catalog_id",catalog["catalog_id"])}'
    if investigation:
        content += hidden("expected_version",value(submitted,"expected_version",investigation["scope_version"]))
    content += f'<section class="panel"><label>Question<textarea name="question" rows="2" required placeholder="Which product mentions and commerce references appear in these selected captions?">{e(get("question"))}</textarea></label><div class="form-grid"><label>Intended market context<input name="market_context" value="{e(get("market_context"))}" required placeholder="JP"></label><label>Platforms<input name="platforms" value="{e(value(submitted,"platforms",", ".join(document["platforms"])))}" required></label></div><p>Market context describes your question; it does not establish audience geography.</p>'
    for name, group, label in [("brand_ids","brands","Brands"),("product_ids","products","Products"),("topic_ids","topics","Topics")]:
        chosen = submitted.get(name, []) if submitted is not None else document[name]
        content += '<fieldset><legend>' + label + '</legend><div class="choice-grid">'
        for entry in catalog[group]:
            content += f'<label class="check"><input type="checkbox" name="{name}" value="{e(entry["id"])}"{checked(entry["id"] in chosen)}>{e(entry["name"])}</label>'
        content += '</div></fieldset>'
    content += '<p>Choose at least one reference. Any selected reference can match; literal PR/Qoo10 markers are summarized within those matching posts.</p><div class="form-grid">'
    for name, label, placeholder in [("caption_language","Required caption language (optional)","Unknown / not requested"),
                                    ("publication_from","Published from","2026-01-01T00:00:00+00:00"),
                                    ("publication_to","Published through","2026-10-14T00:00:00+00:00")]:
        content += f'<label>{label}<input name="{name}" value="{e(get(name))}" placeholder="{placeholder}"></label>'
    return content + '</div><p>A required language cannot be established by the current script rules; it produces a visible not-assessable result. Publication windows use timezone-aware timestamps.</p></section><button type="submit">Save investigation scope</button></form>'


def scope_summary(scope):
    document = scope["document"]
    content = f'<section class="panel"><h2>Scope {scope["version"]} · human question</h2><p class="lede">{e(document["question"])}</p><p>Market context: {e(document["market_context"])} · Platforms: {e(", ".join(document["platforms"]))}</p><p>Requested references: {e(", ".join(document["brand_ids"] + document["product_ids"] + document["topic_ids"]))}</p><p>Required caption language: {e(document["caption_language"] or "Not requested")}<br>Publication window: {e(document["publication_from"] or "Open")} → {e(document["publication_to"] or "Open")}</p><small>Recorded by {e(scope["recorded_by"])} · {e(scope["recorded_at"])}</small></section>'
    return content


def investigation_page(investigation, datasets, csrf):
    investigation_id = investigation["investigation_id"]
    current = investigation["scopes"][-1]
    content = f'<p><a href="/investigations">← Investigations</a></p><div class="heading"><div><p class="eyebrow">Snapshot investigation</p><h1>{e(current["document"]["question"])}</h1></div><a class="button secondary" href="/investigations/{e(investigation_id)}/edit">Revise scope</a></div>' + scope_summary(current)
    content += '<section class="panel"><h2>Prepare a scoped snapshot insight</h2><p>No market-growth baseline or commercial outcomes are available. A refresh creates a successor answer, not a change alert.</p>'
    if datasets:
        content += f'<form method="post" action="/investigations/{e(investigation_id)}/insights">{hidden("csrf",csrf)}{hidden("request_id",str(uuid.uuid4()))}{hidden("scope_id",current["id"])}{hidden("expected_version",investigation["insight_version"])}<label>Dataset<select name="dataset_id">{options([(d["dataset_id"],d["dataset_id"]) for d in datasets],datasets[0]["dataset_id"])}</select></label><button type="submit">Prepare rule-based insight</button></form>'
    else:
        content += '<p>No frozen dataset is loaded.</p>'
    content += '</section><section class="panel"><h2>Saved insight history</h2>'
    for insight in reversed(investigation["insights"]):
        content += f'<p><a href="/insights/{e(insight["id"])}">Insight revision {insight["version"]}</a> · {e(insight["prepared_at"])}</p>'
    content += ('<p>No insight prepared yet.</p>' if not investigation["insights"] else '') + '</section>'
    if len(investigation["scopes"]) > 1:
        content += '<details class="panel"><summary>Previous scope revisions</summary>' + ''.join(scope_summary(s) for s in investigation["scopes"][:-1]) + '</details>'
    return content


def insight_page(insight, scope, source):
    content = f'<p><a href="/investigations/{e(insight["investigation_id"])}">← Investigation and history</a></p><p class="eyebrow">Pinned snapshot answer</p><h1>Insight revision {insight["version"]}</h1><div class="notice"><strong>Rule-based findings · provisional</strong><p>Within selected observations only. No market growth, audience location or sales conclusion.</p></div>' + scope_summary(scope)
    coverage = insight["coverage"]
    matching = str(len(coverage["actual_observation_ids"])) if coverage["actual_observation_ids"] is not None else 'Unavailable'
    content += f'<p>{len(coverage["scanned_observation_ids"])} observations in the original platform/publication scope · {matching} matched observations · language requirement: {e(coverage["language_constraint"])}</p>'
    for finding in insight["findings"]:
        body = finding["body"]
        members = evidence_members(body["observation_ids"], source) if body else []
        content += '<section class="panel">'
        if body is None or not members:
            content += '<h2>Finding requires review</h2><p>Source-dependent text/counts and excerpts are unavailable under current support health.</p>'
        else:
            content += f'<h2>{e(body["label"])}</h2><p class="lede">{e(body["statement"])}</p><small>Derived literal finding; semantic review is provisional.</small>' + evidence_panel(members,finding["evidence"])
        content += f'<details><summary>Finding reference</summary><p>{e(finding["finding_id"])}</p></details></section>'
    if not insight["findings"]:
        content += '<section class="panel"><h2>' + ('Language constraint not assessable' if coverage["language_constraint"] == "not_assessable" else 'No matching observations in this dataset') + '</h2><p>This result makes no claim about absence of market activity.</p></section>'
    content += '<section class="panel"><h2>Limits and unknowns</h2><ul>' + ''.join('<li>' + e(limit) + '</li>' for limit in insight["limitations"]) + '</ul></section>'
    return content + f'<details class="panel"><summary>Evidence, method and attribution</summary><p>Dataset: {e(insight["dataset_id"])}<br>Digest: {e(insight["digest"])}<br>Knowledge run: {e(insight["knowledge_run_id"])}<br>Method: {e(insight["method_version"])}<br>Prepared by {e(insight["prepared_by"])} ({e(insight["actor_kind"])}) · {e(insight["prepared_at"])}</p></details>'
