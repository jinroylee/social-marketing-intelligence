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

`OfflineTaskWorker(db, evidence_root, workspace_id="local").run_one(task_id, automation_actor)` executes or resumes one admitted task. It commits the attempt ID, initial worker actor, ingestion run ID and collecting phase before collection. Recovery keeps the same attempt/run and original authorized scope/limits, recording each recovery actor in `resumed_by`. The registry contains only the synthetic JSON fixture route. The worker and runner verify the saved manifest digest before collection; a prepared publication or committed publication can finish without reopening the input files.

The runner commits each observation with its collection checkpoint, then commits canonical mapping separately. Public `IngestionRunner.resume(run_id, on_commit=...)` reports `evidence_committed` and `canonical_committed` with the observation ID; `inspect(run_id)` reads committed counts without advancing the run. The task worker persists those phases/counts, then saves the exact ordered observation/derivation/assertion/metric selection before publication. Recovery processes retained pending evidence, reuses applied mappings and publishes the saved selection rather than collecting or selecting it again. An interrupted non-retained payload that cannot be replayed fails explicitly; recovery does not refetch it.

Task progress distinguishes collecting, evidence commit, canonical commit, publication preparation, publication commit, waiting and completion. `on_progress=callback` at trusted worker composition receives source-free task snapshots after these owner commits. Callback exceptions propagate as interruptions, retaining committed effects. The publication callback runs before the task completion acknowledgment. `KnowledgePublications.find_request(request_id, actor, include_synthetic=...)` reopens source-free committed publication metadata, including its actual producer and original coverage. Task reads use that operation to expose a committed publication even if the task/publication link was not yet saved. Recovery checks it before unchanged-support filtering and retains the original usable/partial outcome, support and publication identity under a different recovery actor.

Coverage reports requested inputs, collected/applied/quarantined observations, remaining inputs, eligible/unchanged/unpublished/published members, request/byte use, unresolved identities, missing fields and sanitized issue codes. Remaining inputs count uncollected, pending and quarantined records; identity-free applied input is separately ineligible. A successful subset can publish even when another input fails or a bound stops collection. Unpublished support remains outside current-KB queries. Publication validates current process permission and derivation health again, so withdrawal after preparation fails at publication with no usable-update claim.

| Outcome | Meaning in this slice |
| --- | --- |
| `usable_update` | At least one newly usable exact selection committed, with no reported execution failure. This establishes neither complete market coverage nor business value. |
| `partial_update` | A valid selection committed while collection, limits or mapping left a failed/incomplete remainder. The publication, original failed phase/code and actual coverage are retained. |
| `no_usable_update` | Empty eligible input, no supported fields/metrics, or all eligible support is already published and currently usable, with no execution failure. No new publication or market-absence claim is created. |
| `failure` | No newly usable subset could be committed because collection, limits, normalization, policy or publication failed. Phase/code and actual counts remain visible. |

`KnowledgePublications.unpublished` compares currently usable committed publications using source-owned capture/mapping/selection identities. Equal bytes, provenance, capture/source-as-of times, mapper/policy methods and selected logical fields/metrics are unchanged even when a new run produces new UUIDs. A later capture or mapping is distinct; publication/ingestion time alone establishes no new benefit. Current process permission and derivation health apply to both inputs. This is capture identity comparison, not semantic deduplication or a freshness judgment.

`read(task_id, actor)` survives restart and returns immutable scope/attribution, durable progress and exact support/publication metadata without copying source text or payloads. `list(actor)` returns at most 100 newest workspace tasks. Publication details and `KnowledgeQueries` reopen values under current permissions with explicit synthetic visibility. Terminal retries reopen the same outcome without additional collection.

### Simulated waiting and recovery limits

A trusted `collector=...` worker port can simulate fixture I/O; it still occupies only the `fixture-json` collector slot and grants no live-route or admission authority. `CollectedBatch` can return no observations, an opaque next checkpoint, actual `request_attempts` and `waiting="provider_pending"` or `"provider_operation_ambiguous"`. Ingestion atomically saves the checkpoint, wait reason and usage. `provider_pending` is an adapter promise that checkpoint replay safely resumes an existing operation; it must not start another paid operation. Ambiguous operations remain waiting with `resumable=false`; repeated worker execution makes no collector call. Exhausted bounds stop pending work before another call. Task metadata exposes the reason/resumability without exposing the opaque operation handle. No real provider is enabled, and ambiguous-operation reconciliation is future route-specific work.

Run workers sequentially. Competing-worker claims/fencing, completion notifications and monetary controls remain subsequent work. Recovery preserves the original exact campaign or human-approved proposal authority. Existing direct ingestion commands retain their independent capabilities; offline task authorization grants none of their live capabilities.

## Local operation

After `smi-ingest migrate`, create a campaign through the existing campaign operation. Then use its exact current brief:

```bash
uv run smi-ingest submit-campaign-task CAMPAIGN_ID --brief-id BRIEF_ID --purpose "Fill campaign coverage" --request-id task-1 --offline-manifest examples/synthetic/json-manifest.json --actor local-marketer
uv run smi-ingest inspect-task TASK_ID
uv run smi-ingest run-offline-task TASK_ID --worker-id local-offline-task-worker
```

Submission returns immediately. Run the bounded worker separately, reusing the same command/task ID to resume interrupted work; it uses persisted configuration and needs no caller-supplied route. A failed task command exits nonzero. Operators can run `smi-review --offline-manifest examples/synthetic/json-manifest.json`; campaign pages link a same-origin/CSRF-protected submission form, `/tasks` lists work and `/tasks/TASK_ID` reopens outcomes. Inspection needs no route configuration. Browser actor, origin and limits are established by the server, with forged authority fields rejected.

Supply and review an assistant proposal locally, then explicitly approve its exact displayed digest:

```bash
uv run smi-ingest save-proposal proposal.json --request-id proposal-1 --offline-manifest examples/synthetic/json-manifest.json --actor local-assistant
uv run smi-ingest inspect-proposal PROPOSAL_ID
uv run smi-ingest approve-proposal PROPOSAL_ID --scope-digest DIGEST --request-id approval-1 --actor local-marketer --approve-exact-scope
uv run smi-ingest submit-approved-task PROPOSAL_ID --approval-id APPROVAL_ID --scope-digest DIGEST --request-id assistant-task-1 --actor local-assistant
```

`proposal.json` contains only `purpose`, `intent`, `subject_ids` and `search_queries`; the last two are JSON arrays, with at least one nonempty. The local CLI is an operator boundary: approval runs as its named human; save/submit use the named automation identity. Do not expose its approval or campaign commands as unrestricted assistant tools. In the browser, **Proposals** opens `/proposals`, `/proposals/new` saves supplied scope, and `/proposals/ID` shows the immutable revision before a checked explicit approval action. The protected approval POST saves human approval then acknowledges its one task; the original request identity permits safe completion if interrupted between those commits. Proposal and task pages reopen each other's exact links without configured route access. Existing Host/Origin/CSRF checks and escaped rendering apply.
