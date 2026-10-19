# Evidence and marketer quality review

Technical correctness, translation-assisted language review and marketer usefulness are separate gates. Passing repository checks cannot supply human judgments or validate Japanese-original semantics. Review execution records belong in `.scratch/`; these are the durable review rules.

The same-corpus procedure and recording tool below evaluate the implemented local pilot and require actual human evaluation inputs. They do not establish a mandatory runtime human-review gate for every shortlist. The [operational target](functional-requirements.md) permits automatic shortlist persistence; its methods still need quality evaluation and its authority/publication/spending boundaries need technical verification.

## Same-corpus two-task procedure

Use one frozen dataset/digest for a product/topic investigation and a campaign. Record a named reviewer, review time, task order and prior exposure. Before assisted work, record the marketer's manual monitoring answer and account keep/exclude/defer choices, task time and inspected-post count. Prior development-set exposure must be disclosed; the review is not a controlled causal experiment.

Then save one investigation with a concrete source-backed finding and limits, and create/review a campaign with an exploratory shortlist or deliberate deferral. Reopen both records. Record task times without a speed threshold, inspected posts, missing evidence, corrections, useful observations, a reusable candidate decision and the reasons for those judgments.

Usefulness requires an actual human finding that adds useful understanding and a reusable keep/exclude/defer decision, with no uncorrected material unsupported claim or translation error detected in the chosen process. Material means an error changes a finding, candidate decision or its stated evidence/limits. Unsupported selection to manufacture a pass is invalid. No sales-improvement claim follows from this corpus.

## Language review

`smi-ingest review-packet KNOWLEDGE_RUN_ID` produces an on-demand policy-checked packet of original captions, exact interpretation spans, proposed labels and pending translation/reviewer fields. Record the translation, translator/model/method version, source assertion/observation, supported/unsupported/ambiguous/not-assessable label, ambiguity and material errors/corrections for the reviewed set.

Translation-assisted references remain provisional development-set annotations. Record denominators and exact reviewed membership; no numeric Japanese-original accuracy threshold or generalization claim is invented. Japanese-original accuracy remains `not_validated` until qualified original-language adjudication occurs. A model's own confidence or repeated translation is not that validation.

## Recording and assessment

[`tools/pilot_evaluation.py`](../tools/pilot_evaluation.py) initializes an unanswered review JSON and assesses recorded input. It resolves insight/finding/shortlist links against current public readers, requires the same dataset/digest and human attribution, checks reviewed caption references and keeps unavailable support from counting toward a pass. It never fills baseline, task times, translations or usefulness judgments automatically.

```bash
mkdir -p .scratch/evaluation
uv run --locked python tools/pilot_evaluation.py .scratch/evaluation/marketer-review.json --init
PYTEST_ADDOPTS="--junitxml=.scratch/evaluation/technical-results.xml" uv run --locked python tools/check.py
uv run --locked python tools/pilot_evaluation.py .scratch/evaluation/marketer-review.json \
  --technical-results .scratch/evaluation/technical-results.xml \
  --output .scratch/evaluation/status.json
```

Initialization refuses to overwrite an existing human record. Omit `--init` when one already exists. Technical status comes from actual JUnit results; its scope is the automated checks, with live visual/semantic review separate. Missing input yields `pending`; an uncorrected material defect yields `failed`. Overall passes only when all three gates pass, and even then Japanese-original accuracy remains unvalidated. Local actor context is trusted operator attribution, not hosted identity verification.

Create these execution records when conducting a real review; an unanswered template or an obsolete technical report need not be retained as project state. No actual marketer usefulness/language result is established by the current repository.

The review JSON/status contains evaluation history, not product architecture. Keep source excerpts/translations within the permitted review environment; operator-managed exports are not automatically purged. Use fresh policy-aware readers when reviewing rather than treating saved copied text as current evidence.

## Accepted future operational checks

These are required validation scenarios for future implementation, not tests already passed by the current pilot:

| Scenario | Expected behavior |
| --- | --- |
| Agent saves a ranked recommendation | Persists an attributed shortlist without a human actor, approval or review; no human confirmation is fabricated. |
| Eligible account has incomplete profile | Stable identity and permitted ingested support allow recommendation; missing attributes remain explicit. Reference-only unregistered seeds are excluded. |
| Campaign coverage is insufficient | A bounded discovery task is submitted automatically. Completion notifies/offers regeneration; saved results do not change until explicit regeneration. |
| Assistant requests external enrichment | Exact approved scope is required server-side; forged task origins or expanded queries cannot bypass approval. |
| Retrieval succeeds but ingestion/publication fails | No answer uses the un-ingested response and no notification claims usable KB completion. |
| X anomaly needs context | Uses recorded monitoring evidence and existing KB context, without full ingestion of every post or follow-up external searches. |
| Metered costs approach a configured ceiling | Competing tasks share admission/accounting, pause further chargeable work at the allowance, and reconcile actual charges without duplicate accounting. Meter lag/charge bounds are visible. |
| Cost cannot be derived reliably | Remains a labeled forecast; it does not become zero or a claim of enforced monetary control. |
| Evidence is withdrawn | Generated shortlist, assistant, graph and alert copies respect their source dependencies and expose unavailable support rather than reconstructing denied wording. |
