from __future__ import annotations

import copy
import json
import os
import select
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from html.parser import HTMLParser
from http.client import HTTPConnection
from threading import Thread
from urllib.parse import urlencode, urlsplit

import pytest
from psycopg.types.json import Jsonb

from smi_campaigns import Selection
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgeStore
from smi_campaigns import CampaignStore
from smi_review import ReviewApp, make_server
from smi_review.views import marked_caption, source_link
from test_campaigns import campaigns as campaigns_fixture
from test_evidence_sets import DATASET, HUMAN


campaigns = campaigns_fixture


class Forms(HTMLParser):
    """Collect browser-successful default controls for real HTTP workflow tests."""

    def __init__(self, html):
        super().__init__()
        self.forms = []
        self.current = None
        self.select = None
        self.option = None
        self.textarea = None
        self.template_depth = 0
        self.feed(html)

    def add(self, name, value):
        self.current[1].setdefault(name, []).append(value)

    def handle_starttag(self, tag, attrs):
        if tag == "template":
            self.template_depth += 1
        if self.template_depth:
            return
        attrs = dict(attrs)
        if tag == "form":
            self.current = (attrs.get("action", ""), {})
            self.forms.append(self.current)
        if self.current is None:
            return
        if tag == "input" and "name" in attrs and "disabled" not in attrs:
            if attrs.get("type") != "checkbox" or "checked" in attrs:
                self.add(attrs["name"], attrs.get("value", ""))
        elif tag == "select":
            self.select = (attrs["name"], [])
        elif tag == "option" and self.select:
            self.option = [attrs.get("value", ""), "selected" in attrs]
        elif tag == "textarea":
            self.textarea = [attrs["name"], ""]

    def handle_data(self, data):
        if not self.template_depth and self.textarea is not None:
            self.textarea[1] += data

    def handle_endtag(self, tag):
        if tag == "template":
            self.template_depth -= 1
            return
        if self.template_depth:
            return
        if tag == "form":
            self.current = None
        elif tag == "option" and self.select and self.option:
            self.select[1].append(self.option)
            self.option = None
        elif tag == "select" and self.select:
            choices = self.select[1]
            if choices:
                self.add(self.select[0], next((o[0] for o in choices if o[1]), choices[0][0]))
            self.select = None
        elif tag == "textarea" and self.textarea:
            self.add(*self.textarea)
            self.textarea = None


def form(html, action):
    return next(fields for target, fields in Forms(html).forms if target == action)


def request(url, method="GET", path="/", fields=None, headers=None):
    parsed = urlsplit(url)
    connection = HTTPConnection(parsed.hostname, parsed.port, timeout=15)
    body = urlencode(fields, doseq=True).encode() if fields is not None else None
    defaults = {"Origin": url, "Content-Type": "application/x-www-form-urlencoded"} if method == "POST" else {}
    connection.request(method, path, body, {**defaults, **(headers or {})})
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read().decode()
    connection.close()
    return result


@contextmanager
def running(app):
    with make_server(app, 0) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.url
        finally:
            server.shutdown()
            thread.join(timeout=5)


@pytest.fixture
def review(campaigns):
    app = ReviewApp(campaigns[0].db, "named-reviewer")
    with running(app) as url:
        yield app, url


def start(review, objective="Investigate product content for this campaign"):
    _, url = review
    status, _, html = request(url, path="/campaigns/new")
    assert status == 200
    fields = form(html, "/campaigns")
    fields.update(objective=[objective], target_market=["JP"], known_accounts=["tiktok web:public 6819904612390634498"])
    status, headers, html = request(url, "POST", "/campaigns", fields)
    assert status == 303, html
    return headers["Location"]


def prepare(review):
    campaign_path = start(review)
    _, url = review
    _, _, html = request(url, path=campaign_path)
    action = campaign_path + "/comparisons"
    fields = form(html, action)
    status, headers, html = request(url, "POST", action, fields)
    assert status == 303, html
    return campaign_path, headers["Location"]


