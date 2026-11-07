# Review the r1 design

Review this exact [prototype](prototype.html), [design specification](design-spec.md) and [99-row requirement mapping](fr-ui-traceability.md). Task 1's shared-understanding confirmation is complete. Actual human approval of the UI is still pending, and Task 4 remains gated until that review.

The design is entirely fixture-based. It sends no source requests or email, performs no paid work and does not connect to the installed application. Reloading clears all state. Creating a new fixture campaign resets the active campaign's shortlist history; this is a prototype limit, not the proposed production persistence behavior.

## Open the design

The coordinator preview is <http://127.0.0.1:8876/prototype.html?variant=A#campaigns>. If it is unavailable, double-click `prototype.html`, or run the following command from the repository root:

```sh
python -m http.server 8877 --bind 127.0.0.1 --directory .scratch/product-design-2026-11/task3
```

Then open <http://127.0.0.1:8877/prototype.html?variant=A#campaigns>. Preview is local only. The HTML requires no dependencies or external assets.

Variant A is the recommended evidence workspace. Variant B is a full-width campaign desk with evidence below. Variant C is a research notebook with evidence before the work area. Use the floating arrows or `?variant=B` and `?variant=C`; left/right arrow keys also switch layouts when focus is outside a form, dialog or graph.

## Verification already performed

The JavaScript parses. The source/fixture-state checks run with `node .scratch/product-design-2026-11/task3/verify-prototype.cjs`. They use minimal element stubs, not a DOM renderer or browser, and exercise approval gating/revision changes, append-only shortlist history, human curation membership, publication separation, waiting, context-only investigation, promotion selection, graph filtering/traversal/withdrawal, bilingual draft retention and the ten-keyword bound. [Actual output](verification-results.txt) records the current pass count. The traceability generator checks all 99 Task 1 IDs with no omissions or duplicates.

The coordinator's browser preview attempt was rejected because the user declined browser permission. No alternate browser automation, origin or transport was used. Browser clicks, actual focus/keyboard behavior, screenshots, responsive rendering, screen-reader output and visual quality have not been verified. The scenarios below are pending manual or newly authorized browser review, not a record of completed tests. No actual user/language/usefulness approval is implied.

The required repository check was run; [shared check output](shared-check-results.txt) records its actual result. That check validates the existing repository, not these browser interactions.

## M01. Brief to saved shortlist

1. Start on Campaigns with fixture shortlist v2. Inspect the original criteria, unknown policies, executable interpretation and selected support. Confirm that missing fees, availability and audience location are legible.
2. Open New campaign. Enter a name, then save an empty criterion. The form should preserve your input and require a criterion. Complete the brief and save it. The empty shortlist should offer Generate recommendation.
3. Generate a recommendation. It should save automatically without approval, show relative fit/unknowns and expose a separate configured coverage-discovery task. The incomplete account remains eligible.
4. Inspect a candidate and open its graph. Return to the campaign. Curate a shortlist with only one selected account and save the human revision. Confirm membership and attribution differ from the automated version.
5. Regenerate from current knowledge. Read the scope summary, then create the successor. Open Version history and inspect both prior membership and current version. Earlier brief/support/method/author should remain fixed.

Review whether the coverage warning guides the next decision without blocking a useful limited result. Human curation must remain optional.

## M02. Preserve bilingual work

1. Open Brief & criteria and change name, brand, objective, market, platform, criteria and interpretation without saving. Switch to Korean, then English. The entered text and semantic selection must survive.
2. Write an unsent assistant question and a learning note. Switch language and navigate away/back. The drafts should remain until reload.
3. Select a graph node, change traversal/filter controls, and switch language. Selection, page and depth should remain. Original Japanese evidence must not change.
4. Check both languages for navigation, primary actions, validation guidance, state selector, layout labels and accessibility names. Machine IDs, source text and protocol error codes may remain unchanged.

Review the Korean wording and long CJK labels. A working switch does not certify translation quality or Japanese-language model usefulness.

## M03. Approve one exact research task

