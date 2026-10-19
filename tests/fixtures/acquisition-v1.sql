CREATE TABLE IF NOT EXISTS acquisition_tasks (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL,
    request_id text NOT NULL,
    request_digest text NOT NULL,
    origin text NOT NULL CHECK (origin = 'campaign'),
    campaign_id uuid NOT NULL REFERENCES campaigns(id),
    brief_id uuid NOT NULL REFERENCES campaign_briefs(id),
    initiator_id text NOT NULL,
    initiator_kind text NOT NULL CHECK (initiator_kind IN ('human','automation')),
    scope_version text NOT NULL,
    scope jsonb NOT NULL,
    limits jsonb NOT NULL,
    attempt_limit integer NOT NULL DEFAULT 1 CHECK (attempt_limit > 0),
    manifest_path text NOT NULL,
    manifest_hash text NOT NULL,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','collecting','ingesting','publishing','completed','failed')),
    outcome text CHECK (outcome IN ('usable_update','partial_update','no_usable_update','failure')),
    coverage jsonb NOT NULL DEFAULT '{}',
    failure_phase text,
    failure_code text,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    UNIQUE (workspace_id,request_id)
);
CREATE TABLE IF NOT EXISTS acquisition_attempts (
    id uuid PRIMARY KEY,
    task_id uuid NOT NULL REFERENCES acquisition_tasks(id),
    number integer NOT NULL,
    run_id uuid NOT NULL UNIQUE REFERENCES ingestion_runs(id),
    producer_id text NOT NULL,
    producer_kind text NOT NULL CHECK (producer_kind = 'automation'),
    phases jsonb NOT NULL DEFAULT '["collecting"]',
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    UNIQUE(task_id,number)
);
CREATE TABLE IF NOT EXISTS acquisition_task_publications (
    task_id uuid NOT NULL REFERENCES acquisition_tasks(id),
    publication_id uuid NOT NULL REFERENCES knowledge_publications(id),
    PRIMARY KEY(task_id,publication_id)
);
