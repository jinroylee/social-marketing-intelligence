CREATE TABLE IF NOT EXISTS enrichment_proposals (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL,
    request_id text NOT NULL,
    scope_digest text NOT NULL,
    scope jsonb NOT NULL,
    scope_version text NOT NULL,
    limits jsonb NOT NULL,
    manifest_path text NOT NULL,
    manifest_hash text NOT NULL,
    proposer_id text NOT NULL,
    proposer_kind text NOT NULL CHECK (proposer_kind IN ('human','automation')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(workspace_id,request_id)
);
CREATE TABLE IF NOT EXISTS enrichment_approvals (
    id uuid PRIMARY KEY,
    proposal_id uuid NOT NULL UNIQUE REFERENCES enrichment_proposals(id),
    workspace_id text NOT NULL,
    request_id text NOT NULL,
    scope_digest text NOT NULL,
    approver_id text NOT NULL,
    approver_kind text NOT NULL CHECK (approver_kind = 'human'),
    approved_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(workspace_id,request_id)
);
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

-- Explicit upgrade of the original campaign-only task contract. Existing rows
-- retain their required campaign/brief basis through the origin-basis check.
ALTER TABLE acquisition_tasks ADD COLUMN IF NOT EXISTS approval_id uuid UNIQUE REFERENCES enrichment_approvals(id);
ALTER TABLE acquisition_tasks ALTER COLUMN campaign_id DROP NOT NULL;
ALTER TABLE acquisition_tasks ALTER COLUMN brief_id DROP NOT NULL;
ALTER TABLE acquisition_tasks DROP CONSTRAINT IF EXISTS acquisition_tasks_origin_check;
ALTER TABLE acquisition_tasks ADD CONSTRAINT acquisition_tasks_origin_check CHECK (origin IN ('campaign','assistant'));
ALTER TABLE acquisition_tasks DROP CONSTRAINT IF EXISTS acquisition_tasks_origin_basis_check;
ALTER TABLE acquisition_tasks ADD CONSTRAINT acquisition_tasks_origin_basis_check CHECK (
    (origin = 'campaign' AND campaign_id IS NOT NULL AND brief_id IS NOT NULL AND approval_id IS NULL)
    OR (origin = 'assistant' AND campaign_id IS NULL AND brief_id IS NULL AND approval_id IS NOT NULL)
);

-- Durable single-worker restart frontier; phase metadata contains no source values.
ALTER TABLE acquisition_tasks ADD COLUMN IF NOT EXISTS progress jsonb NOT NULL DEFAULT '{}';
ALTER TABLE acquisition_attempts ADD COLUMN IF NOT EXISTS resumed_by jsonb NOT NULL DEFAULT '[]';
ALTER TABLE acquisition_attempts ADD COLUMN IF NOT EXISTS publication_support jsonb;
ALTER TABLE acquisition_tasks DROP CONSTRAINT IF EXISTS acquisition_tasks_status_check;
ALTER TABLE acquisition_tasks ADD CONSTRAINT acquisition_tasks_status_check CHECK (status IN ('queued','collecting','ingesting','publishing','waiting','completed','failed'));
