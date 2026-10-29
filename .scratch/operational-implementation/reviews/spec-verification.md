# Spec review verification

- Baseline `6220fff49b5b8e982ef5a8d54b7c788e45b0f648` and pinned software head `b75b8b6a454ae9abdb5f7f7450837b79d7801753` both resolve; the requested three-dot diff is nonempty. Reviewed the complete supplied 175-commit list and authoritative ticket acceptance scope. Later root commits were metadata only; no subsequent software changes were reviewed.
- Preserved the existing 890-test broad PASS. No broad check was rerun.
- Targeted command: `UV_OFFLINE=1 uv run --locked python .scratch/operational-implementation/reviews/spec-predispatch-repro.py`; exit 0, 0.84 seconds. Public `CampaignStore.recommend_ranked`, `KnowledgePublications.read` and `EvidenceStore.revoke` use a real isolated PostgreSQL schema. Only the external model transport is simulated. A controlled transport-classification pause occurs after committed comparison preparation and before model I/O; revocation completes and a public publication read confirms unavailable support before the pause is released. Result:

```json
{
  "revoked_before_model_dispatch": true,
  "model_calls_after_revocation": 1,
  "outcome": "stale",
  "reason": "ranking_support_changed",
  "saved_shortlist": null,
  "charged_synthetic_amount": "0.175"
}
```

- Closed suspicion, not a finding: requiring `input_tokens_details.cache_write_tokens` matches the current official Responses contract. Read-only official documentation verification on 2026-10-29 used the fetched [OpenAI prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching), whose Response-usage examples and measurement section include this field. The direct response-reference HTML exceeded the web reader's size limit; the fetched guide independently establishes the field. No live model/API/source request, credential lookup or paid execution occurred. This lookup does not establish account access or live readiness.
- Reviewed current source-policy/copy behavior, task/proposal and recorded schedule authority, worker ownership and receipt recovery, cost liabilities/reconciliation, assistant/semantic full-input checks, graph/lineage composition and quality annotation semantics. Ticket 39 remains actual-human validation, outside fixable software findings.
