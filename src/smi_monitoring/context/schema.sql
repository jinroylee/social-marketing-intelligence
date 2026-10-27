CREATE TABLE IF NOT EXISTS monitoring_alert_investigations (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL,
    request_id text NOT NULL,
    request_digest text NOT NULL,
    alert_kind text NOT NULL CHECK (alert_kind IN ('quantitative', 'semantic')),
    alert_id uuid NOT NULL,
    query_result_id uuid NOT NULL REFERENCES knowledge_query_results(id),
    recent_dependencies jsonb NOT NULL,
    method_version text NOT NULL,
    include_synthetic boolean NOT NULL,
    explanation_withheld boolean NOT NULL DEFAULT FALSE,
    recorded_by text NOT NULL,
    actor_kind text NOT NULL,
    recorded_at timestamptz NOT NULL,
    UNIQUE (workspace_id, request_id)
);
