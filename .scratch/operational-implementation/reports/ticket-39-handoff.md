# Ticket 39: actual human review handoff

Status: **claimed; ready-for-human; actual review pending**. This handoff contains no human evaluation receipt, translation, judgment or measured task result.

## Preparation plan

1. Read the authoritative ticket, resolved blockers, review rules and public interfaces. Complete.
2. Inspect only existing local saved records through public owners without migration, acquisition or new application records. Complete; no selectable examples discovered in the checked scope.
3. Record exact available selections or missing examples, then provide the current reviewer procedure and outstanding external inputs. Complete below.
4. Check only ticket 39 metadata, preserving prior software verification. Complete; local commit is the handoff boundary.

## Established constraints

- Branch `smi/operational-ticket-39` starts at `b75b8b6a454ae9abdb5f7f7450837b79d7801753`; blockers 20, 28, 32 and 38 are resolved.
- Fast-forwarded the coordinator's metadata-only review-baseline commit `3f6ab86e4f19ea248436d44653ff7ffd7f294ec9` before handoff. Ticket 39 changes are confined to its issue, this handoff and its inventory JSON.
- No named actual reviewer, approved result selection, manual baseline, translations or real feedback has been supplied. Actor strings, Git identity, synthetic software fixtures and model output cannot establish these inputs.
- Ticket 38 root shared verification passed 890 tests in 666.47 seconds (exit 0, session 22406). No source/test/product-contract changes or full-gate/build rerun belong to this metadata-only preparation.
- Operational packets supplement the unchanged `local-marketer-review-v1` same-corpus baseline-before-assisted procedure. Technical evidence, translation-assisted review, Japanese-original validation and marketer usefulness remain separate.
- Existing `tools/operational_quality.py` calls `migrate()` before every action, including `read`; do not invoke it for this no-migration inventory. Use public read-only owner operations against the explicit local database/workspace instead.
- Japanese-original accuracy stays `not_validated` without qualified original-language adjudication. No invented numeric accuracy, speed, sales or market claim is permitted.

## Preparation notes

- The initial blocker-20 filename guess did not exist; resolved the authoritative filename through the issue-file inventory and read it. No input or application state changed.
- A guessed `src/smi_review/config.py` path did not exist; current configuration is in the actual CLI/server code. No implementation change is needed.
- Later guessed annotation/task module paths did not exist; the actual public review contract is implemented in `quality/records.py`, and the assistant task composition is in its package initializer. These were read-path corrections only.
- The first offline `uv run` initialized this fresh worktree's ignored `.venv` and editable package. It did not run a verification wheel build or repository gate.

## Exact availability

[Inventory](ticket-39-inventory.json) records the public-operation results at **2026-10-29T09:26:06.927580+00:00**. Scope was explicitly `127.0.0.1:6543/smi`, schema `public`, workspace `local`; no environment-selected database/schema or credential lookup was used. The caller was `ticket-39-read-only-inventory`, kind `automation`, with PostgreSQL `default_transaction_read_only=on`. It is an inventory actor, not an actual reviewer.

| Public operation | Observed result | Selectable IDs / membership |
| --- | --- | --- |
| `EvidenceSetReader.list_sets` | `UndefinedTable`, SQLSTATE `42P01` | None discovered; dataset/digest/observation/assertion membership unavailable |
| `CampaignStore.list_campaigns` | `UndefinedTable`, SQLSTATE `42P01` | None discovered; campaign/brief/comparison/generated shortlist IDs unavailable |
| `MonitoringStore.list_investigations` | `UndefinedTable`, SQLSTATE `42P01` | None discovered; investigation/insight/finding IDs unavailable |
| `RecentMonitoring.list_topics` | `UndefinedTable`, SQLSTATE `42P01` | None discovered; topic/configuration/window/capture membership unavailable |
| `QuantitativeAlerts.notifications` | Empty list | No selectable notification/alert IDs; this operation also returns empty when its optional owner is uninstalled |
| `SemanticAlerts.notifications` | Empty list | No selectable notification/alert IDs; same optional-owner qualification |
| Saved KB answers / assistant enrichment | No ID supplied; `KnowledgeAssistant` has no public list operation | Not inspected by guessed UUID or private-table SQL; exact answer/journey/proposal/approval/task/publication IDs remain required |

