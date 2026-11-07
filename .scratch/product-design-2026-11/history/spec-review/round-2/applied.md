# Round-2 revision as applied by the coordinator

Inputs: [review](review.md) (14 findings: 2 critical, 9 major, 3 minor) and [validation](validation.md) (VERDICT: YES; 12 accepted with modifications, R2-F08 accepted in full, R2-F13 rejected). The coordinator applied validation.md section 4 through [apply_round2.py](apply_round2.py) on `task4/plan_source.json` and regenerated the package. This was the final round at the user's request.

## Applied

- 4a: 45 specs and 89 edges, each with a rationale. New: `operator-commands`, `discovery-operations-screen`, `monitoring-readiness`, `detail-route-readiness`, `email-readiness`. Computed results match validation.md: early real-data check at depth 5 (about 4.5 illustrative weeks), release record at depth 7 (about 9.5 weeks, was 12).
- 4b: `monitoring-depth-and-timing` rewritten as projections of the stored receipt plus a versioned live-page eligibility rule (no columns, no backfill); `client-foundation` narrowed to M with reducers moved to graph, chart and chat specs; `early-marketer-checkpoint` moved into M0 on pre-UI paths; `local-runtime` gains lifecycle maintenance and gives its health UI to the D1 screen; `pilot-scale-retrieval` records index and ranking choices and wires derived scope into installed paths; `inbox-email` defaults to SMTP with Message-ID from the delivery key; `provider-readiness` split into four claimable rows; checklist venues are now only the browser checkpoint and the release record.
- 4c: requirement-ID moves and user-decision `affects` lists.
- 4d: gap-analysis and architecture-target corrections. Both documents are now `.md.tmpl` templates with `{{slug}}` tokens rendered by `write_sequence.py`, so future reordering cannot leave stale S-numbers. The sequence adds size-weighted critical paths and the shared "second to land owns the integration" rule.
- 4e: W02 widened and retitled, blocking no spec; U1, U3, U5 and U7 extended; W01 still blocks only `enable-richer-agent`.

## Deviations

None material. The S01 start gate is unchanged (R2-F13 rejected). No re-measurement spec and no W03 issue were added; the U3 revisit is owned by the probe's X row, with a recorded contingency spec if U3 is answered (a) or (b).
