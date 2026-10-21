# Save recommendations before admitting coverage discovery

Campaign recommendations commit their actual supported shortlist and immutable coverage decision before task-owned automatic discovery admission. This accepts a recoverable gap between the commits so source/configuration/admission failure cannot discard a useful or explicitly empty recommendation, and preserves the dependency from tasks toward campaigns rather than creating a campaign-to-task cycle.

One task-owned disposition per shortlist commits atomically with a fresh server-created nested task or sanitized refusal. Exact retries reopen that disposition; an interrupted admission reuses the pinned assessment and rechecks its current human brief. Source permissions gate historical explanations, worker cost controls govern execution, and newly published knowledge never replaces the saved result without a separate explicit recommendation.