def chosen_form(review, comparison_path):
    app, url = review
    _, _, html = request(url, path=comparison_path)
    fields = form(html, comparison_path + "/shortlists")
    view = app.campaigns.read_comparison(comparison_path.rsplit("/", 1)[1], app.actor)
    candidate = next(c for c in view["candidates"] if c["body"] and c["body"]["judgments"][0]["state"] == "satisfied")
    chosen = Selection(candidate["candidate_id"], "CITED_HUMAN_REASON",
                       tuple(candidate["body"]["judgments"][0]["support_ids"]), tuple(candidate["body"]["unknowns"]))
    fields.update(selected=[chosen.candidate_id], action=["confirm"], reviewed=["yes"])
    fields[f"reason_{chosen.candidate_id}"] = [chosen.reason]
    fields[f"support_{chosen.candidate_id}"] = list(chosen.support_ids)
    fields[f"unknown_{chosen.candidate_id}"] = list(chosen.acknowledged_unknowns)
    return fields, chosen


def test_browser_forms_create_prepare_save_confirm_and_reopen_after_process_restart(review):
    app, url = review
    status, headers, html = request(url)
    assert status == 200 and "Create a brief" in html
    assert headers["Cache-Control"] == "no-store"
    campaign_path, comparison_path = prepare(review)
    _, _, html = request(url, path=comparison_path)
    assert "Rule-based draft" in html and "provisional" in html and "Original captions and provenance" in html
    assert "Translation pending" in html and "Open original source" in html
    assert "6819904612390634498" in html and "both" in html
    fields, chosen = chosen_form(review, comparison_path)
    fields["action"] = ["draft"]
    status, headers, html = request(url, "POST", comparison_path + "/shortlists", fields)
    assert status == 303, html
    draft_path = headers["Location"]
    _, _, html = request(url, path=draft_path)
    assert "CITED_HUMAN_REASON" in html and "named-reviewer" in html
    draft_id = draft_path.rsplit("/", 1)[1]
    _, _, html = request(url, path=comparison_path + "?shortlist_id=" + draft_id)
    confirmed_fields = form(html, comparison_path + "/shortlists")
    assert confirmed_fields["selected"] == [chosen.candidate_id]
    assert confirmed_fields[f"reason_{chosen.candidate_id}"] == ["CITED_HUMAN_REASON"]
    confirmed_fields.update(action=["confirm"], reviewed=["yes"])
    status, headers, html = request(url, "POST", comparison_path + "/shortlists", confirmed_fields)
    assert status == 303, html
    confirmed_path = headers["Location"]
    confirmed_id = confirmed_path.rsplit("/", 1)[1]
    expected = app.campaigns.read_shortlist(confirmed_id, app.actor)
    assert expected["status"] == "confirmed" and expected["version"] == 2
    campaign = app.campaigns.read_campaign(campaign_path.rsplit("/", 1)[1], app.actor)
    assert len(campaign["comparisons"]) == 1 and len(campaign["shortlists"]) == 2
    assert app.campaigns.read_comparison(comparison_path.rsplit("/", 1)[1], app.actor)["actor_kind"] == "automation"

    env = {**os.environ, "SMI_DATABASE_URL": app.campaigns.db.dsn, "SMI_DATABASE_SCHEMA": app.campaigns.db.schema}
    process = subprocess.Popen([sys.executable, "-m", "smi_review", "--port", "0", "--actor", "named-reviewer"],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([process.stdout], [], [], 15)[0], "review server did not start"
        address = process.stdout.readline().split(" · ", 1)[0].split(": ", 1)[1].strip()
        status, _, reopened = request(address, path=confirmed_path)
        assert status == 200 and "CITED_HUMAN_REASON" in reopened and "confirmed" in reopened
        assert expected["recorded_at"] in reopened and expected["recorded_by"] in reopened
        assert "Shortlist revision 2" in reopened
        assert app.campaigns.read_shortlist(confirmed_id, app.actor) == expected
    finally:
        process.terminate()
        process.communicate(timeout=10)


@pytest.mark.parametrize("hostname", ["127.0.0.1", "localhost"])
def test_campaign_form_policy_preserves_origin_and_creation(review, hostname):
    app, address = review
    url = address.replace("127.0.0.1", hostname)
    status, headers, html = request(url, path="/campaigns/new")
    assert status == 200
    fields = form(html, "/campaigns")
    fields.update(objective=["Create a campaign from the browser form"], target_market=["JP"])
    # Fetch serializes a non-CORS form POST's Origin as null under no-referrer.
    origin = "null" if headers["Referrer-Policy"] == "no-referrer" else url
    status, saved_headers, html = request(url, "POST", "/campaigns", fields,
                                          {"Origin": origin, "Sec-Fetch-Site": "same-origin"})
    assert status == 303, html
    assert headers["Referrer-Policy"] == "same-origin"
    assert saved_headers["Referrer-Policy"] == "same-origin"
    status, _, html = request(url, path=saved_headers["Location"])
    assert status == 200 and "Create a campaign from the browser form" in html
    assert len(app.campaigns.list_campaigns(app.actor)) == 1


@pytest.mark.parametrize(("headers", "status"), [
    ({"Host": "foreign.example"}, 403),
    ({"Origin": "null"}, 403),
    ({"Content-Type": "application/json"}, 415),
    ({"Content-Length": "invalid"}, 400),
    ({"Content-Length": "0"}, 413),
])
def test_http_rejections_offer_trusted_recovery_navigation(review, headers, status):
    app, url = review
    _, _, html = request(url, path="/campaigns/new")
    fields = form(html, "/campaigns")
    fields.update(objective=["UNSAVED_REJECTED_INPUT"], target_market=["JP"])
    actual, _, html = request(url, "POST", "/campaigns", fields, headers)
    assert actual == status
    assert "This request was not saved" in html
    assert f'href="{url}/">Open campaign workspace</a>' in html
    assert f'href="{url}/campaigns/new">Create a brief</a>' in html
    assert "foreign.example" not in html and "UNSAVED_REJECTED_INPUT" not in html
    assert not app.campaigns.list_campaigns(app.actor)
    assert request(url, path="/campaigns/new")[0] == 200


@pytest.mark.parametrize("missing", ["objective", "target_market", "platforms", "criterion_0_label"])
def test_invalid_brief_is_visible_and_preserves_human_inputs(review, missing):
    app, url = review
    _, _, html = request(url, path="/campaigns/new")
    fields = form(html, "/campaigns")
    fields.update(objective=["KEEP_THIS_EDIT"], target_market=["JP"])
    fields[missing] = [""]
    status, _, html = request(url, "POST", "/campaigns", fields)
    assert status == 422 and "Action needs attention" in html
    if missing != "objective":
        assert "KEEP_THIS_EDIT" in html
    assert not app.campaigns.list_campaigns(app.actor)


@pytest.mark.parametrize("attack", ["host", "origin", "null_origin", "cross_site", "csrf", "actor", "json"])
def test_http_boundary_rejects_foreign_or_forged_decision_writes(review, attack):
    app, url = review
    _, _, html = request(url, path="/campaigns/new")
    fields = form(html, "/campaigns")
    fields.update(objective=["Human question"], target_market=["JP"])
    headers = {}
    if attack == "host":
        headers["Host"] = "foreign.example"
    elif attack == "origin":
        headers["Origin"] = "https://foreign.example"
    elif attack == "null_origin":
        headers["Origin"] = "null"
    elif attack == "cross_site":
        headers["Sec-Fetch-Site"] = "cross-site"
    elif attack == "csrf":
        fields["csrf"] = ["無効なトークン"]
    elif attack == "actor":
        fields["actor"] = ["forged-human"]
    else:
        headers["Content-Type"] = "application/json"
    status, _, _ = request(url, "POST", "/campaigns", fields, headers)
    assert status in {403, 415, 422}
    assert not app.campaigns.list_campaigns(app.actor)


def test_http_retry_and_stale_save_preserve_edits_without_overwriting(review):
    app, url = review
    _, comparison_path = prepare(review)
    fields, chosen = chosen_form(review, comparison_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: request(url, "POST", comparison_path + "/shortlists", fields), range(2)))
    assert all(status == 303 for status, _, _ in replies)
    assert len({headers["Location"] for _, headers, _ in replies}) == 1
    stale = copy.deepcopy(fields)
    stale["request_id"] = ["stale-browser-save"]
    stale[f"reason_{chosen.candidate_id}"] = ["PRESERVE_CONFLICT_EDIT"]
    status, _, html = request(url, "POST", comparison_path + "/shortlists", stale)
    assert status == 409 and "PRESERVE_CONFLICT_EDIT" in html and "shortlist_version_conflict" in html
    assert form(html, comparison_path + "/shortlists")["expected_version"] == ["0"]
    unchanged = app.campaigns.read_shortlist(replies[0][1]["Location"].rsplit("/", 1)[1], app.actor)
    assert unchanged["selected"][0]["reason"] == "CITED_HUMAN_REASON"


