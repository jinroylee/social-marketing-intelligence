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
