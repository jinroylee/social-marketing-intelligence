CREATE TABLE IF NOT EXISTS discovery_history (
    task_id uuid PRIMARY KEY REFERENCES acquisition_tasks(id),
    sequence bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
    workspace_id text NOT NULL,
    query_key text NOT NULL,
    query_scope jsonb NOT NULL,
    retrieval_context jsonb NOT NULL,
    policy jsonb,
    decision text NOT NULL CHECK (decision IN ('retrieve','skip')),
    reason text NOT NULL,
    freshness text NOT NULL,
    prior_task_id uuid REFERENCES discovery_history(task_id),
    prior_publication_id uuid REFERENCES knowledge_publications(id),
    decided_at timestamptz NOT NULL,
    support jsonb NOT NULL DEFAULT '[]',
    publication_id uuid REFERENCES knowledge_publications(id),
    usable_publication_ids jsonb NOT NULL DEFAULT '[]',
    processing_complete boolean NOT NULL DEFAULT false,
    outcome text,
    failure jsonb,
    completed_at timestamptz
);
CREATE INDEX IF NOT EXISTS discovery_history_query ON discovery_history(workspace_id,query_key,sequence DESC);
