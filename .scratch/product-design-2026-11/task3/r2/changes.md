# Changes for review r2

This revision addresses the user's three requests recorded in the [r1 review](../../ui-review-status.md#actual-r1-review-feedback). It is design-only and awaits actual human approval. Task 4 remains unapproved.

| Review request | Change | Boundary |
| --- | --- | --- |
| R2-CHAT: Make the knowledge assistant a regular chatbot | Scrollable user and assistant turns, thread list, New conversation, bottom multiline composer, Send and Enter, Shift+Enter, and scripted follow-up replies. Sources, claims, and research status are secondary disclosures. Drafts, thread context, and scroll position survive language and navigation changes | Replies use published fixture support. A conversational yes grants no authority. Exact proposal revision review and approval remain a separate modal action |
| R2-STREAM: Visualize monitoring with current data highlighted | Inline SVG time series with chronological UTC windows, red latest point and outlined latest window, pink selected-window shading, metric and history controls, keyboard/table equivalents, and selected evidence. Latest values are 24 posts, 36 median likes, 35% coded negative, or 4 controversy inputs | Missing and unscheduled windows break lines. Zero observed posts stays zero. Each metric retains its own denominator, method, limits, baseline and failure states |
| R2-GRAPH: Make the actual graph more interactive | Concrete production interaction and incremental read contract for pan, zoom, fit, dragging, pins, layouts, expand/collapse, filters, evidence inspection, and keyboard/list access | The mock graph stays simplified. No new graph engine, graph database, acquisition authority, identity, or causal inference |

The visual plan keeps campaign-first layout A and the accepted four-color palette. A familiar conversation occupies the assistant work area. The monitoring time series becomes the main visual there, with evidence below. This directly implements the requested familiarity without reworking unrelated campaign and operations pages. Layouts B and C remain available.

The full 99-ID matrix, local-pilot sequence, EN/KO switch, original-language sources, inbox and email design, richer-agent roadmap, and evidence/authority boundaries remain in the r2 handoff. See the [specification](design-spec.md), [mapping](fr-ui-traceability.md), [review guide](review-guide.md), and [verification](verification.md).

All writes are within this directory. The [r1 integrity snapshot](r1-integrity.json) supports a repeatable unchanged-r1 check. No browser access, rendering, screenshots, production implementation, email, or external calls were performed. Visual, keyboard, accessibility, and human acceptance remain pending.
