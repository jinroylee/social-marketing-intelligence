CREATE TABLE IF NOT EXISTS monitoring_source_policies (
    workspace_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    document JSONB NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, context_id)
);
CREATE TABLE IF NOT EXISTS monitoring_topics (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    topic_key TEXT NOT NULL,
    version INTEGER NOT NULL,
    UNIQUE (workspace_id, topic_key)
);
CREATE TABLE IF NOT EXISTS monitoring_topic_revisions (
    id UUID PRIMARY KEY,
    topic_id UUID NOT NULL REFERENCES monitoring_topics(id),
    version INTEGER NOT NULL,
    document JSONB NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    UNIQUE (topic_id, version),
    UNIQUE (topic_id, request_id)
);
CREATE TABLE IF NOT EXISTS monitoring_windows (
    id UUID PRIMARY KEY,
    topic_id UUID NOT NULL REFERENCES monitoring_topics(id),
    revision_id UUID NOT NULL REFERENCES monitoring_topic_revisions(id),
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    coverage JSONB NOT NULL,
    acquisition JSONB NOT NULL,
    collected_by TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL,
    UNIQUE (topic_id, window_end)
);
CREATE TABLE IF NOT EXISTS recent_x_observations (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    capture_id TEXT NOT NULL,
    native_id TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    capture_key TEXT NOT NULL,
    capture_digest TEXT NOT NULL,
    acquisition JSONB NOT NULL,
    missing_fields JSONB NOT NULL,
    policy_context_id TEXT NOT NULL,
    captured_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    metric_measured_at TIMESTAMPTZ,
    imported_at TIMESTAMPTZ NOT NULL,
    retain_until TIMESTAMPTZ NOT NULL,
    body JSONB,
    purged_reason TEXT,
    FOREIGN KEY (workspace_id, policy_context_id) REFERENCES monitoring_source_policies(workspace_id, context_id),
    UNIQUE (workspace_id, capture_key)
);
CREATE TABLE IF NOT EXISTS monitoring_window_members (
    window_id UUID NOT NULL REFERENCES monitoring_windows(id),
    observation_id UUID NOT NULL REFERENCES recent_x_observations(id),
    PRIMARY KEY (window_id, observation_id)
);
CREATE TABLE IF NOT EXISTS monitoring_x_withdrawals (
    workspace_id TEXT NOT NULL,
    native_id TEXT NOT NULL,
    withdrawn_by TEXT NOT NULL,
    withdrawn_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (workspace_id, native_id)
);
