CREATE TABLE IF NOT EXISTS operational_review_packets (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL,
    request_id text NOT NULL,
    request_digest text NOT NULL,
    result_kind text NOT NULL CHECK (result_kind IN ('recommendation','answer','semantic_alert')),
    result_id uuid NOT NULL,
    include_synthetic boolean NOT NULL,
    manifest jsonb NOT NULL,
    exported_by text NOT NULL,
    exported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id)
);

CREATE TABLE IF NOT EXISTS operational_review_records (
    id uuid PRIMARY KEY,
    packet_id uuid NOT NULL REFERENCES operational_review_packets(id),
    version integer NOT NULL CHECK (version BETWEEN 1 AND 50),
    request_id text NOT NULL,
    request_digest text NOT NULL,
    attribution jsonb NOT NULL,
    body jsonb,
    purged boolean NOT NULL DEFAULT false,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (packet_id, request_id),
    UNIQUE (packet_id, version)
);
