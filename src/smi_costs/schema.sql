CREATE TABLE IF NOT EXISTS cost_scopes (
    workspace_id text NOT NULL,
    scope_id text NOT NULL,
    configuration jsonb NOT NULL,
    operator_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, scope_id)
);
CREATE TABLE IF NOT EXISTS cost_operations (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL,
    scope_id text NOT NULL,
    request_id text NOT NULL,
    actor_id text NOT NULL,
    actor_kind text NOT NULL CHECK (actor_kind IN ('human','automation')),
    method text NOT NULL,
    task_id uuid,
    attempt_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, request_id),
    UNIQUE (workspace_id, id),
    FOREIGN KEY (workspace_id, scope_id) REFERENCES cost_scopes(workspace_id, scope_id),
    CHECK ((task_id IS NULL) = (attempt_id IS NULL))
);
CREATE TABLE IF NOT EXISTS cost_entries (
    workspace_id text NOT NULL,
    measurement_id text NOT NULL,
    operation_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind IN ('usage','forecast','commitment','unknown','meter_failure')),
    body jsonb NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, measurement_id),
    FOREIGN KEY (workspace_id, operation_id) REFERENCES cost_operations(workspace_id, id)
);
