# Offline acquisition tasks

[`smi_tasks`](../src/smi_tasks/__init__.py) owns durable admission and outcomes for one campaign-authorized synthetic offline route. Existing campaigns, ingestion evidence and knowledge publication retain their owners. Tasks are distinct from ingestion runs and publications: accepting work does not fetch, and fetching alone does not establish usable knowledge.

## Submission and authority

`AcquisitionTasks(db, workspace_id="local", route=OfflineRoute(...))` accepts a trusted operator's route configuration. `OfflineRoute(manifest_path, version="offline-fixture-v1", limits=RunLimits(max_requests=10, max_pages=10, max_records=10))` permits only `fixture-json` with `synthetic: true`. Request/page/record limits are positive integers at most 100 and bytes at most 10 MiB; the default byte limit is 1 MiB. The configured manifest is at most 1 MiB and 100 input items. An empty item list is a completed empty input. Live collectors and models are unavailable through this task path.

`submit_campaign(campaign_id, actor, brief_id=..., purpose=..., request_id=...)` reopens an existing workspace-owned campaign and admits only its current exact brief. The trusted caller constructs `ActorContext`; the operation establishes `origin="campaign"` itself. The acknowledgment commits the task ID, workspace, initiating human/automation actor, campaign/brief/version, purpose, unverified input references, route/configuration version, manifest digest, request identity, resource limits, one-attempt limit and queued status. It reads configuration, without reading payloads or executing the collector. Purpose or source/model text cannot select another origin or approve assistant work.

A workspace/request identity binds that complete scope and initiator. Identical concurrent retries return one task; changed scope, configuration, limits or actor conflicts. A successful retry can reopen the original acknowledgment after the campaign has a successor brief. New submissions against the old brief fail. The queued task retains its original authorized scope. An unconfigured route, foreign workspace or unsupported route cannot dispatch work.

## Bounded worker and outcomes

`OfflineTaskWorker(db, evidence_root, workspace_id="local").run_one(task_id, automation_actor)` executes at most one queued task. It commits the attempt ID, actual worker actor, ingestion run ID and collecting phase before collection. The existing ingestion runner uses a registry containing only the local JSON fixture collector/mapper. A changed manifest digest fails before collection; the runner also rechecks its persisted digest. Restarting the application does not change scope or limits.

Task detail records collecting, ingesting and publishing progress separately, actual collected/applied/quarantined observation counts, request/byte usage, sanitized issue codes, exact attempts/runs and publication IDs. The runner performs collection and normalization within the collecting call; the ingesting checkpoint records its returned ingestion report. A process crash during that call therefore retains collecting status until recovery is implemented.

| Outcome | Meaning in this slice |
| --- | --- |
| `usable_update` | At least one exact newly usable capture/mapping selection committed to a knowledge publication with the actual automation producer. This does not establish complete market coverage or business value. |
| `no_usable_update` | Empty eligible input, no supported fields/metrics, or the exact capture/mapping selection is already published and currently usable. No new publication is created and market absence is unknown. |
| `failure` | Collection, limits, normalization, process permission or publication prevented this task from declaring a usable update. The phase/code and actual counts remain visible. Already ingested support stays outside KB queries until explicitly published. |

`KnowledgePublications.unpublished` owns comparison against currently usable committed publications using source-owned capture/mapping/selection identities. Equal bytes, provenance, capture/source-as-of times, mapper/policy methods and selected logical fields/metrics are unchanged even when a new run produces new UUIDs. A later capture or mapping is distinct; publication/ingestion time alone does not establish a new benefit. Current process permission and current derivation health apply to both inputs. This is capture identity comparison, not general semantic deduplication or a freshness judgment.

`read(task_id, actor)` survives restart and returns immutable scope/attribution plus current task metadata without copying source text or payloads. `list(actor)` returns at most 100 newest workspace tasks. Publication details and subsequent `KnowledgeQueries` searches reopen source values under current permissions, with explicit synthetic visibility. Terminal worker retries reopen the same attempt/run/publications without additional collection.

Interrupted active execution raises `task_execution_incomplete`; it does not silently reacquire input. Single-worker recovery, preserving successful subsets as `partial_update`, pending providers, competing-worker claims, completion notifications, assistant approval and costs are subsequent work. The reserved partial outcome is not emitted by this implementation. Existing direct ingestion commands retain their independent capabilities; authorization for this offline task path grants none of their live capabilities.

## Local operation

After `smi-ingest migrate`, create a campaign through the existing campaign operation. Then use its exact current brief:

```bash
uv run smi-ingest submit-campaign-task CAMPAIGN_ID --brief-id BRIEF_ID --purpose "Fill campaign coverage" --request-id task-1 --offline-manifest examples/synthetic/json-manifest.json --actor local-marketer
uv run smi-ingest inspect-task TASK_ID
uv run smi-ingest run-offline-task TASK_ID --worker-id local-offline-task-worker
```

Submission returns immediately. Run the bounded worker separately; it uses persisted configuration and needs no caller-supplied route. A failed task command exits nonzero. Operators can run `smi-review --offline-manifest examples/synthetic/json-manifest.json`; campaign pages link a same-origin/CSRF-protected submission form, `/tasks` lists work and `/tasks/TASK_ID` reopens outcomes. Inspection needs no route configuration. Browser actor, origin and limits are established by the server, with forged authority fields rejected.
