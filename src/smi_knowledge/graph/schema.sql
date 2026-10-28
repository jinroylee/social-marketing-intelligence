CREATE TABLE IF NOT EXISTS knowledge_graph_searches (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL,
    request_id text NOT NULL,
    request_digest text NOT NULL,
    query_result_id uuid NOT NULL REFERENCES knowledge_query_results(id),
    scope jsonb NOT NULL,
    method_version text NOT NULL,
    producer_id text NOT NULL,
    producer_kind text NOT NULL CHECK (producer_kind IN ('human', 'automation')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id)
);