def test_confirmation_requires_reviewer_acknowledgement_and_current_brief(review):
    app, url = review
    campaign_path, comparison_path = prepare(review)
    fields, _ = chosen_form(review, comparison_path)
    fields.pop("reviewed")
    status, _, html = request(url, "POST", comparison_path + "/shortlists", fields)
    assert status == 422 and "human_review_acknowledgement_required" in html
    _, _, html = request(url, path=campaign_path + "/edit")
    revision = form(html, campaign_path + "/briefs")
    revision["objective"] = ["Successor question"]
    assert request(url, "POST", campaign_path + "/briefs", revision)[0] == 303
    fields["reviewed"] = ["yes"]
    status, _, html = request(url, "POST", comparison_path + "/shortlists", fields)
    assert status == 409 and "brief_version_conflict" in html
    assert app.campaigns.read_campaign(campaign_path.rsplit("/", 1)[1], app.actor)["shortlist_version"] == 0


def test_withdrawal_hides_captions_and_saved_or_submitted_reasons(review):
    app, url = review
    _, comparison_path = prepare(review)
    fields, chosen = chosen_form(review, comparison_path)
    status, headers, _ = request(url, "POST", comparison_path + "/shortlists", fields)
    assert status == 303
    view = app.campaigns.read_comparison(comparison_path.rsplit("/", 1)[1], app.actor)
    candidate = next(c for c in view["candidates"] if c["candidate_id"] == chosen.candidate_id)
    source = app.evidence.read(DATASET, app.actor)
    member = next(m for m in source["members"] if m["observation_id"] == candidate["body"]["observations"][0])
    caption = next(a["value"] for a in member["assertions"] if a["field"] == "caption")
    with app.campaigns.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s",
                           (Jsonb({**member["policy"], "revoked": True}), member["observation_id"]))
    _, _, html = request(url, path=headers["Location"])
    assert "CITED_HUMAN_REASON" not in html and "Review required" in html
    assert caption not in html
    assert "named-reviewer" in html and candidate["account_key"]["native_id"] in html
    fields["request_id"] = ["save-after-withdrawal"]
    fields["expected_version"] = ["1"]
    fields[f"reason_{chosen.candidate_id}"] = ["CITED_HUMAN_REASON " + caption]
    status, _, html = request(url, "POST", comparison_path + "/shortlists", fields)
    assert status == 422 and "CITED_HUMAN_REASON" not in html and caption not in html
    with app.campaigns.db.connect() as connection:
        row = connection.execute("SELECT reason,reason_withdrawn FROM shortlist_selections").fetchone()
    assert row == {"reason": None, "reason_withdrawn": True}


