# Data model and ERD

## Implemented relational model

The physical schemas are owned by [ingestion](../src/smi_ingestion/schema.sql), [shared knowledge](../src/smi_knowledge/schema.sql), [campaign decisions](../src/smi_campaigns/schema.sql), [campaign planning](../src/smi_campaigns/planning/schema.sql), [monitoring](../src/smi_monitoring/schema.sql), [offline tasks](../src/smi_tasks/schema.sql) and [offline costs](../src/smi_costs/schema.sql). The diagrams show primary keys, important foreign keys and ownership fields; the SQL is authoritative for the complete columns and constraints.

```mermaid
erDiagram
    ingestion_runs ||--o{ source_observations : captures
    ingestion_runs ||--o{ ingestion_issues : reports
    source_observations o|--o{ ingestion_issues : concerns
    source_observations ||--o{ derivations : interpreted_by
    canonical_entities ||--o{ external_identities : identified_by
    derivations ||--o{ field_assertions : produces
    canonical_entities ||--o{ field_assertions : described_by
    derivations ||--o{ metric_observations : produces
    canonical_entities ||--o{ metric_observations : measured_by
    derivations ||--o{ unresolved_candidates : reports
    ingestion_runs ||--o| evidence_sets : materializes
    evidence_sets ||--|{ evidence_set_members : pins
    source_observations ||--o| evidence_set_members : binds
    derivations ||--o| evidence_set_members : freezes

    ingestion_runs {
        uuid id PK
        text workspace_id
        text adapter_id
        text manifest_hash
        jsonb checkpoint
        jsonb waiting
        boolean input_complete
        jsonb limits
        text status
    }
    source_observations {
        uuid id PK
        uuid run_id FK
        int item_index
        text adapter_id
        text provider_id
        timestamptz captured_at
        timestamptz source_as_of
        timestamptz ingested_at
        jsonb policy
        boolean synthetic
        text payload_hash
        text payload_path
        jsonb coverage
    }
    ingestion_issues {
        bigint id PK
        uuid run_id FK
        uuid observation_id FK
        text code
    }
    canonical_entities {
        uuid id PK
        text kind
        boolean synthetic
    }
    external_identities {
        text platform PK
        text namespace PK
        text kind PK
        text native_id PK
        boolean synthetic PK
        uuid entity_id FK
    }
    derivations {
        uuid id PK
        uuid observation_id FK
        text mapper_key
        text policy_version
        boolean active
    }
    field_assertions {
        uuid id PK
        uuid derivation_id FK
        uuid entity_id FK
        text field
        text state
        jsonb value
        text source_locator
    }
    metric_observations {
        uuid id PK
        uuid derivation_id FK
        uuid entity_id FK
        text definition
        text native_name
        numeric value
        text precision
        text unit
        timestamptz measured_at
    }
    unresolved_candidates {
        uuid id PK
        uuid derivation_id FK
        text kind
        text source_locator
        text reason
    }
    evidence_sets {
        text workspace_id PK
        text dataset_id PK
        text digest
        jsonb manifest
        uuid run_id FK
        boolean synthetic
        text importer_version
        text imported_by
        timestamptz imported_at
    }
    evidence_set_members {
        text workspace_id PK, FK
        text dataset_id PK, FK
        int position PK
        uuid origin_observation_id
        uuid origin_run_id
        uuid observation_id FK
        uuid derivation_id FK
    }
```

## Identity, membership and time

- Canonical entities currently have only `account` and `content` kinds. Their UUIDs are separate from native string identifiers. Synthetic evidence has separate identities even if its native strings match real records.
- Field assertion states are `observed`, `not_returned`, `unavailable` and `removed`. Zero is a value, not a missing state. Current views may additionally report conflicts or aggregate unknowns.
- A derivation identifies one mapper/policy interpretation of one observation. Exactly one derivation per observation can be active; old derivations remain addressable.
- Dataset identity is `(workspace_id, dataset_id)`. It binds an immutable byte digest, manifest and import run. A member pins both the local observation and a derivation belonging to that observation through a composite foreign key.
- Original source observation/run UUIDs are lineage metadata. They are not foreign keys into the local database. Dataset membership is not inferred from all rows sharing an account or run date.
- `captured_at` is the source capture; `source_as_of` is a separately reported source time when known; `ingested_at` and `imported_at` are local recording times. Metrics and publication assertions retain their own time semantics.
- Policy remains on the source observation and is evaluated at read time. A frozen member can remain addressable while its source content becomes unavailable.

