# Set pilot acceptance criteria and the first implementation boundary

Label: wayfinder:grilling
Type: grilling
Mode: HITL
Status: resolved
Assignee: Codex / pilot_acceptance
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 05, 06, 11

## Question

What measurable evidence will demonstrate that this pilot helps the marketer, and which minimal implementation boundaries and first end-to-end build step will satisfy that test within the selected workload and cost limits?

Decide review responsibilities, Japanese-language evaluation examples and thresholds, evidence traceability, uncertainty and missing-data behavior, source freshness, cost ceilings, and the measurement plan's limits. Specify how a locally run system becomes reviewable by the marketer and what must change for later hosted operation. Use the proposed Python/PostgreSQL architecture as a starting point, checking each service against the actual workflow and solo maintenance burden. Identify any still-open prerequisites rather than presenting unresolved assumptions as a build-ready specification. Production code and deployment are outside this ticket.

Explicitly establish whether the marketer can review Japanese-language originals or needs translation, and who can validate consequential language judgments. This was unanswered during the first-decision discussion and has not been assumed. Compare the pilot against the stated intuition/monitoring baseline using reviewable evidence and a chosen usefulness measure. A sales objective does not by itself provide sales outcome data: decide the initial sales measurement plan and distinguish missing commercial results from observed evidence of content/product relevance.

Respect the accepted [decision-brief workflow](05-prototype-marketer-output.md): evaluate bounded market monitoring and human-initiated campaign planning as independently usable features over shared evidence. Include cases in which monitoring yields an insight without creating a campaign, and a marketer starts a campaign without a detected signal. Define the minimum monitoring output that belongs in this pilot alongside automated draft comparisons and marketer-confirmed shortlist persistence.

## Comments

### Draft acceptance and handoff — 2026-10-12

Prepared [Pilot acceptance and first implementation boundary](../pilot-acceptance.md) after the builder confirmed account-first candidates, exploratory briefs with explicit unknowns, and snapshot investigations. The draft separates mandatory provenance/persistence/policy correctness, scoped Japanese-language review, marketer usefulness, and initial workload/cost decisions. It identifies the missing reset-safe offline importer and frozen evidence-set reader, then proposes a campaign-first local vertical slice and independent monitoring over the same evidence boundary. No source calls, provider spending, production code, infrastructure changes, or schema changes were made.

Three live decisions remain: actual Japanese-original review capability or translation path; the proposed two-task usefulness gate against the marketer's manual approach; and the proposed local preparation workload and USD 10 rolling-30-day LLM development allowance. The issue remains claimed until those human answers settle the requirements. Translation-only or no language reviewer can validate technical/workflow behavior while consequential Japanese judgments remain provisional; neither path silently establishes original-language accuracy.

### Review path answered — 2026-10-12

The builder selected **translation-assisted review only**. No Japanese-original reviewer is established. The accepted path displays original permitted caption spans and attributable translations, records unresolved nuance and detected material errors, and leaves consequential Japanese-original judgments provisional. The usefulness question prompted an explanation rather than acceptance; a simplified follow-up remains pending together with the workload/spend decision. A lack of detected translation errors is not treated as validated original-language accuracy.

### Estimated envelope answered — 2026-10-12

The builder accepted the small initial workload/spend envelope with one explicit correction: **do not enforce those limits programmatically; estimate budget by purpose**. The plan therefore uses about 10 monitoring summaries and 10 comparison preparations per month, with roughly USD 10 per 30 days of model use, as forecasting assumptions. Monitoring, comparison, translation and evaluation costs are estimated; actual usage can inform the estimate. There is no budget/workload rejection, spending limiter or automatic threshold stop. Existing ingestion run bounds are separate established behavior. The draft's initially proposed hard-cap behavior has been superseded by this human decision. The usefulness follow-up remains unanswered, so this ticket stays claimed.

### Usefulness gate answered — 2026-10-12

After explanation, the builder selected **use these usefulness and evidence checks**. The marketer evaluates an independently saved monitoring investigation and a human-started campaign comparison against the same fixed evidence/manual baseline. A useful evidence-linked finding and a reusable keep/exclude/defer candidate decision are required; detected material errors must be corrected or withheld. Manual/system time is recorded without a required speed improvement. Original Japanese nuance remains provisional under the confirmed translation-assisted path.

## Answer

Resolved through the builder's live answers. [Pilot acceptance and first implementation boundary](../pilot-acceptance.md) contains the reviewable acceptance cases and first build handoff.

- **Independent product paths:** saved snapshot investigations summarize product/topic evidence without creating campaigns. A marketer can start a five-element brief without a signal; automation prepares account comparisons and a human confirms a versioned exploratory shortlist.
- **Review and usefulness:** translation-assisted review is the available path. Show originals and attributable translations, correct detected material errors, and visibly retain provisional Japanese judgments. Evaluate one investigation and one campaign against the same-sample manual approach; require a useful source-backed observation and a reusable keep/exclude/defer decision. Record task times without a speed target or claim of sales lift.
- **Correctness:** all source-backed displayed findings and selected-account reasons need resolvable permitted support; preserve exact identity, times, dataset membership, missingness/conflicts and human review state. Saving/reopening must survive restart, retry and revision conflicts. Permission withdrawal must affect introduced extracts, copied reasons and saved views, not only raw files. The artifact specifies failure cases for these behaviors without claiming existing implementation passes them.
- **Operating estimate:** one local marketer, about 10 monitoring summaries and 10 comparison preparations per month, and roughly USD 10 per 30 days of model use are planning assumptions. Estimate monitoring/comparison/translation/evaluation costs and optionally observe actual usage. Do not enforce budget/workload limits programmatically. Zero new paid data calls are needed for the frozen-sample build; established ingestion run bounds remain separate.
- **First build boundary:** from a clean local PostgreSQL database, import the 19-post snapshot with reset-safe origin-to-local evidence bindings, create a human campaign brief, prepare a source-linked account draft, confirm it as a human, and reopen the exact saved revision in a local browser. Add independent saved investigations and descriptive measurement/decision-note revisions over the same evidence seam to complete pilot acceptance. Use one Python application/PostgreSQL instance; production deployment, vendor choice, ranking infrastructure and a universal ontology are unnecessary to specify this slice.
- **Sales and source limits:** a measurement plan records proposed measures, definitions, windows, source/matching assumptions and gaps; it computes no sales attribution or lift from public engagement. Live sources, creator histories, commercial outcomes, qualified Japanese-original validation and hosted/public readiness remain later milestones. Deferred source/use-rights review is not publication clearance.

No destination-level decision remains that blocks the specified first local slice. Extraction rules, migration details and the local template framework are bounded implementation choices; broader evaluation and outcome learning are later iterations. Verification checked the accepted domain contract, sample memberships/current code seams and all local artifact links. No production code, schema, provider calls, spending or implementation-test results were introduced by this planning resolution.
