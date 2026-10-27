CREATE TABLE IF NOT EXISTS monitoring_semantic_assessments (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    window_id UUID NOT NULL REFERENCES monitoring_windows(id),
    assessment_digest TEXT NOT NULL,
    method JSONB NOT NULL,
    configuration JSONB NOT NULL,
    input_observation_ids UUID[] NOT NULL,
    input_digest TEXT NOT NULL,
    status TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reason TEXT,
    limitations JSONB NOT NULL,
    judgments JSONB NOT NULL DEFAULT '[]',
    support_purged BOOLEAN NOT NULL DEFAULT FALSE,
    operation_id UUID REFERENCES cost_operations(id),
    usage JSONB,
    recorded_by TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    UNIQUE (workspace_id, assessment_digest)
);
CREATE TABLE IF NOT EXISTS monitoring_semantic_requests (
    workspace_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    assessment_id UUID NOT NULL REFERENCES monitoring_semantic_assessments(id),
    PRIMARY KEY (workspace_id, request_id)
);
CREATE TABLE IF NOT EXISTS monitoring_semantic_alerts (
    id UUID PRIMARY KEY,
    assessment_id UUID NOT NULL UNIQUE REFERENCES monitoring_semantic_assessments(id),
    notification_id UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL
);