## Implemented shared knowledge model

```mermaid
erDiagram
    knowledge_brands ||--o{ knowledge_products : markets
    knowledge_catalogs ||--o{ knowledge_runs : configures
    evidence_sets ||--o{ knowledge_runs : supports
    knowledge_runs ||--o{ knowledge_assertions : produces
    knowledge_query_results ||--o{ knowledge_query_members : preserves
    knowledge_publications ||--o{ knowledge_query_members : supplies
    source_observations ||--o{ knowledge_query_members : governs
    derivations ||--o{ knowledge_query_members : freezes
    knowledge_publications ||--|{ knowledge_publication_support : pins
    source_observations ||--o{ knowledge_publication_support : governs
    derivations ||--o{ knowledge_publication_support : freezes
    knowledge_publications ||--o{ knowledge_publication_interpretations : includes
    knowledge_assertions ||--o{ knowledge_publication_interpretations : interprets
    canonical_entities ||--o{ knowledge_assertions : interpreted_by
    field_assertions ||--o{ knowledge_assertions : supports
    source_observations ||--o{ knowledge_assertions : governs

    knowledge_query_results {
        uuid id PK
        text workspace_id
        text request_id
        text request_digest
        text method_version
        jsonb query_scope
        text purpose
        boolean synthetic
        text producer_id
        text producer_kind
        jsonb coverage
        jsonb unknowns
        timestamptz queried_at
    }
    knowledge_query_members {
        uuid result_id PK, FK
        int position PK
        uuid publication_id FK
        uuid observation_id FK
        uuid derivation_id FK
        uuid_array assertion_ids
        uuid_array metric_ids
        uuid_array interpretation_ids
        jsonb versions
    }
    knowledge_publications {
        uuid id PK
        text workspace_id
        text request_id
        text request_digest
        text method_version
        text producer_id
        text producer_kind
        boolean synthetic
        jsonb coverage
        timestamptz published_at
    }
    knowledge_publication_support {
        uuid publication_id PK, FK
        int position PK
        uuid observation_id FK
        uuid derivation_id FK
        uuid_array assertion_ids
        uuid_array metric_ids
        text content_version
    }
    knowledge_publication_interpretations {
        uuid publication_id PK, FK
        int position PK
        uuid interpretation_id FK
    }
    knowledge_brands {
        text workspace_id PK
        text brand_id PK
        text preferred_name
        text recorded_by
    }
    knowledge_products {
        text workspace_id PK, FK
        text product_id PK
        text brand_id FK
        text preferred_name
        text recorded_by
    }
    knowledge_catalogs {
        text workspace_id PK
        text catalog_id PK
        text digest
        jsonb document
        text recorded_by
        timestamptz recorded_at
    }
    knowledge_runs {
        uuid id PK
        text workspace_id FK
        text dataset_id FK
        text catalog_id FK
        text method_version
        text request_id
        text recorded_by
        timestamptz recorded_at
        jsonb coverage
    }
    knowledge_assertions {
        uuid id PK
        uuid run_id FK
        uuid subject_id FK
        uuid source_assertion_id FK
        uuid observation_id FK
        text predicate
        jsonb value
        text basis
        int span_start
        int span_end
        text excerpt
        text review_status
        text support_state
        timestamptz recorded_at
    }
```

Publication membership pins exact observation/derivation/assertion/metric IDs and existing interpretation IDs, independent of frozen datasets. Assertion/metric arrays are validated against their nominated derivation by the ingestion public interface before the publication transaction commits. Publications retain ordered membership, producer, method and original coverage; current reads apply source policy without copying source text. The workspace/request identity binds the payload and producer. Ingestion run workspace ownership scopes both fresh and imported support; upgrades preserve imported workspace context.

Query results preserve the actual bounded selection rather than only the query text. Their member rows retain exact source/interpretation IDs and source-free method, publication and freshness metadata; values are re-read through the publication owner under current policy. The public owner validates all membership against immutable publications, and source/derivation locks remain held until result commit. Workspace/request identity binds scope, purpose, synthetic mode, method and producer. New publications and withdrawal cannot rewrite prior membership or original coverage; current availability, supersession and age are separate read attributes. Query storage holds no raw source fact or interpretation-value copy.

