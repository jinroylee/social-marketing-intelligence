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

-- A configuration revision changes the cap, never the workspace/day identity.
CREATE TABLE IF NOT EXISTS scheduled_post_days (
    workspace_id text NOT NULL REFERENCES keyword_schedules(workspace_id),
    accounting_day date NOT NULL,
    accounting_timezone text NOT NULL,
    day_start timestamptz NOT NULL,
    day_end timestamptz NOT NULL,
    allowance_version integer NOT NULL,
    allowance_limit integer NOT NULL CHECK (allowance_limit > 0),
    PRIMARY KEY(workspace_id,accounting_day),
    FOREIGN KEY(workspace_id,allowance_version) REFERENCES keyword_schedule_configurations(workspace_id,version)
);
CREATE TABLE IF NOT EXISTS scheduled_post_admissions (
    observation_id uuid PRIMARY KEY REFERENCES source_observations(id),
    occurrence_id uuid NOT NULL REFERENCES keyword_schedule_occurrences(id),
    workspace_id text NOT NULL,
    accounting_day date NOT NULL,
    platform text,
    namespace text,
    native_id text,
    synthetic boolean NOT NULL,
    disposition text NOT NULL CHECK (disposition IN ('new_posts','known_refreshes','deduplicated_posts','limit_excluded_posts','ineligible_posts')),
    FOREIGN KEY(workspace_id,accounting_day) REFERENCES scheduled_post_days(workspace_id,accounting_day)
);
CREATE UNIQUE INDEX IF NOT EXISTS scheduled_unique_new_post ON scheduled_post_admissions
    (workspace_id,accounting_day,platform,namespace,native_id,synthetic) WHERE disposition='new_posts';

-- Upgrade queued/completed history without mutating immutable occurrence context.
-- Only enforced canonical effects create admission rows; earlier usage is not invented.
INSERT INTO scheduled_post_days(workspace_id,accounting_day,accounting_timezone,day_start,day_end,allowance_version,allowance_limit)
SELECT DISTINCT ON (o.workspace_id,o.accounting_day)
    o.workspace_id,o.accounting_day,o.context->>'accounting_timezone',
    (o.context->>'day_start')::timestamptz,(o.context->>'day_end')::timestamptz,
    c.version,(c.document->>'daily_allowance')::integer
FROM keyword_schedule_occurrences o JOIN keyword_schedule_configurations c
    ON c.workspace_id=o.workspace_id AND c.recorded_at < (o.context->>'day_end')::timestamptz
ORDER BY o.workspace_id,o.accounting_day,c.version DESC
ON CONFLICT(workspace_id,accounting_day) DO NOTHING;
