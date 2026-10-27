# Local task completion inbox

Own `CompletionInbox` reads and reconciliation of source-free task completion identities. Read [the task contract](../../../docs/tasks.md#durable-completion-inbox) before changing delivery, migration or current-policy navigation. Task admission, scope and execution remain with the parent package; publications and their current support remain with `KnowledgePublications`.

The worker inserts the one event in its fenced completion transaction, alongside the terminal outcome, attempt completion and publication link. Keep every write on that existing ownership connection. `task_id` is unique; retries preserve the event identity. Migration and workspace-scoped reconciliation insert only missing events for terminal tasks, preserving their historical outcome and completion time.

Persist identity, task reference and time only. Build messages from sanitized task coverage/failure and publication reads at display time. Recheck exact support through the publication owner's display interface; expose source-dependent navigation only when some pinned support is available and current. Historical publication counts and outcome remain distinct from current availability. Copying source wording, references, task-purpose text or cached availability into events would bypass policy.

Keep the inbox local and bounded. Expose campaign/source identities and a regeneration link only for usable/partial automatic campaign-discovery outcomes with currently permitted published support. No-update/failure/unavailable support conveys no new usable evidence. Execution belongs to `smi_tasks.campaigns`; external message transports and spending remain separate workflows. Verify delivery through public inbox/worker and HTTP/CLI operations with real PostgreSQL, including completion rollback, lost acknowledgment, process death, concurrent retries, upgrades and policy withdrawal.

`read_task(task_id, actor)` reopens the exact event independently of the newest-100 list window. The assistant journey composes this public read; it does not query completion tables or cache source availability.
