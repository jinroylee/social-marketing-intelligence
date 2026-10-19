# Offline acquisition tasks

[`smi_tasks`](../src/smi_tasks/__init__.py) owns durable admission and outcomes for campaign and exactly approved assistant submissions through one synthetic offline route. Existing campaigns, ingestion evidence and knowledge publication retain their owners. Tasks are distinct from ingestion runs and publications: accepting work does not fetch, and fetching alone does not establish usable knowledge.

## Submission and authority

`AcquisitionTasks(db, workspace_id="local", route=OfflineRoute(...), authority=TaskAuthority(...))` accepts trusted operator configuration. Authority defaults to no campaign submitters or human approvers. `TaskAuthority.for_human(actor_id)` assigns campaign submission and proposal approval to the named local human; `campaign_automations=frozenset({...})` separately configures specific campaign service principals. A generic automation actor, an assistant identity or a client-supplied human label grants neither role. Keep this configuration at the application composition boundary, outside assistant/model/form control. These are trusted local identities, not hosted authentication. `OfflineRoute(manifest_path, version="offline-fixture-v1", limits=RunLimits(max_requests=10, max_pages=10, max_records=10))` permits only `fixture-json` with `synthetic: true`. Request/page/record limits are positive integers at most 100 and bytes at most 10 MiB; the default byte limit is 1 MiB. The configured manifest is at most 1 MiB and 100 input items. An empty item list is a completed empty input. Live collectors and models are unavailable through this task path.

`submit_campaign(campaign_id, actor, brief_id=..., purpose=..., request_id=...)` reopens an existing workspace-owned campaign and admits only its current exact brief. The trusted caller constructs `ActorContext`; both its kind and identity must have the configured campaign role. The operation establishes `origin="campaign"` itself. The acknowledgment commits the task ID, workspace, initiating human/automation actor, campaign/brief/version, purpose, unverified input references, route/configuration version, manifest digest, request identity, resource limits, one-attempt limit and queued status. It reads configuration, without reading payloads or executing the collector. Purpose or source/model text cannot select another origin or approve assistant work.

A workspace/request identity binds that complete scope and initiator. Identical concurrent retries return one task; changed scope, configuration, limits or actor conflicts. A successful retry can reopen the original acknowledgment after the campaign has a successor brief. New submissions against the old brief fail. The queued task retains its original authorized scope. An unconfigured route, foreign workspace or unsupported route cannot dispatch work.

## Supplied proposal and exact approval

`EnrichmentProposal(purpose, intent, subject_ids=(), search_queries=())` supplies an explicit `refresh`, `fill` or `expansion` intent and at least one subject or search query. Each list has at most 30 unique nonempty values, each at most 500 characters; purpose is at most 1000 characters. `from_document` parses these JSON fields and rejects authority/extra fields. `save_proposal(proposal, actor, request_id=...)` saves one immutable identifiable revision. A changed proposal requires a fresh revision ID and fresh approval. Saving grants no acquisition authority and submits no task.

The saved scope includes workspace, purpose/intent, subject/search scope, the configured fixture route/version, exact supplied references, manifest digest, and resource limits. `read_proposal(id, actor)` reopens that scope, its digest, actual proposer, creation time and optional human approval/task; `list_proposals(actor)` returns at most 100 recent revision summaries. The digest pins the entire executable configuration as well as the stated intent. The synthetic route executes its listed supplied references; subject/search metadata does not claim that it performs query discovery or verifies the references' semantic relevance. No conversation or model generation is installed.

`approve_proposal(id, human_actor, scope_digest=..., request_id=...)` is the explicit human action. It requires both human kind and an operator-configured approver identity and records exact revision/digest, workspace, actual human and time. Saved assistant text, a generated `approved` statement, actor kind alone and a supplied origin cannot create approval. Approval does not execute acquisition.

`submit_approved(id, actor, approval_id=..., scope_digest=..., request_id=...)` requires the actual stored approval for that exact workspace/revision/digest. It submits only the saved scope and limits, establishes assistant origin itself, and retains the actual submitter separately from the human approver. A replaced manifest fails before acknowledgment; the worker checks again before collection. Current route configuration cannot broaden the saved scope. Explicit on-demand subjects/queries need no scheduled-keyword membership; scheduled authorization remains unimplemented.

Concurrent identical request-ID retries return the same proposal, approval or task. A changed payload under that identity conflicts. One proposal has at most one approval, and one approval has at most one logical task. Reusing an already approved proposal or submitted approval with a different request ID is explicitly rejected with `approval_request_conflict` / `task_request_conflict`; retain the original request identity for retries. Approval reads expose that identity so a human can finish an approved but not yet submitted action after restart. An approved task's scope, approver and attribution remain historical even when the server is reopened with different operator configuration.

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

Interrupted active execution raises `task_execution_incomplete`; it does not silently reacquire input. Single-worker recovery, preserving successful subsets as `partial_update`, pending providers, competing-worker claims, completion notifications and costs are subsequent work. The reserved partial outcome is not emitted by this implementation. Existing direct ingestion commands retain their independent capabilities; authorization for this offline task path grants none of their live capabilities.

## Local operation

After `smi-ingest migrate`, create a campaign through the existing campaign operation. Then use its exact current brief:

```bash
uv run smi-ingest submit-campaign-task CAMPAIGN_ID --brief-id BRIEF_ID --purpose "Fill campaign coverage" --request-id task-1 --offline-manifest examples/synthetic/json-manifest.json --actor local-marketer
uv run smi-ingest inspect-task TASK_ID
uv run smi-ingest run-offline-task TASK_ID --worker-id local-offline-task-worker
```

Submission returns immediately. Run the bounded worker separately; it uses persisted configuration and needs no caller-supplied route. A failed task command exits nonzero. Operators can run `smi-review --offline-manifest examples/synthetic/json-manifest.json`; campaign pages link a same-origin/CSRF-protected submission form, `/tasks` lists work and `/tasks/TASK_ID` reopens outcomes. Inspection needs no route configuration. Browser actor, origin and limits are established by the server, with forged authority fields rejected.

Supply and review an assistant proposal locally, then explicitly approve its exact displayed digest:

```bash
uv run smi-ingest save-proposal proposal.json --request-id proposal-1 --offline-manifest examples/synthetic/json-manifest.json --actor local-assistant
uv run smi-ingest inspect-proposal PROPOSAL_ID
uv run smi-ingest approve-proposal PROPOSAL_ID --scope-digest DIGEST --request-id approval-1 --actor local-marketer --approve-exact-scope
uv run smi-ingest submit-approved-task PROPOSAL_ID --approval-id APPROVAL_ID --scope-digest DIGEST --request-id assistant-task-1 --actor local-assistant
```

`proposal.json` contains only `purpose`, `intent`, `subject_ids` and `search_queries`; the last two are JSON arrays, with at least one nonempty. The local CLI is an operator boundary: approval runs as its named human; save/submit use the named automation identity. Do not expose its approval or campaign commands as unrestricted assistant tools. In the browser, **Proposals** opens `/proposals`, `/proposals/new` saves supplied scope, and `/proposals/ID` shows the immutable revision before a checked explicit approval action. The protected approval POST saves human approval then acknowledges its one task; the original request identity permits safe completion if interrupted between those commits. Proposal and task pages reopen each other's exact links without configured route access. Existing Host/Origin/CSRF checks and escaped rendering apply.
