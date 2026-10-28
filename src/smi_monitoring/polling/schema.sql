CREATE TABLE IF NOT EXISTS monitoring_poll_activations (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    topic_key TEXT NOT NULL,
    topic_revision_id UUID NOT NULL REFERENCES monitoring_topic_revisions(id),
    topic_version INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    next_window_end TIMESTAMPTZ NOT NULL,
    activated_by TEXT NOT NULL,
    activated_at TIMESTAMPTZ NOT NULL,
    enabled BOOLEAN NOT NULL,
    checked_at TIMESTAMPTZ,
    UNIQUE (workspace_id, request_id)
);
CREATE TABLE IF NOT EXISTS monitoring_poll_occurrences (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    topic_key TEXT NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    topic_revision_id UUID NOT NULL REFERENCES monitoring_topic_revisions(id),
    state TEXT NOT NULL,
    acquisition JSONB NOT NULL,
    reason TEXT,
    operation_id UUID,
    window_id UUID REFERENCES monitoring_windows(id),
    initiated_by TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    dispatched_by TEXT,
    recorded_at TIMESTAMPTZ NOT NULL,
    UNIQUE (workspace_id, topic_key, window_end),
    activation_id UUID NOT NULL REFERENCES monitoring_poll_activations(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS monitoring_one_active_poll ON monitoring_poll_activations(workspace_id,topic_key) WHERE enabled;
CREATE TABLE IF NOT EXISTS monitoring_source_cooldowns (
    route TEXT PRIMARY KEY,
    next_allowed_at TIMESTAMPTZ NOT NULL
);
