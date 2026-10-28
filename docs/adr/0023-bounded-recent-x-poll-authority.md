# Pin recurring X authority and uncertain response identity

Status: accepted and implemented

Use one explicit operator activation of one topic revision and one official recent-search page. Runtime enablement, credentials, current source policy and shared declared-cost admission remain independent gates. A configuration edit must not silently broaden recurring paid authority. Each stable topic/end attempt survives activations, worker restarts and presentation pagination; original response and final billing are separate outcomes.

A per-topic PostgreSQL session lock coordinates the worker, and every dependent mutation/admission transaction uses that ownership session. External HTTP occurs after commit with no open transaction. Session loss stops local effects while keeping any dispatched commitment. Reclaiming the topic cannot reissue an already dispatched attempt. This follows the ownership principle in [ADR 0005](0005-task-session-effect-ownership.md) without making monitoring a KB task or requiring publication of every post.

Only the first ten-post page is collected. A remaining page, unknown source time or incomplete field stays a coverage limitation rather than triggering a pagination loop. Shared admission reserves the configured ten-post declared bound per attempt; response rows and soft provider deduplication do not establish a final invoice. Final provider-basis reconciliation cannot restore a lost response or grant another request. An operator can deactivate and explicitly activate a later interval, retaining the skipped interval and its liability. This sacrifices automatic recovery/completeness for bounded scope, honest uncertainty and protection against duplicate chargeable work. No provider-side exactly-once or zero-overshoot guarantee is established.

The recent owner retains policy, source-time identity, expiry, native withdrawal and promoted-copy inheritance through public prepare/save transaction ports. Polling retains only source-free authority/attempt metadata. See [the installed contract](../monitoring.md#gated-periodic-live-recent-x) for limits, interface and external prerequisites.
