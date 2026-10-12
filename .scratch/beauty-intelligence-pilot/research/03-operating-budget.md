# Local-first operating envelope within USD 100/month

Research date: 2026-09-28. All linked official pages were opened on this date. Parent: [pilot map](../map.md). Ticket: [Establish a local-first operating envelope within USD 100 per month](../issues/03-research-operating-budget.md).

## Finding

A bounded, text-first pilot is plausibly compatible with the eventual **USD 100 total monthly operating envelope**. The worked example below estimates **$5.51/month for model processing** and **$19.91/month including a small hosted server and backups**, before data acquisition, other services, tax, and contingency. This is arithmetic feasibility, not demonstrated performance or source access. A paid data minimum can invalidate the envelope even when model costs are small.

Start on the builder's existing computer, with files and a local database, manual imports of obtainable evidence, and deliberate processing runs. No new recurring infrastructure subscription is necessary for this shape. An existing off-device backup destination is assumed; if absent, its acquisition or subscription is an additional cost. Local electricity, internet, hardware wear, and the builder's time are real but unpriced here. Local operation does not provide an always-on shared service.

The providers below are **pricing illustrations only**. None is selected, purchased, configured, or authorized by this note. In particular, the user has not set a development LLM allowance. Do not interpret the proposed active-operation allocations as development spend approval.

## Verified rates versus proposed amounts

Prices are USD, before any applicable tax or currency conversion. No promotional credits, prompt-cache savings, or batch discounts are needed for the calculation.

