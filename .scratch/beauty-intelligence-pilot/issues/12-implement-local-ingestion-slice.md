# Implement the local source-to-canonical ingestion slice

Label: wayfinder:task
Type: task
Mode: AFK
Status: resolved
Assignee: Codex
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: 04

## Question

Build and verify the approved local acquisition foundation: two synthetic source formats enter through collectors and source-specific mappers, retained raw observations support replay, and a shared PostgreSQL canonical writer records identity, provenance, and metric history.

This is execution within the map at the builder's explicit request on 2026-09-29. The builder deleted the former implementation plan and does not want the uninstalled plugin or its workflow. Follow the [approved source-to-canonical design](../source-to-canonical-design.md), using ordinary implementation judgment. Do not recreate the deleted plan, require TikTok API credentials, or claim fixture data is live evidence.

## Completion evidence

A runnable local CLI/demo and tests showing JSON and HTML inputs converge on compatible canonical identities, safe replay, provenance, refresh history, bounded/partial runs, and explicit unknowns. Document exact commands and any limitations. Link the code and verification result in the answer when resolved.

## Answer

Implemented the approved local slice on 2026-09-29. The runnable entry point is [the local CLI](../../../src/smi_ingestion/cli.py), using [the shared contracts](../../../src/smi_ingestion/contracts.py), [source adapters](../../../src/smi_ingestion/adapters/registry.py), [raw evidence store](../../../src/smi_ingestion/evidence.py), [canonical writer and reader](../../../src/smi_ingestion/canonical.py), and [runner](../../../src/smi_ingestion/runner.py). [README](../../../README.md) gives setup and demo commands. The source examples are visibly synthetic and isolated from the supplied real TikTok URL.

Verification: `uv run pytest -q` passed **26 tests** against local PostgreSQL 16. A separate fresh schema was migrated using the actual CLI; ingesting JSON and HTML produced one content identity and two dated metric observations; ordinary inspection hid synthetic data; replay reported `duplicate` and left the observation count unchanged. The fresh demo schema was removed after verification. Local Markdown links were checked. No actual TikTok source was accessed, and no provider eligibility or API cost was established.

The collector interface currently accepts one raw observation per bounded call; an API page can be represented as one raw observation with a mapper that emits several candidates. A future live connector must validate permissions, response format, identity namespace, limits, and retention independently. Discovery, campaign measurement, and the marketer brief remain later parts of this map.
