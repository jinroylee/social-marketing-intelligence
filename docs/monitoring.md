# Independent monitoring

[`smi_monitoring`](../src/smi_monitoring/__init__.py) owns human investigation scopes and versioned, rule-based insight revisions. It consumes public knowledge/evidence interfaces and has no campaign dependency or campaign-creation action.

Snapshot investigations and [bounded offline recent-X evidence](#bounded-offline-recent-x-evidence) are separate implemented paths. The [target anomaly flow](functional-requirements.md#c--lightweight-x-monitoring-and-anomaly-detection) remains future work; snapshot preparation does not implement anomaly investigation or its tool restrictions.

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

## Bounded offline recent X evidence

[`smi_monitoring.recent`](../src/smi_monitoring/recent/__init__.py) owns `RecentMonitoring` and `OfflineXRoute`. It installs independent tables with `migrate()`; the existing `MonitoringStore.migrate()` also installs this additive schema. Existing investigation IDs, frozen source membership, snapshot answers and form protections retain their original meaning. Recent collection requires no catalog, canonical ingestion, campaign or per-post knowledge publication.

Construct the store with a trusted local `OfflineXRoute(path)`, an explicit `operators=frozenset({...})`, and optionally a trusted UTC clock. Source/provider/model calls are absent. The route is synthetic test evidence and establishes no live X readiness or human usefulness validation. No daemon or scheduler is installed: an operator explicitly invokes each poll.

### Topic and policy operations

`set_policy(document, human_operator, expected_version=...)` creates or updates current source permission. The exact fields are `context_id`, boolean `can_process`, `can_display`, `can_retain`, `revoked`, and nullable timezone-aware `expires_at`. New policies use version 0; changes require the exact current version. Policies are configured separately from topic edits; saving a topic grants no permission.

`configure(topic_key, settings, human_operator, expected_version=..., request_id=...)` saves immutable topic revisions. New topics use version 0. Keys are 1–80 lowercase letters/digits/underscore/hyphen; queries are 1–200 characters of literal case-insensitive text. Exact settings are:

| Setting | Contract |
| --- | --- |
| `query` | Literal post text match; no inferred topic, language or sentiment |
| `cadence_minutes` | Integer 1–1,440; UTC epoch-aligned explicit poll boundaries |
| `window_minutes` | Integer 1–10,080; inclusive publication start, exclusive end |
| `max_records` | Integer 1–100 unique source captures admitted per window |
| `retention_hours` | Integer 1–720; local maximum copied-body lifetime |
| `source_policy_id` | Existing current source permission context |

Identical configuration requests reopen their saved revision even after edits; changed actor/input conflicts and stale expected versions fail. Topics are separate from scheduled KB keywords, even if their query text overlaps. At most 50 topics, 100 revisions per topic, 50 source policy contexts and 20,000 native withdrawal identities are retained per workspace. These finite audit caps reject further additions; the implementation does not silently delete history or recycle identities.

### Poll identity, source times and coverage

`poll(topic_key, window_end, human_operator)` takes an explicit timezone-aware end. New windows must be within the preceding seven days, no later than the trusted clock, and aligned to the configured cadence from the UTC epoch. The window starts `window_minutes` earlier. A topic plus normalized end is one logical poll across configuration changes/restarts/concurrent retries: an existing window reopens before consulting the new configuration or fixture. A new end uses the then-current immutable topic revision. Collection/retries both require the current trusted operator role. Failed input, source-time, file or identity validation commits no window.

The route reads exactly one regular local JSON file, at most 262,144 bytes and 200 input records, with one bounded file-read request and no network access. The top-level fields are `coverage` (`complete`, `partial` or `missing`) and `records`; `missing` requires an empty list. Each record has exactly `capture_id`, digit-string X `native_id` (1–24 digits), nullable `text` (at most 4,096 characters), nullable timezone-aware `published_at`, `captured_at`, `metric_measured_at`, and a `metrics` object. Native source references are canonical `https://x.com/i/status/ID` pointers, not verified availability. Example: [recent X fixture](../examples/monitoring/recent-x.json).

Capture, publication, metric measurement and local import times remain distinct. Known capture/measurement times cannot be in the future; publication cannot follow its capture and measurement cannot follow a known capture. Unknown publication or text makes window/query eligibility unassessable and excludes that row; unknown capture is retained visibly without a freshness claim. Missing measurements/counts remain unknown, never zero. Original source capture identity is native post plus original capture time, independently of mutable text and fixture `capture_id` labels. With unknown capture, available original publication/measurement times form a conservative identity and establish no refresh. Changed values within that identity fail; genuinely later source captures remain separate observations. Reuse preserves the first import/acquisition metadata, body tombstone and retention deadline; a later import cannot manufacture source freshness.

Selection deduplicates source captures before a stable native/capture ordering and configured record cap. Windows retain original configuration, human query, requested bounds, scanned/selected/unassessable/duplicate/withdrawn counts, truncation, field completeness and declared fixture coverage. Unknown eligibility, capture time, withdrawn input or truncation makes an otherwise complete sample partial. `complete` means only that the supplied local fixture scan completed: market coverage stays `unknown`, `baseline=null`, and empty results establish no market absence or quantitative/semantic change. Acquisition retains route/version, synthetic classification, exact file SHA-256/bytes/request count and original policy version; it creates no task receipt or billing claim.

Metrics have X-specific meanings: `like_count` is public likes, `repost_count` public reposts, `reply_count` public replies and `view_count` reported views at `metric_measured_at`. They are nonnegative integers up to 10^15, not unique audience, sentiment, sales or cross-source comparable engagement. No combined engagement metric is synthesized.

### Reopen and lifecycle

`list_topics(actor)`, `read_topic(key, actor)`, `read_window(id, actor)`, `timeline(key, actor, limit=50, offset=0)` and `read_observation(id, actor)` reopen workspace-scoped data after restart without the fixture route. Window reads pin original membership and return at most 100 observations. The topic view shows the latest 100 windows and all bounded topic revisions; older windows reopen by ID. Timeline pages contain 1–100 distinct captures, ordered by original capture (unknown last) then stable observation ID; offset is bounded by 20,000 and `has_more` is explicit. A topic retains at most 1,000 windows and the workspace at most 20,000 observations, including tombstones. Further new windows/captures fail atomically at those finite caps. Repeated window membership is not a new source post or refresh.

Current process/display/retention policy is checked under the same workspace lock as collection and policy writes. Process and display reads use their corresponding permission independently; neither bypasses retention. Retained bodies contain only text and original metric values. On source retention denial, revocation, policy expiry or local expiry, synchronous reconciliation permanently removes those bodies while keeping source-free lineage/times/missingness and original collection coverage. Permission recovery, retries or renamed fixture labels cannot restore them. Reads never substitute later evidence into a historical window.

The local body deadline is the earlier of original known capture and first import plus the configured retention duration. With unknown capture, first import bounds local storage only and grants no recency claim. Reuse can shorten, never extend this deadline. `withdraw(native_id, human_operator)` permanently removes all current copied bodies for that native post and excludes future captures, retaining an attributable native tombstone. Policy mutations, new polls and policy-aware reads reconcile synchronously; no background deletion or universal file cleanup is claimed. The caller-supplied local fixture remains an external input file, not a retained product copy.

The [local browser workflow](local-review.md#bounded-offline-recent-x-topics) exposes topic, window and capture views; policy writes/withdrawal remain trusted Python operations. `purpose="display"` is the default on window/timeline/detail; trusted process reads explicitly select `purpose="process"`. Source text is escaped and governed again on each request.

## Accepted future X anomaly path

Comparable baselines, quantitative/semantic detection, alerts, notification delivery, live X collection, a recurring scheduler and selective KB promotion remain unimplemented. Full KB modeling of every recent post is not required before future detection. [ADR 0004](adr/0004-lightweight-monitoring-evidence.md) records the separate evidence lifecycle.

Future anomaly investigation uses existing KB context only, without additional external searches, scope expansion or campaign creation. Alert copies will need the same source policy and retention lifecycle; promotion will use normal ingestion/publication with lineage rather than making the entire feed a KB publication. The installed topic/window/timeline path grants none of those future actions.
