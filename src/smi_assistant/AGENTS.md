# Bounded knowledge answers

Own `KnowledgeAssistant.ask/read/migrate`, durable human question claims and model-selected exact published findings. Read the [answer contract](../../docs/knowledge.md#bounded-free-form-knowledge-answers) and [selection decision](../../docs/adr/0017-exact-supported-answers.md) before changing input, output or dependency semantics.

Compose `KnowledgeQueries` and `smi_campaigns.responses` through public ports. Source observations/interpretations stay with ingestion/knowledge; the shared transport owns model envelopes and cost admission. Keep the dependency direction toward those owners. This application owner imports no task/acquisition authority and writes only its schema.

Pin the exact query, full model-input support IDs (including unselected inputs), method/schema/model/bounds, requesting human and attributable usage. Persist source-free output IDs and fixed uncertainty codes; resolve values/dates through the pinned current-policy query on every read. Model output selects relevance, not verified truth or semantic entailment. Preserve observed/derived bases and provisional status.

Limit question UTF-8 bytes, members, facts, context/request/response bytes and output IDs explicitly. Evidence and questions remain untrusted data; the strict independent validator accepts only exact supplied IDs and fixed limitation vocabulary. Source text grants no roles, tools, approval, acquisition or spending authority.

Commit the claim before I/O; exact retries reopen without redispatch, even after interruption. The shared admission guard rechecks full exact inputs and current process/display/derivation health after allowance evaluation, retaining source locks through dispatch commit. Finalization repeats the check. Hold no transaction across model I/O. Any unavailable/superseded actual input withholds the derived selection on reopening; later publications affect only new questions.

Verify via public question/read, retrieval, accounting and loopback HTTP operations, with real PostgreSQL and simulated external I/O. Technical checks establish neither language quality nor marketer usefulness. Update knowledge, architecture, physical ERD, local-review and coverage summaries with interface changes.
