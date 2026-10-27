# Separate timely X monitoring from full KB publication

Status: accepted; bounded offline evidence collection implemented, detection/promotion pending

X anomaly detection uses bounded recent monitoring observations without requiring full ontology ingestion of every post. The shared KB remains authoritative for KB queries, campaign recommendations and assistant answers; the monitoring evidence collection is authoritative only for its scoped recent detection windows and alert support.

Retain necessary source evidence, method/baseline versions, times, coverage and policy dependencies so alerts remain inspectable. Selectively promote useful observations through the normal KB ingestion/publication pipeline. Anomaly investigation reads existing KB context and cannot launch additional external searches.

The trade-off is a separate bounded evidence lifecycle and consistency boundary in return for timely, inexpensive detection. Retention/withdrawal must govern both monitoring observations and copied alert explanations. Snapshot investigations still require prepared knowledge and frozen evidence. The separate recent owner now implements bounded local fixture topics/windows/captures without full KB publication; live X collection, detection, alert copies and promotion remain future work. Original native/capture identity outlives fixture labels and local import time so re-import cannot reconstruct purged support or create freshness. Source-free window lineage survives copied-body deletion, trading finite audit capacity for honest retries and policy history. See [the installed contract](../monitoring.md#bounded-offline-recent-x-evidence).
