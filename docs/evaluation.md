# Evidence and marketer quality review

Technical correctness, translation-assisted language review and marketer usefulness are separate gates. Passing repository checks cannot supply human judgments or validate Japanese-original semantics. Retain actual review evidence in its permitted review environment; these are the durable review rules. Unanswered templates and obsolete execution narratives need not be retained.

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

## Current human review readiness

Actual review is **pending**. Packet/export software and simulated test actors are not review receipts. Select or provision actual permitted saved records through their normal public workflows; a curated sample file alone is not an imported, selected, currently permitted review corpus.

A real review needs an actual named reviewer/attestation, timezone and prior exposure; identify qualified Japanese-original adjudication separately. Select exact permitted records before showing assisted results:

- A generated current-KB recommendation (model-ranked when assessing rank/rationale), its campaign/brief/comparison/shortlist and regeneration history.
- A saved KB answer with its exact query/input manifest and enrichment proposal/revision/digest, approval, task, completion and publication history.
- Quantitative and semantic X alerts, their assessment/topic/revision/window/baseline memberships and saved existing-KB context. X windows retain their own sampling/coverage/retention and do not silently become the TikTok corpus.
- The frozen dataset ID/digest and exact observations/assertions for the same-corpus investigation/campaign baseline. The legacy evaluator requires actual reviewer attribution on its linked human records; an operational generated shortlist and a human-confirmed shortlist are distinct records.

Record baseline-before-assisted observations honestly, with actual task order/times/counts, translations and translator/method/model attribution, useful finding, reusable candidate decision or deliberate deferral, missing evidence and real campaign/assistant/alert feedback. If prior assistance prevents a valid baseline, disclose it and leave that gate pending. Missing journey states remain limitations; do not reconstruct them as historical evidence. Quantitative-alert/journey feedback goes in the actual review record/session note because the operational packet tool supports recommendation, answer and semantic alert only.

Keep full selected/submitted/currently countable/unavailable denominators, negative/ambiguous/not-assessable judgments and material corrections. No actual human language/usefulness gate has passed. Japanese-original accuracy remains `not_validated` without qualified original-language adjudication; recorded annotations alone establish neither source truth nor generalized accuracy, causal speed or sales.

