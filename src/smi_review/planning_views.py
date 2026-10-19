"""Human proposed-measurement and decision-feedback forms/history."""

import uuid

from .views import e, error_message, hidden, options, value


PLAN_LABELS = {"objective": "Sales objective / planning purpose", "outcome_definition": "Proposed outcome definition",
               "intended_source": "Intended outcome source", "source_owner": "Source owner", "listing": "Listing / SKU context",
               "currency": "Currency", "period": "Measurement period", "baseline": "Baseline",
               "matching_approach": "Account-to-campaign and order matching", "attribution_assumptions": "Attribution assumptions / window"}


def planning_page(campaign, brief, records, csrf, submitted=None, kind=None, error=None):
    campaign_id = campaign["campaign_id"]
    plan_form = submitted if kind == "plan" else None
    note_form = submitted if kind == "note" else None
    content = f'<p><a href="/campaigns/{e(campaign_id)}">← Campaign and shortlist history</a></p><p class="eyebrow">Measurement and learning</p><h1>Record intent, prerequisites and feedback.</h1><div class="notice"><strong>Proposed measurement only</strong><p>No outcome access is verified. Views and engagement do not produce revenue, conversion or lift.</p></div>'
    if error:
        content += error_message(error)
    relevant = [s for s in campaign["shortlists"] if s["brief_id"] == brief["id"]]
    latest = records["plans"][-1]["document"] if records["plans"] and records["plans"][-1]["brief_id"] == brief["id"] else {}
    if relevant:
        content += f'<form class="panel" method="post" action="/campaigns/{e(campaign_id)}/plans"><h2>Propose a measurement plan</h2>{hidden("csrf",csrf)}{hidden("request_id",value(plan_form,"request_id",str(uuid.uuid4())))}{hidden("expected_version",value(plan_form,"expected_version",records["plan_version"]))}{hidden("brief_id",brief["id"])}<label>Relevant shortlist<select name="shortlist_id">{options([(s["id"],f"Revision {s['version']} · {s['status']}") for s in relevant],value(plan_form,"shortlist_id",relevant[-1]["id"]))}</select></label><div class="form-grid">'
        for name, label in PLAN_LABELS.items():
            default = latest.get(name) or (brief["document"]["objective"] if name == "objective" else "")
            required = ' required' if name in {"objective", "outcome_definition"} else ''
            content += f'<label>{label}<textarea rows="2" name="{name}"{required} placeholder="Unknown / not yet agreed">{e(value(plan_form,name,default))}</textarea></label>'
        content += f'<label>Product references<input name="product_ids" value="{e(value(plan_form,"product_ids",", ".join(latest.get("product_ids",brief["document"]["product_ids"]))))}"></label></div><label>Known gaps · one per line<textarea name="gaps" rows="3" required>{e(value(plan_form,"gaps","\n".join(latest.get("gaps",["Outcome data access is unverified.","No commercial baseline supplied."]))))}</textarea></label><p>These are human proposals. Missing sources, identifiers, unmatched orders and overlapping touches remain gaps.</p><button type="submit">Save proposed plan revision</button></form>'
    else:
        content += '<section class="panel"><h2>Select a relevant shortlist first</h2><p>A proposed plan pins the current brief and one of its saved shortlist revisions. An empty/deferred shortlist is valid.</p></section>'
    if campaign["shortlists"]:
        content += f'<form class="panel" method="post" action="/campaigns/{e(campaign_id)}/notes"><h2>Add a human decision note</h2>{hidden("csrf",csrf)}{hidden("request_id",value(note_form,"request_id",str(uuid.uuid4())))}{hidden("expected_version",value(note_form,"expected_version",records["note_version"]))}<label>Relevant shortlist<select name="shortlist_id">{options([(s["id"],f"Revision {s['version']} · {s['status']}") for s in campaign["shortlists"]],value(note_form,"shortlist_id",campaign["shortlists"][-1]["id"]))}</select></label><label>Feedback, assumptions or learning<textarea name="text" required rows="3">{e(value(note_form,"text"))}</textarea></label><p>Human input, not an independently verified outcome. The shortlist support governs copied note text.</p><button type="submit">Record decision note</button></form>'
    content += '<section class="panel"><h2>Plan revision history</h2>'
    for plan in reversed(records["plans"]):
        content += f'<article><h3>Plan {plan["version"]} · proposed</h3><small>{e(plan["recorded_by"])} · {e(plan["recorded_at"])}</small><p>Outcome access: not verified · No measured results</p><dl class="facts">'
        for name, label in PLAN_LABELS.items():
            content += f'<div><dt>{label}</dt><dd>{e(plan["document"][name] or "Unknown")}</dd></div>'
        content += '</dl><h3>Known gaps</h3><ul>' + ''.join('<li>' + e(gap) + '</li>' for gap in plan["document"]["gaps"]) + f'</ul><p><a href="/shortlists/{e(plan["shortlist_id"])}">Pinned shortlist</a> · Brief: {e(plan["brief_id"])}</p></article>'
    content += ('<p>No plan recorded yet.</p>' if not records["plans"] else '') + '</section><section class="panel"><h2>Decision note history</h2>'
    for note in reversed(records["notes"]):
        content += f'<article><h3>Note {note["version"]} · human supplied</h3><small>{e(note["recorded_by"])} · {e(note["recorded_at"])}</small><p>{e(note["text"]) if note["text"] is not None else "Note text unavailable; source support requires review."}</p><a href="/shortlists/{e(note["shortlist_id"])}">Pinned shortlist</a></article>'
    return content + ('<p>No decision notes recorded yet.</p>' if not records["notes"] else '') + '</section>'
