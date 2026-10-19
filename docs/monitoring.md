# Independent snapshot monitoring

[`smi_monitoring`](../src/smi_monitoring/__init__.py) owns human investigation scopes and versioned, rule-based insight revisions. It consumes public knowledge/evidence interfaces and has no campaign dependency or campaign-creation action.

The following sections describe implemented snapshot investigations. The [target X-monitoring flow](functional-requirements.md#c--lightweight-x-monitoring-and-anomaly-detection) is a separate future path; current source-free preparation does not implement anomaly investigation or its tool restrictions.

## Scope and preparation

`InvestigationScope` requires a catalog, question, intended market context, platforms and at least one Brand/Product/topic reference. Market context describes human intent, not audience geography. Publication bounds use timezone-aware timestamps. See the [example scope](../examples/monitoring/hero-cushion-scope.json).

`MonitoringStore.start(scope, human_actor, request_id=...)` creates the first scope. `revise_scope(..., expected_version=..., request_id=...)` appends a successor. `prepare_insight(investigation_id, scope_id, knowledge_run_id, actor, expected_version=..., request_id=...)` pins the current scope, exact knowledge run/catalog, dataset ID/digest, actual observations, method/version, actor and time. Human or automation contexts can prepare answers; scope writes require a trusted human.

The method is `rule_based`, `caption-snapshot-summary-v1`. It filters processable, retainable, current observations by platform/publication time. Any selected reference may match. Within matched posts, it summarizes requested mentions/topics and literal PR/Qoo10 markers, retaining exact interpretation/assertion/span dependencies.

Counts use distinct content identities and exact namespace/native account keys. Repeated captures are not extra posts. A PR marker is not a paid contract; Qoo10 wording is not a conversion; family mentions are not exact variants. Findings remain provisional and sample-scoped, without stance, efficacy, audience or sales inference.

Caption language is an explicit optional constraint. The current method establishes script only, so requiring a language returns `language_constraint="not_assessable"` and no asserted language-filtered subset. Leave it empty for literal-scope retrieval without a language claim. An empty window/reference result means “no matching observations in this dataset,” not market absence.

## Revisions and policy

Separate scope/insight heads are serialized under an investigation lock. Expected versions reject competing edits; identical request retries return the original record. Changed inputs/actors under the same ID conflict. A fresh answer uses a new request; earlier answers remain tied to their original scope. `list_investigations`, `read_investigation` and `read_insight` reopen history across restarts.

Coverage records original requested coverage, scanned/matched observation IDs, language status and `baseline=null`. `trend_status="not_assessable"` prevents snapshot findings from becoming growth/change alerts. No repeated-capture scheduler or trend estimator is implemented.

Commit-time source/derivation locks recheck finding dependencies and surviving knowledge support; withdrawal/correction causes `insight_support_changed` and rolls back. Reads hide denied finding statements/counts/excerpts; superseded support requires review. Retention withdrawal, expiry or revocation purges finding bodies while preserving permitted IDs, original membership and attribution. Permission recovery or identical retries cannot reconstruct them.

Redaction is conservative per finding: one withdrawn dependency withholds its aggregate rather than silently recomputing history. Matching membership/counts are also withheld (`actual_observation_ids=null`) while a finding is unavailable, so coverage cannot reproduce a hidden aggregate. Original stored audit membership remains pinned. A successor can summarize still-permitted evidence. Reconciliation is synchronous; no background deletion or universal file cleanup is claimed.

## Browser workflow

`/investigations` is independently reachable in the [local review application](local-review.md). Create/revise a scope, choose a dataset, prepare an insight and expand findings for original captions, highlighted support, source/date lineage, capture age and limits. Scope/answer history is retained. Preparation makes no source/provider/model call; translations and language adjudication remain pending until supplied.

## Accepted future X light path

Periodically collect recent X posts for configured monitoring topics into bounded monitoring observations. Detect quantitative volume/engagement anomalies against recorded windows/baselines and semantic sentiment/controversy changes using versioned methods. Distinguish missing collection coverage, repeated captures and source failures from actual changes.

Full KB/ontology modeling of every post is not required before detection. Retain necessary alert evidence and detection context separately, with provenance, policy dependencies and explicit retention settings. Promote selected useful material through normal KB ingestion/publication. The KB remains authoritative for KB facts; a monitoring observation or alert is not automatically a published knowledge assertion. [ADR 0004](adr/0004-lightweight-monitoring-evidence.md) records this boundary.

Investigate significant anomalies using existing KB context only; the investigation cannot launch further external searches or create a campaign. Save concise evidence-backed alert explanations/history and notify users. Source withdrawal or expiry governs stored alert copies as well as observations, with unavailable support made visible. Polling/detection uses applicable source/request limits and hybrid spending controls; lightweight does not mean unbounded.

An X collector, scheduler, recent-observation store, comparable baselines, quantitative/semantic methods, alert lifecycle and notification delivery are all unimplemented. Existing snapshot-insight tables are not a substitute for these records. Exact windows, significance, delivery and retention settings belong to explicit operating configuration.
