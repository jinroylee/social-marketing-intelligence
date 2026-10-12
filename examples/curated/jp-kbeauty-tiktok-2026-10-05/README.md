# Korean cushion content in Japanese TikTok: local development sample

`observations.json` is a **fixed, real-world public-page snapshot**, not synthetic data and not a live source. It contains 19 individually verified TikTok videos from 17 accounts, captured on 2026-10-05 UTC through the existing `tiktok-web` adapter. The 19 posts cover APRILSKIN Hero Cushion (6), another APRILSKIN cushion (1), and cushions from TIRTIR (3), HERA (3), CLIO (2), WAKEMAKE (3), and fwee (1). One APRILSKIN URL was supplied by the builder; the others were discovered through public search results and verified on their direct TikTok video pages. Two additional candidate URLs did not resolve and were excluded.

The JSON file is the stable offline input for ontology, retrieval, and agent experiments. Each record carries a direct source URL, platform post and author IDs, handle, publication and capture times, public caption, and the four public engagement counts actually returned by TikTok. The `curation` object contains simple development labels: brand/product context assigned from the visible post, literal `#PR` and `Qoo10` marker checks, and a Japanese-script check. Those labels are **not** proof of paid sponsorship, audience location, campaign participation, product sales, or market performance. Counts are a point-in-time observation, not a longitudinal series.

The sample is hand-selected and spans posts from 2023 through 2026. It is suitable for testing parsing, provenance, evidence-backed summaries, and missing-data behavior. It is not a representative Japan-market sample, a recent-post history for any creator, or a basis for ranking creator performance. Profile follower counts, audience geography, impressions, conversions, sales, and the contents of the videos themselves are absent. The snapshot does not contain media files or raw page HTML.

The three manifests are the live source inputs that produced this snapshot. All three completed with one HTTP 200 per selected video, 19 applied observations, zero quarantines and zero unresolved identities. The local canonical database now contains these records under `tiktok / web:public`. The completed run IDs are included in `observations.json`. To collect a **new** snapshot from the same URLs after a database reset or on another date, run:

Two earlier attempts with the CLI's default **total-run** 1 MiB byte budget stopped after recording the first two APRILSKIN posts. Those extra same-day measurements remain in the local database; `observations.json` includes only the three completed runs, so use its run IDs for a fixed baseline.

```bash
docker compose up -d --wait postgres
uv run smi-ingest migrate
uv run smi-ingest ingest examples/curated/jp-kbeauty-tiktok-2026-10-05/aprilskin-manifest.json --max-requests 10 --max-bytes 8388608
uv run smi-ingest ingest examples/curated/jp-kbeauty-tiktok-2026-10-05/direct-competitors-manifest.json --max-requests 10 --max-bytes 8388608
uv run smi-ingest ingest examples/curated/jp-kbeauty-tiktok-2026-10-05/adjacent-cushions-manifest.json --max-requests 10 --max-bytes 8388608
```

These commands use the live web and may produce different counts or unavailable pages. Reading `observations.json` requires no network and reproduces the captured 2026-10-05 observations. For one canonical record in the current database:

```bash
uv run smi-ingest inspect tiktok web:public content 7632620458235530504
```
