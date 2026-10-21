CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    brief_version INTEGER NOT NULL DEFAULT 1,
    shortlist_version INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id)
);

CREATE TABLE IF NOT EXISTS campaign_briefs (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    version INTEGER NOT NULL,
    document JSONB NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, version),
    UNIQUE (campaign_id, request_id)
);

-- Existing revisions did not record a profile; never invent their historical version.
ALTER TABLE campaign_briefs ADD COLUMN IF NOT EXISTS executable_profile JSONB;

CREATE TABLE IF NOT EXISTS comparison_drafts (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    brief_id UUID NOT NULL REFERENCES campaign_briefs(id),
    knowledge_run_id UUID NOT NULL REFERENCES knowledge_runs(id),
    dataset_id TEXT NOT NULL,
    dataset_digest TEXT NOT NULL,
    method_version TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    coverage JSONB NOT NULL,
    prepared_by TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, request_id)
);

CREATE TABLE IF NOT EXISTS comparison_candidates (
    id UUID PRIMARY KEY,
    comparison_id UUID NOT NULL REFERENCES comparison_drafts(id),
    position INTEGER NOT NULL,
    account_key JSONB NOT NULL,
    account_id UUID REFERENCES canonical_entities(id),
    origin TEXT NOT NULL CHECK (origin IN ('marketer_known','retrieved','both')),
    body JSONB,
    UNIQUE (comparison_id, account_key),
    UNIQUE (comparison_id, position)
);

CREATE TABLE IF NOT EXISTS comparison_support (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES comparison_candidates(id),
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    source_assertion_id UUID NOT NULL REFERENCES field_assertions(id),
    interpretation_id UUID REFERENCES knowledge_assertions(id)
);

CREATE TABLE IF NOT EXISTS shortlist_revisions (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    brief_id UUID NOT NULL REFERENCES campaign_briefs(id),
    comparison_id UUID NOT NULL REFERENCES comparison_drafts(id),
    version INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft','confirmed')),
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, version),
    UNIQUE (campaign_id, request_id)
);

CREATE TABLE IF NOT EXISTS shortlist_selections (
    id UUID PRIMARY KEY,
    revision_id UUID NOT NULL REFERENCES shortlist_revisions(id),
    candidate_id UUID NOT NULL REFERENCES comparison_candidates(id),
    reason TEXT,
    reason_basis TEXT NOT NULL DEFAULT 'human_supplied',
    support_ids UUID[] NOT NULL,
    acknowledged_unknowns JSONB NOT NULL,
    reason_withdrawn BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (revision_id, candidate_id)
);

-- Attempts retain only validated interpretation and source-free method/cost provenance.
CREATE TABLE IF NOT EXISTS campaign_criteria_interpretations (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    brief_id UUID NOT NULL REFERENCES campaign_briefs(id),
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in_progress','succeeded','blocked','invalid','refused','incomplete','meter_failure','transport_uncertain','stale')),
    reason TEXT,
    configuration JSONB,
    operation_id UUID,
    usage JSONB,
    executable_profile JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (campaign_id, request_id)
);

ALTER TABLE comparison_drafts ADD COLUMN IF NOT EXISTS criteria_interpretation_id UUID
    REFERENCES campaign_criteria_interpretations(id);

-- A comparison pins either a legacy frozen run or an immutable current-KB query.
ALTER TABLE comparison_drafts ALTER COLUMN knowledge_run_id DROP NOT NULL;
ALTER TABLE comparison_drafts ALTER COLUMN dataset_id DROP NOT NULL;
ALTER TABLE comparison_drafts ALTER COLUMN dataset_digest DROP NOT NULL;
ALTER TABLE comparison_drafts ADD COLUMN IF NOT EXISTS knowledge_query_result_id UUID REFERENCES knowledge_query_results(id);
ALTER TABLE comparison_support ALTER COLUMN source_assertion_id DROP NOT NULL;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='comparison_drafts'::regclass AND conname='comparison_source_mode') THEN
        ALTER TABLE comparison_drafts ADD CONSTRAINT comparison_source_mode CHECK (
            (knowledge_query_result_id IS NULL AND knowledge_run_id IS NOT NULL AND dataset_id IS NOT NULL AND dataset_digest IS NOT NULL)
            OR (knowledge_query_result_id IS NOT NULL AND knowledge_run_id IS NULL AND dataset_id IS NULL AND dataset_digest IS NULL)
        );
    END IF;
END $$;

-- Legacy human revisions keep their exact status/attribution and unrecorded order.
ALTER TABLE shortlist_revisions DROP CONSTRAINT IF EXISTS shortlist_revisions_status_check;
ALTER TABLE shortlist_revisions ADD CONSTRAINT shortlist_revisions_status_check CHECK (status IN ('draft','confirmed','generated'));
ALTER TABLE shortlist_revisions ADD COLUMN IF NOT EXISTS actor_kind TEXT NOT NULL DEFAULT 'human';
ALTER TABLE shortlist_revisions ADD COLUMN IF NOT EXISTS method_version TEXT;
ALTER TABLE shortlist_revisions ADD COLUMN IF NOT EXISTS ordering TEXT;
ALTER TABLE shortlist_revisions ADD COLUMN IF NOT EXISTS selection_summary JSONB;
ALTER TABLE shortlist_selections ADD COLUMN IF NOT EXISTS position INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS shortlist_selection_order ON shortlist_selections(revision_id,position);
ALTER TABLE shortlist_revisions ADD COLUMN IF NOT EXISTS source_shortlist_id UUID REFERENCES shortlist_revisions(id);

-- Source-derived inputs and validated judgments share candidate dependency cleanup.
ALTER TABLE comparison_candidates ADD COLUMN IF NOT EXISTS ranking_input JSONB;
ALTER TABLE comparison_candidates ADD COLUMN IF NOT EXISTS ranking_judgment JSONB;

CREATE TABLE IF NOT EXISTS campaign_ranking_assessments (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    brief_id UUID NOT NULL REFERENCES campaign_briefs(id),
    comparison_id UUID NOT NULL UNIQUE REFERENCES comparison_drafts(id),
    shortlist_id UUID UNIQUE REFERENCES shortlist_revisions(id),
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    producer_id TEXT NOT NULL,
    candidate_ids UUID[] NOT NULL,
    expected_brief_version INTEGER NOT NULL,
    expected_shortlist_version INTEGER NOT NULL,
    include_synthetic BOOLEAN NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in_progress','succeeded','blocked','invalid','refused','incomplete','meter_failure','transport_uncertain','stale')),
    reason TEXT,
    configuration JSONB,
    operation_id UUID,
    usage JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (campaign_id, request_id)
);
