# Operational ontology methods for Social Marketing Intelligence

Research date: 2026-09-22  
Question: Which Palantir-style ontology concepts should a small founding team adopt, and how should they be adapted for a decision-support product that never executes external marketing actions?

## Executive findings

1. **Adopt the operational role, not Palantir's product surface.** Palantir defines its Ontology as an operational layer above datasets and models, with semantic primitives (objects, properties, links) and kinetic primitives (actions, functions, dynamic security). It is designed to power investigations, applications, and agents rather than merely catalog data. The useful pattern is a stable, governed business API between changing sources and product experiences—not an attempt to reproduce Foundry. ([Palantir, Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview); [Palantir, introductory concepts](https://www.palantir.com/docs/foundry/getting-started/introductory-concepts))
2. **Preserve four distinct concerns:** source observations, canonical assertions/state, the operational ontology, and physical projections. Palantir explicitly separates its data layer from its object layer and maps datasets into real-world objects and links. For this product, the canonical layer must additionally arbitrate source conflicts, identity, time, and uncertainty before the ontology exposes business meaning. Search, vector, graph, cache, and analytical stores should remain rebuildable projections rather than independent authorities. This last decomposition is a product-specific architectural inference from Palantir's separation, not a claim about Foundry internals. ([Palantir, datasets](https://www.palantir.com/docs/foundry/data-integration/datasets); [Palantir, Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview))
3. **Model real entities and meaningful relationships, not API payloads.** Palantir's current design guidance says to model reality rather than systems, separate identity from observations, keep types focused, and make every link answer a domain question. A relationship with its own dates, role, status, or evidence should become a relationship object, such as `Collaboration` or a time-bounded creator/account association. ([Palantir, design best practices](https://www.palantir.com/docs/foundry/ontology/ontology-best-practices); [Palantir, structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance))
4. **Treat identity resolution as evidence-based decision-making.** Give every real-world entity an opaque, immutable internal identifier; keep source-native IDs, handles, URLs, names, and aliases as time-bounded identifiers. Entity resolution should yield match, non-match, or review-needed decisions with scores, evidence, method versions, and reversible merge/split history. The classic Fellegi–Sunter framework explicitly preserves an undecided region at controlled error rates, which is a better product model than forcing every candidate into a match. ([RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html); [Fellegi and Sunter, 1969](https://nhis.ipums.org/nhis/resources/Fellegi69.pdf))
5. **Make provenance, time, and uncertainty first-class where they affect a decision.** W3C PROV's entities, activities, agents, generation, use, attribution, and derivation provide a technology-neutral vocabulary for lineage. Bitemporal modeling separates when a claim was valid in the domain from when the system recorded it. Assertions should retain evidence, observation/ingestion times, method or model version, and confidence semantics. Do this selectively for consequential, volatile, derived, or conflicting facts; wrapping every scalar in an assertion object would overburden a small team. ([W3C PROV-DM](https://www.w3.org/TR/prov-dm/); [Jensen and Snodgrass, Temporal Data Models](https://www.cs.arizona.edu/~rts/pubs/TRmerged.pdf))
6. **Keep “actions” inside the product boundary.** Palantir action types are governed transactions that can validate permissions and update multiple objects and links, with action logs recording who decided what and when. Here, useful actions are internal affordances such as save a shortlist, accept an identity match, annotate evidence, acknowledge an alert, or record a campaign brief. Publishing, outreach, ad buying, contracting, or changing an external system remains outside the product; at most the ontology records a recommendation, a human decision, and a later observed outcome. ([Palantir, action types](https://www.palantir.com/docs/foundry/action-types/overview); [Palantir, action log](https://www.palantir.com/docs/foundry/action-types/action-log))
7. **Validate through questions and workflows.** Structural correctness alone does not show that marketers or agents can use the model. Palantir recommends task-based analytical drills using real business questions, echoing competency-question methods in ontology engineering. A small team's acceptance suite should combine competency questions, data invariants, permission tests, temporal examples, and agent/application contract tests. ([Palantir, Ontology design validation](https://www.palantir.com/docs/foundry/ontology/ontology-design-validation); [Grüninger and Fox, 1995](https://doi.org/10.1007/978-0-387-34847-6_3))
8. **RDF, OWL, SHACL, and graph storage are optional tools.** RDF supplies an interoperable graph data model; OWL adds formal semantics, imports, and version IRIs; SHACL validates RDF graphs against shapes. None is required to obtain stable domain objects, provenance, policies, or a semantic API. Adopt them only when an actual interoperability, reasoning, or partner-exchange requirement repays the additional modeling and operational cost. W3C's RDF 1.2 specification was still a Candidate Recommendation in April 2026, another reason to choose standards deliberately rather than by fashion. ([W3C RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/); [W3C OWL 2](https://www.w3.org/TR/owl2-new-features/); [W3C SHACL](https://www.w3.org/TR/shacl/))

## What “operational ontology” should mean here

Palantir's documented system combines four things:

- **Semantics:** object types, properties, links, and interfaces map data to real-world concepts.
- **Logic:** functions express reusable business computations.
- **Affordances:** actions make governed changes or trigger governed workflows.
- **Policy:** security applies to ontology resources, object instances, properties, and actions.

Applications then discover objects, traverse relationships, run analyses, call functions, and submit actions through that shared model. Palantir's object-aware applications cover discovery, exploratory analysis, dashboards, and workflow-specific applications; its AIP tooling builds agents and functions on the same ontology and governance foundation. ([Palantir, ontology-aware applications](https://www.palantir.com/docs/foundry/ontology/applications); [Palantir, AIP overview](https://www.palantir.com/docs/foundry/aip))

For Social Marketing Intelligence, define the Operational Ontology as:

> A versioned, permission-aware business interface that exposes stable social-marketing objects, relationships, evidence-backed facts, read/query logic, and governed internal decisions to applications and agents.

It is not the canonical database itself. Canonical state decides which assertions currently represent the platform's best understanding; the ontology gives that understanding names, relationships, behavior, and policy that marketers and software can use. It is also not a synonym for a graph. A relational schema and typed service can implement the first version well.

### Recommended layer contract

| Concern | Owns | Must not become |
| --- | --- | --- |
| Source observations | Immutable or replayable source payloads, source identifiers, collection context, observed and ingested times, source terms/deletion state | A product-facing domain model |
| Canonical knowledge | Entity resolution, normalized measures, assertions and conflicts, preferred-value policy, valid/system time, derivation metadata | A copy of one vendor's schema |
| Operational Ontology | Stable type and relationship names, documented property semantics, permitted queries/functions/internal actions, authorization contract | A storage topology or exhaustive mirror of all data |
| Physical projections | Relational serving tables, search indexes, vector indexes, graph views, OLAP tables, caches | Independent systems of record |

The dependency direction should be one-way: observations feed canonical knowledge; canonical knowledge implements the ontology; projections serve declared read patterns and can be rebuilt. Applications and agents depend on ontology contracts. Exceptional analyst access to lower layers should be explicit and should not leak source-specific fields into durable product behavior.

## Recommended modeling method

### Start from decisions and competency questions

Begin with the recurring decisions and investigations, not a master entity diagram. Examples:

- Which creators fit this brand, product, audience, market, and campaign constraint, and what evidence supports each fit?
- Are two platform accounts controlled by the same creator, and what evidence or reviewer established that link?
- Which content and collaborations explain a change in brand conversation, and what is observed versus inferred?
- What did the platform know when a recommendation was made, and how has that knowledge since changed?
- Which metrics are comparable across platforms, windows, and collection methods?
- Why can this user or agent see this creator property or run this internal action?

Grüninger and Fox used competency questions to characterize what an ontology must be capable of representing and answering. Palantir's 2026 validation guidance applies the same operational idea: derive unfamiliar questions from real operating rhythms, give them to people and agents, and treat time-to-answer, ambiguity, and failed navigation as design evidence. ([Grüninger and Fox, 1995](https://doi.org/10.1007/978-0-387-34847-6_3); [Palantir, Ontology design validation](https://www.palantir.com/docs/foundry/ontology/ontology-design-validation))

Turn the highest-value questions into acceptance tests before expanding the model. A concept belongs in the first ontology only if it supports one or more validated workflows, preserves a critical invariant, or is required for provenance, policy, or interoperability.

### Keep the core small and reality-based

A reasonable proposal-level Core Ontology is:

- `Creator`: a real-world person or organization that creates content.
- `PlatformAccount`: a platform-specific identity; it is never interchangeable with a Creator.
- `Content`: a platform-specific published media item or durable content unit.
- `Brand`, `Product`, `Campaign`.
- `Collaboration`: a relationship object connecting the relevant creator, brand/product, campaign, and content when the relationship needs dates, status, evidence, or role.
- `Topic` and `AudienceSegment`, each with explicitly documented semantics and scope.
- `MetricObservation`: a metric value tied to subject, platform, definition, window, observation time, and provenance.
- `SocialEvent` or `Signal`: a detected occurrence that groups evidence and may later be confirmed, dismissed, or reclassified.
- Cross-cutting `Assertion`, `SourceObservation`, and `IdentityDecision` concepts where explicit evidence/history is required.

Object types should be singular concepts a domain expert recognizes. Properties should be curated and named for meaning. Links should exist because the relationship matters to a question, not because two source tables share a key. Palantir explicitly distinguishes a direct link from an object-backed link: when a relationship has its own dates, role, status, or allocation, model the relationship as an object. ([Palantir, design best practices](https://www.palantir.com/docs/foundry/ontology/ontology-best-practices); [Palantir, structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance))

Examples for this domain:

- `Creator —controls→ PlatformAccount` may need a relationship object because control can change over time and can be uncertain.
- `Creator —collaboratedWith→ Brand` should usually be derived through `Collaboration`, because date, campaign, compensation disclosure, evidence, and role belong to the relationship.
- `Content —mentions→ Product` may be a direct link only when it is an accepted, context-free relationship; an extracted or disputed mention should remain an assertion with evidence and method version.

### Use interfaces sparingly for shared capabilities

Palantir interfaces define a common shape—properties, links, and actions—that multiple object types implement, allowing workflows to target a capability instead of each concrete type. Its guidance favors composition and extension over wide sparse objects or deep inheritance. ([Palantir, structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance); [Palantir, interface link types](https://www.palantir.com/docs/foundry/interfaces/interface-link-types-overview))

For a small team, an interface is justified only after two or more real workflows need the same capability. Possible future examples are `HasPlatformPresence`, `Measurable`, or `EvidenceBacked`; do not create an abstract interface hierarchy up front. A conventional typed application interface is sufficient—the proposal need not commit to a metadata-driven interface engine.

### Derive convenience, retain one owner for each fact

Palantir recommends storing each fact once, using derived properties for linked values and aggregations, and documenting deliberate denormalization. Its derived properties are read-only and evaluated under the security context of the source objects. ([Palantir, structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance); [Palantir, derived properties](https://www.palantir.com/docs/foundry/object-link-types/derived-properties))

Apply that rule to semantic ownership, while allowing physical serving copies:

- `Brand.name` belongs to Brand; Content may expose it through a view, not own another authoritative copy.
- `Creator.collaborationCount` is a derived aggregate over accepted Collaboration records with a declared window and definition.
- Cross-platform engagement rate is a function or versioned analytical result, because platform denominators and available metrics differ; it should not masquerade as a timeless base property.
- Materialized or cached results must name the defining logic version and rebuild source.

## Identity and entity resolution

### Stable identifiers

Use an opaque internal identifier for every canonical entity. UUIDs are a standards-based option intended to provide uniqueness across space and time, but they only solve identifier allocation—not identity resolution. ([RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html))

Maintain separate identifier records with at least:

- source or namespace;
- source-native immutable ID when available;
- identifier kind (`platform_user_id`, handle, URL, vendor ID, business registration ID, etc.);
- value and normalized value;
- valid-from/valid-to and first/last observed times;
- provenance and status;
- canonical entity ID.

Never use a mutable handle, display name, URL slug, hashtag, or email as the canonical key. Enforce uniqueness only within the correct source namespace and time scope. Retain alias history because handles can change, be recycled, or be observed inconsistently.

### Resolution as a governed, reversible decision

Fellegi and Sunter formalized record linkage as decisions among link, non-link, and possible-link regions under bounded false-link and false-non-link error. That remains a strong conceptual basis even if modern embeddings or supervised models produce the score. ([Fellegi and Sunter, 1969](https://nhis.ipums.org/nhis/resources/Fellegi69.pdf))

Represent each material resolution decision with:

- candidate entity IDs and compared identifiers/features;
- outcome: `matched`, `not_matched`, `needs_review`, later `superseded`;
- score plus the score's method-specific meaning;
- resolver/rule/model name and version;
- evidence references;
- decision maker (system or human) and decision time;
- merge/split/reassignment history.

Do not destroy source records after a merge. A correction must be able to split a mistaken canonical entity and replay downstream projections. High-impact or low-confidence matches should enter human review; negative evidence and prior rejected pairs should be retained so the system does not repeatedly suggest the same false match.

## Provenance, assertions, uncertainty, and time

### A selective assertion model

W3C PROV models things as entities, transformations as activities, and responsible parties or software as agents; it supports generation, use, attribution, association, and derivation, including provenance about provenance. These concepts can be implemented in ordinary relational tables and event metadata; RDF serialization is optional. ([W3C PROV-DM](https://www.w3.org/TR/prov-dm/); [W3C PROV overview](https://www.w3.org/TR/prov-overview/))

For facts that can conflict, change, or come from models, use an assertion record conceptually containing:

`subject · predicate · value/object · assertion_kind · evidence · valid_time · observed_at · recorded_at · producer · method_version · confidence · status`

Use three explicit assertion kinds:

- **Observed:** reported directly by a source under a defined collection method.
- **Derived:** produced by a rule, model, LLM, aggregation, or analyst transformation.
- **Human:** supplied, corrected, or verified by an authorized person.

An observed value is not automatically true, and a human assertion is not automatically permanent. Multiple assertions may coexist. Canonical state selects or synthesizes the current preferred view under a versioned policy while retaining conflicts and evidence. The UI and agent response should be able to explain the chosen value and disclose material disagreement.

Avoid reifying every property. Use explicit assertions for uncertain identity, extracted topics/mentions, creator attributes inferred from content, audience estimates, collaboration detection, event classification, fraud signals, and other consequential inferences. Simple internally assigned IDs or an authoritative campaign name can use normal columns with field-level provenance.

### Bitemporal knowledge

Temporal-database research distinguishes **valid time**—when a fact holds in the modeled world—from **transaction/system time**—when the database records that version; using both yields a bitemporal model. ([Jensen and Snodgrass, Temporal Data Models](https://www.cs.arizona.edu/~rts/pubs/TRmerged.pdf))

Also distinguish `observed_at` and `ingested_at`; neither is necessarily valid time. Recommended rules:

- Apply valid and system intervals to volatile, correction-prone assertions and relationship objects, not mechanically to every table.
- Make system history append-only: corrections close one system interval and create another.
- Keep a fast current-state projection for product queries.
- Record source deletion/unavailability separately from “the fact ceased to be true.”
- Snapshot or reference the assertion and logic versions used for consequential recommendations so an analyst can reconstruct what the platform knew then.

### Uncertainty semantics

A bare `confidence = 0.82` is not portable across methods. Store what the score means, the method/model version, calibration population if applicable, and the decision threshold/version that consumed it. Distinguish probability-like confidence from similarity, classifier margin, evidence coverage, and data-quality scores. Missing means unknown, not false.

Recommendations should expose evidence and uncertainty appropriate to the decision: source coverage, freshness, conflicting evidence, model version, and any human verification. Keep model output and canonical acceptance as separate states so a new model run does not silently rewrite a reviewed fact.

## Logic, actions, applications, and agents

### Functions and logic

Use functions for reusable, preferably side-effect-free domain logic such as:

- creator eligibility and portfolio constraint checks;
- comparable metric normalization;
- brand/creator fit scoring with explanation;
- campaign lift calculations under a named method;
- entity-match candidate generation;
- evidence retrieval and “as known at time T” queries.

Version logic independently from object schemas. Persist a result only when latency, reproducibility, or audit needs justify it; if persisted, include inputs or input snapshot, method version, output, and generated time.

### Actions as internal affordances

Palantir defines an action as a governed transaction over objects, properties, and links; the same validation and action logic can be shared across applications. Its action log distinguishes the decision context from full object edit history and operational success/failure metrics. ([Palantir, action types](https://www.palantir.com/docs/foundry/action-types/overview); [Palantir, action log](https://www.palantir.com/docs/foundry/action-types/action-log); [Palantir, action metrics](https://www.palantir.com/docs/foundry/action-types/action-metrics))

Adopt the contract, even if implemented as ordinary service endpoints:

- stable action name and business purpose;
- typed parameters and preconditions;
- authorization rule;
- validation and idempotency behavior;
- declared internal state changes;
- actor, time, reason, and result log.

Initial actions should modify only internal knowledge or workflow state: verify/reject an identity link, save/remove a shortlist item, annotate an assertion, acknowledge/dismiss a signal, create an investigation, or record a campaign hypothesis. Do not expose connectors for publishing, messaging, purchasing, contracting, or mutating a social platform. If a workflow discusses such an act, model it as a recommendation or proposed next step and record the human's decision separately.

### Applications

Applications should consume the Ontology rather than source schemas. Useful first experiences are object views, linked investigations, comparison/shortlist workspaces, evidence drill-down, and saved monitoring. Palantir's application taxonomy shows why the same ontology can support walk-up discovery, exploratory analysis, dashboards, and custom workflow applications without each redefining domain meaning. ([Palantir, ontology-aware applications](https://www.palantir.com/docs/foundry/ontology/applications))

### Agents

Agents should receive a typed, permission-filtered ontology tool surface rather than database credentials or vendor payloads. Palantir's AIP documentation places agents and workflows on the Ontology and its MCP documentation scopes tokens to both the application's allowed operations and the requesting user/service user's underlying object, action, and query permissions. ([Palantir, AIP architecture](https://www.palantir.com/docs/foundry/architecture-center/aip-architecture); [Palantir, Ontology MCP authorization](https://www.palantir.com/docs/foundry/ontology-mcp/authentication-and-authorization))

For this product:

- default agent tools to read/query, compute, compare, and draft;
- allow only the internal ontology actions above, under the user's permission context;
- require evidence references for factual answers and recommendations;
- log tool calls, inputs, selected evidence, output, latency, and errors;
- evaluate answer correctness, evidence grounding, permission behavior, refusal boundaries, and stability across model/prompt versions.

Palantir's AIP Evals provides a useful methodology: test cases, explicit evaluators, comparisons across function versions/models, thresholds, and repeated runs to measure variance. The product can implement this without adopting Palantir. ([Palantir, AIP Evals](https://www.palantir.com/docs/foundry/aip-evals/overview))

## Permissions, lineage, and observability

### Policy

Separate permissions for ontology definitions, object instances, properties, and internal actions. Palantir's model distinguishes resource/schema visibility from data visibility and supports row/object and column/property rules whose intersection produces cell-level access. It recommends semantic, least-privilege policies rather than duplicated “public” and “restricted” types. ([Palantir, ontology permissions](https://www.palantir.com/docs/foundry/object-permissioning/ontology-permissions); [Palantir, object and property security policies](https://www.palantir.com/docs/foundry/object-permissioning/object-security-policies); [Palantir, structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance))

Small-team minimum:

- tenant/workspace isolation;
- roles for admin, builder/analyst, and viewer;
- property restrictions for sensitive personal/contact, contractual, or first-party data;
- per-action authorization and audit;
- user-scoped agent access;
- policy propagation or deliberate exclusion when data enters a projection/export;
- deletion and retention handling across downstream lineage.

Do not build a general-purpose policy language initially. Express a short set of auditable policies in application code and metadata, with contract tests. Preserve a route to relationship- or purpose-based rules if agency/brand collaboration later requires them.

### Lineage and data quality

Palantir's data lineage shows upstream/downstream datasets, schema, freshness, and generating code; its Data Expectations can block bad outputs and connect checks to monitoring. W3C PROV supplies an interoperable conceptual model for derivations. ([Palantir, Data Lineage](https://www.palantir.com/docs/foundry/data-lineage/overview); [Palantir, Data Expectations](https://www.palantir.com/docs/foundry/maintaining-pipelines/define-data-expectations); [W3C PROV-DM](https://www.w3.org/TR/prov-dm/))

At minimum, capture lineage edges between source observation batches, transforms/model runs, canonical assertions, and materialized projections. Track schema/logic version, inputs, outputs, run, status, and timestamps. Establish checks for uniqueness, referential integrity, allowed values, temporal interval validity, freshness, volume anomalies, unexpected nulls, and projection convergence.

### Observability

Palantir's Ontology/AIP observability combines execution history, metrics, distributed traces, logs, and log search; action metrics add success/failure and P95 duration. ([Palantir, observability](https://www.palantir.com/docs/foundry/observability/overview); [Palantir, Ontology and AIP observability](https://www.palantir.com/docs/foundry/aip/aip-observability))

Monitor the product at three levels:

- **Knowledge health:** source lag, assertion conflict rate, unresolved entity candidates, confidence/calibration drift, stale canonical values, deletion backlog.
- **Projection health:** change-log lag, failed updates, reconciliation differences, rebuild status.
- **Workflow health:** ontology query latency/error, function and internal-action success, agent/tool traces, permission denials, evidence-grounding and evaluation scores.

## Modular extension and evolution

### Core plus extensions

Keep cross-industry meanings in the Core Ontology. Add Beauty, South Korea, and Japan through additive modules or configuration:

- a Beauty extension can link `Product` to a `BeautyProductProfile`, ingredient/formulation claims, shade/color concepts, skin/hair concerns, and category-specific measurements;
- market extensions can represent market-local taxonomy mappings, language/locale labels, local channels, and jurisdiction- or platform-specific classifications;
- workflow extensions can add derived scores, saved investigations, or recommendation outputs without changing core entity identity.

Do not subclass core objects merely because a use case needs extra fields. Prefer a linked extension object when the extension has its own ownership, lifecycle, permissions, or sparse applicability. Promote a concept into Core only after it proves stable and shared across multiple domains. Eric Evans's bounded-context guidance supports keeping a model internally consistent within a context and making mappings explicit at boundaries rather than forcing one universal vocabulary. ([Eric Evans, Domain-Driven Design Reference](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf); [Martin Fowler, Bounded Context](https://martinfowler.com/bliki/BoundedContext.html))

### Evolution discipline

Palantir gives ontology resources experimental, active, promoted, deprecated, and example statuses; active resources receive protections against destructive API-name changes. Its schema migration tooling detects breaking changes, requires a migration choice, creates a new schema version, and rehydrates the object index. ([Palantir, statuses](https://www.palantir.com/docs/foundry/object-link-types/metadata-statuses); [Palantir, schema migrations](https://www.palantir.com/docs/foundry/object-edits/schema-migrations))

Use a simpler analogue:

- mark contracts `experimental`, `stable`, or `deprecated`;
- keep internal IDs and API names stable after promotion;
- favor additive change;
- deprecate with replacement, rationale, and removal date;
- require migration/backfill plans for type, cardinality, identity, or semantic changes;
- version schema, functions, matching methods, canonical-selection policy, and metric definitions separately;
- run competency, data, permission, and consumer contract tests before promotion;
- retain historical interpretation metadata so old recommendations remain explainable.

OWL's imports and version IRIs illustrate useful modular/versioning concepts if semantic-web exchange later becomes necessary, but Git-managed schemas and service contracts can supply the same governance for the initial system. ([W3C OWL 2 imports and versioning](https://www.w3.org/TR/owl2-new-features/))

## Validation stack

Use five complementary layers:

1. **Schema checks:** types, required fields, identifier namespace uniqueness, relationship cardinality.
2. **Semantic invariants:** a PlatformAccount cannot be its controlling Creator; metric definitions/windows must be explicit; accepted relationship intervals cannot be impossible; current preferred assertions must follow the selection policy.
3. **Data and temporal checks:** referential integrity, freshness, null/range checks, interval consistency, reconciliation with source snapshots, projection convergence.
4. **Competency and workflow tests:** people and agents answer seeded real questions, with expected paths/evidence, under a time budget.
5. **Security and agent tests:** expected allow/deny cases, sensitive-property non-disclosure, action authorization, evidence grounding, and evaluation regression.

If the project later exports RDF or needs independent graph conformance, SHACL can express cardinality, datatype, class, closed-shape, and custom constraints and returns machine-readable validation reports. It is an optional exchange/validation mechanism, not a reason to store the operational system in RDF. ([W3C SHACL](https://www.w3.org/TR/shacl/))

## What belongs in the compact proposal

Include:

- the definition of Operational Ontology as the stable business interface for people, applications, and agents;
- the four-part separation of source observations, canonical knowledge, ontology contracts, and rebuildable projections;
- a short initial Core Ontology and the `Creator ≠ PlatformAccount` identity invariant;
- Core plus additive Beauty/market extensions;
- assertions with provenance, observed/system/valid time, method version, and uncertainty for consequential facts;
- functions for reusable logic and internal-only governed actions;
- ontology-level permission intent, user-scoped agents, action/audit history;
- competency-question validation and additive/versioned evolution;
- technology neutrality: relational-first is acceptable, and graph/RDF/OWL/SHACL are optional.

State the product boundary plainly: the platform investigates, explains, recommends, records internal decisions, and learns from observed outcomes; it does not publish, contact creators, buy media, contract, or mutate external marketing systems.

## What is premature

Exclude from the founding proposal or explicitly defer:

- an exhaustive class/property catalog or universal marketing ontology;
- a generic ontology workbench, custom policy DSL, or metadata-driven action engine;
- RDF/OWL reasoning, a triple store, or SHACL in the production path without a partner/exchange need;
- choosing a graph database merely because the model contains relationships;
- reifying every value as an assertion or making every table fully bitemporal;
- dozens of speculative interfaces or deep inheritance trees;
- autonomous external actions or external-system write connectors;
- enterprise-scale ontology councils, release trains, or Palantir-equivalent tooling;
- a second authoritative state in search/vector/graph stores;
- opaque “confidence” numbers with no method-specific semantics or evaluation.

## Decision-ready proposal language

> The platform uses an Operational Ontology as a versioned, permission-aware business interface over canonical social-marketing knowledge. It defines stable objects, meaningful relationships, evidence-backed facts, reusable analytical functions, and governed internal decisions for applications and agents. Source observations and their provenance remain below the ontology; canonical state resolves identity and selects the platform's best current view without discarding conflicts or history; search, vector, graph, and analytical stores are rebuildable projections.
>
> The initial Core Ontology stays cross-industry and compact. Beauty and Korea/Japan semantics are additive extensions or configuration. Stable internal identities remain separate from platform accounts and mutable handles. Consequential derived facts retain evidence, method version, time, and uncertainty. Applications and user-scoped agents may investigate, explain, recommend, and record internal decisions, but they do not execute publishing, outreach, purchasing, contracting, or other external marketing actions.

## Source assessment and limitations

- Palantir documentation is the primary source for Palantir's current terminology and product methods. Claims about its benefits are vendor claims; this note adopts design patterns rather than assuming equivalent outcomes.
- The current Palantir documentation includes 2026 ontology-design and observability guidance. All Palantir pages cited here were checked on 2026-09-22.
- W3C Recommendations and IETF RFCs are normative sources for their respective standards. RDF 1.2 was a Candidate Recommendation, not a W3C Recommendation, in the cited April 2026 snapshot.
- The layered target architecture, selective assertion model, internal-only action boundary, and small-team sequencing are recommendations inferred for this product from the cited methods; they are not prescribed wholesale by any one source.