Catalog documents pin human-configured aliases and product specificity. Business reference IDs persist across catalog revisions. Run identity includes workspace, frozen dataset, catalog, method version and preparation request ID. An explicit new request creates a fresh run under unchanged semantic configuration; retries retain the original run. Each interpretation points to its exact source caption assertion and observation; source policy controls its permitted use and retained copies. Withdrawal purges values/excerpts while retaining support metadata. A separate semantic-review/correction lifecycle remains future work.

## Implemented campaign model

```mermaid
erDiagram
    campaigns ||--|{ campaign_briefs : described_by
    campaigns ||--o{ comparison_drafts : evaluates
    campaign_briefs ||--o{ comparison_drafts : frames
    campaigns ||--o{ campaign_ranking_assessments : assesses
    campaign_briefs ||--o{ campaign_ranking_assessments : pins
    comparison_drafts ||--o| campaign_ranking_assessments : supplies
    shortlist_revisions o|--o| campaign_ranking_assessments : saves
    campaigns ||--o{ campaign_criteria_interpretations : interprets
    campaign_briefs ||--o{ campaign_criteria_interpretations : pins
    campaign_criteria_interpretations o|--o{ comparison_drafts : selected_as
    knowledge_runs o|--o{ comparison_drafts : supports
    knowledge_query_results o|--o{ comparison_drafts : pins_current_support
    comparison_drafts ||--o{ comparison_candidates : contains
    canonical_entities o|--o{ comparison_candidates : identifies
    comparison_candidates ||--o{ comparison_support : cites
    source_observations ||--o{ comparison_support : governs
    field_assertions o|--o{ comparison_support : supports
    knowledge_assertions o|--o{ comparison_support : interprets
    campaigns ||--o{ shortlist_revisions : records
    campaign_briefs ||--o{ shortlist_revisions : frames
    comparison_drafts ||--o{ shortlist_revisions : informs
    shortlist_revisions ||--o{ shortlist_selections : selects
    comparison_candidates ||--o{ shortlist_selections : chosen_as

    campaigns {
        uuid id PK
        text workspace_id
        text owner_id
        text request_id
        text request_digest
        int brief_version
        int shortlist_version
        timestamptz created_at
    }
    campaign_briefs {
        uuid id PK
        uuid campaign_id FK
        int version
        jsonb document
        jsonb executable_profile
        text request_id
        text request_digest
        text recorded_by
        timestamptz recorded_at
    }
    campaign_criteria_interpretations {
        uuid id PK
        uuid campaign_id FK
        uuid brief_id FK
        text request_id
        text request_digest
        text requested_by
        text status
        text reason
        jsonb configuration
        uuid operation_id
        jsonb usage
        jsonb executable_profile
        timestamptz recorded_at
        timestamptz finished_at
    }
    campaign_ranking_assessments {
        uuid id PK
        uuid campaign_id FK
        uuid brief_id FK
        uuid comparison_id FK
        uuid shortlist_id FK
        text request_id
        text request_digest
        text producer_id
        uuid_array candidate_ids
        int expected_brief_version
        int expected_shortlist_version
        boolean include_synthetic
        text status
        text reason
        jsonb configuration
        uuid operation_id
        jsonb usage
        timestamptz recorded_at
        timestamptz finished_at
    }
    comparison_drafts {
        uuid id PK
        uuid knowledge_query_result_id FK
        uuid criteria_interpretation_id FK
        uuid campaign_id FK
        uuid brief_id FK
        uuid knowledge_run_id FK
        text dataset_id
        text dataset_digest
        text method_version
        text request_id
        text request_digest
        jsonb coverage
        text prepared_by
        text actor_kind
        timestamptz prepared_at
    }
    comparison_candidates {
        uuid id PK
        uuid comparison_id FK
        int position
        jsonb account_key
        uuid account_id FK
        text origin
        jsonb body
        jsonb ranking_input
        jsonb ranking_judgment
    }
    comparison_support {
        bigint id PK
        uuid candidate_id FK
        uuid observation_id FK
        uuid source_assertion_id FK
        uuid interpretation_id FK
    }
    shortlist_revisions {
        uuid id PK
        uuid campaign_id FK
        uuid brief_id FK
        uuid comparison_id FK
        int version
        text status
        text request_id
        text request_digest
        text recorded_by
        text actor_kind
        text method_version
        text ordering
        jsonb selection_summary
        timestamptz recorded_at
    }
    shortlist_selections {
        uuid id PK
        uuid revision_id FK
        uuid candidate_id FK
        int position
        text reason
        text reason_basis
        uuid_array support_ids
        jsonb acknowledged_unknowns
        boolean reason_withdrawn
    }
```

