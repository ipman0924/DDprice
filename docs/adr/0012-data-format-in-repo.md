# ADR-0012: Store the daily data in the repo as Parquet, not CSV

Status: Accepted
Date: 2026-08-18

## Context

The GitHub Actions workflow ([ADR-0009](0009-refresh-via-github-actions.md)) commits a daily snapshot of the DD feed to the repo. Options:

- **Commit raw CSV** — ~19 MB/day, ~7 GB/year of git history if uncompressed.
- **Commit Parquet** — same data at ~2–4 MB (columnar compression), and pandas reads it 5–10× faster than CSV.
- **Use Git LFS** — solves the size issue but adds an LFS budget line and slight friction on clone.
- **Commit to a data-only orphan branch** — keeps `main` git history small; slightly weirder to reason about.

## Decision

**Commit as `data/feed.parquet`** to `main`, alongside `data/meta.json` (small — includes `refreshed_at`, row count, and source file hash).

Rationale:

- **~5× smaller than CSV** at this data. Repo growth over a year is manageable (< 2 GB).
- **~10× faster to load** than CSV in pandas — noticeably better cold start.
- **No LFS setup.**
- **Parquet is boring, well-supported, and self-describing** (schema in the file).

To keep repo size in check longer-term, the workflow **overwrites `data/feed.parquet` rather than accumulating dated files.** Each daily commit replaces the previous snapshot; the *history* preserves what previous snapshots looked like if someone ever wants to reconstruct. If a user later wants historical price/stock trends, that's a separate feature (a small orphan branch of dated snapshots would be the answer).

## Consequences

- **`app.py` reads with `pd.read_parquet("data/feed.parquet")`** — one line.
- **Fast cold start**: Parquet read + cached DataFrame is well under 1 second at this size.
- **The raw CSV is not committed** to avoid duplicating data. If someone needs the original CSV, GitHub Actions can attach it as a workflow artifact (retained 90 days) for spot-checks.
- **Downside:** you cannot `cat data/feed.parquet` to eyeball the data — you need a tool (pandas, DuckDB, `parquet-tools`). Acceptable given the audience.