| Item | Verified public price | Official source |
| --- | --- | --- |
| Illustrative text model, GPT-4.1 mini | $0.40 per million input tokens; $1.60 per million output tokens | [Model pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini) |
| Optional text-embedding-3-small | $0.02 per million input tokens | [Embedding model pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small) |
| Illustrative DigitalOcean Basic VM | 1 vCPU, 2 GiB RAM, 50 GiB SSD, 2,000 GiB transfer: $12/month | [Droplet pricing](https://www.digitalocean.com/pricing/droplets) |
| Weekly VM backup | 20% of VM price; here $12 × 0.20 = $2.40/month | [Droplet backup pricing](https://www.digitalocean.com/pricing/droplets) |
| Optional independent object backup, Cloudflare R2 Standard | 10 GB-month, 1 million Class A and 10 million Class B operations/month free; then $0.015/GB-month, $4.50/million Class A, $0.36/million Class B; internet egress free | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) |

This deliberately uses an inexpensive, documented model as a cost basis rather than selecting the newest model. Japanese extraction quality, evidence grounding, and suitability for the marketer workflow still require evaluation. If another model is needed, substitute its rates and rerun the calculation before using it. API-key usage follows API pricing; an existing ChatGPT/Codex subscription must not be treated as credit paying for this application's API calls. [Official OpenAI subscription/API pricing distinction](https://learn.chatgpt.com/docs/pricing)

## Bounded text workload and arithmetic

These are **proposed planning assumptions**, not observed demand or approved quotas: one builder and one pilot marketer; at most 2,000 newly processed evidence records and 100 synthesis/report runs per month; one extraction per new or changed record; no full-corpus reprocessing on every report. A record may be a post plus a bounded comment excerpt or a review, provided the selected source permits obtaining it and the planned model processing. This does not promise 2,000 accessible records. The [access investigation](02-affordable-data-access.md) documents source-specific analytical-use gates; this calculation does not assume those have been satisfied.

All input budgets include instructions, source text, retrieved context, and schemas. Japanese/Korean text is counted in actual model tokens, not converted from an English words-per-token estimate. Oversized records must be split, sampled explicitly, or deferred; extra chunks count as extra calls.

| Work | Input tokens/month | Output tokens/month | Calculation | Cost |
| --- | ---: | ---: | --- | ---: |
| 2,000 extractions, each at most 3,000 input / 500 output | 6,000,000 | 1,000,000 | 6 × $0.40 + 1 × $1.60 | $4.00 |
| 100 reports, each at most 8,000 input / 1,500 output | 800,000 | 150,000 | 0.8 × $0.40 + 0.15 × $1.60 | $0.56 |
| Bounded evaluation/retry pool, 20% of above tokens | 1,360,000 | 230,000 | 1.36 × $0.40 + 0.23 × $1.60 | $0.912 |
| Optional embeddings: 2,000 × 1,000 source tokens plus 100 × 200 query tokens | 2,020,000 | — | 2.02 × $0.02 | $0.0404 |
| **Model total** | | | **$4 + $0.56 + $0.912 + $0.0404** | **$5.5124** |

Embeddings are optional: start with structured filters and local text search if sufficient. This price buys vector generation, not a hosted vector database. Store any vectors in the same local/VM data store and include them in its storage and backup limits. Re-embedding a changed corpus is new usage.

A development sample one tenth this size—200 extractions, 10 reports, proportional retries and embeddings—has an illustrative API cost of **$0.55124**, plus any source cost. This is a cost estimate, not a proposed monthly subscription or a spend commitment. Repeated experiments consume the sample allowance again.

## Local and optional hosted shapes

| Dimension | Start locally | Optional hosted pilot |
| --- | --- | --- |
| Application | Existing computer; single application process, local job runner | One $12 VM; same application and one bounded worker |
| Persistent state | Local relational database plus evidence files | Database/files on included VM SSD; no managed DB required by this example |
| Access | Builder-operated sessions and exported pilot artifacts | Authenticated access for builder and initial marketer; concurrency limited to two user sessions, one processing job |
| Proposed storage ceiling | 1 GB live evidence/database, bounded logs | Same 1 GB logical dataset; leave OS/build/log headroom on VM disk |
| Backup | Existing independent disk/destination, or optional encrypted object backup | $2.40 weekly VM backup plus independent application-consistent encrypted daily export |
| Calculated recurring base | $5.51 at full worked text workload | $12 + $2.40 + $5.5124 = **$19.9124** |

For the object-backup example, retain seven daily exports, each **at most 1 GB including metadata**, and allow at most 10,000 writes/lists and 10,000 reads monthly. At a conservative 7 GB-month, storage is `max(7 − 10, 0) × $0.015 = $0`; both operation counts are inside R2 Standard's included quantities. If total retained data reaches 20 GB-month, storage becomes `(20 − 10) × $0.015 = $0.15`, with operation charges still dependent on usage. Cloudflare rounds up billable units; all buckets sharing the allowance must be counted. These are byte/operation limits, not claims about compression. [R2 billing units and allowances](https://developers.cloudflare.com/r2/pricing/)

Retain at least one validated backup until its successor is verified. Test restoration; a second copy on the same laptop or VM is not the independent backup assumed here. A daily export implies up to approximately one day of data loss between successful runs. The VM backup is supplemental system recovery, not a replacement for database-consistent exports.

The hosted shape is a hypothesis for low concurrency and queued text work. It needs a small load and restore test before adoption. It excludes local model inference, parallel browser farms, high availability, a second always-on environment, and large media archives. Prefer running heavy development builds locally. Failure to fit RAM or processing latency is a reason to reduce/defer work or rebudget, not to enable autoscaling silently.

## Proposed active-operation allocation

The following is a **budget envelope**, not a predicted invoice. It applies to the entire pilot, including every new required service. Local operation can avoid the server line; its savings remain unspent until deliberately reassigned.

| Category | Proposed maximum allocation/month | Interpretation |
| --- | ---: | --- |
| Hosting, persistent storage, backups, transfer | $20 | Worked hosted base is $14.40 before any object overage |
| Models, embeddings, model tools, evaluation and retries | $20 | Worked text usage is $5.51; media experiments consume this same allocation |
| Data/source access | $35 | **Single uncommitted reserve**; no source fee or access right established |
| Other required services | $5 | Domain amortization, email, monitoring or similar only if actually needed and fitting this amount |
| Tax, FX/card charges and incident contingency | $20 | Unspent buffer, not an extra workload budget |
| **Total** | **$100** | No category is added again elsewhere |

Scheduled service commitments plus metered consumption should stay at or below **$80 before tax**, preserving $20 for the final line. The worked hosted cost plus the full data and other-service reserves is `$19.9124 + $35 + $5 = $59.9124`; this is not $59.91 of confirmed spending. The difference to the caps is remaining headroom inside the allocations, not another reserve.

Unknown source fees are decisive. If a necessary source costs more than $35/month, has a large setup fee, or requires another paid subscription, this proposal must be reallocated explicitly or that route deferred. Avoid minimum annual contracts during access uncertainty. If a development assistant subscription is newly required for this project, count its actual project-attributable recurring cost in the total and reduce other allocations. Existing unrelated personal subscriptions are not assumed to fund the application and are not newly purchased here.

No tax rate, KRW/USD rate, or card fee is asserted. The actual supplier, billing location, business status, and payment method determine them. Reconcile the USD-equivalent total paid after conversion; reduce the pre-tax ceiling if the $20 reserve proves inadequate.

## Media and tool sensitivity

Media is disabled in the base calculation. The official estimated transcription rate for `gpt-4o-mini-transcribe` is $0.003/minute: 100 two-minute clips add about `$0.60`; 2,000 such clips add `$12`; 20,000 add `$120` for transcription alone. These estimates exclude acquisition, storage, visual analysis, and subsequent text processing. Actual token-based billing and measured sample costs remain the control. [OpenAI transcription pricing](https://developers.openai.com/api/docs/pricing)

Vision input is charged as tokens, with model, resolution and detail affecting the count. As a sensitivity assumption, if a measured image workload adds 1 million billable input tokens at the illustrative text-model rate, it adds $0.40 before prompts and outputs. That is **not** a guaranteed image count. Video frame sampling can multiply image calls; downloaded originals and frames can dominate storage and CPU. Start with a separately bounded, manually selected sample and measure it. [Official vision cost calculation](https://developers.openai.com/api/docs/guides/images-vision)

Built-in search is also outside the base. OpenAI web search lists $10/1,000 calls plus content tokens; 1,000 calls therefore introduce at least $10 of tool charges. It does not establish permission or access to social-platform data. Any such fee belongs to the existing model/tools allocation, while a separately contracted source belongs to the single data reserve. No hosted file-search storage, image generation, GPU, paid proxy, or crawler subscription is included. [OpenAI tool pricing](https://developers.openai.com/api/docs/pricing)

## Cost controls and failure behavior required before unattended operation

1. Maintain a persistent per-month ledger covering every provider. Reserve the worst-case permitted request cost **before** dispatch, including outstanding concurrent calls; reconcile returned usage afterward. Include fixed commitments, tool calls, duplicate attempts, and retention. Unknown or unpriceable work is deferred.
2. Enforce both the workload ceilings above and monetary ceilings. For the proposed active $20 model allocation, an illustrative application stop at $18 leaves reconciliation headroom; configure a provider hard limit no higher than $20 and alerts earlier. Development gets a separately explicit cap before paid automation; the active allocation is not its default.
3. Use model allowlists, output-token limits, maximum input sizes, one worker, idempotent content hashes, no recursive agent loops, and a finite retry pool. At the 20% retry/evaluation pool limit, defer additional work. Do not fail over to a more expensive model automatically.
4. On a cost limit, missing usage records, exhausted data quota, or repeated errors: stop paid dispatch, keep the job pending with its reason, and preserve existing evidence and saved outputs. Allow local reading/export/manual work. Never invent freshness or silently replace unavailable evidence with model guesses.
5. Disable automatic resource growth. Cap uploads, backup bytes, retention, and outbound transfer in the application; stop optional ingestion before the disk fills. Alert early enough to preserve backups. Reconcile provider dashboards at least weekly and before large runs.
6. OpenAI currently documents enforceable organization/project spend limits, with relevant `429` errors, **but enforcement can lag slightly**. Budget alerts alone do not stop requests. DigitalOcean explicitly says its spend alerts are **not caps**. Application admission control and spare budget are therefore still necessary. [OpenAI spend controls](https://developers.openai.com/api/docs/guides/spend-limits), [DigitalOcean spend alerts](https://docs.digitalocean.com/platform/billing/spend-alerts/)

## Decisions still needed

- What monthly development API cap is acceptable, distinct from the eventual $100 total?
- Which permitted source route supplies the first usable sample, and what are its actual recurring fees, quotas, retention conditions, and minimum commitments?
- Can the pilot begin with bounded text evidence and user-supplied excerpts, adding a small media sample only if the marketer task requires it?
- Is builder-operated local access sufficient initially, and is an independent backup destination already available?

Recheck rates before purchase or implementation and after any model/provider change. Source availability and useful Japanese-language output remain unverified; cheap token arithmetic cannot resolve either.
