from email.message import Message
from io import BytesIO
from urllib.response import addinfourl

import pytest

from smi_ingestion.adapters.tiktok_oembed import TikTokOEmbedTransport
from smi_ingestion.adapters.tiktok_web import TikTokWebTransport


@pytest.mark.parametrize("transport,content_type", [
    (TikTokWebTransport(), "text/html"),
    (TikTokOEmbedTransport(), "application/json"),
])
def test_redirect_does_not_dispatch_an_uncounted_http_request(monkeypatch, transport, content_type):
    dispatched = []

    def fake_https_open(self, request):
        dispatched.append(request.full_url)
        headers = Message()
        headers["Content-Type"] = content_type
        status = 302 if len(dispatched) == 1 else 200
        if status == 302:
            separator = "&" if "?" in request.full_url else "?"
            headers["Location"] = request.full_url + separator + "redirected=1"
        response = addinfourl(BytesIO(b"{}"), headers, request.full_url, status)
        response.msg = "Found" if status == 302 else "OK"
        return response

    monkeypatch.setattr("urllib.request.HTTPSHandler.https_open", fake_https_open)
    response = transport.fetch("https://www.tiktok.com/@example_creator", 1024)
    assert len(dispatched) == 1
    assert response.status == 302