This establishes only the checked local scope, not absence in other installations or schemas. No migration, import, seed, packet export, collector, question/model execution or application write occurred. No ephemeral test IDs were reused. The repository's curated 19-post/17-account snapshot is an available file asset, not an imported, selected, currently permitted review corpus or evidence of human validation.

## Inputs needed before review

The facilitator/reviewer must supply the following; no item has been supplied yet:

1. The actual reviewer's name or agreed attributable identifier, confirmation that they will perform/attest the review, review timezone and prior exposure (including development-set/results exposure). Identify any qualified Japanese-original adjudicator separately; otherwise keep that dimension unvalidated.
2. An existing permitted local database/schema/workspace and explicit result selection: one saved generated current-KB recommendation (ranked when evaluating rank/rationale), one KB answer with its assistant-enrichment journey/history, one quantitative X alert and one semantic X alert with their existing-KB investigation/context links. Record exact campaign/brief/comparison/shortlist, answer/query, proposal/revision/digest/approval/task/completion/publication, alert/assessment/topic/configuration/window/context IDs as applicable. Missing histories remain a review limitation rather than being reconstructed.
3. The permitted frozen dataset ID/digest and exact observation/assertion review membership for the unchanged same-corpus investigation/campaign procedure. Record each X baseline/detection/semantic window's exact start/end, captured member IDs and sampling/coverage/retention limits separately. An X window is not silently the same corpus as a TikTok snapshot; a current-KB query manifest is not a legacy frozen-dataset digest.
4. Actual baseline-before-assisted observations and actual later assisted feedback, translations and measurements described below. Selecting results or exporting packets cannot supply them. If a valid baseline cannot now be collected because of prior assistance, disclose that fact and keep the baseline gate pending.

The selection must be fixed and source-permitted before any quality claim. Record exclusions and reasons; do not choose an easier unsupported subset to manufacture success. Reopen original support through current public readers before use. Keep copied packets/translations only within their permitted environment; stale exports are not replacement evidence.

## Human session procedure

1. **Record identity and order first.** In a session note, record the actual reviewer, planned monitoring/campaign/assistant/alert task order, actual timezone-aware review times, prior exposure and corpus/window membership. Include the translation method/version and any language qualifications. Record actual deviations and start/end times as they occur.
2. **Complete the manual baseline before showing assisted results.** Using the selected original permitted corpus, the marketer records their monitoring answer and account-level keep/exclude/defer choices with reasons, actual elapsed seconds and inspected-post count. Record `completed_before_assistance` honestly. Do not backfill a plausible baseline from generated output.
3. **Perform the same-corpus assisted tasks.** Save/reopen an investigation and concrete supported finding, then a campaign with a human confirmed shortlist or deliberate deferral, retaining the same dataset/digest. Record actual monitoring and campaign seconds, inspected posts, missing evidence, corrections, a useful finding (or explicit negative judgment), and a reusable keep/exclude/defer decision with reasons (or explicit negative judgment). The legacy evaluator requires the investigation/campaign/shortlist's recorded human attribution to match the reviewer; existing records from another actor cannot be relabeled. Its confirmed human shortlist and the operational generated recommendation are distinct IDs and records.
4. **Review the selected operational journeys after baseline.** Give actual feedback on campaign order/rationale/gaps and saved-history/regeneration behavior; answer support/gaps, exact approval/scope, task outcome and publication-before-later-query behavior; and quantitative versus provisional semantic alert interpretation. Keep recent X evidence, baseline comparability and existing KB context distinct, with dates and limits. Examine the selected existing histories through their public readers/UI. Do not approve or execute new acquisition, invoke a model, or invent missing journey states for this review.
5. **Annotate the complete fixed membership.** Use the exported review template for each result, with the fields below. A partial review preserves the full denominator and remains pending. Record material unsupported claims, translation mistakes and usability failures even when they cause failure. Material means the error changes the finding, decision or stated support/limits. Link corrections or a follow-up defect to the exact affected IDs; an unresolved material error cannot support a pass.
6. **Reopen and report separately.** Reopen product records and packets under current policy. Report selected/submitted/currently countable/unavailable denominators and all four labels; unavailable items cannot count as supported. Preserve actual negative/ambiguous/not-assessable outcomes. Technical evidence remains separate; `recorded` annotation/usefulness is not verified truth or an automatic overall pass. Japanese-original accuracy stays `not_validated` without qualified original-language adjudication. Make no numeric generalized accuracy, causal speed, sales or market claim.

