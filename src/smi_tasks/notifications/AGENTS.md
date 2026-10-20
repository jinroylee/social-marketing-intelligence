# Local task completion inbox

Own `CompletionInbox` reads and reconciliation of source-free task completion identities. Read [the task contract](../../../docs/tasks.md#durable-completion-inbox) before changing delivery, migration or current-policy navigation. Task admission, scope and execution remain with the parent package; publications and their current support remain with `KnowledgePublications`.

The worker inserts the one event in its fenced completion transaction, alongside the terminal outcome, attempt completion and publication link. Keep every write on that existing ownership connection. `task_id` is unique; retries preserve the event identity. Migration and workspace-scoped reconciliation insert only missing events for terminal tasks, preserving their historical outcome and completion time.

Persist identity, task reference and time only. Build messages from sanitized task coverage/failure and publication reads at display time. Recheck exact support through the publication owner's display interface; expose source-dependent navigation only when some pinned support is available and current. Historical publication counts and outcome remain distinct from current availability. Copying source wording, references, task-purpose text or cached availability into events would bypass policy.

Keep the inbox local and bounded. External message transports, campaign regeneration and spending belong to separate workflows. Verify delivery through public inbox/worker and HTTP/CLI operations with real PostgreSQL, including completion rollback, lost acknowledgment, process death, concurrent retries, upgrades and policy withdrawal.
