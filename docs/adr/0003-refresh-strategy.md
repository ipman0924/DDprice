# ADR-0003: Nightly truncate-and-load with backup-swap for crash safety

Status: **Superseded by [ADR-0009](0009-refresh-via-github-actions.md)** — refresh runs in GitHub Actions, not on a persistent server. Truncate+load is no longer meaningful; the new model is "generate a data file and commit it."
Date: 2026-08-18

## Context

The DD feed is a full daily snapshot (~19 MB, ~102k rows). We need a strategy for pulling it and updating the live table each night. Options considered:

- **Atomic swap** — load into shadow table, validate, rename. Zero downtime, safe on crash.
- **Truncate + load** — wipe live table, insert new rows. Users see partial/empty data during the load window.
- **Incremental upsert** — diff by StockCode, only touch changed rows. More complex; useful for change history.

## Decision

Use **truncate + load with a backup-swap safety net**, run once at **00:00 Australia/Sydney** time. DD publish the feed on a daily cadence, aligning with this window.

Pipeline steps:

1. Download CSV to a temp file (see [ADR-0004](0004-failure-handling.md) for retries).
2. **Rename `feed` → `feed_backup`** (fast metadata operation).
3. Create empty `feed` table with the correct schema.
4. Stream-parse the CSV, insert rows in batches.
5. Validate: row count within expected range (e.g. ≥ 50k), no NULL StockCodes.
6. On success: drop `feed_backup`.
7. On any failure between step 2 and 6: drop `feed`, rename `feed_backup` → `feed`.

The user's app is expected to be unused around midnight AEST, so the visible gap during load is acceptable. The backup-swap ensures a mid-load crash does not leave the app with broken data.

## Consequences

- **Simple and easy to reason about.** No shadow tables or view indirection.
- **Backup step is O(rename) — effectively free.** No 2× storage duration issue.
- **Recovery is manual-free** — the pipeline restores itself on crash.
- **Trade-off accepted:** users hitting the app during the ~1–2 minute load window at midnight see empty or partial data. This is a business decision by the owner.

## Rejected: atomic swap

Rejected in favor of implementation simplicity. Backup-swap gets us most of the safety benefit without needing a view layer or dual-table naming discipline.

## Rejected: incremental upsert

No requirement for change history at this stage. Would add complexity with no matching benefit.