def test_escaped_data_and_fixed_asset_routes(review):
    _, url = review
    campaign_path = start(review, '<img src=x onerror="alert(1)">')
    _, _, html = request(url, path=campaign_path)
    assert '<img src=x' not in html and '&lt;img src=x' in html
    assert '<script>' not in marked_caption('<script>alert(1)</script>', [])
    assert 'href=' not in source_link('javascript:alert(1)')
    status, headers, _ = request(url, path="/static/review.css")
    assert status == 200 and headers["Content-Type"].startswith("text/css")
    assert request(url, path="/static/../app.py")[0] == 404


def test_listing_interfaces_are_workspace_scoped_and_content_free(review):
    app, _ = review
    assert app.evidence.list_sets(app.actor)[0]["posts"] == 19
    assert "captions" not in json.dumps(app.evidence.list_sets(app.actor))
    assert app.knowledge.list_catalogs(app.actor)[0]["catalog_id"] == "beauty-caption-lexicon-v1"
    foreign = ActorContext("foreign", HUMAN.actor_id, "human")
    for call in (app.evidence.list_sets, app.knowledge.list_catalogs, app.campaigns.list_campaigns):
        with pytest.raises(EvidenceError, match="workspace_access_denied"):
            call(foreign)


def test_missing_setup_is_sanitized_and_empty_workspace_guides_loading(stack):
    db = stack[0]
    app = ReviewApp(db)
    with running(app) as url:
        status, _, html = request(url)
        assert status == 503 and "database_unavailable" in html
        assert db.dsn not in html and db.schema not in html
        KnowledgeStore(db).migrate()
        CampaignStore(db).migrate()
        status, _, html = request(url)
        assert status == 200 and "Load your evidence first" in html and "No campaigns yet" in html
        status, _, html = request(url, path="/campaigns/new")
        assert status == 200 and "Offline sample setup" in html
