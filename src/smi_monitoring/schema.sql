CREATE TABLE IF NOT EXISTS monitoring_investigations (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    scope_version INTEGER NOT NULL DEFAULT 1,
    insight_version INTEGER NOT NULL DEFAULT 0,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id)
);
CREATE TABLE IF NOT EXISTS investigation_scopes (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL REFERENCES monitoring_investigations(id),
    version INTEGER NOT NULL,
    document JSONB NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (investigation_id, version),
    UNIQUE (investigation_id, request_id)
);
CREATE TABLE IF NOT EXISTS insight_revisions (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL REFERENCES monitoring_investigations(id),
    scope_id UUID NOT NULL REFERENCES investigation_scopes(id),
    version INTEGER NOT NULL,
    knowledge_run_id UUID NOT NULL REFERENCES knowledge_runs(id),
    dataset_id TEXT NOT NULL,
    dataset_digest TEXT NOT NULL,
    method_version TEXT NOT NULL,
    coverage JSONB NOT NULL,
    limitations JSONB NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    prepared_by TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (investigation_id, version),
    UNIQUE (investigation_id, request_id)
);
CREATE TABLE IF NOT EXISTS insight_findings (
    id UUID PRIMARY KEY,
    insight_id UUID NOT NULL REFERENCES insight_revisions(id),
    position INTEGER NOT NULL,
    body JSONB,
    UNIQUE (insight_id, position)
);
CREATE TABLE IF NOT EXISTS insight_support (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    finding_id UUID NOT NULL REFERENCES insight_findings(id),
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    source_assertion_id UUID NOT NULL REFERENCES field_assertions(id),
    interpretation_id UUID REFERENCES knowledge_assertions(id)
);