## Current commands for the later human session

These are **instructions, not executed review commands**. Replace every variable with the selected actual reviewer/result IDs and operator-confirmed local schema. No such values currently exist in this handoff. Use an already provisioned result workspace. `operational_quality.py` currently runs review-table `migrate()` on every action; that behavior is why it was not used during this read-only preparation. Do not run these commands as a workaround for missing result-owner tables or missing examples.

```bash
# After identity/selection are fixed; complete and save the manual baseline first.
# Pin the documented local development endpoint rather than inherit another DSN.
export SMI_DATABASE_URL='postgresql://smi:local_only_change_me@127.0.0.1:6543/smi'
mkdir -p .scratch/evaluation
uv run --locked python tools/pilot_evaluation.py .scratch/evaluation/marketer-review.json --init
# Human: record/save the actual manual baseline before the assisted steps below.

# Open the existing local workspace for the named actual reviewer; no live flags.
uv run --locked smi-review --schema "$REVIEW_SCHEMA" --actor "$ACTUAL_REVIEWER"

# After baseline: export each selected existing result with its own stable request ID.
uv run --locked python tools/operational_quality.py --schema "$REVIEW_SCHEMA" --workspace local --actor "$ACTUAL_REVIEWER" export recommendation "$GENERATED_SHORTLIST_ID" --request-id "$RECOMMENDATION_EXPORT_REQUEST" > .scratch/evaluation/recommendation-packet.json
uv run --locked python tools/operational_quality.py --schema "$REVIEW_SCHEMA" --workspace local --actor "$ACTUAL_REVIEWER" export answer "$ANSWER_ID" --request-id "$ANSWER_EXPORT_REQUEST" > .scratch/evaluation/answer-packet.json
uv run --locked python tools/operational_quality.py --schema "$REVIEW_SCHEMA" --workspace local --actor "$ACTUAL_REVIEWER" export semantic_alert "$SEMANTIC_ALERT_ID" --request-id "$ALERT_EXPORT_REQUEST" > .scratch/evaluation/semantic-alert-packet.json

# Human editor: copy only the packet's review_template into HUMAN_REVIEW_FILE;
# complete it with actual observations. Repeat record/read for each packet.
uv run --locked python tools/operational_quality.py --schema "$REVIEW_SCHEMA" --workspace local --actor "$ACTUAL_REVIEWER" record "$PACKET_ID" "$HUMAN_REVIEW_FILE" --request-id "$REVIEW_REQUEST"
uv run --locked python tools/operational_quality.py --schema "$REVIEW_SCHEMA" --workspace local --actor "$ACTUAL_REVIEWER" read "$PACKET_ID"

# Assess the completed same-corpus record against its actual linked records.
uv run --locked python tools/pilot_evaluation.py .scratch/evaluation/marketer-review.json --schema "$REVIEW_SCHEMA" --output .scratch/evaluation/status.json
```

Initialization refuses to overwrite an existing human record; omit `--init` if one exists. Its default `dataset_id` names the documented curated sample: retain it only if that is the actual selected imported dataset, otherwise record the actual dataset ID. Add actual task order/timestamps to the record's `notes` or linked session note. The last command intentionally omits `--technical-results` unless an actual compatible JUnit artifact is available; that leaves its technical field pending rather than inventing XML from the preserved 890-test log. Do not rerun the shared gate just to populate human-review metadata. The prior technical PASS remains separately cited below.