The [shared acceptance scenarios](implementation-spec.md#acceptance-scenarios) cover authority, eligibility, publication, recovery, costs and policy independently. Technical verification and the four quality dimensions below remain separate.

## Operational result-review packets

`OperationalReviews` in [`smi_review.quality`](../src/smi_review/quality/__init__.py) supplies a small public Python export/record/reopen contract for a saved generated current-KB recommendation, bounded KB answer or retained X semantic alert. [`tools/operational_quality.py`](../tools/operational_quality.py) exposes the same local journey. Existing `local-marketer-review-v1` same-corpus records and `tools/pilot_evaluation.py` remain unchanged; an operational packet does not replace the manual-before-assisted procedure.

Run the tool against the provisioned local result workspace. Every CLI action currently calls the review owner’s `migrate()`, including `read`; use public read-only owner operations for a strictly no-migration inventory. The named `--actor` is trusted operator attribution, not hosted identity verification. `SMI_DATABASE_URL`/`SMI_DATABASE_SCHEMA` select the database without being printed. Add `--include-synthetic` before the action only when deliberately reviewing simulated evidence.

```bash
uv run --locked python tools/operational_quality.py --actor ACTUAL_REVIEWER export answer ANSWER_ID --request-id EXPORT_REQUEST
uv run --locked python tools/operational_quality.py --actor ACTUAL_REVIEWER record PACKET_ID HUMAN_REVIEW.json --request-id REVIEW_REQUEST
uv run --locked python tools/operational_quality.py --actor ACTUAL_REVIEWER read PACKET_ID
```

Use `recommendation SHORTLIST_ID` or `semantic_alert ALERT_ID` instead of `answer ANSWER_ID` for the other result types. Python callers construct `OperationalReviews(db, workspace_id, recent=...)`, call `migrate()` once after the result-owner schemas exist, then `export(kind, result_id, actor, request_id=...)`, `record(packet_id, review, actor, request_id=...)` and `read(packet_id, actor)`. A supplied public `RecentMonitoring` must belong to the same database/workspace; it retains the configured retention clock. Production reads use the actual clock. No source/model transport or credentials are accepted by the review owner.

Export pins exact reviewed membership, all actual result-input support IDs/dependencies, original result IDs and method/model/schema versions. Original text, Unicode `[start,end)` spans and capture/source-publication/ingestion dates are read afresh through their public owners. Interpretation spans belong only to the exact selected publication bundle and source assertion. Each original text retains its subject identity and that subject's source publication date; absent/conflicting dates remain unknown. Packet export time does not refresh the source or supply a human review time. Results remain provisional observed/derived/generated judgments with their original limitations.

Copy only the returned `review_template` object into the human submission file. All its reviewer, time, translation, translator, label and material-error fields start unanswered. Supply actual values:

- `reviewer` must equal the trusted human actor; `attested` must be `true`. Supply an actual timezone-aware `reviewed_at` and the review `method_version`.
- `denominator` must equal the complete frozen `membership` count. `items` is a unique nonempty subset of those IDs; partial review retains the complete denominator and a pending completion status.
- Every item supplies `item_id`, the actual `translation`, a `translator` object with `actor_id`, `kind` (`human` or `automation`), `method_version` and `model_version` (required for automation; explicitly null for human translation), `label`, `ambiguity`, `material_error`, `error` and `correction`.
- Labels use the existing compatible wire vocabulary `supported`, `unsupported`, `ambiguous`, `not_assessable`. A material error requires an explicit description. Optional ambiguity/error/correction fields are explicitly null when absent. A correction is supplied text, never inferred from a label or another model call.
- `marketer_usefulness` stays null unless a human supplies `useful` (boolean), `rationale`, actual nonnegative `task_seconds` and actual `inspected_posts`. There is no speed target. Review submissions are bounded to 256 KiB.

Equal request retries reopen the same packet/record; changed retry bodies or authors conflict while support is available. New review requests append attributable serial revisions/corrections. Each packet admits at most 50 records and each workspace at most 5,000 packets; returned `bounds` states these limits. Exact retries remain recoverable at the limits; a new append/export beyond its limit is refused. `records` retains safe attribution/membership/history, and `review` exposes the latest currently permitted annotation body. `denominators` separately states original selected membership, submitted membership, currently countable reviewed membership and unavailable membership. `label_counts` counts only currently available annotations, including ambiguous and not-assessable items. No unsupported/unavailable item is silently counted as supported.

Export, record and read recheck current workspace, full input process/display/retention permission and derivation health through the owning public readers, including unselected/unresolved model inputs. Source locks last through local review commits. Any unavailable input withholds dependent result/annotation bodies and countable labels; retention loss permanently clears all retained annotation bodies for the reopened packet. Safe IDs, method/attribution metadata and purge tombstones remain. An unavailable record returns `recording_status: support_unavailable` before validating submitted annotations or checking retry conflicts, so required cleanup commits even for an invalid/conflicting submission. It appends no new review. A new unavailable export creates no packet and returns a source-free unavailable outcome; retention reconciliation also clears existing review copies for that exact result. Current readers never treat saved translations as replacement source evidence. This reconciliation occurs on these public operations, without a background deletion guarantee. Exported JSON and human submission files are operator-managed copies: keep them only in the source-permitted environment, remove them when required, and reopen before use.

The four `quality` dimensions deliberately have no automatic overall pass. `technical` remains pending in this contract; assess actual automated results independently. `translation_assisted` is pending for missing/partial review, failed for an explicit uncorrected material error, and recorded when the selected set has attributed annotations without such an error. Recorded describes the supplied review, not verified source truth or numeric model accuracy. `japanese_original` remains `not_validated`; this translation-assisted journey supplies no qualified original-language adjudication. `marketer_usefulness` is pending without actual human input, failed for an explicit negative judgment or uncorrected material error, and recorded for an explicit positive judgment. No source-truth, Japanese-original accuracy, generalization, causal speed or sales claim is inferred. Software tests using synthetic actors and translations are not actual human review receipts; real named review remains a separate prerequisite.
