CREATE TABLE IF NOT EXISTS monitoring_promotions (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    window_id UUID NOT NULL REFERENCES monitoring_windows(id),
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    outcome TEXT NOT NULL,
    items JSONB NOT NULL,
    UNIQUE (workspace_id, request_id)
);
CREATE TABLE IF NOT EXISTS monitoring_promoted_captures (
    workspace_id TEXT NOT NULL,
    monitoring_observation_id UUID NOT NULL REFERENCES recent_x_observations(id),
    run_id UUID NOT NULL REFERENCES ingestion_runs(id),
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    publication_id UUID NOT NULL REFERENCES knowledge_publications(id),
    PRIMARY KEY (workspace_id, monitoring_observation_id)
);
