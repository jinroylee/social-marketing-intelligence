CREATE TABLE IF NOT EXISTS knowledge_brands (
    workspace_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    preferred_name TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    PRIMARY KEY (workspace_id, brand_id)
);

CREATE TABLE IF NOT EXISTS knowledge_products (
    workspace_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    preferred_name TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    PRIMARY KEY (workspace_id, product_id),
    FOREIGN KEY (workspace_id, brand_id) REFERENCES knowledge_brands(workspace_id, brand_id)
);

CREATE TABLE IF NOT EXISTS knowledge_catalogs (
    workspace_id TEXT NOT NULL,
    catalog_id TEXT NOT NULL,
    digest TEXT NOT NULL,
    document JSONB NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, catalog_id)
);

CREATE TABLE IF NOT EXISTS knowledge_runs (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    catalog_id TEXT NOT NULL,
    method_version TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT 'initial',
    recorded_by TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    coverage JSONB NOT NULL,
    FOREIGN KEY (workspace_id, dataset_id) REFERENCES evidence_sets(workspace_id, dataset_id),
    FOREIGN KEY (workspace_id, catalog_id) REFERENCES knowledge_catalogs(workspace_id, catalog_id)
);

ALTER TABLE knowledge_runs ADD COLUMN IF NOT EXISTS request_id TEXT NOT NULL DEFAULT 'initial';
-- Upgrade the previous semantic-key uniqueness without replacing historical runs.
DO $$
DECLARE old_constraint RECORD;
BEGIN
    FOR old_constraint IN
        SELECT c.conname FROM pg_constraint c
        WHERE c.conrelid = 'knowledge_runs'::regclass AND c.contype = 'u'
        AND (SELECT array_agg(a.attname::text ORDER BY k.position)
             FROM unnest(c.conkey) WITH ORDINALITY AS k(column_number, position)
             JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.column_number)
            = ARRAY['workspace_id', 'dataset_id', 'catalog_id', 'method_version']
    LOOP
        EXECUTE format('ALTER TABLE knowledge_runs DROP CONSTRAINT %I', old_constraint.conname);
    END LOOP;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS knowledge_run_request
    ON knowledge_runs(workspace_id, dataset_id, catalog_id, method_version, request_id);

CREATE TABLE IF NOT EXISTS knowledge_assertions (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES knowledge_runs(id),
    subject_id UUID NOT NULL REFERENCES canonical_entities(id),
    source_assertion_id UUID NOT NULL REFERENCES field_assertions(id),
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    predicate TEXT NOT NULL CHECK (predicate IN ('brand_mention','product_mention','script_evidence','topic_mention','literal_marker')),
    value JSONB,
    basis TEXT NOT NULL CHECK (basis IN ('derived')),
    span_start INTEGER NOT NULL,
    span_end INTEGER NOT NULL CHECK (span_end > span_start AND span_start >= 0),
    excerpt TEXT,
    review_status TEXT NOT NULL DEFAULT 'provisional',
    support_state TEXT NOT NULL DEFAULT 'active' CHECK (support_state IN ('active','withdrawn')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS knowledge_assertion_support ON knowledge_assertions(observation_id);

CREATE TABLE IF NOT EXISTS knowledge_publications (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    method_version TEXT NOT NULL,
    producer_id TEXT NOT NULL,
    synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    producer_kind TEXT NOT NULL CHECK (producer_kind IN ('human','automation')),
    coverage JSONB NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id)
);

CREATE TABLE IF NOT EXISTS knowledge_publication_support (
    publication_id UUID NOT NULL REFERENCES knowledge_publications(id),
    position INTEGER NOT NULL,
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    derivation_id UUID NOT NULL,
    assertion_ids UUID[] NOT NULL,
    metric_ids UUID[] NOT NULL,
    PRIMARY KEY (publication_id, position),
    UNIQUE (publication_id, observation_id),
    FOREIGN KEY (derivation_id, observation_id) REFERENCES derivations(id, observation_id)
);

CREATE TABLE IF NOT EXISTS knowledge_publication_interpretations (
    publication_id UUID NOT NULL REFERENCES knowledge_publications(id),
    position INTEGER NOT NULL,
    interpretation_id UUID NOT NULL REFERENCES knowledge_assertions(id),
    PRIMARY KEY (publication_id, position),
    UNIQUE (publication_id, interpretation_id)
);

CREATE TABLE IF NOT EXISTS knowledge_query_results (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    method_version TEXT NOT NULL,
    query_scope JSONB NOT NULL,
    purpose TEXT NOT NULL CHECK (purpose IN ('display','process')),
    synthetic BOOLEAN NOT NULL,
    producer_id TEXT NOT NULL,
    producer_kind TEXT NOT NULL CHECK (producer_kind IN ('human','automation')),
    coverage JSONB NOT NULL,
    unknowns JSONB NOT NULL,
    queried_at TIMESTAMPTZ NOT NULL,
    UNIQUE (workspace_id, request_id)
);

CREATE TABLE IF NOT EXISTS knowledge_query_members (
    result_id UUID NOT NULL REFERENCES knowledge_query_results(id),
    position INTEGER NOT NULL,
    publication_id UUID NOT NULL REFERENCES knowledge_publications(id),
    observation_id UUID NOT NULL REFERENCES source_observations(id),
    derivation_id UUID NOT NULL,
    assertion_ids UUID[] NOT NULL,
    metric_ids UUID[] NOT NULL,
    interpretation_ids UUID[] NOT NULL,
    versions JSONB NOT NULL,
    PRIMARY KEY (result_id, position),
    FOREIGN KEY (derivation_id, observation_id) REFERENCES derivations(id, observation_id)
);

ALTER TABLE knowledge_publication_support ADD COLUMN IF NOT EXISTS content_version text;
CREATE INDEX IF NOT EXISTS publication_support_content_version ON knowledge_publication_support(content_version);