Campaign heads serialize brief/shortlist saves. Revision/request uniqueness separates a new automated recommendation or human decision from retries. `generated` revisions record the actual automation kind/producer, shortlist method, comparison ordering and source-free candidate/selection/exclusion/deferral summary. Selection positions are unique per revision and pin either deterministic comparison order or validated model assessment order. Existing human draft/confirmed records retain attribution and null method/order/summary/positions; migration does not infer historical order or review. Each new brief atomically saves the human document (including optional original prose) and its exact structured executable profile, with stable criterion IDs, unknown policies and installed criteria/ranking/coverage versions. The profile is one-to-one with its brief revision and contains its exact ID/version; older rows keep a null profile rather than reconstructed history. Its current ranking is explicitly unranked and coverage descriptive. Comparisons pin exact brief/profile and knowledge IDs plus dataset digest and actual member IDs. Candidate keys retain platform/namespace/native string identity; an absent requested account has no canonical account UUID. Explicit support rows bind copied bodies and automated or human reasons to their source-policy dependencies. Purging removes the source-derived copy, not the selected membership or actor history.

`campaign_ranking_assessments` is a durable one-call claim for an exact comparison/brief/producer/request, expected heads and assessed candidate IDs. Its optional shortlist link identifies a validated automatic save; failed/interrupted claims have no saved fallback. Configuration pins actual model/method/schema/ranking profile; logical cost-operation references preserve cost ownership without cross-owner SQL. Candidate `ranking_input` and `ranking_judgment` retain only required governed input components and validated structured judgments; they share `comparison_support` cleanup. No transaction spans provider I/O. Final publication rechecks pinned support and both heads; reported consumption remains accounted for unusable results. See [the ranking contract](campaigns.md#bounded-supported-llm-ranking).

## Monitoring and planning tables

```mermaid
erDiagram
    monitoring_investigations ||--|{ investigation_scopes : scopes
    monitoring_investigations ||--o{ insight_revisions : answers
    investigation_scopes ||--o{ insight_revisions : asks
    knowledge_runs ||--o{ insight_revisions : informs
    insight_revisions ||--o{ insight_findings : contains
    insight_findings ||--|{ insight_support : cites
    source_observations ||--o{ insight_support : governs
    field_assertions ||--o{ insight_support : supports
    knowledge_assertions o|--o{ insight_support : interprets
    campaigns ||--o{ measurement_plan_revisions : plans
    campaign_briefs ||--o{ measurement_plan_revisions : describes
    shortlist_revisions ||--o{ measurement_plan_revisions : anchors
    campaigns ||--o{ decision_note_revisions : learns
    shortlist_revisions ||--o{ decision_note_revisions : receives
    decision_note_revisions ||--o{ decision_note_support : depends_on
    source_observations ||--o{ decision_note_support : governs
    field_assertions o|--o{ decision_note_support : supports
    knowledge_assertions o|--o{ decision_note_support : interprets

    monitoring_investigations {
        uuid id PK
        text workspace_id
        text owner_id
        int scope_version
        int insight_version
        text request_id
        text request_digest
        timestamptz created_at
    }
    investigation_scopes {
        uuid id PK
        uuid investigation_id FK
        int version
        jsonb document
        text request_id
        text request_digest
        text recorded_by
        timestamptz recorded_at
    }
    insight_revisions {
        uuid id PK
        uuid investigation_id FK
        uuid scope_id FK
        uuid knowledge_run_id FK
        int version
        text dataset_id
        text dataset_digest
        text method_version
        jsonb coverage
        jsonb limitations
        text request_id
        text request_digest
        text prepared_by
        text actor_kind
        timestamptz prepared_at
    }
    insight_findings {
        uuid id PK
        uuid insight_id FK
        int position
        jsonb body
    }
    insight_support {
        bigint id PK
        uuid finding_id FK
        uuid observation_id FK
        uuid source_assertion_id FK
        uuid interpretation_id FK
    }
    measurement_plan_revisions {
        uuid id PK
        uuid campaign_id FK
        uuid brief_id FK
        uuid shortlist_id FK
        int version
        jsonb document
        text status
        text request_id
        text request_digest
        text recorded_by
        timestamptz recorded_at
    }
    decision_note_revisions {
        uuid id PK
        uuid campaign_id FK
        uuid shortlist_id FK
        int version
        text text
        text basis
        uuid_array support_ids
        text request_id
        text request_digest
        text recorded_by
        timestamptz recorded_at
    }
    decision_note_support {
        bigint id PK
        uuid note_id FK
        uuid observation_id FK
        uuid source_assertion_id FK
        uuid interpretation_id FK
    }
```

Monitoring has no campaign foreign key. Its scope and insight heads preserve independent question/answer history. Finding bodies carry sample-derived text/counts and can be purged while support/attribution metadata remains. Plans pin a brief and relevant shortlist and remain proposed; notes pin historical shortlists and conservatively inherit selected-source dependencies. Plan/note version heads are derived under campaign locks.

## Product domain model

This conceptual model expresses the accepted domain. Evidence, Brand/Product references, human campaign decisions/plans/notes and snapshot monitoring are implemented. Creator associations, operational ranking/automatic shortlist saving, scheduled acquisition authority, lightweight X alerts, spending controls and actual outcomes/attribution remain accepted future design; the physical diagrams describe implemented tables, including task execution ownership and independent synthetic accounting below.

```mermaid
erDiagram
    Brand ||--o{ Product : markets
    PlatformAccount ||--o{ Content : authors_under
    Creator ||--o{ AccountAssociation : associated_through
    PlatformAccount ||--o{ AccountAssociation : associated_through
    Campaign ||--|{ BriefRevision : described_by
    BriefRevision ||--o{ ComparisonDraft : evaluated_by
    EvidenceSet ||--o{ ComparisonDraft : supports
    ComparisonDraft ||--o{ CandidateJudgment : contains
    PlatformAccount ||--o{ CandidateJudgment : evaluated_by
    Campaign ||--o{ ShortlistRevision : records
    ComparisonDraft ||--o{ ShortlistRevision : informs
    ShortlistRevision ||--o{ SelectedAccount : selects
    PlatformAccount ||--o{ SelectedAccount : selected_as
    Campaign ||--o{ MeasurementPlanRevision : plans
    ShortlistRevision ||--o{ DecisionNote : receives
    MonitoringInvestigation ||--o{ InsightRevision : answered_by
    EvidenceSet ||--o{ InsightRevision : supports
```

Semantic assertions connect Brand/Product/topic interpretations to exact source assertion/span references, with basis, method and review context. These relationships are owned by shared knowledge, while brief, comparison and shortlist revisions are owned by campaign decisions. The same platform account can participate in many campaign-specific comparisons without becoming globally “discovered” or “selected.”

An optional Creator association carries its own evidence, role and applicable interval. An identity correction does not rewrite historical selected account IDs. Monitoring can produce an insight without any campaign, and a campaign can start without an insight.

## Implemented offline task model

```mermaid
erDiagram
    campaigns ||--o{ acquisition_tasks : authorizes
    campaign_briefs ||--o{ acquisition_tasks : pins
    enrichment_proposals ||--o| enrichment_approvals : receives
    enrichment_approvals o|--o| acquisition_tasks : authorizes_assistant
    acquisition_tasks ||--o| task_completion_events : completes
    acquisition_tasks ||--o{ acquisition_attempts : executes
    ingestion_runs ||--o| acquisition_attempts : records
    acquisition_tasks ||--o{ acquisition_task_publications : receipts
    knowledge_publications ||--o{ acquisition_task_publications : makes_usable
    enrichment_proposals {
        uuid id PK
        text workspace_id
        text request_id
        text scope_digest
        jsonb scope
        text scope_version
        jsonb limits
        text manifest_path
        text manifest_hash
        text proposer_id
        text proposer_kind
        timestamptz created_at
    }
    enrichment_approvals {
        uuid id PK
        uuid proposal_id FK
        text workspace_id
        text request_id
        text scope_digest
        text approver_id
        text approver_kind
        timestamptz approved_at
    }
    acquisition_tasks {
        uuid id PK
        text workspace_id
        text request_id
        text request_digest
        text origin
        uuid campaign_id FK
        uuid brief_id FK
        uuid approval_id FK
        text initiator_id
        text initiator_kind
        text scope_version
        jsonb scope
        jsonb limits
        int attempt_limit
        text manifest_path
        text manifest_hash
        text status
        text outcome
        jsonb progress
        uuid execution_id
        int execution_backend_pid
        jsonb execution_actor
        jsonb coverage
        text failure_phase
        text failure_code
        timestamptz submitted_at
        timestamptz finished_at
    }
    acquisition_attempts {
        uuid id PK
        uuid task_id FK
        int number
        uuid run_id FK
        text producer_id
        text producer_kind
        jsonb phases
        jsonb resumed_by
        int recovery_count
        jsonb publication_support
        timestamptz started_at
        timestamptz finished_at
    }
    task_completion_events {
        uuid id PK
        uuid task_id FK, UK
        timestamptz created_at
    }
    acquisition_task_publications {
        uuid task_id PK, FK
        uuid publication_id PK, FK
    }
```

Task admission persists its campaign/brief or exact proposal/approval basis, configuration and resource limits before returning. Proposal IDs identify immutable supplied revisions; each pins purpose, refresh/fill/expansion intent, subject/search and input scope, route/configuration and limits. Approval records the configured human, exact digest and request identity; one proposal permits at most one approval and one approval at most one task. The origin-basis constraint requires campaign plus brief for campaign tasks, or approval with no campaign/brief for assistant tasks. The migration preserves original campaign-only rows. Workspace/request identity binds the full scope and initiator. Only server-established campaign/assistant origins and a synthetic fixture-json route are installed. Actor roles come from trusted server configuration, separately from submitted identity metadata. Attempts retain exact run IDs, initial automation producers, recovery actors, committed phases and the exact prepared source-support selection; task/publication links are task-owned receipts committed atomically with the actual publication, before terminal acknowledgment. Task data copies no source wording. Current-policy publication reads remain responsible for values. Publication support's source-owned `content_version` fingerprint compares capture/mapping/selection identity across new run UUIDs without copying payloads; denied or superseded support does not suppress a newly usable publication. See [the task contract](tasks.md) for installed lifecycle and recovery limits. Task `progress` records the durable phase/observation frontier. A publication committed before task acknowledgment is reopened through the publication owner by request identity only after validating the task receipt, exact prepared support and source-owned attempt/run lineage. Ingestion-run `waiting` stores only a bounded reason/resumability pair; the opaque operation handle remains in its checkpoint. No-observation waits and their request usage commit together. These columns upgrade existing rows without changing their IDs or authority basis.

Task `execution_id`, `execution_backend_pid` and `execution_actor` identify the latest claim. Their metadata grants no ownership by itself: the exact backend's task-specific session lock determines running state. Owner transactions validate the execution ID and nonterminal task under its row lock and use that same connection for all dependent owner mutations. Disconnected sessions become recoverable without creating another attempt. `recovery_count` retains total handoffs; `resumed_by` keeps the most recent 20 actors and `phases` the most recent 100 entries. Migration truncates legacy arrays while preserving the original producer, IDs, exact support and total known recovery count. See [ADR 0005](adr/0005-task-session-effect-ownership.md).

A terminal outcome, attempt completion and one `task_completion_events` row commit on the same fenced task connection. Any task/publication receipt already committed atomically with its publication on that session; it survives a lost terminal acknowledgment. The event has one unique task reference and retains only source-free identity/time. Migration and workspace reconciliation backfill legacy terminal tasks idempotently. Inbox messages read the immutable outcome/coverage from the task and current display/support state from the publication owner, retaining historical counts while withholding unavailable publication links. See [the completion contract](tasks.md#durable-completion-inbox).

## Implemented offline accounting model

```mermaid
erDiagram
    cost_scopes ||--o{ cost_operations : classifies
    cost_operations ||--o{ cost_entries : records
    cost_scopes ||--o| cost_ceilings : controls
    cost_scopes ||--o{ cost_route_controls : binds
    cost_operations ||--o| cost_admissions : dispatches
    cost_operations ||--o{ cost_reconciliations : reconciles
    cost_entries ||--o| cost_reconciliations : final_measurement
    cost_operations ||--o{ cost_meter_recoveries : recovers
    cost_reconciliations {
        text workspace_id PK, FK
        text reconciliation_id PK
        uuid operation_id FK
        text measurement_id UK, FK
        jsonb body
        timestamptz recorded_at
    }
    cost_meter_recoveries {
        text workspace_id PK, FK
        text recovery_id PK
        uuid operation_id FK
        jsonb body
        timestamptz recorded_at
    }
    cost_ceilings {
        text workspace_id PK, FK
        text scope_id PK, FK
        numeric amount
        boolean paused
        text operator_id
        timestamptz updated_at
    }
    cost_route_controls {
        text workspace_id PK, FK
        text adapter_id PK
        text scope_id FK
        numeric max_units
        text operator_id
        timestamptz created_at
    }
    cost_admissions {
        text workspace_id PK, FK
        uuid operation_id PK, FK
        numeric max_units
        numeric reserved_amount
        text state
        text reason
        jsonb dispatched_by
        timestamptz updated_at
    }
    cost_scopes {
        text workspace_id PK
        text scope_id PK
        jsonb configuration
        text operator_id
        timestamptz created_at
    }
    cost_operations {
        uuid id PK
        text workspace_id FK
        text scope_id FK
        text request_id
        text actor_id
        text actor_kind
        text method
        uuid task_id
        uuid attempt_id
        timestamptz created_at
    }
    cost_entries {
        text workspace_id PK, FK
        text measurement_id PK
        uuid operation_id FK
        text kind
        jsonb body
        timestamptz recorded_at
    }
```

`cost_scopes.configuration` explicitly persists immutable provider/service, metered or forecast-only classification, currency, UTC period, unit/rate version/rate where applicable, and explicit provider-reported measurement basis for opted-in provider scopes; default synthetic documents retain their historical shape. The configuring human and time are retained. Scope identity is workspace-local; changed configuration conflicts. `cost_operations` pins one workspace/request identity to that scope, actual actor/method and either both exact task/attempt IDs or neither. Task references are logical, validated through the public task owner's injected resolver rather than a cross-owner foreign key or direct SQL. This preserves acyclic module dependencies and equivalent model attribution without a task.

`cost_entries` has a workspace-global measurement identity and composite operation/workspace foreign key. `kind` separates usage, forecast, declared outstanding commitment, unknown and meter failure. The body stores canonical exact decimal strings, actual recorder, provenance and measurement time; usage adds unit/rate/version, derived amount and synthetic or provider-reported basis; provider usage retains source-free token/cache/reasoning counts, and final operator reports remain distinct from verified invoices; forecasts require assumptions. Repeated identities reconcile once and changed reuse conflicts without overwriting history. Totals remain per-operation/currency/period and missing categories remain unknown. Declared commitments remain outstanding until an explicit final reconciliation names them; independent usage does not retire them. `cost_ceilings` holds current trusted amount/pause control for that exact immutable currency/period scope. `cost_route_controls` permanently binds the installed synthetic fixture route to one scope and its one-request service contract. `cost_admissions` has one row per operation and a bounded reservation plus dispatched/settled/refused state, reason and actual dispatcher. The scope row serializes ledger writes, decisions and settlement across connections; no transaction spans external I/O. Automatic adapter settlement appends usage and replaces only its own dispatched reservation; final reconciliation can also resolve explicitly named declarations and uncertainty. Session-loss uncertainty retains liabilities and pauses replay. `cost_reconciliations` binds a workspace-global event identity to one final usage entry and exact named admission/declaration/uncertainty targets in its immutable body, with operator, final outcome, report evidence/provenance and reconciliation time. The final measurement is unique per workspace across reconciliation events; explicit targets are validated under the scope lock. An equal existing measurement retains its original recorder. Reconciliation changes active totals rather than updating/deleting the entry audit. `cost_meter_recoveries` retains workspace-global health-check identity, exact already-reconciled failure IDs, operator, evidence/provenance and recovery time; no amount or dispatch permission follows from it. Unrecovered meter failure still blocks the scope after final usage. Both new tables use composite workspace/operation references; accounting retains no task dependency. See [the accounting contract](costs.md#final-synthetic-reconciliation-and-meter-recovery).

## Accepted future operational records

These are conceptual relationships for the [operational requirements](functional-requirements.md), not installed tables or a migration specification. The physical ERDs above describe the installed schema, including explicit knowledge publication, exact query results and campaign and exactly approved assistant offline task/attempt paths. Synthetic accounting and bounded ceiling/admission are installed above; commercial reconciliation and the broader operational relationships below remain conceptual.

```mermaid
erDiagram
    KeywordSubscription o|--o{ AcquisitionTask : schedules
    CoverageAssessment o|--o{ AcquisitionTask : requests
    AcquisitionTask ||--o{ AcquisitionAttempt : executes
    AcquisitionAttempt ||--o{ SourceObservation : captures
    AcquisitionTask ||--o{ KnowledgePublication : produces
    KnowledgePublication ||--o{ PublishedSupport : exposes
    SourceObservation ||--o{ PublishedSupport : supports
    BriefRevision ||--o{ RankedRecommendation : requests
    PublishedSupport }o--o{ RankedRecommendation : supports
    RankedRecommendation ||--o{ ShortlistRevision : saved_as
    RankedRecommendation ||--o| CoverageAssessment : assesses
    ShortlistRevision ||--o{ OptionalHumanReview : receives
    AcquisitionTask ||--o{ CompletionNotification : reports
    MonitoringTopic ||--o{ DetectionWindow : configures
    DetectionWindow ||--o{ MonitoringObservation : observes
    DetectionWindow ||--o{ AnomalyAlert : detects
    MonitoringObservation }o--o{ AnomalyAlert : supports
    MonitoringObservation o|--o{ SourceObservation : selectively_promoted_to
    KnowledgePublication }o--o{ AnomalyAlert : supplies_existing_context
    AnomalyAlert ||--o{ AlertNotification : reports
    AcquisitionAttempt ||--o{ SpendMeasurement : incurs
    SpendScope ||--o{ SpendMeasurement : accounts_for
    SpendScope ||--o{ SpendCeiling : constrains
    SpendScope ||--o{ SpendForecast : forecasts
```

Task origin distinguishes scheduled discovery, automatic campaign coverage and approved assistant enrichment. Assistant tasks require their exact scope-bound approval; the optional approval relationship does not authorize another origin to masquerade as an approved assistant task. Attempts and publications preserve retries, actual membership, failures and the distinction between retrieved versus usable knowledge.

A ranked recommendation can be saved automatically as a shortlist revision with its producer/method, order, rationale, support and gaps. Optional human review is separate from persistence; no human record is invented for an automatic save. Stable account identity and an ingested permitted supporting observation admit incomplete profiles to ranking. The installed deterministic `recommend` operation saves ordered `generated` revisions automatically; LLM ranking remains future work. See the [automatic persistence contract](campaigns.md#automatic-deterministic-shortlist-persistence).

Monitoring observations and alert support have their own bounded lifecycle and source policy. Selected promotion does not require every X post to become a full KB entity. Detection windows retain baseline/method/time/coverage context; an alert investigation can read existing publications without initiating external acquisition.

Spend measurements distinguish actual derived charges from forecasts, with currency, unit/rate versions, accounting periods, task/attempt attribution and meter provenance. Configured metered scopes have ceilings and coordinated in-flight commitments/reconciliation; unmeterable portions retain forecasts. These future commercial relationships do not extend the installed bounded synthetic enforcement to unbounded/delayed provider charges or prescribe particular ceiling amounts.

Campaign criteria attempts pin exact immutable brief input and retain sanitized outcome/configuration/usage plus only a validated generated profile. `operation_id` is an accounting-owner logical reference, without a cross-owner SQL foreign key. Comparison drafts optionally pin one succeeded interpretation; null retains the original human structured-profile path. Campaign and cost SQL stay with their owners. See [the interpretation contract](campaigns.md#bounded-natural-language-interpretation).

Provider cost provenance shares the same physical accounting tables. Explicit provider-basis final reconciliation and meter recovery preserve named targets, immutable original rates, overage visibility and one-use dispatch without relabelling synthetic evidence. Accounting reports its generic declared bounded-provider contract premise; the interpretation configuration owns exact verified snapshot/input/output provenance.

Current-KB comparison drafts pin `knowledge_query_result_id`; their legacy `knowledge_run_id`, `dataset_id` and `dataset_digest` are null. A database check requires exactly one of these source modes. Frozen drafts keep their original run/dataset fields and a null query link. Draft coverage includes the immutable actual execution profile. `comparison_support.source_assertion_id` and `decision_note_support.source_assertion_id` are nullable for metric-only account support; the observation and linked query manifest retain exact metric/derivation identities.