1. Open Knowledge assistant. Inspect extractive support, dates, coverage and full-input limits. Explore the target synthesis claim and research step list.
2. Choose refresh, fill or expansion. Review enrichment proposal. The approval action must be disabled until the checkbox is checked.
3. Revise scope. Change the subject/query or record bound and save a new revision. The displayed revision must increase and approval must again be absent. Invalid bounds should preserve your edits and show guidance.
4. Approve the exact saved revision. It should acknowledge one queued task. Open the task and progress to running, then retrieved. Returned material is still not usable in an answer.
5. Progress to published. Return to the old question/shortlist. They should remain unchanged. Use a new explicit question or regeneration request after reviewing the completion.
6. Use the global Budget and Meter failure states. Approval must never imply that blocked paid work can proceed. Return to Normal for further review.

The target synthesis is a design concept. Actual claim validation, richer research semantics and backend submission/retry behavior still require specifications and acceptance.

## M04. Investigate each monitoring method

1. Open Market monitoring. Select volume, engagement, sentiment/semantic shift and controversy in turn. Read both success result and method/evidence details.
2. Confirm that engagement uses the same native metric at matched post age, and semantic shift exposes both numerator/denominator and percentage-point change. Neither should imply sales or population sentiment.
3. Change Comparison support to Insufficient baseline. The UI should show no assessable spike/shift and retain a snapshot path. Change it to Method validation failed. The generated signal should be withheld without proposing automatic external research.
4. Restore Comparable baseline. Investigate with existing knowledge. A saved explanation should retain distinct recent/historical dates and avoid causal claims or campaign creation.
5. Open evidence timeline and semantic evidence. Review ambiguity and alert history.
6. Try promotion with no selected observation. Select one, review exact membership and inherited policy/deadline, then confirm. Only that selected evidence should be promoted.
7. Open topic configuration and pause/activation. Confirm that saving settings does not itself grant source permission or spending authority. Open a snapshot investigation and distinguish it from recurring monitoring.

The normal fixture values are examples, not recommended universal thresholds, cadence or retention.

## M05. Explore and withdraw graph support

1. Open Knowledge graph. Search for `Air`, clear the text, and filter account/content/brand/product kinds. Compare observed, derived and human bases.
2. Select a post node. Set depth to two or three. Select the human catalog relationship and inspect who supplied it. Select the derived product mention and inspect span/method/provisional status.
3. Use the equivalent entity/relationship list and compare it with the canvas inspector. Zoom in/out and reset view.
4. Simulate source withdrawal. The selected post should become unavailable, with its caption/label and dependent relationships withheld. Historical source-free identity may remain. A reload resets the fixture; a production withdrawal cannot be undone by a view reset.
5. Inspect conflicting display names. They must not establish cross-platform Creator equivalence, endorsement or causal connection.

The specified direction/predicate/platform/namespace/time/observation and explicit bound controls are implementation work beyond the compact prototype's filter set. Review their contracts in the specification.

## M06. Follow pipeline and safe recovery

1. Open a campaign or assistant task. Follow origin/scope, worker status, attempt, observations, mapping/derivation and publication. A queued task must not appear already published.
2. Inspect progressive acquisition. Broad discovery, selected API detail, permitted oEmbed/web scope and value/resource/cost stopping should be understandable without provider plumbing.
3. Simulate Unknown response. Inspect safe recovery. The UI should retain waiting and outstanding liability, with no blind paid reissue.
4. Open attributed spending. Distinguish original terminal outcome from currently permitted publication support, especially under Partial or Unavailable state.

## M07. Configure bounded recurring discovery

1. Open Scheduled discovery. Confirm the count of registered keywords and the shared 22/50 daily new-post admission summary.
2. Register keywords until the count reaches ten. The eleventh must be refused. New rows should appear, with no invented yield.
3. Inspect occurrence config, new/refresh/excluded counts and independent request/record/byte bounds. Duplicate post identity must not imply another new-post admission.
4. Review schedule settings and local health. The pilot design includes automation, but this fixture does not run a daemon. Monitor topics remain a different destination.