For the legacy caption review, use the selected actual knowledge run with `uv run --locked smi-ingest --schema "$REVIEW_SCHEMA" review-packet "$KNOWLEDGE_RUN_ID" --actor "$ACTUAL_REVIEWER"`. Record exact observation/source-assertion IDs, actual translation and translator/method version, label, ambiguity, material errors/corrections, and `corrected` truthfully. The legacy fields are `manual_baseline` (completion timing, exposure, monitoring answer, account choices, seconds, inspected posts), `assisted` (insight/finding/confirmed-shortlist IDs, monitoring/campaign seconds, inspected posts, useful observation, reusable decision/reason, missing evidence and human usefulness booleans), and `language_review.items`. This is the unchanged `local-marketer-review-v1` contract; operational templates do not replace it.

For each operational `review_template`:

- Set `reviewer` to the actual trusted human `--actor`, `attested` to their actual attestation, `reviewed_at` to the real timezone-aware review time and `method_version` to the used review method.
- Preserve the full `denominator` and frozen member IDs. Supply each reviewed item's actual `translation`, `translator` (`actor_id`, `kind`, `method_version`, and actual `model_version` for automation or explicit null for human translation), label (`supported`, `unsupported`, `ambiguous`, `not_assessable`), `ambiguity`, boolean `material_error`, `error` and `correction`. Absent optional text is explicitly null; a material error requires a description. No translation/model call was authorized or run in this preparation.
- Leave `marketer_usefulness` null until the human supplies boolean `useful`, a substantive `rationale`, actual nonnegative `task_seconds` and integer `inspected_posts`. There is no speed target. Keep the useful finding and reusable decision/reasons in the session/legacy record as well; a single usefulness boolean does not establish them.
- Equal retries use the same request ID/body; corrections use a new request ID and retain history. Limits are 256 KiB per submission, 50 records per packet and 5,000 packets per workspace. Add `--include-synthetic` before the action only if the reviewer explicitly selects simulated evidence; report that limitation rather than treating it as real-source validation. Quantitative-alert and journey feedback belongs in the session note, since the operational packet CLI exports only recommendation, answer and semantic alert.

## Preserved verification and completion boundary

Ticket 38's [report](ticket-38.md) records the actual independent root check: **890 tests / 666.47 seconds / exit 0 / session 22406**, plus the verified existing wheel/protected files. This preparation changes no source, test, product document, schema or module interface and does not repeat that gate/build. Metadata verification is recorded in the ticket comment; the coordinator receives the exact handoff commit identity.

Own metadata checks passed: inventory JSON scope/results, local Markdown links, claimed/ready-for-human state, all six human criteria still unchecked, `git diff --check`, and unchanged source/tests/tools/product contracts against `3f6ab86e4f19ea248436d44653ff7ffd7f294ec9`. The current packet CLI's `--help` was checked without invoking an action or migration. No code behavior changed, so no new behavior test or TDD cycle applies to this preparation.

Actual reviewer attribution/attestation, selected permitted IDs/membership, manual baseline, assisted measurements, translations, campaign/assistant/alert feedback, useful finding, reusable decision, and correction/adjudication outcomes all remain **not supplied**. No human quality gate has passed. Ticket 39 must remain claimed until actual review evidence is recorded and assessed; the overall operational objective is not complete.

## Suggested coordinator question

“Who will perform the attributable marketer review, and which existing local schema/workspace and permitted saved recommendation, answer/enrichment journey and quantitative/semantic alert IDs may they review? Please have that reviewer provide the manual baseline before assisted results, prior exposure/task order, actual times/counts, translations/method attribution and actual feedback using the prepared handoff.”

Independent work remaining with the coordinator: complete the already requested Standards/Spec reviews and preserve technical evidence. No agent can independently supply the missing human observations, select an undisclosed permitted corpus, or mark ticket 39 resolved.
