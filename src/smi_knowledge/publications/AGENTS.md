# Knowledge publication

Own atomic, bounded availability of ingested support through `KnowledgePublications`. Use `IngestedEvidence` for source reads and `KnowledgeStore.read_interpretations` for existing caption interpretations. Publication membership stores exact IDs and versions; source text stays with its existing owner.

Publish from trusted human or automation actors. Persist the actual actor kind/identity. A workspace/request identity pins the ordered payload and producer; identical retries return the original publication and changed payloads conflict. Commit only process-permitted, current support with matching interpretation dependencies, holding owner locks through commit.

Reopen exact membership under the requested current policy. Preserve original publication coverage/time and expose current support health separately. A retry cannot repair purged interpretation copies or substitute newer source support. Source-only accounts may retain unknown profile/interpretation attributes.

Keep frozen datasets unchanged. Acquisition authority, current-KB search and consequential query-result pinning belong to their own workflows. Update the knowledge contract, physical ERD and local publication surface when changing this interface.
