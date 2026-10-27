CREATE TABLE IF NOT EXISTS assistant_enrichment_requests (
    id UUID PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    answer_id UUID NOT NULL REFERENCES knowledge_answers(id),
    requester_id TEXT NOT NULL,
    include_synthetic BOOLEAN NOT NULL,
    gap TEXT NOT NULL,
    proposal_body JSONB NOT NULL,
    proposal_request_id TEXT NOT NULL UNIQUE,
    proposal_id UUID UNIQUE REFERENCES enrichment_proposals(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id)
);
