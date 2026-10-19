# Ticket 01: ingestion completion and safe resume

Status: implemented locally; ticket remains claimed pending integration validation.

## Change and interface

`EvidenceStore.save(..., *, complete: bool = False, connection=None)` now accepts the final-input marker already passed by `IngestionRunner.resume`. The default preserves callers such as `SnapshotImporter` that omit it. Existing SQL saves observation metadata, checkpoint, usage counters and completion in the same transaction. Caller-owned connections retain commit/rollback authority and payload cleanup after rollback. No schema migration or new module was required; the existing physical completion column is now shown in the ERD and the operational contract is documented in `docs/architecture.md`.

## Red and green evidence

- Red: `UV_OFFLINE=1 uv run --locked pytest -q tests/test_pipeline.py -k 'resume_final_capture_at_limit or resume_maps_durably_saved_observation'` produced **3 failed, 28 deselected**. The default caller raised `NameError: name 'complete' is not defined`; request/record-limit final capture cases raised `TypeError: EvidenceStore.save() got an unexpected keyword argument 'complete'`.
- Green after the focused signature repair: the same command produced **3 passed, 28 deselected**.
- Added public-operation coverage confirms both request/record-limit final captures resume twice without another collector call or duplicate metric, an interrupted nonfinal capture keeps its original observation and continues from the checkpoint, and an outer transaction atomically commits or rolls back the observation, checkpoint, counters and completion marker. Reads through `EvidenceStore` remain unchanged while the caller transaction is uncommitted.
- `UV_OFFLINE=1 uv run --locked pytest -q tests/test_pipeline.py`: **34 passed**. This includes existing legacy migration, retained replay, committed transient derivation and policy scenarios.
- `UV_OFFLINE=1 uv run --locked python tools/check.py`: **passed**, including Ruff, documentation links, physical ERD coverage, relative instruction symlinks, PostgreSQL preflight and **209 passed** pytest cases in 141.81 seconds.
- `git diff --check`: passed. No genuine blocker remains.

## Scope

Tests use the real temporary-schema PostgreSQL fixture and local synthetic collection. No real external/provider/model calls, push or PR occurred. The branch incorporated integration commit `e3711cf` before completion. No later ticket was claimed or implemented. Integration validation and ticket resolution belong to the merger.
