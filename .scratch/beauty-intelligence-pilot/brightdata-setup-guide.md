# Bright Data setup for the TikTok ingestion pilot

This project uses Bright Data's **TikTok Scraper API** with a normal Bright Data API key. The key is already present in the local `.env` as `BRIGHTDATA_API_TOKEN`; do not replace it unless it is expired or belongs to a different account. Bright Data's [TikTok quickstart](https://docs.brightdata.com/products/scrapers/tiktok/quickstart) documents an account and API key as its prerequisites. It does not document a separate scraper activation, proxy zone, TikTok developer app, or dataset-creation step for these ready-made endpoints.

**Latest check, 2026-10-12:** after the builder completed API setup, one profile request and one ten-post request both returned HTTP 200 and were ingested into the local database. The earlier **"Customer is not active"** response was not reproduced. See the [retry and mapper-correction report](../brightdata-source-readiness/api-retry-2026-10-12.md). Sections 4 and 5 describe the earlier block and are troubleshooting steps if it recurs; another diagnostic scrape is not needed to establish that this retry succeeded.

Run the interactive account checklist from the repository root if you prefer guided steps:

```bash
./.scratch/beauty-intelligence-pilot/brightdata-setup-wizard.sh
```

## 1. Verify the API key

1. Sign in to [Bright Data Account settings → Users and API keys](https://brightdata.com/cp/setting/users).
2. In the **API key** section, check that the existing key is active and has an API-using permission. Bright Data says the **User** permission enables API usage. The separate **Agent API keys** section is for MCP/agents and is not the credential this adapter expects.
3. If no usable key exists, click **Add API key**, choose your user, **User** permission and an expiration date, then **Save**. Copy the new key when shown; Bright Data shows it only once. Replace only the `BRIGHTDATA_API_TOKEN=` value in the local `.env`. Never paste the key into a manifest, chat, or a command-line argument. The [authentication guide](https://docs.brightdata.com/api-reference/authentication) describes these controls.

The existing `BRIGHTDATA_API_TOKEN` does **not** need a TikTok Business or TikTok Developer account. Bright Data's API accepts it in the `Authorization: Bearer` header.

## 2. Check free usage before another request

1. Open [billing settings](https://brightdata.com/cp/billing/settings) and locate your current free-credit balance and usage in the account dashboard. The exact screen can vary by account, so follow any account navigation if the link redirects.
2. For this free-only local test, verify that free credits remain, no funds are deposited, and auto-recharge is off. Do not add a payment method or select a paid plan just to run this test.

Bright Data currently advertises **5,000 free monthly credits** for new accounts, shared with its Scraper API and other eligible products. It says requests stop with an error when credits run out and there is no deposited balance; deposited funds allow pay-as-you-go usage to continue. Check the dashboard's actual balance before assuming the full amount is still available. [Bright Data TikTok pricing and free-tier FAQ](https://brightdata.com/products/web-scraper/tiktok).

## 3. Use the two ready-made TikTok datasets

These are the only Bright Data datasets the current local adapter needs. The `gd_lkf2st302ap89utw5k` ID in your example is the **comments** dataset, which this pilot does not currently use:

| Purpose | Dataset ID | Input | Result needed |
| --- | --- | --- | --- |
| Creator profile | `gd_l1villgoiiidt09ci` | `https://www.tiktok.com/@username` | Profile and public counts |
| Recent posts by creator | `gd_m7n5v2gq296pex2f5m` | The same profile URL, `num_of_posts: 10` | Dates, captions, URLs, engagement counts |

Both are selected through `POST https://api.brightdata.com/datasets/v3/scrape?dataset_id=...&format=json` using the same key. See the [TikTok endpoint guide](https://docs.brightdata.com/products/scrapers/tiktok/send-first-request) and [Posts by Profile Fast reference](https://docs.brightdata.com/api-reference/scrapers/social-media-apis/tiktok-posts-by-profile-fast-api-collect-by-url). No endpoint IDs need to be copied into `.env`: the adapter already defines them.

## 4. Resolve the inactive account response

Your direct Scraper API test returned **"Customer is not active"**. This strongly suggests an account-status block, but Bright Data does not publicly document that exact error's conditions, so do not assume a specific cause or keep changing dataset IDs.

1. Sign in to the [Bright Data dashboard](https://brightdata.com/cp/setting/users). Look for an account-verification email, activation prompt, or onboarding task. Complete any available account-verification action that fits your free-only plan.
2. If the dashboard offers no resolution, use [Bright Data support](https://brightdata.com/contact) or the dashboard's support option. Ask them to check why your new account returns `Customer is not active` for `POST /datasets/v3/scrape` and whether they can enable the free TikTok Scraper API tier. Include the HTTP status, dataset ID and time if known. **Do not include your API token.**
3. Wait until the account is active before another scrape request. Bright Data's [TikTok quickstart](https://docs.brightdata.com/products/scrapers/tiktok/quickstart) says a new account and API key should normally suffice; the provider needs to explain why this account differs.

## 5. Diagnose the earlier HTTP 400 after account activation

Two previous profile requests for `@maronayannyan` returned HTTP 400 on **2026-09-30 at 05:04 and 05:05 UTC**. One used the API reference's `{"input": [...]}` body; the other used the TikTok quickstart's top-level array. Neither returned a profile, and the provider error text was not saved. The docs currently show both body shapes; the status alone cannot establish whether the problem is account access, input validation, or something else.

First, inspect any Scraper API request/error history shown in your Bright Data dashboard for those times. If you cannot see a reason there, Bright Data has confirmed the account is active, and you confirmed step 2, run **one** direct quickstart request from the repository root. This may use free credits if it returns a record. It tests Bright Data's documented sample profile separately from the project's creator and prints an error body without printing the key:

```bash
uv run --env-file .env python - <<'PY'
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

token = os.environ.get("BRIGHTDATA_API_TOKEN", "").strip()
if not token:
    raise SystemExit("BRIGHTDATA_API_TOKEN is missing from .env")

request = Request(
    "https://api.brightdata.com/datasets/v3/scrape"
    "?dataset_id=gd_l1villgoiiidt09ci&format=json",
    data=json.dumps([{"url": "https://www.tiktok.com/@tiktok"}]).encode(),
    headers={"Authorization": f"Bearer {token}",
             "Content-Type": "application/json"},
    method="POST",
)
try:
    with urlopen(request, timeout=70) as response:
        status, body = response.status, response.read(4096)
except HTTPError as error:
    status, body = error.code, error.read(4096)

print(f"HTTP {status}")
if status == 200:
    print("The profile API returned data; do not paste the full profile response.")
else:
    print(body.decode("utf-8", "replace").replace(token, "[REDACTED]")[:2000])
PY
```

`200` confirms the sample profile route works; `202` means Bright Data accepted the job but returned a snapshot ID for later retrieval. For `400`, copy the **status and error body only** into the next conversation message. For `401` or `403`, check the key's validity, expiry, and permission in step 1. Do not run repeated trial requests while the reason remains unknown. Bright Data's [quickstart](https://docs.brightdata.com/products/scrapers/tiktok/quickstart) documents the 200/202 and 401/403 meanings.

Once the 400 is understood and the documented sample works, run the existing bounded pipeline for the chosen creator:

```bash
uv run --env-file .env smi-ingest ingest examples/live/brightdata-tiktok-manifest.json --max-requests 12
```

The manifest asks for one profile and ten recent posts. The adapter makes at most two scrape POSTs for that creator and does not automatically retry a paid POST. If it reports a pending snapshot, use `smi-ingest resume RUN_ID` instead of starting another ingestion. The pipeline result will show whether the data mapped into the local canonical database.
