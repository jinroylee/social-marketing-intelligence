-- Schedule ownership is independent of monitoring and task execution effects.
CREATE TABLE IF NOT EXISTS keyword_schedules (
    workspace_id text PRIMARY KEY,
    accounting_timezone text NOT NULL,
    current_version integer NOT NULL DEFAULT 0,
    last_tick_at timestamptz
);
CREATE TABLE IF NOT EXISTS keyword_schedule_configurations (
    workspace_id text NOT NULL REFERENCES keyword_schedules(workspace_id),
    version integer NOT NULL CHECK (version > 0),
    document jsonb NOT NULL,
    digest text NOT NULL,
    operator_id text NOT NULL,
    recorded_at timestamptz NOT NULL,
    PRIMARY KEY(workspace_id,version)
);
CREATE TABLE IF NOT EXISTS keyword_schedule_occurrences (
    id uuid PRIMARY KEY,
    workspace_id text NOT NULL REFERENCES keyword_schedules(workspace_id),
    configuration_version integer NOT NULL,
    keyword_key text NOT NULL,
    accounting_day date NOT NULL,
    context jsonb NOT NULL,
    initiator_id text NOT NULL,
    initiator_kind text NOT NULL CHECK (initiator_kind IN ('human','automation')),
    status text NOT NULL CHECK (status IN ('pending','submitted','refused')),
    reason text,
    task_id uuid UNIQUE REFERENCES acquisition_tasks(id),
    recorded_at timestamptz NOT NULL,
    FOREIGN KEY(workspace_id,configuration_version) REFERENCES keyword_schedule_configurations(workspace_id,version),
    UNIQUE(workspace_id,accounting_day,keyword_key),
    CHECK ((status='submitted') = (task_id IS NOT NULL))
);
