# Primary model-provider contract verification

Verified 2026-10-20 through read-only official documentation. This is preparation for ticket 13, not evidence of live API execution, account access, pricing, or human quality validation. The user permits primary-documentation lookups only; provider calls remain simulated.

## Selected bounded route

Use one explicitly configured OpenAI Responses route. The [create reference](https://developers.openai.com/api/reference/resources/responses/methods/create) specifies HTTPS POST to `https://api.openai.com/v1/responses` with bearer authentication. Structured text configuration belongs under `text.format`. `max_output_tokens` covers generated visible and reasoning tokens. The response usage object reports input, output, total, cached-input and reasoning token counts; usage can be absent. The `store` option defaults to true when omitted. These are contract facts, not evidence that a particular model or account supports a configuration.

The [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs) describes strict JSON-schema text output. Fields must be required; nullable values can express optional information. Object schemas disallow additional properties. Refusals and incomplete responses need separate handling rather than assuming every response contains usable schema-conforming content.

The [token-counting guide](https://developers.openai.com/api/docs/guides/token-counting) documents a separate input-count operation with the same input format as Responses. Counts include request structure. Local plain-text tokenization does not establish an exact count for the complete request. Reported generated-token usage can exceed visible text, including non-visible formatting tokens; output limits cover those generated tokens too.

## Repository implementation implications

These are design implications to check against the existing cost and campaign contracts during ticket 13:

- Require explicit model, classification, rates, credential/configuration and finite request/output bounds. Do not infer current pricing or model eligibility from examples. Mark simulated configuration and rates as synthetic.
- Use one bounded request, no tools, explicit `store=false`, no implicit retries, and no hidden live token-count request. An input-cost bound needs a defensible configured measurement policy; character counts alone must not be described as exact provider token counts.
- Acquire cost admission before transport. Use provider-reported usage for settlement, including failed interpretation/refusal cases when valid usage is available. Missing/invalid usage or a transport outcome with uncertain consumption must follow existing uncertainty/reconciliation semantics, never become zero-cost success.
- Validate payload shape, supported campaign criteria, revision linkage, and authority boundaries independently of provider schema compliance. Model text is data; it cannot create task authority or broaden constraints.
- Preserve truthful unavailable/blocked states for missing configuration. Keep raw credential/prompt/response data out of operational cost records. Default PostgreSQL/HTTP tests use simulated transport, including malformed output, refusal, incomplete output, missing usage, admission rejection and authority-forgery cases.
- Record explicit provider/method/schema versions in the resulting interpretation. No live receipt or language/usefulness result exists from this research.

## Retrieval evidence

The web reader opened both guides as HTML. The create-reference HTML exceeded its 4 MiB limit; Markdown retrieval through that reader failed because it did not support the content type. Bounded HTTPS GETs to the three corresponding `.md` URLs on `developers.openai.com` succeeded (506646, 136333 and 22672 bytes). Temporary source cache: `/tmp/smi-primary-contract-docs/`. No model endpoint was called.