Actual day rollover, concurrency, server authority and background recovery require real acceptance tests after implementation.

## M08. Interpret spending and meter failure

1. Open Spending. Read measured actual $12.40, outstanding $4.00 and forecast-only $8–15. These are synthetic fixture amounts, not live prices or charges.
2. Check the exact scope/currency/period, unit/rate basis and remaining metered allowance. Forecast-only amounts must not appear inside an enforced all-in cap. Unknown cost must not become zero.
3. Inspect Meter recovery. Final liability reconciliation and restored meter health should be separate. A recovered cost does not recover an unknown response.
4. Select Budget and Meter failure demo states. Inspect the different recovery messages. Switch back to Normal.

## M09. Review inbox and email boundaries

1. Open Inbox and mark the completion read. Review task outcome and unchanged saved shortlist.
2. Open failed email delivery. The delivery retry identity must be separate from task execution. It must not imply another source request or completed user reading.
3. Open Delivery settings. Review configured-recipient intent and the source-free status/link payload. Local links require access to the pilot machine/runtime.
4. Review and regenerate from the completion. The explicit successor action should match the campaign flow.

No email is sent by the prototype. Provider, sender, actual recipients/credentials, safe payload and retry policy remain implementation decisions.

## M10. Check states, keyboard and narrow layouts

1. At desktop width around 1440px, compare A/B/C, then review at 768px and 390px. Tables should scroll inside their containers; the body, dialogs and CJK content must remain usable.
2. Use Tab from the start. The skip link should enter the workspace, navigation/buttons should expose visible focus, and form labels should identify their inputs.
3. Open a dialog, use Tab/Shift+Tab, then Escape. Confirm focus trapping and return to a useful control. These native-dialog behaviors require actual browser verification.
4. Tab to a graph node/edge or the alternative list. Enter/Space should select and update its inspector. A mouse should not be necessary for evidence access.
5. Type inside a form and use left/right arrows. They must not switch layout while editing. Outside a form/graph/dialog, the review switcher should respond.
6. Select each global state in both languages. Restricted/Unavailable must not show source captions; Loading/Error must not submit new work. Partial/Stale should guide rather than silently rewrite history.
7. Check reduced motion and 200% zoom. Confirm text, controls, dialog scroll and the fixture/switcher chrome remain reachable. A full accessibility audit remains later work.

## M11. Separate plans, outcomes and real review

1. Open Measurement & learning. Save a proposed plan with intended source/owner, periods, matching and attribution gaps. It must not display observed results.
2. Save a human note against an exact shortlist. Confirm author and human-supplied status are clear. Discuss withholding/purging source-dependent note text when support becomes unavailable.
3. Inspect future outcomes/portfolio/lift boundaries and the disabled lift action. No engagement-to-sales or causal result may be fabricated.
4. Preview the exact quality packet and pending named-review status. Distinguish reviewer judgments, translation method, original-language validation and technical checks.

## Material choices for actual human review

These are new design choices, not a repeat of the confirmed requirements interview:

- Choose A, B, C or specific elements to combine. A is recommended for simultaneous decision/evidence review.
- Decide whether the information density and evidence inspector are comfortable for campaign work, and whether the mobile evidence order should favor the result or its support.
- Review the language and completeness of brief criteria, missing-information explanations and approval wording. Request changes where a status still sounds like a verified fact.
- Review method-success presentations for engagement and semantic shift, including the needed comparison details and uncertainty. The displayed values are fixtures; operators still configure real thresholds.
- Review the target research-plan/claim-inspector experience. Accepting that UI does not approve an unvalidated synthesis algorithm or loosen exact external approval.
- Review the proposed source-free email/link design and the local-pilot access limitation. Provider/credentials/recipient policy and live sending remain separate implementation/operation choices.

Record the actual reviewer, date, exact revision and artifact digest, accepted layout/changes, and any required corrections. The design author and coordinator must not mark this review approved themselves. Task 4 starts only after actual human approval of the exact corrected revision.
