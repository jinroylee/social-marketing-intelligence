# Social Marketing Intelligence

A local evidence-backed workspace for market investigation and internal campaign decisions. It preserves source provenance and current permissions across knowledge queries, campaign recommendations, approved acquisition tasks and independent monitoring.

Start with the **[complete user and operator guide](docs/user-guide.md)** for every implemented workflow, exact commands and Python entry points, IDs to retain, execution/recovery steps and how each feature reaches storage. The [documentation index](docs/README.md) links architecture, all physical ERDs, requirements, owner contracts and durable ADRs. The [roadmap](docs/roadmap.md) distinguishes installed software from live/human readiness and future capabilities.

## Quickstart

Prerequisites: Python 3.12+, `uv`, and Docker with Compose (or an existing development PostgreSQL instance). From the repository root:

```bash
docker compose up -d --wait postgres
uv sync --locked
uv run --locked smi-ingest migrate
uv run --locked smi-ingest import-snapshot examples/curated/jp-kbeauty-tiktok-2026-10-05/snapshot-manifest.json
uv run --locked smi-ingest register-catalog examples/catalogs/beauty-v1.json
uv run --locked smi-review --actor local-marketer
```

Open <http://127.0.0.1:8765>. This imports a fixed offline sample of 19 posts from 17 accounts captured on 2026-10-05; no provider/model request is made. In the browser, create a brief and prepare a frozen comparison or independent investigation. Literal interpretations remain provisional; audience geography, contracts, sales and full account histories remain unknown.

For current-KB search, recommendations or answers, explicitly prepare/publish the intended support using the guide's **[complete offline walkthrough](docs/user-guide.md#4-offline-smoke-walkthrough)**. Import, knowledge preparation and publication have separate IDs. Model answers/ranking require trusted Python configuration; a key in an env file alone enables nothing.

Compose starts **PostgreSQL only**, on host `127.0.0.1:6543`; it does not launch a web service, task consumer or scheduler. `smi-review` is a separate loopback host process. Submitted tasks return `task_id` before collection; execute each through `smi-ingest run-offline-task TASK_ID`. Keyword due ticks and recent-X polling are separately invoked operations. See [start/stop/restart and environment settings](docs/user-guide.md#2-install-configure-start-and-stop).

`SMI_DATABASE_URL`, optional existing `SMI_DATABASE_SCHEMA` and `SMI_EVIDENCE_DIR` configure the application. Entry points read the process environment; use `uv run --env-file .env ...` explicitly if needed. The default local database password is a development placeholder. Keep actual credentials outside committed files. Ctrl-C stops the server; `docker compose stop postgres` stops PostgreSQL while preserving its volume.

## Verify

```bash
uv run --locked python tools/check.py --static
docker compose up -d --wait postgres
uv run --locked python tools/check.py
```

The shared local/CI checks cover lint, documentation consistency and PostgreSQL tests in isolated temporary schemas. Tests select `SMI_TEST_DATABASE_URL` separately from the application DSN. See [verification and troubleshooting](docs/user-guide.md#25-check-build-and-troubleshoot) and [development prerequisites](docs/development.md).

Live sources/model execution are independently gated and unverified for operational readiness. Actual named human language/marketer validation remains pending. [Source integrations](docs/source-integrations.md), [cost controls](docs/costs.md) and [evaluation](docs/evaluation.md) define those boundaries; technical tests do not establish live access, source-use permission, semantic accuracy or business value.
