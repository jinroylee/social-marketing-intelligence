# Pin historical support while evaluating current source policy

Status: accepted

Evidence sets and consequential decisions pin exact observation/derivation references instead of re-running a current-value query whenever they are reopened. Source permissions, expiry and withdrawal are evaluated at each use. This makes historical reasoning reproducible without granting indefinite permission to display or process its source content.

The trade-off is retaining explicit membership, lineage and dependency records rather than storing only a query or an unrestricted explanation snapshot. Later captures cannot silently change a saved result. Withdrawn support produces unavailable markers and redacted dependent text; a correction can flag support for reassessment without rewriting the original account membership or producer attribution.

The evidence layer implements pinned dataset reads and current source-policy filtering. Shared knowledge records exact source dependencies and reconciles retained interpretation values/excerpts. Campaign comparisons and shortlist reasons inherit those dependencies, with conservative redaction and copy cleanup while preserving account membership and reviewer metadata. Future stores must implement the same dependency contract as they are introduced. This decision does not claim that physical deletion across every store is already available.

Automatically saved deterministic recommendations retain automation/method attribution and separately identify any optional human review. Pinning evidence does not require a human approval gate; [ADR 0003](0003-automatic-shortlist-persistence.md) defines that authority. [Lightweight monitoring evidence](0004-lightweight-monitoring-evidence.md) must preserve equivalent dependencies for alert copies without forcing full KB publication for every post.
