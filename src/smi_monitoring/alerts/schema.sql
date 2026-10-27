CREATE TABLE IF NOT EXISTS monitoring_volume_assessments (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    detection_window_id UUID NOT NULL REFERENCES monitoring_windows(id),
    baseline_window_id UUID REFERENCES monitoring_windows(id),
    pair_digest TEXT NOT NULL,
    method JSONB NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('significant_change','no_change','not_assessable')),
    limitations JSONB NOT NULL,
    recorded_by TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    UNIQUE (workspace_id, pair_digest)
);
CREATE TABLE IF NOT EXISTS monitoring_detection_requests (
    workspace_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    assessment_id UUID NOT NULL REFERENCES monitoring_volume_assessments(id),
    PRIMARY KEY (workspace_id, request_id)
);
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id UUID PRIMARY KEY,
    assessment_id UUID NOT NULL UNIQUE REFERENCES monitoring_volume_assessments(id),
    notification_id UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL
);
