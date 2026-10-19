# Separate timely X monitoring from full KB publication

Status: accepted; implementation pending

X anomaly detection uses bounded recent monitoring observations without requiring full ontology ingestion of every post. The shared KB remains authoritative for KB queries, campaign recommendations and assistant answers; the monitoring evidence collection is authoritative only for its scoped recent detection windows and alert support.

Retain necessary source evidence, method/baseline versions, times, coverage and policy dependencies so alerts remain inspectable. Selectively promote useful observations through the normal KB ingestion/publication pipeline. Anomaly investigation reads existing KB context and cannot launch additional external searches.

The trade-off is a separate bounded evidence lifecycle and consistency boundary in return for timely, inexpensive detection. Retention/withdrawal must govern both monitoring observations and copied alert explanations. Current snapshot monitoring still requires prepared knowledge and frozen evidence; the light path is an additional future owner, not an existing X connector or an exception to evidence provenance.
