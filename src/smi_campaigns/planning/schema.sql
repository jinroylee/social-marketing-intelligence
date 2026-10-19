CREATE TABLE IF NOT EXISTS measurement_plan_revisions (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    brief_id UUID NOT NULL REFERENCES campaign_briefs(id),
    shortlist_id UUID NOT NULL REFERENCES shortlist_revisions(id),
    version INTEGER NOT NULL,
    document JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status='proposed'),
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, version),
    UNIQUE (campaign_id, request_id)
);
CREATE TABLE IF NOT EXISTS decision_note_revisions (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    shortlist_id UUID NOT NULL REFERENCES shortlist_revisions(id),
    version INTEGER NOT NULL,
    text TEXT,
    basis TEXT NOT NULL DEFAULT 'human_supplied',
    support_ids UUID[] NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, version),
    UNIQUE (campaign_id, request_id)
);
CREATE TABLE IF NOT EXISTS decision_note_support (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_id UUID NOT NULL REFERENCES decision_note_revisions(id),
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    source_assertion_id UUID NOT NULL REFERENCES field_assertions(id),
    interpretation_id UUID REFERENCES knowledge_assertions(id)
);
