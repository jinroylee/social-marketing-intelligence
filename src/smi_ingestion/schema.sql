CREATE TABLE IF NOT EXISTS ingestion_runs (
    id UUID PRIMARY KEY,
    manifest_path TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    checkpoint JSONB NOT NULL DEFAULT '{"index":0}'::jsonb,
    limits JSONB NOT NULL,
    bytes_used BIGINT NOT NULL DEFAULT 0,
    requests_used INTEGER NOT NULL DEFAULT 0,
    records_used INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',
    input_complete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS requests_used INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS input_complete BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS source_observations (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES ingestion_runs(id),
    item_index INTEGER NOT NULL,
    source_item_key TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    format_version TEXT NOT NULL,
    reference TEXT NOT NULL,
    platform_hint TEXT,
    resource_kind_hint TEXT,
    native_id_hint TEXT,
    handle_hint TEXT,
    media_type TEXT NOT NULL,
    captured_at TIMESTAMPTZ,
    source_as_of TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    policy JSONB NOT NULL,
    synthetic BOOLEAN NOT NULL,
    payload_hash TEXT NOT NULL,
    payload_path TEXT,
    coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    UNIQUE (run_id, item_index)
);

CREATE TABLE IF NOT EXISTS ingestion_issues (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES ingestion_runs(id),
    observation_id UUID REFERENCES source_observations(id),
    code TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_entities (
    id UUID PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('account', 'content')),
    synthetic BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS external_identities (
    platform TEXT NOT NULL,
    namespace TEXT NOT NULL,
    kind TEXT NOT NULL,
    native_id TEXT NOT NULL,
    synthetic BOOLEAN NOT NULL,
    entity_id UUID NOT NULL REFERENCES canonical_entities(id),
    PRIMARY KEY (platform, namespace, kind, native_id, synthetic)
);

CREATE TABLE IF NOT EXISTS derivations (
    id UUID PRIMARY KEY,
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    mapper_key TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (observation_id, mapper_key, policy_version)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_derivation ON derivations(observation_id) WHERE active;

CREATE TABLE IF NOT EXISTS field_assertions (
    id UUID PRIMARY KEY,
    derivation_id UUID NOT NULL REFERENCES derivations(id),
    entity_id UUID NOT NULL REFERENCES canonical_entities(id),
    field TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('observed', 'not_returned', 'unavailable', 'removed')),
    value JSONB,
    source_locator TEXT NOT NULL,
    reason TEXT,
    UNIQUE (derivation_id, entity_id, field, source_locator)
);

CREATE TABLE IF NOT EXISTS metric_observations (
    id UUID PRIMARY KEY,
    derivation_id UUID NOT NULL REFERENCES derivations(id),
    entity_id UUID NOT NULL REFERENCES canonical_entities(id),
    definition TEXT NOT NULL,
    native_name TEXT NOT NULL,
    value NUMERIC,
    raw_display TEXT,
    precision TEXT NOT NULL CHECK (precision IN ('exact', 'approximate')),
    unit TEXT NOT NULL,
    measured_at TIMESTAMPTZ,
    source_locator TEXT NOT NULL,
    UNIQUE (derivation_id, entity_id, definition, source_locator)
);

CREATE TABLE IF NOT EXISTS unresolved_candidates (
    id UUID PRIMARY KEY,
    derivation_id UUID NOT NULL REFERENCES derivations(id),
    kind TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    reason TEXT NOT NULL,
    UNIQUE (derivation_id, kind, source_locator)
);

CREATE INDEX IF NOT EXISTS observation_run_status ON source_observations(run_id, status);
CREATE INDEX IF NOT EXISTS identity_entity ON external_identities(entity_id);
