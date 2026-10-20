# Knowledge publication

Own atomic, bounded availability of ingested support through `KnowledgePublications`. Use `IngestedEvidence` for source reads and `KnowledgeStore.read_interpretations` for existing caption interpretations. Publication membership stores exact IDs and versions; source text stays with its existing owner.

Publish from trusted human or automation actors. Persist the actual actor kind/identity. A workspace/request identity pins the ordered payload and producer; identical retries return the original publication and changed payloads conflict. Commit only process-permitted, current support with matching interpretation dependencies, holding owner locks through commit.

Public list/read operations can join a caller-owned transaction; source and derivation locks remain held through the caller’s dependent commit. List bounds and newest-first ordering support bounded query traversal. Use `find_request` for source-free committed metadata after a lost acknowledgment, preserving original producer/coverage without reselecting support. Reopen exact membership under the requested current policy. Preserve original publication coverage/time and expose current support health separately. A retry cannot repair purged interpretation copies or substitute newer source support. Source-only accounts may retain unknown profile/interpretation attributes.

`publish` and `unpublished` also join a caller-owned connection, including legacy identity updates and policy locks. Task workers supply their execution session so losing it aborts actual publication effects. A separate connection after a task ownership check breaks that fence. Unchanged-support filtering remains capture comparison across committed publications; simultaneous distinct tasks can prepare the same capture before either publishes.

Use source-owned capture/mapping/selection content identities for `unpublished` comparisons. Require current process permission and current derivations on both sides; ingestion/publication time or new UUIDs alone cannot establish a usable task update. Preserve exact publication membership while lazily filling legacy identity metadata.

Keep frozen datasets unchanged. Acquisition authority, current-KB search and consequential query-result pinning belong to their own workflows. Update the knowledge contract, physical ERD and local publication surface when changing this interface.
